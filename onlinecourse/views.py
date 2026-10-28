from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponseForbidden, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View

from .models import Course, Lesson, Enrollment, Question, Choice, Submission


def index(request):
    courses = Course.objects.all().order_by('id')

    return render(
        request,
        'onlinecourse/course_list_bootstrap.html',
        {
            'course_list': courses,
            'courses': courses,
        }
    )


def registration_request(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        if not username or not password:
            messages.error(request, 'Username and password are required.')
            return render(request, 'onlinecourse/registration.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'onlinecourse/registration.html')

        user = User.objects.create_user(
            username=username,
            first_name=request.POST.get('first_name', ''),
            last_name=request.POST.get('last_name', ''),
            password=password,
        )
        login(request, user)
        messages.success(request, f'Account created for {username}!')
        return redirect('onlinecourse:index')

    return render(request, 'onlinecourse/registration.html')


def course_details(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    lessons = course.lessons.all().prefetch_related('questions__choices')

    is_enrolled = False

    if request.user.is_authenticated:
        is_enrolled = Enrollment.objects.filter(
            user=request.user,
            course=course
        ).exists()

    return render(
        request,
        'onlinecourse/course_details_bootstrap.html',
        {
            'course': course,
            'lessons': lessons,
            'is_enrolled': is_enrolled,
        }
    )


class CourseDetailsView(View):
    template_name = 'onlinecourse/course_details_bootstrap.html'

    def get(self, request, course_id):
        course = get_object_or_404(Course, pk=course_id)
        lessons = course.lessons.all().prefetch_related('questions__choices')

        is_enrolled = False

        if request.user.is_authenticated:
            is_enrolled = Enrollment.objects.filter(
                user=request.user,
                course=course
            ).exists()

        return render(
            request,
            self.template_name,
            {
                'course': course,
                'lessons': lessons,
                'is_enrolled': is_enrolled,
            }
        )


@login_required
def enroll(request, course_id):
    course = get_object_or_404(Course, pk=course_id)

    Enrollment.objects.get_or_create(
        user=request.user,
        course=course,
        defaults={'mode': Enrollment.AUDIT}
    )

    return redirect(
        'onlinecourse:course_details',
        course_id=course.id
    )


@login_required
def submit(request, course_id):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    course = get_object_or_404(Course, pk=course_id)

    enrollment, _ = Enrollment.objects.get_or_create(
        user=request.user,
        course=course,
        defaults={'mode': Enrollment.AUDIT}
    )

    # Get questions associated with this course through its lessons
    lesson_questions = Question.objects.filter(
        lesson__course=course
    )

    # Also include questions directly associated with the course
    course_questions = Question.objects.filter(
        courses=course
    )

    questions = (
        lesson_questions | course_questions
    ).distinct().order_by('order', 'id')

    question_ids = set(questions.values_list('id', flat=True))

    valid_choices = Choice.objects.filter(
        question_id__in=question_ids
    ).select_related('question')

    valid_choice_map = {
        choice.id: choice
        for choice in valid_choices
    }

    selected_ids = set()

    # Handle radio buttons or checkboxes named choice_<question_id>
    for key, values in request.POST.lists():
        if key.startswith('choice_'):
            for value in values:
                if str(value).isdigit():
                    selected_ids.add(int(value))

    # Handle other common form field names
    for key in (
        'choice',
        'choices',
        'selected_choice',
        'selected_choices'
    ):
        for value in request.POST.getlist(key):
            if str(value).isdigit():
                selected_ids.add(int(value))

    # Handle checkbox fields whose names are choice IDs
    for key, values in request.POST.lists():
        if key.isdigit():
            if any(
                value in ('on', '1', 'true', 'True')
                for value in values
            ):
                selected_ids.add(int(key))

    # Ignore choices that do not belong to questions in this course
    selected_choices = [
        valid_choice_map[choice_id]
        for choice_id in selected_ids
        if choice_id in valid_choice_map
    ]

    choices_by_question = {}

    for choice in selected_choices:
        choices_by_question.setdefault(
            choice.question_id, []
        ).append(choice)

    last_submission = None

    # Save one submission per question, including unanswered questions
    for question in questions:
        question_choices = choices_by_question.get(
            question.id, []
        )

        submission, _ = Submission.objects.update_or_create(
            user=request.user,
            question=question,
            defaults={
                'enrollment': enrollment,
                'choice': (
                    question_choices[0]
                    if question_choices
                    else None
                ),
            }
        )

        submission.choices.set(question_choices)
        last_submission = submission

    if last_submission:
        return redirect(
            'onlinecourse:show_exam_result',
            course_id=course.id,
            submission_id=last_submission.id
        )

    return redirect(
        'onlinecourse:show_exam_result_course',
        course_id=course.id
    )


@login_required
def show_exam_result(request, course_id, submission_id=None):
    course = get_object_or_404(Course, pk=course_id)

    lesson_questions = Question.objects.filter(
        lesson__course=course
    )

    course_questions = Question.objects.filter(
        courses=course
    )

    questions = (
        lesson_questions | course_questions
    ).distinct().order_by('order', 'id')

    # Ensure the requested submission belongs to the current user
    if submission_id is not None:
        target_submission = get_object_or_404(
            Submission,
            pk=submission_id
        )

        if (
            target_submission.user_id != request.user.id
            and not request.user.is_staff
        ):
            return HttpResponseForbidden(
                'You are not allowed to view this result.'
            )

        # Prevent a submission from being used with the wrong course
        if target_submission.enrollment_id:
            if target_submission.enrollment.course_id != course.id:
                return HttpResponseForbidden(
                    'This result does not belong to this course.'
                )

        elif target_submission.question_id:
            question_belongs_to_course = (
                target_submission.question.lesson.course_id == course.id
                or target_submission.question.courses.filter(
                    pk=course.id
                ).exists()
            )

            if not question_belongs_to_course:
                return HttpResponseForbidden(
                    'This result does not belong to this course.'
                )

    user_submissions = Submission.objects.filter(
        user=request.user,
        question__in=questions
    ).select_related(
        'question',
        'choice'
    ).prefetch_related(
        'choices'
    )

    submission_map = {
        submission.question_id: submission
        for submission in user_submissions
    }

    results = []
    total_score = 0
    total_marks = 0
    correct_count = 0

    for question in questions:
        submission = submission_map.get(question.id)

        selected_choices = []

        if submission:
            selected_choices = list(
                submission.choices.all()
            )

            # Support submissions stored using only the single-choice FK
            if not selected_choices and submission.choice_id:
                selected_choices = [submission.choice]

        selected_ids = [
            choice.id for choice in selected_choices
        ]

        is_correct = question.is_get_score(selected_ids)
        marks = question.grade or 0
        score = marks if is_correct else 0

        total_marks += marks
        total_score += score

        if is_correct:
            correct_count += 1

        results.append({
            'question': question,
            'answered': bool(selected_choices),
            'selected_choice': (
                selected_choices[0]
                if selected_choices
                else None
            ),
            'selected_choices': selected_choices,
            'choices': question.choices.all(),
            'is_correct': is_correct,
            'grade': marks,
            'score': score,
        })

    percentage = (
        (total_score / total_marks) * 100
        if total_marks
        else 0
    )

    passed = percentage >= 70
    unanswered_count = sum(
        not result['selected_choices']
        for result in results
    )
    incorrect_count = len(results) - correct_count - unanswered_count

    context = {
        'course': course,
        'results': results,
        'total_questions': len(results),
        'unanswered_count': unanswered_count,
        'incorrect_count': incorrect_count,
        'earned_score': total_score,
        'total_score': total_marks,
        'total_marks': total_marks,
        'score': total_score,
        'percentage': percentage,
        'passed': passed,
        'is_passed': passed,
        'correct_count': correct_count,
        'passing_threshold': 70,
        'message': (
            'You passed the exam.'
            if passed
            else 'Exam Attempt Failed. Please review the questions and try again.'
        ),
        'submission_id': submission_id,
    }

    return render(
        request,
        'onlinecourse/show_exam_result_bootstrap.html',
        context
    )


@login_required
def show_exam_result_course(request, course_id):
    return show_exam_result(
        request,
        course_id
    )
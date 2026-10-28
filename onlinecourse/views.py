from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponseForbidden, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from .models import Course, Enrollment, Question, Choice, Submission


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


def get_course_questions(course):
    """
    Return questions associated with a course through its lessons
    or through the Question.courses many-to-many relationship.
    """
    lesson_questions = Question.objects.filter(
        lesson__course=course
    )

    course_questions = Question.objects.filter(
        courses=course
    )

    return (
        lesson_questions | course_questions
    ).distinct().order_by('order', 'id')


def course_details(request, course_id):
    course = get_object_or_404(Course, pk=course_id)

    lessons = course.lessons.all().prefetch_related(
        'questions__choices'
    )

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
        return course_details(request, course_id)


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

    questions = get_course_questions(course)

    question_ids = set(
        questions.values_list('id', flat=True)
    )

    valid_choices = Choice.objects.filter(
        question_id__in=question_ids
    ).select_related('question')

    valid_choice_map = {
        choice.id: choice
        for choice in valid_choices
    }

    selected_ids = set()

    # Handle fields such as choice_1=5
    for key, values in request.POST.lists():
        if key.startswith('choice_'):
            for value in values:
                if str(value).isdigit():
                    selected_ids.add(int(value))

    # Handle alternative common form field names
    for key in (
        'choice',
        'choices',
        'selected_choice',
        'selected_choices'
    ):
        for value in request.POST.getlist(key):
            if str(value).isdigit():
                selected_ids.add(int(value))

    # Handle checkbox fields named using choice IDs
    for key, values in request.POST.lists():
        if key.isdigit():
            if any(
                value in ('on', '1', 'true', 'True')
                for value in values
            ):
                selected_ids.add(int(key))

    # Ignore invalid choice IDs and choices outside this course
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

    # Save one submission for each question, including unanswered ones.
    # update_or_create prevents duplicate submissions for the same
    # user and question when the exam is submitted again.
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

    questions = get_course_questions(course)

    # Verify ownership and course association when a submission ID
    # is supplied in the URL.
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

        if target_submission.enrollment_id:
            if target_submission.enrollment.course_id != course.id:
                return HttpResponseForbidden(
                    'This result does not belong to this course.'
                )

        elif target_submission.question_id:
            target_question = target_submission.question

            belongs_to_course = (
                target_question.lesson.course_id == course.id
                or target_question.courses.filter(
                    pk=course.id
                ).exists()
            )

            if not belongs_to_course:
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

            # Support submissions stored in the single-choice field.
            if not selected_choices and submission.choice_id:
                selected_choices = [submission.choice]

        selected_ids = [
            choice.id for choice in selected_choices
        ]

        # Use the model's scoring method to check the answer.
        is_correct = question.is_get_score(selected_ids)

        marks = question.grade or 0
        score = marks if is_correct else 0

        total_marks += marks
        total_score += score

        if is_correct:
            correct_count += 1

        results.append({
            'question': question,
            'selected_choice': (
                selected_choices[0]
                if selected_choices
                else None
            ),
            'selected_choices': selected_choices,
            'choices': question.choices.all(),
            'is_correct': is_correct,
            'answered': bool(selected_choices),
            'grade': marks,
            'score': score,
        })

    total_questions = len(results)

    incorrect_count = sum(
        1
        for item in results
        if item['answered'] and not item['is_correct']
    )

    unanswered_count = sum(
        1
        for item in results
        if not item['answered']
    )

    percentage = (
        (total_score / total_marks) * 100
        if total_marks
        else 0
    )

    percentage = round(percentage, 2)
    passing_threshold = 70
    passed = percentage >= passing_threshold

    if passed:
        message = 'You have successfully passed the examination!'
    else:
        message = (
            'Exam Attempt Failed. You did not reach the passing score. '
            'Please review your answers and try again.'
        )

    context = {
        'course': course,
        'results': results,

        # Score information
        'total_score': total_marks,
        'total_marks': total_marks,
        'earned_score': total_score,
        'score': total_score,
        'percentage': percentage,

        # Question statistics
        'total_questions': total_questions,
        'correct_count': correct_count,
        'incorrect_count': incorrect_count,
        'unanswered_count': unanswered_count,

        # Pass/fail information
        'passed': passed,
        'is_passed': passed,
        'passing_threshold': passing_threshold,
        'message': message,

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
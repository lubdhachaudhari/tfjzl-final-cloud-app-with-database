from django.conf import settings
from django.db import models
from django.utils.timezone import now


class Instructor(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    full_time = models.BooleanField(default=True)
    total_learners = models.IntegerField(default=0)

    def __str__(self):
        if self.user:
            return f"Instructor: {self.user.username}"
        return f"Instructor #{self.id}"


class Learner(models.Model):
    STUDENT = 'student'
    DEVELOPER = 'developer'
    DATA_SCIENTIST = 'data_scientist'
    DATABASE_ADMIN = 'dba'

    OCCUPATION_CHOICES = [
        (STUDENT, 'Student'),
        (DEVELOPER, 'Developer'),
        (DATA_SCIENTIST, 'Data Scientist'),
        (DATABASE_ADMIN, 'Database Admin'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    occupation = models.CharField(
        max_length=20,
        choices=OCCUPATION_CHOICES,
        default=STUDENT
    )
    social_link = models.URLField(max_length=200, blank=True)

    def __str__(self):
        name = self.user.username if self.user else f"#{self.id}"
        return f"{name}, {self.occupation}"


class Course(models.Model):
    name = models.CharField(max_length=200, default="Online Course")
    image = models.ImageField(
        upload_to='course_images/',
        blank=True,
        null=True
    )
    description = models.TextField(max_length=2000, blank=True)
    pub_date = models.DateField(null=True, blank=True, default=now)
    instructors = models.ManyToManyField(Instructor, blank=True)
    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='Enrollment',
        blank=True,
        related_name='enrolled_courses'
    )
    total_enrollment = models.IntegerField(default=0)

    def __str__(self):
        return f"Course: {self.name}"


class Lesson(models.Model):
    title = models.CharField(max_length=200, default="Lesson Title")
    order = models.IntegerField(default=0)
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='lessons'
    )
    content = models.TextField(blank=True)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.course.name} - Lesson: {self.title}"


class Enrollment(models.Model):
    AUDIT = 'audit'
    HONOR = 'honor'
    VERIFIED = 'verified'

    COURSE_MODES = [
        (AUDIT, 'Audit'),
        (HONOR, 'Honor'),
        (VERIFIED, 'Verified'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    date_enrolled = models.DateField(default=now)
    mode = models.CharField(
        max_length=20,
        choices=COURSE_MODES,
        default=AUDIT
    )
    rating = models.FloatField(default=5.0)

    class Meta:
        unique_together = ('user', 'course')

    def __str__(self):
        return f"Enrollment: {self.user.username} in {self.course.name}"


class Question(models.Model):
    SINGLE = 'single'
    MULTIPLE = 'multiple'

    QUESTION_TYPES = [
        (SINGLE, 'Single Choice'),
        (MULTIPLE, 'Multiple Choice'),
    ]

    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='questions'
    )
    question_text = models.CharField(max_length=1000)
    question_type = models.CharField(
        max_length=20,
        choices=QUESTION_TYPES,
        default=SINGLE
    )
    grade = models.IntegerField(default=1)
    order = models.IntegerField(default=0)
    courses = models.ManyToManyField(
        Course,
        blank=True,
        related_name='questions'
    )

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"Q{self.id}: {self.question_text[:50]}"

    @property
    def choice_set(self):
        return self.choices

    def is_get_score(self, selected_ids):
        if not selected_ids:
            return False

        if isinstance(selected_ids, (int, str)):
            try:
                selected_ids = [int(selected_ids)]
            except (TypeError, ValueError):
                return False
        else:
            selected_ids = [
                int(value)
                for value in selected_ids
                if str(value).isdigit()
            ]

        correct_ids = set(
            self.choices.filter(is_correct=True).values_list(
                'id', flat=True
            )
        )

        if not correct_ids:
            return False

        return set(selected_ids) == correct_ids


class Choice(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='choices'
    )
    choice_text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        status = "Correct" if self.is_correct else "Incorrect"
        return f"Choice: {self.choice_text} [{status}]"

    @property
    def text(self):
        return self.choice_text

    @property
    def content(self):
        return self.choice_text


class Submission(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='submissions'
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='submissions',
        null=True,
        blank=True
    )
    choice = models.ForeignKey(
        Choice,
        on_delete=models.CASCADE,
        related_name='submissions',
        null=True,
        blank=True
    )
    enrollment = models.ForeignKey(
        Enrollment,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='submissions'
    )
    choices = models.ManyToManyField(
        Choice,
        blank=True,
        related_name='multi_submissions'
    )
    submitted_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-submitted_at', 'id']
        unique_together = ('user', 'question')

    def __str__(self):
        question_id = self.question_id if self.question_id else "All"
        choice_id = self.choice_id if self.choice_id else "Multi"
        return (
            f"Submission by {self.user.username} "
            f"for Q{question_id} Choice {choice_id}"
        )
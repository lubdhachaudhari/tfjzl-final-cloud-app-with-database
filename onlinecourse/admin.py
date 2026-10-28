from django.contrib import admin
from .models import (
    Course,
    Lesson,
    Instructor,
    Learner,
    Question,
    Choice,
    Submission,
)


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 2

class QuestionInline(admin.StackedInline):
    model = Question
    extra = 2


class QuestionAdmin(admin.ModelAdmin):
    list_display = ('question_text', 'lesson', 'grade')
    inlines = [ChoiceInline]


class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order')
    list_filter = ('course',)
    inlines = [QuestionInline]

class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'pub_date', 'total_enrollment')
    list_filter = ('pub_date',)
    search_fields = ('name',)


class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('id', 'enrollment')
    list_filter = ('enrollment',)


class InstructorAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'full_time', 'total_learners')


class LearnerAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'occupation')


admin.site.register(Course, CourseAdmin)
admin.site.register(Lesson, LessonAdmin)
admin.site.register(Instructor, InstructorAdmin)
admin.site.register(Learner, LearnerAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Choice)
admin.site.register(Submission, SubmissionAdmin)
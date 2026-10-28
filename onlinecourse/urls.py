from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'onlinecourse'

urlpatterns = [
    path('', views.index, name='index'),

    path(
        'course/<int:course_id>/',
        views.course_details,
        name='course_details'
    ),

    path(
        'course/<int:course_id>/enroll/',
        views.enroll,
        name='enroll'
    ),

    path(
        'course/<int:course_id>/submit/',
        views.submit,
        name='submit'
    ),

    path(
        'course/<int:course_id>/result/',
        views.show_exam_result,
        name='show_exam_result_course'
    ),

    path(
        'course/<int:course_id>/submission/<int:submission_id>/result/',
        views.show_exam_result,
        name='show_exam_result'
    ),

    path(
        'course/<int:course_id>/exam_result/',
        views.show_exam_result_course,
        name='exam_result_course'
    ),

    path(
        'course/<int:course_id>/exam_result/<int:submission_id>/',
        views.show_exam_result,
        name='exam_result'
    ),

    path(
        'login/',
        auth_views.LoginView.as_view(
            template_name='onlinecourse/login.html'
        ),
        name='login'
    ),

    path(
        'logout/',
        auth_views.LogoutView.as_view(
            next_page='onlinecourse:index'
        ),
        name='logout'
    ),

    path(
        'registration/',
        views.registration_request,
        name='registration'
    ),
]
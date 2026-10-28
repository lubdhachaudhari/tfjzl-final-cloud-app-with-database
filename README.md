
# IBM Full Stack Software Developer: Django Online Course & Mock Examination System

A comprehensive, fully functional Django web application developed for the IBM Full Stack Software Developer / Back-End Developer curriculum on Coursera (*Django Application Development with SQL and Databases*).

This project implements an online course learning platform with an interactive mock examination engine, score calculation algorithms, user authentication, and advanced Django Administration with inline configurations.



## Table of Contents
1. [Key Features](#key-features)
2. [Project Architecture & Directory Structure](#project-architecture--directory-structure)
3. [Technology Stack](#technology-stack)
4. [Installation & Setup](#installation--setup)
5. [Database Migrations & Development Sample Data](#database-migrations--development-sample-data)
6. [Running the Application](#running-the-application)
7. [Running Tests](#running-tests)
8. [Django Admin Portal & Screenshot Verification](#django-admin-portal--screenshot-verification)
9. [Examination Engine & Result Verification](#examination-engine--result-verification)
10. [GitHub Deployment & Workflow](#github-deployment--workflow)

## 1. Key Features

- **Course Catalog & Lesson Navigation:** Browse courses, view lesson syllabi in collapsible accordion components, and track enrollment metrics.
- **Mock Examination System:**
  - Automated question evaluation supporting single-choice questions.
  - Radio button inputs with CSRF protection.
  - Strict validation against question-choice associations.
  - Idempotent submission tracking prevents score inflation upon retakes.
- **Detailed Examination Performance Reports:**
  - Pass/Fail evaluation based on a consistent 70% threshold.
  - "Congratulations" greeting with trophy badge upon successful completion.
  - Summary metrics: total questions, correct answers, incorrect answers, raw score, and percentage.
  - Question-by-question review with color-coded feedback (green checkmark for correct answers, red for incorrect selections).
  - Strict privacy protections preventing students from viewing other users' private exam reports.
- **Customized Django Administration:**
  - `LessonAdmin` with nested `QuestionInline` (`admin.StackedInline`).
  - `QuestionAdmin` with nested `ChoiceInline` (`admin.TabularInline`).
  - Full model registration across both Authentication & Authorization and OnlineCourse modules.



## 2. Project Architecture & Directory Structure

```
coursera-django-final/
├── manage.py
├── 03-admin-site.jpeg            # Genuine screenshot of Django administration portal
├── 07-final.jpeg                 # Genuine screenshot of successful exam result page
├── .gitignore
├── README.md
├── myproject/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── onlinecourse/
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py                # Course, Lesson, Instructor, Learner, Question, Choice, Submission, Enrollment
│   ├── admin.py                 # QuestionInline, ChoiceInline, QuestionAdmin, LessonAdmin, CourseAdmin
│   ├── views.py                 # CourseListView, CourseDetailsView, enroll, submit, show_exam_result, auth views
│   ├── urls.py                  # submit, show_exam_result, course_details, index, auth routes
│   ├── tests.py                 # Comprehensive Django test suite (13 test cases)
│   ├── migrations/
│   │   ├── __init__.py
│   │   └── 0001_initial.py
│   ├── management/
│   │   └── commands/
│   │       ├── __init__.py
│   │       └── setup_sample_data.py
│   └── templates/
│       └── onlinecourse/
│           ├── base.html
│           ├── course_details_bootstrap.html  # Exact required course detail template
│           ├── show_exam_result_bootstrap.html # Exact required exam result template
│           ├── course_list_bootstrap.html
│           ├── login.html
│           └── registration.html
└── scripts/
    └── take_screenshots.py      # Automated headless screenshot verification runner
```



## 3. Technology Stack

- **Python:** 3.10+ (tested on Python 3.14)
- **Framework:** Django 5.x / 6.x
- **Database:** SQLite3 (standard for local development)
- **Frontend:** HTML5, CSS3, Bootstrap 5.3, Bootstrap Icons
- **Version Control:** Git & GitHub
## 4. Installation & Setup

### Prerequisites
- Python 3.10 or higher installed.
- Git installed.

### Step 1: Clone the Repository
```bash
git clone https://github.com/<your-username>/<your-repo-name>.git
cd coursera-django-final
```

### Step 2: Create and Activate a Virtual Environment
```bash
# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install django pillow
```



## 5. Database Migrations & Development Sample Data

### Apply Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Populate Development Sample Data
The project includes a custom, idempotent management command (`setup_sample_data`) that creates:
- Superuser credentials: `username: admin`, `password: admin123`
- Student credentials: `username: student1`, `password: password123`
- Course: *"Cloud App Development with Django and Databases"*
- Lessons, questions, choices, and correct-answer indicators.

Run the command:
```bash
python manage.py setup_sample_data
```

*(Note: Running this command multiple times will not create duplicate records).*



## 6. Running the Application

Start the Django local development server:
```bash
python manage.py runserver
```

Open your browser and navigate to:
- **Course Portal:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Course Details & Examination:** [http://127.0.0.1:8000/onlinecourse/course/1/](http://127.0.0.1:8000/onlinecourse/course/1/)
- **Django Administration:** [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)



## 7. Running Tests

The application includes an extensive test suite verifying:
- Model relationships and foreign key cascades.
- `Question.is_get_score()` evaluation logic.
- Admin inline configurations (`QuestionInline`, `ChoiceInline`, `LessonAdmin`, `QuestionAdmin`).
- URL route resolution for `submit` and `show_exam_result`.
- Exam submission handling, score calculation, and 70% threshold verification.
- Proper handling of unanswered questions and rejection of invalid choice IDs.
- Privacy authorization checks preventing unauthorized result viewing.
- Template rendering and exact file naming (`course_details_bootstrap.html`).

Run all tests:
```bash
python manage.py test onlinecourse
```



## 8. Django Admin Portal & Screenshot Verification

The administration site organizes models into:
- **Authentication and Authorization:** Groups, Users
- **OnlineCourse:** Choices, Courses, Enrollments, Instructors, Learners, Lessons, Questions, Submissions

![Admin Portal](03-admin-site.jpeg)
*Figure 1: Genuine screenshot of the running Django administration site (`03-admin-site.jpeg`).*


## 9. Examination Engine & Result Verification

Upon submitting the course exam with correct answers, the application calculates the total score, validates the 70% passing threshold, and displays the personalized "Congratulations" banner, performance statistics, and detailed question breakdown.

![Exam Result](07-final.jpeg)
*Figure 2: Genuine screenshot of the real exam result page displaying Congratulations and performance report (`07-final.jpeg`).*



## 10. GitHub Deployment & Workflow

To push this repository to your personal GitHub account:

```bash
# 1. Initialize git (if not already done)
git init
git branch -M main

# 2. Stage and commit all files
git add .
git commit -m "feat: complete IBM Django online course project with exam system and admin inlines"

# 3. Link your remote GitHub repository
git remote add origin https://github.com/<your-username>/<your-repo-name>.git

# 4. Push to GitHub
git push -u origin main
```



## License
Educational project developed under the IBM Full Stack Software Developer program.

# IBM Django Online Course

A Django web application for managing online courses, lessons, and mock examinations.

## Features

- Course and lesson management
- Django administration interface
- Question and choice management
- Mock exam submission
- Exam score calculation and results
- Bootstrap-based user interface

## Technology Stack

- Python
- Django
- SQLite
- HTML and Bootstrap

## Setup

1. Install Python.
2. Install Django:

   `pip install django`

3. Apply database migrations:

   `python manage.py migrate`

4. Create an administrator:

   `python manage.py createsuperuser`

5. Start the development server:

   `python manage.py runserver`

6. Open `http://127.0.0.1:8000/` in your browser.

## Project Status

Development in progress.


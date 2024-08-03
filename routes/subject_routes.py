from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, app
from datetime import datetime

from sqlalchemy.exc import IntegrityError

from models import Subject, Faculty, Schedule, CourseYearLevelSemesterSubject, Course, YearLevel, Semester, Section
from webforms.subject_form import SubjectForm, EditSubjectForm, CourseYearLevelSemesterSubjectForm
from app import db

subject_bp = Blueprint('subject', __name__)


# @subject_bp.route('/')
# def manage_subject():
#     # Fetch all the course, year level, and semester combinations
#     combinations = CourseYearLevelSemesterSubject.query.all()
#     print(combinations)
#     # Group subjects by course, year level, and semester
#     grouped_subjects = {}
#     for combo in combinations:
#         key = (combo.course_id, combo.year_level_id, combo.semester_id)
#         if key not in grouped_subjects:
#             grouped_subjects[key] = []
#         grouped_subjects[key].append(combo.subject)
#
#     # Render the HTML template with the fetched data and models
#     return render_template('subject/manage_subject.html',
#                            grouped_subjects=grouped_subjects,
#                            Course=Course,
#                            YearLevel=YearLevel,
#                            Semester=Semester)


@subject_bp.route("/", methods=["GET", "POST"])
def manage_subjects():
    form = CourseYearLevelSemesterSubjectForm()
    subjects = Subject.query.all()
    courses = Course.query.all()  # Fetch all courses

    selected_course = request.args.get('course', type=int)

    if form.validate_on_submit():
        selected_subjects = request.form.getlist('subjects')  # Get selected subjects
        print("Form is valid")
        print("Selected Subjects:", selected_subjects)

        if not selected_subjects:
            flash('No subjects selected.', 'danger')
            return redirect(url_for('subject.manage_subjects'))

        successful_additions = 0
        duplicate_entries = 0
        same_subject_in_both_semesters = 0

        for subject_id in selected_subjects:
            # Check if the subject already exists for the course and year level in any semester
            existing_subject = CourseYearLevelSemesterSubject.query.filter_by(
                course_id=form.course.data,
                year_level_id=form.year_level.data,
                subject_id=subject_id
            ).first()

            if existing_subject:
                if existing_subject.semester_id != form.semester.data:
                    same_subject_in_both_semesters += 1
                else:
                    duplicate_entries += 1
                continue

            new_detail = CourseYearLevelSemesterSubject(
                course_id=form.course.data,
                year_level_id=form.year_level.data,
                semester_id=form.semester.data,
                subject_id=subject_id,
            )
            db.session.add(new_detail)
            try:
                db.session.commit()
                successful_additions += 1
            except IntegrityError:
                db.session.rollback()
                duplicate_entries += 1

        if successful_additions > 0:
            flash(f'{successful_additions} subject(s) added successfully!', 'success')
        if duplicate_entries > 0:
            flash(f'{duplicate_entries} subject(s) already exist for the selected course, year level, and semester.',
                  'warning')
        if same_subject_in_both_semesters > 0:
            flash(
                f'{same_subject_in_both_semesters} subject(s) cannot be assigned to both first and second semesters for the selected course and year level.',
                'warning')

        return redirect(url_for('subject.manage_subjects'))
    else:
        print("Form is not valid")

    # Group details by course
    details = CourseYearLevelSemesterSubject.query.all()
    if selected_course:
        details = [detail for detail in details if detail.course_id == selected_course]

    return render_template('subject/manage_subjects.html', form=form, details=details,
                           subjects=subjects, courses=courses, selected_course=selected_course)


@subject_bp.route('/add_subject', methods=['GET', 'POST'])
def add_subject():
    form = SubjectForm()

    # Fetch faculties, courses, year levels, semesters, and sections from the database
    faculties = Faculty.query.all()
    form.faculty.choices = [(facu.id, facu.full_name) for facu in faculties]

    courses = Course.query.all()
    form.course.choices = [(course.id, course.course_name) for course in courses]

    year_levels = YearLevel.query.all()
    form.year_level.choices = [(year.id, year.level_name) for year in year_levels]

    semesters = Semester.query.all()
    form.semester.choices = [(sem.id, sem.semester_name) for sem in semesters]

    sections = Section.query.all()
    form.section.choices = [(section.id, section.section_name) for section in sections]

    if form.validate_on_submit():
        # Process form data
        subject_name = form.name.data
        code = form.code.data
        units = form.units.data
        faculty_ids = form.faculty.data  # This will be a list of selected faculty IDs

        day = form.day.data
        schedule_from = form.schedule_from.data
        schedule_to = form.schedule_to.data

        course_id = form.course.data
        year_level_id = form.year_level.data
        semester_id = form.semester.data
        section_id = form.section.data

        # Convert to time objects
        schedule_time_from = datetime.combine(datetime.min, schedule_from).time()
        schedule_time_to = datetime.combine(datetime.min, schedule_to).time()

        # Create a new subject
        new_subject = Subject(subject_name=subject_name, subject_code=code, subject_units=units)

        # Add selected faculties to the subject
        for faculty_id in faculty_ids:
            faculty = Faculty.query.get(faculty_id)
            new_subject.faculties.append(faculty)

        db.session.add(new_subject)
        db.session.commit()  # Commit to get the new_subject ID

        # Create a new schedule linked to the subject
        new_schedule = Schedule(
            day=day,
            start_time=schedule_time_from,
            end_time=schedule_time_to,
            subject_id=new_subject.id,
            section_id=section_id
        )

        db.session.add(new_schedule)
        db.session.commit()

        # Create a new CourseYearLevelSemesterSubject entry
        new_cylss = CourseYearLevelSemesterSubject(
            course_id=course_id,
            year_level_id=year_level_id,
            semester_id=semester_id,
            subject_id=new_subject.id
        )

        db.session.add(new_cylss)
        db.session.commit()

        flash('Subject added successfully!')
        return redirect(url_for('subject.add_subject'))

    return render_template('subject/add_subject.html', form=form)


@subject_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_subject(id):
    subj = Subject.query.get_or_404(id)
    form = EditSubjectForm(obj=subj)

    # Fetch faculties from the database and populate choices
    faculties = Faculty.query.all()
    form.faculty.choices = [(facu.id, facu.full_name) for facu in faculties]

    if form.validate_on_submit():
        # Update the subject object with form data
        subj.subject_name = form.name.data
        subj.code = form.code.data
        subj.units = form.units.data
        subj.faculty_id = form.faculty.data

        db.session.commit()
        flash('Subject has been updated successfully!')
        return redirect(url_for('subject.manage_subject'))

    # Fetch the schedule details to display in the form
    schedules = subj.schedule_details

    return render_template('subject/edit_subject.html', form=form, subject=subj, schedules=schedules)

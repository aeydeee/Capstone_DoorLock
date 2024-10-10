from flask import Blueprint, render_template, redirect, url_for, flash, jsonify, request
from datetime import datetime

from flask_login import login_required

from decorators import cspc_acc_required, admin_required
from models import Schedule, Faculty, Subject, FacultySubjectSchedule, YearLevel, Course, \
    Section, Semester, CourseYearLevelSemesterSubject, faculty_subject_association, student_subject_association
from webforms.delete_form import DeleteForm
from webforms.schedule_form import EditScheduleForm, NewScheduleForm
from app import db

schedule_bp = Blueprint('schedule', __name__)


@schedule_bp.route('/view_all_schedules')
@login_required
@cspc_acc_required
@admin_required
def view_schedules():
    delete_form = DeleteForm()

    # Query schedules joined with necessary tables without filtering by faculty_id
    schedules = Schedule.query.join(Subject, Schedule.subject_id == Subject.id) \
        .join(FacultySubjectSchedule, Schedule.id == FacultySubjectSchedule.schedule_id) \
        .join(Faculty, FacultySubjectSchedule.faculty_id == Faculty.id) \
        .join(Course, FacultySubjectSchedule.course_id == Course.id) \
        .join(YearLevel, FacultySubjectSchedule.year_level_id == YearLevel.id) \
        .join(Section, FacultySubjectSchedule.section_id == Section.id) \
        .join(Semester, FacultySubjectSchedule.semester_id == Semester.id).all()

    # Format start and end times to 12-hour format and remove SemesterEnum prefix
    for sched in schedules:
        sched.formatted_start_time = datetime.strptime(str(sched.start_time), "%H:%M:%S").strftime("%I:%M %p")
        sched.formatted_end_time = datetime.strptime(str(sched.end_time), "%H:%M:%S").strftime("%I:%M %p")
        sched.formatted_semester_name = str(sched.faculty_subject_schedules[0].semester.display_name)

    return render_template('schedule/view_all_schedules.html', schedules=schedules, delete_form=delete_form)


@schedule_bp.route('/view_schedule/<int:faculty_id>')
@login_required
@cspc_acc_required
@admin_required
def view_schedule(faculty_id):
    delete_form = DeleteForm()
    faculty = Faculty.query.get_or_404(faculty_id)

    # Query schedules joined with necessary tables and filtered by faculty_id
    schedules = Schedule.query.join(Subject, Schedule.subject_id == Subject.id) \
        .join(FacultySubjectSchedule, Schedule.id == FacultySubjectSchedule.schedule_id) \
        .join(Faculty, FacultySubjectSchedule.faculty_id == Faculty.id) \
        .join(Course, FacultySubjectSchedule.course_id == Course.id) \
        .join(YearLevel, FacultySubjectSchedule.year_level_id == YearLevel.id) \
        .join(Section, FacultySubjectSchedule.section_id == Section.id) \
        .join(Semester, FacultySubjectSchedule.semester_id == Semester.id) \
        .filter(Faculty.id == faculty_id).all()

    # Format start and end times to 12-hour format and remove SemesterEnum prefix
    for sched in schedules:
        sched.formatted_start_time = datetime.strptime(str(sched.start_time), "%H:%M:%S").strftime("%I:%M %p")
        sched.formatted_end_time = datetime.strptime(str(sched.end_time), "%H:%M:%S").strftime("%I:%M %p")
        sched.formatted_semester_name = str(sched.faculty_subject_schedules[0].semester.display_name)

    return render_template('schedule/view_schedule.html', faculty=faculty, schedules=schedules, delete_form=delete_form)


@schedule_bp.route('/get_subjects/<int:faculty_id>', methods=['GET'])
def get_subjects(faculty_id):
    subjects = Subject.query.filter_by(faculty_id=faculty_id).all()
    subjects_list = [(subj.id, subj.subject_name) for subj in subjects]
    return jsonify(subjects_list)


@schedule_bp.route('/get_options/<int:subject_id>', methods=['GET'])
@login_required
def get_options(subject_id):
    # Query to get all courses that offer the given subject
    course_year_level_semester_subjects = CourseYearLevelSemesterSubject.query.filter_by(subject_id=subject_id).all()

    # Extract unique courses for the given subject
    courses = set((cy.course.id, cy.course.course_name) for cy in course_year_level_semester_subjects)

    return jsonify({
        'courses': list(courses)
    })


@schedule_bp.route('/get_year_levels_and_semesters/<int:subject_id>/<int:course_id>', methods=['GET'])
@login_required
def get_year_levels_and_semesters(subject_id, course_id):
    # Query to get year levels and semesters for the selected subject and course
    course_year_level_semester_subjects = CourseYearLevelSemesterSubject.query.filter_by(
        subject_id=subject_id,
        course_id=course_id
    ).all()

    # Extract unique year levels and semesters
    year_levels = set((cy.year_level.id, cy.year_level.display_name) for cy in course_year_level_semester_subjects)
    semesters = set((cy.semester.id, cy.semester.display_name) for cy in course_year_level_semester_subjects)

    return jsonify({
        'year_levels': list(year_levels),
        'semesters': list(semesters)
    })


@schedule_bp.route('/add_schedule/<int:faculty_id>', methods=['GET', 'POST'])
@login_required
@cspc_acc_required
@admin_required
def add_schedule(faculty_id):
    faculty = Faculty.query.get_or_404(faculty_id)
    form = NewScheduleForm()

    # Initialize subject choices
    form.subject_id.choices = [(subject.id, subject.subject_name) for subject in Subject.query.all()]

    # Handle POST request
    if request.method == 'POST' and form.subject_id.data:
        subject_id = form.subject_id.data

        course_year_level_semester_subjects = CourseYearLevelSemesterSubject.query.filter_by(
            subject_id=subject_id).all()

        form.course_id.choices = [(cy.course.id, cy.course.course_name) for cy in course_year_level_semester_subjects]
        form.year_level_id.choices = [(cy.year_level.id, cy.year_level.display_name) for cy in
                                      course_year_level_semester_subjects]
        form.semester_id.choices = [(cy.semester.id, cy.semester.display_name) for cy in
                                    course_year_level_semester_subjects]

    if form.validate_on_submit():
        print("Form validated and submitted")  # Debugging line

        # Check for schedule conflicts across all faculty members
        conflicting_schedule = Schedule.query.filter(
            Schedule.day == form.day.data,
            Schedule.start_time < form.end_time.data,
            Schedule.end_time > form.start_time.data
        ).first()

        # if conflicting_schedule:
        #     flash('Schedule conflict detected with an existing schedule!', 'danger')
        #     return redirect(url_for('schedule.add_schedule', faculty_id=faculty_id))

        # Create a new schedule if no conflicts
        new_schedule = Schedule(
            day=form.day.data,
            start_time=form.start_time.data,
            end_time=form.end_time.data,
            subject_id=form.subject_id.data,
            section_id=form.section_id.data
        )
        db.session.add(new_schedule)
        db.session.commit()

        # Create a new FacultySubjectSchedule entry
        new_faculty_subject_schedule = FacultySubjectSchedule(
            faculty_id=faculty_id,
            schedule_id=new_schedule.id,
            subject_id=form.subject_id.data,
            course_id=form.course_id.data,
            year_level_id=form.year_level_id.data,
            semester_id=form.semester_id.data,
            section_id=form.section_id.data
        )
        db.session.add(new_faculty_subject_schedule)

        # Check if the faculty-subject association already exists
        existing_association = db.session.query(faculty_subject_association).filter_by(
            faculty_id=faculty_id, subject_id=form.subject_id.data).first()

        if not existing_association:
            stmt = faculty_subject_association.insert().values(
                faculty_id=faculty_id,
                subject_id=form.subject_id.data
            )
            db.session.execute(stmt)

        db.session.commit()

        flash('Schedule has been added successfully!', 'success')
        return redirect(url_for('schedule.view_schedule', faculty_id=faculty_id))

    else:
        print("Form did not validate")  # Debugging line
        print(form.errors)  # Debugging line to print out form errors

    return render_template('schedule/add_schedule.html', form=form, faculty=faculty)


@schedule_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@cspc_acc_required
@admin_required
def edit_schedule(id):
    # Fetch the schedule by ID
    sched = Schedule.query.get_or_404(id)

    # Get the faculty associated with this schedule
    faculty_subject_schedule = FacultySubjectSchedule.query.filter_by(schedule_id=id).first()

    if not faculty_subject_schedule:
        flash('No associated faculty found for this schedule.', 'danger')
        return redirect(url_for('schedule.view_schedule', faculty_id=faculty_subject_schedule.faculty_id))

    faculty = Faculty.query.get_or_404(faculty_subject_schedule.faculty_id)
    form = EditScheduleForm(obj=sched)

    # Ensure day field is pre-selected with the correct value
    if request.method == 'GET':
        if hasattr(sched.day, 'name'):
            form.day.data = sched.day.name.lower()  # Use the name attribute if it's an enum
        else:
            form.day.data = str(sched.day).lower()  # Otherwise, convert the day to string

    form.subject_id.choices = [(subject.id, subject.subject_name) for subject in faculty.subjects]

    # Prepare subject-related info only for the specific faculty
    subject_info = {}
    for subject in faculty.subjects:
        connections = CourseYearLevelSemesterSubject.query.filter_by(subject_id=subject.id).all()
        subject_info[subject.id] = [{
            'course_name': conn.course.course_name,
            'year_level_name': conn.year_level.level_name.name,  # Convert enum to string
            'semester_name': conn.semester.semester_name.name  # Convert enum to string
        } for conn in connections]

    if form.validate_on_submit():
        # Check for schedule conflicts, excluding the current schedule being edited
        conflicting_schedule = Schedule.query.filter(
            Schedule.id != sched.id,  # Exclude the current schedule
            Schedule.day == form.day.data,
            Schedule.start_time < form.end_time.data,
            Schedule.end_time > form.start_time.data
        ).first()

        if conflicting_schedule:
            flash('Schedule conflict detected with an existing schedule!', 'danger')
            return redirect(url_for('schedule.edit_schedule', id=id))

        # Update the schedule if no conflicts
        sched.day = form.day.data
        sched.start_time = form.start_time.data
        sched.end_time = form.end_time.data
        sched.subject_id = form.subject_id.data
        sched.section_id = form.section_id.data

        db.session.commit()

        # Get the first connection for the subject
        subject_conn = subject_info[form.subject_id.data][0]

        # Retrieve the IDs using ORM relationships
        course_id = Course.query.filter_by(course_name=subject_conn['course_name']).first().id
        year_level_id = YearLevel.query.filter_by(level_name=subject_conn['year_level_name']).first().id
        semester_id = Semester.query.filter_by(semester_name=subject_conn['semester_name']).first().id

        # Update only the relevant FacultySubjectSchedule
        faculty_subject_schedule.subject_id = form.subject_id.data
        faculty_subject_schedule.course_id = course_id
        faculty_subject_schedule.year_level_id = year_level_id
        faculty_subject_schedule.semester_id = semester_id
        faculty_subject_schedule.section_id = form.section_id.data

        db.session.commit()

        flash('Schedule and faculty assignment have been updated successfully!', 'success')
        return redirect(url_for('schedule.view_schedule', faculty_id=faculty.id))

    return render_template('schedule/edit_schedule.html', form=form, schedule=sched, subject_info=subject_info,
                           faculty=faculty)


@schedule_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
@cspc_acc_required
@admin_required
def delete_schedule(id):
    schedule = Schedule.query.get_or_404(id)

    # Manually delete related entries in student_subject_association
    db.session.execute(
        student_subject_association.delete().where(
            student_subject_association.c.schedule_id == id
        )
    )

    # Delete related entries in FacultySubjectSchedule
    FacultySubjectSchedule.query.filter_by(schedule_id=id).delete()

    # Retrieve all faculties associated with the subject
    faculties = schedule.subject.faculties

    # Delete the faculty-subject associations for this subject
    for faculty in faculties:
        db.session.execute(
            faculty_subject_association.delete().where(
                faculty_subject_association.c.faculty_id == faculty.id,
                faculty_subject_association.c.subject_id == schedule.subject_id
            )
        )

    # Proceed with the deletion of the schedule
    db.session.delete(schedule)
    db.session.commit()

    flash('Schedule and associated faculty-subject links deleted successfully', 'success')
    return redirect(url_for('faculty.manage_faculty'))

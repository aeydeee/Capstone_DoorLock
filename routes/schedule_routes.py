from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from datetime import datetime, timedelta
from models import Schedule, Faculty, Subject, faculty_subject_association, FacultySubjectSchedule, YearLevel, Course, \
    Section, Semester, CourseYearLevelSemesterSubject
from webforms.delete_form import DeleteForm
from webforms.schedule_form import ScheduleForm, EditScheduleForm, NewScheduleForm
from app import db

schedule_bp = Blueprint('schedule', __name__)


@schedule_bp.route('/view_schedule/<int:faculty_id>')
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
        sched.formatted_semester_name = str(sched.faculty_subject_schedules[0].semester.semester_name).replace(
            'SemesterEnum.', '')

    return render_template('schedule/view_schedule.html', faculty=faculty, schedules=schedules, delete_form=delete_form)


@schedule_bp.route('/get_subjects/<int:faculty_id>', methods=['GET'])
def get_subjects(faculty_id):
    subjects = Subject.query.filter_by(faculty_id=faculty_id).all()
    subjects_list = [(subj.id, subj.subject_name) for subj in subjects]
    return jsonify(subjects_list)


@schedule_bp.route('/new_add_schedule/<int:faculty_id>', methods=['GET', 'POST'])
def new_add_schedule(faculty_id):
    form = NewScheduleForm()

    # Get the faculty and their subjects
    faculty = Faculty.query.get_or_404(faculty_id)
    form.subject_id.choices = [(subject.id, subject.subject_name) for subject in faculty.subjects]

    # Create a dictionary to hold subject-related info
    subject_info = {}
    for subject in faculty.subjects:
        connections = CourseYearLevelSemesterSubject.query.filter_by(subject_id=subject.id).all()
        subject_info[subject.id] = [{
            'course_id': conn.course_id,
            'year_level_id': conn.year_level_id,
            'semester_id': conn.semester_id
        } for conn in connections]

    if form.validate_on_submit():
        new_schedule = Schedule(
            day=form.day.data,
            start_time=form.start_time.data,
            end_time=form.end_time.data,
            subject_id=form.subject_id.data,
            section_id=form.section_id.data
        )
        db.session.add(new_schedule)
        db.session.commit()

        subject_conn = subject_info[form.subject_id.data][0]
        new_faculty_subject_schedule = FacultySubjectSchedule(
            faculty_id=faculty_id,
            schedule_id=new_schedule.id,
            subject_id=form.subject_id.data,
            course_id=subject_conn['course_id'],
            year_level_id=subject_conn['year_level_id'],
            semester_id=subject_conn['semester_id'],
            section_id=form.section_id.data
        )
        db.session.add(new_faculty_subject_schedule)
        db.session.commit()

        flash('Schedule and faculty assignment added successfully!', 'success')
        return redirect(url_for('schedule.new_add_schedule', faculty_id=faculty_id))

    return render_template('schedule/new_add_schedule.html', form=form, faculty_id=faculty_id,
                           subject_info=subject_info)


@schedule_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_schedule(id):
    sched = Schedule.query.get_or_404(id)
    form = EditScheduleForm(obj=sched)

    if form.validate_on_submit():
        # Update the schedule object with form data
        form.populate_obj(sched)

        # Convert to time objects
        schedule_time_from = datetime.combine(datetime.min, form.schedule_time_from.data).time()
        schedule_time_to = datetime.combine(datetime.min, form.schedule_time_to.data).time()

        sched.schedule_time_from = schedule_time_from
        sched.schedule_time_to = schedule_time_to

        db.session.commit()
        flash('Schedule has been updated successfully!')
        return redirect(url_for('schedule.view_schedule', faculty_id=sched.faculty_id))

    return render_template('schedule/edit_schedule.html', form=form, schedule=sched)


@schedule_bp.route('/delete/<int:id>', methods=['POST'])
def delete_schedule(id):
    schedule = Schedule.query.get_or_404(id)
    db.session.delete(schedule)
    db.session.commit()
    flash('Schedule deleted successfully', 'success')
    return redirect(url_for('schedule.view_schedule', faculty_id=schedule.faculty_id))

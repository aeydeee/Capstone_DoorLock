from datetime import datetime, timedelta

from flask import Blueprint, request, render_template, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from flask import current_app as app

from app import db
from models import Faculty, User, Student, Attendance, Schedule, Subject, \
    student_subject_association, faculty_subject_association
from webforms.attendance_form import SelectScheduleForm
from webforms.delete_form import DeleteForm
from webforms.search_form import SearchForm

instructor_bp = Blueprint('instructor', __name__)


@instructor_bp.route('/students')
@login_required
def view_students():
    delete_form = DeleteForm()

    # Query all students joined with necessary tables and filtered by faculty_id
    students = Student.query.join(User, Student.user_id == User.id).join(
        student_subject_association, Student.id == student_subject_association.c.student_id
    ).join(Subject, student_subject_association.c.subject_id == Subject.id).join(
        faculty_subject_association, Subject.id == faculty_subject_association.c.subject_id
    ).join(Faculty, faculty_subject_association.c.faculty_id == Faculty.id).filter(
        Faculty.id == current_user.faculty_details.id
    ).all()

    return render_template('instructor/view_students.html', students=students, form=delete_form)


@instructor_bp.route('/get_schedules/<int:subject_id>', methods=['GET'])
def get_schedules(subject_id):
    print(f"Fetching schedules for subject_id: {subject_id}")  # Debugging statement
    schedules = Schedule.query.filter_by(subject_id=subject_id).all()
    schedule_list = [
        {'id': schedule.id, 'day': schedule.day, 'from': str(schedule.schedule_from), 'to': str(schedule.schedule_to)}
        for schedule in schedules]
    print(f"Schedules found: {schedule_list}")  # Debugging statement
    return jsonify(schedule_list)


@instructor_bp.route('/student_subject_association', methods=['GET', 'POST'])
def select_schedule():
    form = SelectScheduleForm()
    form.set_choices()

    if form.validate_on_submit():
        user_id = 22  # Replace with actual user ID for testing
        schedule_id = form.schedule_id.data
        subject_id = form.subject_id.data

        active_attendance = Attendance.query.filter_by(user_id=user_id, time_out=None).first()

        if active_attendance:
            flash(
                'You are already marked as present for another subject. Please finish the current class before attending a new one.',
                'error')
            return redirect(url_for('instructor.select_schedule'))

        time_in = datetime.now()
        attendance = Attendance(user_id=user_id, subject_id=subject_id, time_in=time_in)
        attendance.status = 'present'  # Assuming attendance.status can be set to 'present' here

        db.session.add(attendance)
        db.session.commit()
        flash('Attendance marked successfully!', 'success')
        return redirect(url_for('instructor.select_schedule'))

    return render_template('instructor/select_schedule.html', form=form)


def check_lateness(attendance):
    current_day = attendance.time_in.strftime('%A').lower()
    schedule = Schedule.query.filter_by(subject_id=attendance.subject_id, day=current_day).first()

    if schedule:
        scheduled_start_time = datetime.combine(attendance.time_in.date(), schedule.schedule_from)
        scheduled_end_time = datetime.combine(attendance.time_in.date(), schedule.schedule_to)

        if attendance.time_in > scheduled_end_time:
            return 'absent'
        elif attendance.time_in > (scheduled_start_time + timedelta(minutes=15)):
            return 'late'
        else:
            return 'present'
    else:
        return 'absent'


@instructor_bp.route('/attendance', methods=['GET', 'POST'])
@login_required
def view_attendance():
    section_filter = request.args.get('section', '')
    year_filter = request.args.get('year', '')
    subject_filter = request.args.get('subject', '')
    date_filter = request.args.get('date', '')

    # Fetch unique sections, years, and subjects for the filters that are handled by the current_user instructor
    sections = db.session.query(StudentCourseAndYear.section).distinct() \
        .join(StudentCourseAndYear.student) \
        .join(Student.subjects) \
        .filter(Subject.faculty_id == current_user.faculty_details.id) \
        .all()

    years = db.session.query(StudentCourseAndYear.year_level).distinct() \
        .join(StudentCourseAndYear.student) \
        .join(Student.subjects) \
        .filter(Subject.faculty_id == current_user.faculty_details.id) \
        .all()

    subjects = db.session.query(Subject.subject_name).distinct() \
        .filter(Subject.faculty_id == current_user.faculty_details.id) \
        .all()

    # Initialize the query for filtering students
    query = Student.query.join(student_subject_association).join(Subject).filter(
        Subject.faculty_id == current_user.faculty_details.id
    )

    if section_filter:
        query = query.join(Student.student_course_and_year).filter(
            StudentCourseAndYear.section.ilike(f'%{section_filter}%'))

    if year_filter:
        query = query.join(Student.student_course_and_year).filter(
            StudentCourseAndYear.year_level.ilike(f'%{year_filter}%'))

    if subject_filter:
        query = query.filter(Subject.subject_name.ilike(f'%{subject_filter}%'))

    # Execute the query
    students = query.all()

    # Fetch attendance status for each student
    student_attendance = {}
    for student in students:
        attendance_query = Attendance.query.filter_by(user_id=student.user_id)
        if subject_filter:
            attendance_query = attendance_query.join(Subject).filter(
                Subject.subject_name.ilike(f'%{subject_filter}%'))
        if date_filter:
            attendance_query = attendance_query.filter(db.func.date(Attendance.time_in) == date_filter)
        attendance = attendance_query.order_by(Attendance.time_in.desc()).first()
        if attendance:
            student_attendance[student.id] = attendance.status
        else:
            student_attendance[student.id] = 'No Record'

    # Render the template with the filtered students and attendance status
    return render_template('instructor/view_attendance.html', students=students, student_attendance=student_attendance,
                           sections=sections, years=years, subjects=subjects, section_filter=section_filter,
                           year_filter=year_filter, subject_filter=subject_filter, date_filter=date_filter)

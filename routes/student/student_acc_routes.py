import os
import re
import uuid
from datetime import datetime

from flask import Blueprint, render_template, flash, redirect, url_for, request, current_app, session
from flask_login import login_required, current_user
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from werkzeug.utils import secure_filename

from app import db
from decorators import student_required, email_required, own_student_account_required, check_totp_verified
from models import Program, student_course_association, Schedule, Student, YearLevel, Program, Section, Semester, User, \
    FacultyCourseSchedule, ProgramYearLevelSemesterCourse, SchoolYear
from webforms.student_form import EditStudentForm

student_acc_bp = Blueprint('student_acc', __name__)


@student_acc_bp.route("/course/<int:student_id>", methods=["GET", "POST"])
@login_required
@student_required
@check_totp_verified
def view_student_account_schedule(student_id):
    student = Student.query.get_or_404(current_user.student_details.id)

    # Query regular courses matching student's program, year level, and semester
    regular_courses = Program.query \
        .join(ProgramYearLevelSemesterCourse, Program.id == ProgramYearLevelSemesterCourse.course_id) \
        .filter(ProgramYearLevelSemesterCourse.program_id == student.program_id) \
        .filter(ProgramYearLevelSemesterCourse.year_level_id == student.year_level_id) \
        .filter(ProgramYearLevelSemesterCourse.semester_id == student.semester_id) \
        .join(student_course_association, Program.id == student_course_association.c.course_id) \
        .filter(student_course_association.c.student_id == student_id) \
        .all()

    # Query all courses the student is enrolled in using the student_course_association table
    all_courses = Program.query \
        .join(student_course_association, Program.id == student_course_association.c.course_id) \
        .filter(student_course_association.c.student_id == student_id) \
        .all()

    # Identify irregular courses by excluding regular courses
    regular_course_ids = {sub.id for sub in regular_courses}
    irregular_courses = [sub for sub in all_courses if sub.id not in regular_course_ids]

    # Get schedule details including faculty for regular courses
    schedule_details = Schedule.query \
        .join(FacultyCourseSchedule, FacultyCourseSchedule.schedule_id == Schedule.id) \
        .filter(Schedule.course_id.in_([course.id for course in regular_courses])) \
        .filter(FacultyCourseSchedule.program_id == student.program_id,
                FacultyCourseSchedule.year_level_id == student.year_level_id,
                FacultyCourseSchedule.semester_id == student.semester_id) \
        .filter(Schedule.section_id == student.section_id) \
        .all()

    # Prepare a mapping of course_id to schedule and faculty details for regular courses
    schedule_map = {}
    for schedule in schedule_details:
        for faculty_schedule in schedule.faculty_course_schedules:
            if schedule.course_id not in schedule_map:
                schedule_map[schedule.course_id] = []
            formatted_start_time = datetime.strptime(str(schedule.start_time), "%H:%M:%S").strftime("%I:%M %p")
            formatted_end_time = datetime.strptime(str(schedule.end_time), "%H:%M:%S").strftime("%I:%M %p")
            schedule_map[schedule.course_id].append({
                'formatted_start_time': formatted_start_time,
                'formatted_end_time': formatted_end_time,
                'day': schedule.day.name,
                'faculty_name': faculty_schedule.faculty.full_name,
                'faculty_email': faculty_schedule.faculty.user.email
            })

    # Assign the formatted schedule details to each regular program
    for sub in regular_courses:
        sub.schedule_details_formatted = schedule_map.get(sub.id, [])

    # The same for irregular courses, filtering by the student_course_association's schedule_id
    irregular_schedule_details = Schedule.query \
        .join(student_course_association, Schedule.id == student_course_association.c.schedule_id) \
        .filter(student_course_association.c.student_id == student_id) \
        .filter(Schedule.course_id.in_([course.id for course in irregular_courses])) \
        .all()

    irregular_schedule_map = {}
    for schedule in irregular_schedule_details:
        for faculty_schedule in schedule.faculty_course_schedules:
            if schedule.course_id not in irregular_schedule_map:
                irregular_schedule_map[schedule.course_id] = []
            formatted_start_time = datetime.strptime(str(schedule.start_time), "%H:%M:%S").strftime("%I:%M %p")
            formatted_end_time = datetime.strptime(str(schedule.end_time), "%H:%M:%S").strftime("%I:%M %p")
            irregular_schedule_map[schedule.course_id].append({
                'formatted_start_time': formatted_start_time,
                'formatted_end_time': formatted_end_time,
                'day': schedule.day.name,
                'faculty_name': faculty_schedule.faculty.full_name,
                'faculty_email': faculty_schedule.faculty.user.email
            })

    for sub in irregular_courses:
        sub.schedule_details_formatted = irregular_schedule_map.get(sub.id, [])

    return render_template('student_acc/view_schedule.html', student=student,
                           regular_courses=regular_courses,
                           irregular_courses=irregular_courses)


@student_acc_bp.route("/profile/<int:student_id>", methods=["GET", "POST"])
@login_required
@student_required
@own_student_account_required
def student_profile(student_id):
    student = Student.query.filter_by(id=student_id, user_id=current_user.id).first_or_404()
    user = student.user
    form = EditStudentForm(student_id=student.id, obj=user)

    # Helper functions for cleaning and validating
    def clean_field(field_value):
        return " ".join(field_value.strip().split()) if field_value else ""

    def convert_to_hex(rfid_uid):
        try:
            rfid_int = int(rfid_uid)
            rfid_hex = format(rfid_int, '08X')
            rfid_hex = ''.join(reversed([rfid_hex[i:i + 2] for i in range(0, len(rfid_hex), 2)]))
            return rfid_hex
        except ValueError:
            return rfid_uid.lower() if rfid_uid else ""

    def generate_school_year(semester_id):
        current_year = datetime.now().year
        if semester_id == 1:  # First Semester
            return f"{current_year}-{current_year + 1}"
        elif semester_id == 2:  # Second Semester
            return f"{current_year - 1}-{current_year}"
        return None

    # Populate choices for form fields with a default "Select..." option
    form.year_level_id.choices = [('', 'Select Year Level')] + [(y.id, y.display_name) for y in YearLevel.query.all()]
    form.program_id.choices = [('', 'Select Program')] + [(c.id, c.program_name.title()) for c in Program.query.all()]
    form.section_id.choices = [('', 'Select Section')] + [(s.id, s.display_name) for s in Section.query.all()]
    form.semester_id.choices = [('', 'Select Semester')] + [(sem.id, sem.display_name) for sem in Semester.query.all()]

    rfid_uid = form.rfid_uid.data if form.rfid_uid.data else None

    # Convert RFID UID to hexadecimal only if not None
    if rfid_uid:
        rfid_uid = convert_to_hex(rfid_uid)

    if request.method == "GET":
        form.rfid_uid.data = user.rfid_uid.upper() if user.rfid_uid else ''
        form.f_name.data = user.f_name or ''
        form.l_name.data = user.l_name or ''
        form.m_name.data = user.m_name or ''
        form.gender.data = user.gender or ''
        form.student_number.data = student.student_number.upper() or ''
        form.year_level_id.data = student.year_level_id or None
        form.program_id.data = student.program_id or None
        form.section_id.data = student.section_id or None
        form.semester_id.data = student.semester_id or None

    if form.validate_on_submit():
        # Clean other fields
        f_name_clean = clean_field(form.f_name.data.lower())
        l_name_clean = clean_field(form.l_name.data.lower())
        m_name_clean = clean_field(form.m_name.data.lower())
        gender_clean = clean_field(form.gender.data.lower())
        student_number_clean = clean_field(form.student_number.data.lower())

        # Check for existing RFID, email, and student number (only if RFID is not None)
        rfid_uid_exists = User.query.filter(User.rfid_uid == rfid_uid, User.id != user.id).first() if rfid_uid else None
        email_exists = User.query.filter(User.email == form.email.data, User.id != user.id).first()
        student_number_exists = Student.query.filter(Student.student_number == student_number_clean,
                                                     Student.user_id != user.id).first()

        if rfid_uid_exists:
            flash('RFID was already used', 'error')
        elif email_exists:
            flash('Email was already registered', 'error')
        elif student_number_exists:
            flash('Student ID is already in use', 'error')
        else:
            try:
                with db.session.begin_nested():
                    # Assign RFID UID, setting to None if blank
                    user.rfid_uid = rfid_uid if rfid_uid else None
                    user.f_name = f_name_clean
                    user.l_name = l_name_clean
                    user.m_name = m_name_clean
                    user.gender = gender_clean

                    student.student_number = student_number_clean
                    student.year_level_id = form.year_level_id.data
                    student.program_id = form.program_id.data
                    student.section_id = form.section_id.data
                    student.semester_id = form.semester_id.data

                    # Generate the school year based on the selected semester
                    school_year_label = generate_school_year(form.semester_id.data)

                    if school_year_label:
                        school_year = SchoolYear.query.filter_by(year_label=school_year_label).first()
                        if not school_year:
                            school_year = SchoolYear(year_label=school_year_label)
                            db.session.add(school_year)
                            db.session.flush()  # Ensure we have the school_year.id

                        student.school_year_id = school_year.id

                db.session.commit()
                flash('Student details updated successfully!', 'success')
                session['email'] = user.email
                return redirect(url_for('totp.two_factor_setup'))

            except SQLAlchemyError as e:
                db.session.rollback()

                if isinstance(e.orig, IntegrityError) and "Duplicate entry" in str(e.orig):
                    field_name = str(e.orig).split("'")[3]

                    field_name_map = {
                        'rfid_uid': 'RFID',
                        'email': 'Email',
                        'student_number': 'Student ID',
                    }

                    friendly_field_name = field_name_map.get(field_name, field_name)
                    flash(f"The {friendly_field_name} you entered is already in use. Please use a different value.",
                          'error')
                else:
                    flash('An error occurred while updating the student details. Please try again.', 'error')

    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error: {error}", 'error')

    return render_template('student_acc/student_profile.html', form=form, student=student)

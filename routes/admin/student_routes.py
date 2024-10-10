import csv
import io
import json
import os
import re
import uuid
from datetime import datetime

import numpy as np
import pandas as pd
import pyqrcode
from flask import Blueprint, request, render_template, current_app, flash, redirect, url_for, session, Response, \
    make_response, send_file, abort, jsonify
from flask_login import login_required
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import joinedload
# from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from app import db
from decorators import cspc_acc_required, admin_required
from models import User, Student, \
    Subject, Attendance, CourseYearLevelSemesterSubject, Section, Course, YearLevel, Semester, \
    student_subject_association, Schedule, FacultySubjectSchedule, YearLevelEnum, SectionEnum, SemesterEnum, Faculty

from webforms.delete_form import DeleteForm
from webforms.search_form import AssignStudentForm
from webforms.student_form import StudentForm, EditStudentForm, AssignBackSubjectForm
from webforms.upload_form import UploadForm

student_bp = Blueprint('student', __name__)

# Mapping from CSV values to enum names
YEAR_LEVEL_MAPPING = {
    'first year': 'FIRST_YEAR',
    'second year': 'SECOND_YEAR',
    'third year': 'THIRD_YEAR',
    'fourth year': 'FOURTH_YEAR'
}

SEMESTER_MAPPING = {
    'first semester': 'FIRST_SEMESTER',
    'second semester': 'SECOND_SEMESTER',
    'summer term': 'SUMMER_TERM'
}

SECTION_MAPPING = {
    'a': 'A',
    'b': 'B',
    'c': 'C',
    'd': 'D',
    'e': 'E',
    'f': 'F',
    'g': 'G',
    'h': 'H',
    'i': 'I',
    'j': 'J',
    'k': 'K',
    'l': 'L',
    'm': 'M'
}


def get_enum_name(mapping, value):
    """Convert CSV value to enum name."""
    value = value.strip().lower()
    return mapping.get(value)


# EXPORT ROUTES
def export_csv():
    # Retrieve all students
    students = Student.query.all()

    # Convert students to a list of dictionaries
    student_data = [{
        'student_number': student.student_number,
        'email': student.user.email,
        'name': f"{student.user.f_name} {student.user.l_name}",
        # Add more fields as necessary
    } for student in students]

    # Create DataFrame
    df = pd.DataFrame(student_data)

    # Export to CSV
    csv_data = df.to_csv(index=False)

    # Create response
    response = make_response(csv_data)
    response.headers["Content-Disposition"] = "attachment; filename=students.csv"
    response.headers["Content-Type"] = "text/csv"
    return response


def export_pdf():
    # Retrieve all students
    students = Student.query.all()

    # Create PDF buffer
    buffer = io.BytesIO()

    # Create a PDF object
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.setTitle("Student List")

    # Define the PDF content
    y = 750
    pdf.drawString(100, y, "Student List")
    y -= 20

    for student in students:
        pdf.drawString(100, y,
                       f"Student ID: {student.student_number}, Email: {student.user.email}, Name: {student.user.f_name} {student.user.l_name}")
        y -= 15
        if y < 50:
            pdf.showPage()
            y = 750

    pdf.save()

    # Move buffer cursor to the beginning
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name='students.pdf', mimetype='application/pdf')


@student_bp.route('/qrcode/<int:student_id>')
def student_qrcode(student_id):
    student = Student.query.get_or_404(student_id)
    if student.user.totp_secret is None:
        abort(404)

    # Generate QR code for TOTP using the student's secret key
    url = pyqrcode.create(student.user.get_totp_uri())
    stream = io.BytesIO()
    url.svg(stream, scale=3)
    return stream.getvalue(), 200, {
        'Content-Type': 'image/svg+xml',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
    }


@student_bp.route('/reset_schedules', methods=['POST'])
@login_required
@cspc_acc_required
@admin_required
def reset_schedules():
    try:
        db.session.execute(student_subject_association.delete())
        db.session.commit()
        flash('All student subjects and schedules have been reset.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error occurred: {str(e)}', 'danger')

    # Redirect to the page where the reset button is located (you can change this)
    return redirect(url_for('student.manage_student'))


@student_bp.route('/', methods=['GET', 'POST'])
@login_required
@cspc_acc_required
@admin_required
def manage_student():
    upload_form = UploadForm()
    delete_form = DeleteForm()
    assign_form = AssignStudentForm()

    # Check for export requests
    export_type = request.args.get('export')

    if export_type == 'csv':
        return export_csv()
    elif export_type == 'pdf':
        return export_pdf()

    if upload_form.validate_on_submit():
        file = upload_form.file.data
        filename = secure_filename(file.filename)

        success_count = 0
        error_count = 0

        def convert_to_hex(rfid_uid):
            try:
                # Try to interpret the RFID UID as an integer (which means it's in decimal)
                rfid_int = int(rfid_uid)

                # Convert the integer to a hexadecimal string
                rfid_hex = format(rfid_int, '08X')

                # Adjust the byte order (reverse for little-endian)
                rfid_hex = ''.join(reversed([rfid_hex[i:i + 2] for i in range(0, len(rfid_hex), 2)]))

                return rfid_hex
            except ValueError:
                # If it raises a ValueError, it means rfid_uid is already a valid hexadecimal string
                return rfid_uid.lower()  # Return as uppercase hex

        try:
            if filename.endswith('.csv'):
                df = pd.read_csv(file)
            elif filename.endswith('.xlsx'):
                df = pd.read_excel(file)

            for index, row in df.iterrows():
                row = row.replace({np.nan: None})
                row = row.apply(lambda x: x.strip().lower() if isinstance(x, str) else x)

                # Print row for debugging
                print(f"Processing row {index + 1}: {row}")

                # Skip the row if essential fields are missing
                if row['student_number'] is None or row['email'] is None:
                    flash(f'Skipping row {index + 1} due to missing essential data.', 'warning')
                    continue

                # Convert RFID UID or set to None if missing
                if 'rfid_uid' in row and row['rfid_uid'] is not None:
                    row['rfid_uid'] = convert_to_hex(row['rfid_uid'])
                else:
                    row['rfid_uid'] = None  # This will be saved as NULL in the DB

                # Check for existing email, username, and student number
                # rfid_uid_exists = User.query.filter_by(rfid_uid=row['rfid_uid']).first()
                email_exists = User.query.filter_by(email=row['email']).first()
                # username_exists = User.query.filter_by(username=row['username']).first()
                student_number_exists = Student.query.filter_by(student_number=row['student_number']).first()

                # Only check for RFID uniqueness if rfid_uid is not None
                rfid_uid_exists = None
                if row['rfid_uid'] is not None:
                    rfid_uid_exists = User.query.filter_by(rfid_uid=row['rfid_uid']).first()

                if rfid_uid_exists:
                    flash(f"Row {index + 1}: RFID {row['rfid_uid']} is already in use", 'error')
                    error_count += 1
                elif email_exists is not None:
                    flash(f"Row {index + 1}: Email {row['email']} is already registered", 'error')
                    error_count += 1
                elif student_number_exists is not None:
                    flash(f"Row {index + 1}: Faculty Number {row['student_number']} is already in use", 'error')
                    error_count += 1
                else:
                    try:
                        with db.session.begin_nested():
                            date_formats = ['%m/%d/%Y', '%d-%m-%Y', '%Y/%m/%d', '%Y-%m-%d']

                            # Normalizing gender input to match the Enum values
                            gender_mapping = {
                                'm': 'male',
                                'f': 'female',
                                'male': 'male',
                                'female': 'female'
                            }

                            # Assuming 'row['gender']' contains the gender value from your data source
                            gender_value = row['gender'].lower()  # normalize input to lowercase
                            normalized_gender = gender_mapping.get(gender_value)

                            if normalized_gender is None:
                                flash(
                                    f"Invalid gender value '{row['gender']}' for {semester_id}. Expected 'male' or 'female'.",
                                    'error')
                                continue  # Skip this row and move to the next one

                            # Define helper functions
                            def get_course_id(course_code):
                                course = Course.query.filter_by(course_code=course_code.upper()).first()
                                return course.id if course else None

                            def get_year_level_id(level_name):
                                level_enum = get_enum_name(YEAR_LEVEL_MAPPING, level_name)
                                level = YearLevel.query.filter_by(level_code=YearLevelEnum.code(level_enum)).first()
                                return level.id if level else None

                            def get_section_id(section_name):
                                section_enum = get_enum_name(SECTION_MAPPING, section_name)
                                section = Section.query.filter_by(
                                    section_code=SectionEnum.code(section_enum)).first()
                                return section.id if section else None

                            def get_semester_id(semester_name):
                                semester_enum = get_enum_name(SEMESTER_MAPPING, semester_name)
                                semester = Semester.query.filter_by(
                                    semester_code=SemesterEnum.code(semester_enum)).first()
                                return semester.id if semester else None

                            # Retrieve IDs based on CSV values
                            course_id = get_course_id(row['course_code'])
                            year_level_id = get_year_level_id(row['level_name'])
                            section_id = get_section_id(row['section_name'])
                            semester_id = get_semester_id(row['semester_name'])

                            # Validate the existence of required entities
                            if not course_id:
                                flash(f"Course code {row['course_code']} not found.", 'error')
                                continue
                            if not year_level_id:
                                flash(f"Year Level '{row['level_name']}' not found.", 'error')
                                continue
                            if not section_id:
                                flash(f"Section '{row['section_name']}' not found.", 'error')
                                continue
                            if not semester_id:
                                flash(f"Semester '{row['semester_name']}' not found.", 'error')
                                continue

                            # Use 'pbkdf2:sha256' for better compatibility
                            # password_hash = generate_password_hash(row['student_number'], method='pbkdf2:sha256')

                            # Create a new User instance
                            user = User(
                                rfid_uid=row['rfid_uid'],
                                f_name=row['f_name'],
                                l_name=row['l_name'],
                                m_name=row['m_name'],
                                email=row['email'],
                                role='student',
                                gender=row['gender'],

                            )
                            db.session.add(user)
                            db.session.flush()  # Get user.id without committing

                            student = Student(
                                student_number=row['student_number'],
                                course_id=course_id,
                                year_level_id=year_level_id,
                                section_id=section_id,
                                semester_id=semester_id,
                                user=user  # Link User instance
                            )
                            db.session.add(student)

                            # Commit the transaction
                        db.session.commit()
                        success_count += 1

                    except SQLAlchemyError as e:
                        db.session.rollback()
                        error_count += 1
                        print(f"SQLAlchemyError at row {index + 1}: {e}")
                        if isinstance(e.orig, IntegrityError) and "Duplicate entry" in str(e.orig):
                            field_name = str(e.orig).split("'")[3]
                            field_name_map = {
                                'rfid_uid': 'RFID',
                                'email': 'Email',
                                'student_number': 'Student ID',
                            }
                            friendly_field_name = field_name_map.get(field_name, field_name)
                            flash(f"Row {index + 1}: The {friendly_field_name} for {row['email']} is already in use.",
                                  'error')
                        else:
                            flash(f'Row {index + 1}: An error occurred while adding {row["email"]}. Please try again.',
                                  'error')

            if success_count > 0:
                flash(f'{success_count} students were successfully imported.', 'success')
            if error_count > 0:
                flash(f'{error_count} students could not be imported due to errors.', 'danger')

        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'danger')
            print(f"Exception at row {index + 1}: {e}")

    # Populate the subject dropdown with subject name and student names
    subjects = Subject.query.all()
    assign_form.subject.choices = [
        # (subject.id, f"{subject.subject_name} - {', '.join(student.full_name for student in subject.faculties)}")
        (subject.id, f"{subject.subject_name}")
        for subject in subjects
    ]

    # Retrieve all students or filter by course, year level, and section
    course_section = request.args.get('course_section', '')
    print(f"course_section: {course_section}")  # Debugging line

    if course_section:
        parts = course_section.rsplit(' ', 3)  # Adjusted to expect 4 parts including the semester
        print(f"parts: {parts}")  # Debugging line

        if len(parts) == 4:
            course_name, year_level_code, section_id, semester_name = parts

            # Handle possible prefix in year level and section
            if year_level_code.startswith('YearLevelEnum.'):
                year_level_code = year_level_code.replace('YearLevelEnum.', '')

            if section_id.startswith('SectionEnum.'):
                section_id = section_id.replace('SectionEnum.', '')

            print(
                f"course_name: {course_name}, year_level_code: {year_level_code}, section_name: {section_id}, semester_name: {semester_name}")  # Debugging line

            # Ensure Enum values are handled correctly in queries
            students = Student.query.join(Course).join(YearLevel).join(Section).join(Semester).filter(
                Course.course_code == course_name.strip(),
                YearLevel.level_name == YearLevelEnum.code(year_level_code.strip()),
                Section.section_name == SectionEnum.code(section_id.strip()),
                Semester.semester_name == SemesterEnum.code(semester_name.strip())
            ).all()

        else:
            students = Student.query.all()
    else:
        students = Student.query.all()

    return render_template(
        'student/manage_student.html',
        students=students,
        assign_form=assign_form,
        delete_form=delete_form,
        upload_form=upload_form
    )


@student_bp.route('/assign_students_to_subject', methods=['POST'])
@login_required
@cspc_acc_required
@admin_required
def assign_students_to_subject():
    assign_form = AssignStudentForm()
    assign_form.subject.choices = [
        (subject.id, f"{subject.subject_name} - {', '.join(student.full_name for student in subject.faculties)}")
        # (subject.id, f"{subject.subject_name}")
        for subject in Subject.query.all()
    ]

    if assign_form.validate_on_submit():
        selected_subject_ids = assign_form.subject.data  # Use .data directly for multiple selections
        selected_student_ids = request.form.getlist('student_ids')

        if not selected_student_ids:
            flash('No students selected for assignment.',
                  'error')
            return redirect(url_for('student.manage_student'))

        if not selected_subject_ids:
            flash('No subjects selected for assignment.', 'error')
            return redirect(url_for('student.manage_student'))

        for student_id in selected_student_ids:
            student = Student.query.get(student_id)
            if student:
                for subject_id in selected_subject_ids:
                    subject = Subject.query.get(subject_id)
                    if subject and subject not in student.subjects:
                        student.subjects.append(subject)
                db.session.add(student)

        db.session.commit()
        flash('Students successfully assigned to the selected subjects.', 'success')
        return redirect(url_for('student.manage_student'))
    else:
        for field, errors in assign_form.errors.items():
            for error in errors:
                flash(f"Error in {getattr(assign_form, field).label.text}: {error}", 'error')
        return redirect(url_for('student.manage_student'))


@student_bp.route("/subject/<int:student_id>/delete/<int:subject_id>", methods=["POST"])
@login_required
@cspc_acc_required
@admin_required
def delete_student_subject(student_id, subject_id):
    student = Student.query.get_or_404(student_id)
    subject = Subject.query.get_or_404(subject_id)

    # Remove the subject association with the student
    student.subjects.remove(subject)
    db.session.commit()

    flash(f"Successfully removed {subject.subject_name} from {student.full_name}.", "success")
    return redirect(url_for('student.manage_students_schedule_subjects', student_id=student_id))


@student_bp.route("/add", methods=["GET", "POST"])
@login_required
@cspc_acc_required
@admin_required
def add_student():
    form = StudentForm()
    form.year_level_id.choices = [(y.id, y.display_name) for y in YearLevel.query.all()]
    form.course_id.choices = [(c.id, c.course_name) for c in Course.query.all()]
    form.section_id.choices = [(s.id, s.display_name) for s in Section.query.all()]
    form.semester_id.choices = [(sem.id, sem.display_name) for sem in Semester.query.all()]

    print("Raw form data:", request.form)

    if form.validate_on_submit():
        def clean_field(field_value):
            return " ".join(field_value.strip().split())

        def convert_to_hex(rfid_uid):
            try:
                # Try to interpret the RFID UID as an integer (which means it's in decimal)
                rfid_int = int(rfid_uid)

                # Convert the integer to a hexadecimal string
                rfid_hex = format(rfid_int, '08X')

                # Adjust the byte order (reverse for little-endian)
                rfid_hex = ''.join(reversed([rfid_hex[i:i + 2] for i in range(0, len(rfid_hex), 2)]))

                return rfid_hex
            except ValueError:
                # If it raises a ValueError, it means rfid_uid is already a valid hexadecimal string
                return rfid_uid.lower()  # Return as uppercase hex

        def is_valid_cspc_email(email):
            """Check if the email ends with '@cspc.edu.ph'."""
            return email.lower().endswith('@my.cspc.edu.ph')

        # Convert the RFID UID to hexadecimal before saving
        form.rfid_uid.data = convert_to_hex(form.rfid_uid.data)

        # Check if the email is valid
        email = clean_field(form.email.data.lower())
        if not is_valid_cspc_email(email):
            flash('Email must be from the CSPC domain', 'error')
            return render_template('student/add_student.html', form=form)

        # Check for existing email, username, and student number
        rfid_uid_exists = User.query.filter_by(rfid_uid=clean_field(form.rfid_uid.data.lower())).first()
        email_exists = User.query.filter_by(email=clean_field(form.email.data.lower())).first()
        # username_exists = User.query.filter_by(username=clean_field(form.username.data.lower())).first()
        student_number_exists = Student.query.filter_by(
            student_number=clean_field(form.student_number.data.lower())).first()

        if rfid_uid_exists is not None:
            flash('RFID was already used', 'error')
        elif email_exists is not None:
            flash('Email was already registered', 'error')
        # elif username_exists is not None:
        #     flash('Username is already taken', 'error')
        elif student_number_exists is not None:
            flash('Student ID is already in use', 'error')
        else:
            try:
                with db.session.begin_nested():
                    # hashed_pw = generate_password_hash(form.password.data, "pbkdf2:sha256")
                    user = User(
                        rfid_uid=clean_field(form.rfid_uid.data.lower()),
                        # username=clean_field(form.username.data.lower()),
                        f_name=clean_field(form.f_name.data.lower()),
                        l_name=clean_field(form.l_name.data.lower()),
                        m_name=clean_field(form.m_name.data.lower()),
                        # m_initial=clean_field(form.m_initial.data.lower()),
                        email=clean_field(form.email.data.lower()),
                        # date_of_birth=form.date_of_birth.data,
                        # place_of_birth=clean_field(form.place_of_birth.data.lower()),
                        role='student',
                        gender=clean_field(form.gender.data.lower()),
                        # civil_status=clean_field(form.civil_status.data.lower()),
                        # nationality=clean_field(form.nationality.data.lower()),
                        # citizenship=clean_field(form.citizenship.data.lower()),
                        # religion=clean_field(form.religion.data.lower()),
                        # dialect=clean_field(form.dialect.data.lower()),
                        # tribal_aff=clean_field(form.tribal_aff.data.lower()),
                        # profile_pic=None
                    )
                    db.session.add(user)
                    db.session.flush()  # Get user.id without committing

                    # if 'profile_pic' in request.files and request.files['profile_pic'].filename != '':
                    #     profile_pic = request.files['profile_pic']
                    #     pic_filename = secure_filename(profile_pic.filename)
                    #     pic_name = str(uuid.uuid1()) + "_" + pic_filename
                    #     user.profile_pic = pic_name
                    #     profile_pic.save(os.path.join(current_app.config['UPLOAD_FOLDER'], pic_name))

                    # # Add ContactInfo
                    # contact_info = ContactInfo(
                    #     user_id=user.id,
                    #     contact_number=form.contact_number.data,
                    #     h_city=clean_field(form.home_addr_text.data.lower()),
                    #     h_barangay=clean_field(form.home_brgy_text.data.lower()),
                    #     h_house_no=clean_field(form.home_house_no.data.lower()),
                    #     h_street=clean_field(form.home_street.data.lower()),
                    #     curr_city=clean_field(form.curr_addr_text.data.lower()),
                    #     curr_barangay=clean_field(form.curr_brgy_text.data.lower()),
                    #     curr_house_no=clean_field(form.curr_house_no.data.lower()),
                    #     curr_street=clean_field(form.curr_street.data.lower())
                    # )
                    # db.session.add(contact_info)
                    #
                    # # Add FamilyBackground
                    # family_background = FamilyBackground(
                    #     user_id=user.id,
                    #     mother_full_name=clean_field(form.mother_full_name.data.lower()),
                    #     mother_educ_attainment=clean_field(form.mother_educ_attainment.data.lower()),
                    #     mother_addr=clean_field(form.mother_addr_text.data.lower()),
                    #     mother_brgy=clean_field(form.mother_brgy_text.data.lower()),
                    #     mother_cont_no=form.mother_cont_no.data,
                    #     mother_place_work_or_company_name=clean_field(
                    #         form.mother_place_work_or_company_name.data.lower()),
                    #     mother_occupation=clean_field(form.mother_occupation.data.lower()),
                    #     father_full_name=clean_field(form.father_full_name.data.lower()),
                    #     father_educ_attainment=clean_field(form.father_educ_attainment.data.lower()),
                    #     father_addr=clean_field(form.father_addr_text.data.lower()),
                    #     father_brgy=clean_field(form.father_brgy_text.data.lower()),
                    #     father_cont_no=form.father_cont_no.data,
                    #     father_place_work_or_company_name=clean_field(
                    #         form.father_place_work_or_company_name.data.lower()),
                    #     father_occupation=clean_field(form.father_occupation.data.lower()),
                    #     guardian_full_name=clean_field(form.guardian_full_name.data.lower()),
                    #     guardian_educ_attainment=clean_field(form.guardian_educ_attainment.data.lower()),
                    #     guardian_addr=clean_field(form.guardian_addr_text.data.lower()),
                    #     guardian_brgy=clean_field(form.guardian_brgy_text.data.lower()),
                    #     guardian_cont_no=form.guardian_cont_no.data,
                    #     guardian_place_work_or_company_name=clean_field(
                    #         form.guardian_place_work_or_company_name.data.lower()),
                    #     guardian_occupation=clean_field(form.guardian_occupation.data.lower())
                    # )
                    # db.session.add(family_background)
                    #
                    # # Add EducationalBackground
                    # educational_background = EducationalBackground(
                    #     user_id=user.id,
                    #     elem_school=clean_field(form.elem_school_name.data.lower()),
                    #     elem_address=clean_field(form.elem_school_addr_text.data.lower()),
                    #     elem_graduated=form.elem_year_grad.data,
                    #     junior_school=clean_field(form.junior_hs_school_name.data.lower()),
                    #     junior_address=clean_field(form.junior_hs_school_addr_text.data.lower()),
                    #     junior_graduated=form.junior_hs_year_grad.data,
                    #     senior_school=clean_field(form.senior_hs_school_name.data.lower()),
                    #     senior_address=clean_field(form.senior_hs_school_addr_text.data.lower()),
                    #     senior_graduated=form.senior_hs_year_grad.data,
                    #     senior_track_strand=clean_field(form.senior_strand.data.lower()),
                    #     # tertiary_school=clean_field(form.tertiary_school_name.data.lower()),
                    #     # tertiary_address=clean_field(form.tertiary_school_addr_text.data.lower()),
                    #     # tertiary_graduated=form.tertiary_year_grad.data,
                    #     # tertiary_course=clean_field(form.tertiary_course.data.lower())
                    # )
                    # db.session.add(educational_background)

                    # Add Student
                    student = Student(
                        student_number=clean_field(form.student_number.data.lower()),
                        # password_hash=hashed_pw,
                        year_level_id=form.year_level_id.data,
                        course_id=form.course_id.data,
                        section_id=form.section_id.data,
                        semester_id=form.semester_id.data,
                        user_id=user.id
                    )
                    db.session.add(student)
                    db.session.flush()  # Get student.id without committing

                # Commit the transaction
                db.session.commit()
                flash('Student added successfully!', 'success')
                return redirect(url_for('student.add_student'))

            except SQLAlchemyError as e:
                db.session.rollback()

                if isinstance(e.orig, IntegrityError) and "Duplicate entry" in str(e.orig):
                    field_name = str(e.orig).split("'")[3]

                    # Mapping database columns to user-friendly field names
                    field_name_map = {
                        'rfid_uid': 'RFID',
                        'email': 'Email',
                        # 'username': 'Username',
                        'student_number': 'Student ID',
                    }

                    # Use the user-friendly name if available, else fall back to the database column name
                    friendly_field_name = field_name_map.get(field_name, field_name)
                    flash(f"The {friendly_field_name} you entered is already in use. Please use a different value.",
                          'error')

                else:
                    flash('An error occurred while adding the student. Please try again.', 'error')

    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error: {error}", 'error')

    return render_template('student/add_student.html', form=form)


@student_bp.route("/edit/<int:id>/", methods=["GET", "POST"])
@login_required
@cspc_acc_required
@admin_required
def edit_student(id):
    student = Student.query.get_or_404(id)
    user = student.user
    form = EditStudentForm(obj=user)
    print(request.form)

    # # Initialize variables
    # contact_info = user.contact_info
    # family_background = user.family_background
    # educational_background = user.educational_background
    #
    # # Ensure that the related objects exist
    # if contact_info is None:
    #     contact_info = ContactInfo(user_id=user.id)
    #     db.session.add(contact_info)
    #     db.session.commit()
    #     user.contact_info = contact_info
    #
    # if family_background is None:
    #     family_background = FamilyBackground(user_id=user.id)
    #     db.session.add(family_background)
    #     db.session.commit()
    #     user.family_background = family_background
    #
    # if educational_background is None:
    #     educational_background = EducationalBackground(user_id=user.id)
    #     db.session.add(educational_background)
    #     db.session.commit()
    #     user.educational_background = educational_background

    def clean_field(field_value):
        return " ".join(field_value.strip().split())

    def convert_to_hex(rfid_uid):
        try:
            # Try to interpret the RFID UID as an integer (which means it's in decimal)
            rfid_int = int(rfid_uid)

            # Convert the integer to a hexadecimal string
            rfid_hex = format(rfid_int, '08X')

            # Adjust the byte order (reverse for little-endian)
            rfid_hex = ''.join(reversed([rfid_hex[i:i + 2] for i in range(0, len(rfid_hex), 2)]))

            return rfid_hex
        except ValueError:
            # If it raises a ValueError, it means rfid_uid is already a valid hexadecimal string
            return rfid_uid.lower()  # Return as lowercase hex

    form.year_level_id.choices = [(y.id, y.display_name) for y in YearLevel.query.all()]
    form.course_id.choices = [(c.id, c.course_name) for c in Course.query.all()]
    form.section_id.choices = [(s.id, s.display_name) for s in Section.query.all()]
    form.semester_id.choices = [(sem.id, sem.display_name) for sem in Semester.query.all()]

    if request.method == 'POST':
        print(form.errors)  # This will print any validation errors in the form

    if request.method == "GET":
        # Populate the form with existing data, using `or ''` to handle None values
        form.rfid_uid.data = user.rfid_uid or ''
        # form.username.data = user.username or ''
        form.f_name.data = user.f_name or ''
        form.l_name.data = user.l_name or ''
        form.m_name.data = user.m_name or ''
        # form.m_initial.data = user.m_initial or ''
        form.email.data = user.email or ''
        #         form.date_of_birth.data = user.date_of_birth or ''
        #         form.place_of_birth.data = user.place_of_birth or ''
        form.gender.data = user.gender or ''
        #         form.civil_status.data = user.civil_status or ''
        #         form.nationality.data = user.nationality or ''
        #         form.citizenship.data = user.citizenship or ''
        #         form.religion.data = user.religion or ''
        #         form.dialect.data = user.dialect or ''
        #         form.tribal_aff.data = user.tribal_aff or ''

        # Populate Student-specific data
        form.student_number.data = student.student_number or ''
        form.year_level_id.data = student.year_level_id or None
        form.course_id.data = student.course_id or None
        form.section_id.data = student.section_id or None
        form.semester_id.data = student.semester_id or None

        # # Populate ContactInfo
        # if contact_info:
        #     form.contact_number.data = contact_info.contact_number or ''
        #     form.home_addr_text.data = contact_info.h_city or ''
        #     form.home_brgy_text.data = contact_info.h_barangay or ''
        #     form.home_house_no.data = contact_info.h_house_no or ''
        #     form.home_street.data = contact_info.h_street or ''
        #     form.curr_addr_text.data = contact_info.curr_city or ''
        #     form.curr_brgy_text.data = contact_info.curr_barangay or ''
        #     form.curr_house_no.data = contact_info.curr_house_no or ''
        #     form.curr_street.data = contact_info.curr_street or ''
        #
        # # Populate FamilyBackground
        # if family_background:
        #     form.mother_full_name.data = family_background.mother_full_name or ''
        #     form.mother_educ_attainment.data = family_background.mother_educ_attainment or ''
        #     form.mother_addr_text.data = family_background.mother_addr or ''
        #     form.mother_brgy_text.data = family_background.mother_brgy or ''
        #     form.mother_cont_no.data = family_background.mother_cont_no or ''
        #     form.mother_place_work_or_company_name.data = family_background.mother_place_work_or_company_name or ''
        #     form.mother_occupation.data = family_background.mother_occupation or ''
        #     form.father_full_name.data = family_background.father_full_name or ''
        #     form.father_educ_attainment.data = family_background.father_educ_attainment or ''
        #     form.father_addr_text.data = family_background.father_addr or ''
        #     form.father_brgy_text.data = family_background.father_brgy or ''
        #     form.father_cont_no.data = family_background.father_cont_no or ''
        #     form.father_place_work_or_company_name.data = family_background.father_place_work_or_company_name or ''
        #     form.father_occupation.data = family_background.father_occupation or ''
        #     form.guardian_full_name.data = family_background.guardian_full_name or ''
        #     form.guardian_educ_attainment.data = family_background.guardian_educ_attainment or ''
        #     form.guardian_addr_text.data = family_background.guardian_addr or ''
        #     form.guardian_brgy_text.data = family_background.guardian_brgy or ''
        #     form.guardian_cont_no.data = family_background.guardian_cont_no or ''
        #     form.guardian_place_work_or_company_name.data = family_background.guardian_place_work_or_company_name or ''
        #     form.guardian_occupation.data = family_background.guardian_occupation or ''
        #
        # # Populate EducationalBackground
        # if educational_background:
        #     form.elem_school_name.data = educational_background.elem_school or ''
        #     form.elem_school_addr_text.data = educational_background.elem_address or ''
        #     form.elem_year_grad.data = educational_background.elem_graduated or ''
        #     form.junior_hs_school_name.data = educational_background.junior_school or ''
        #     form.junior_hs_school_addr_text.data = educational_background.junior_address or ''
        #     form.junior_hs_year_grad.data = educational_background.junior_graduated or ''
        #     form.senior_hs_school_name.data = educational_background.senior_school or ''
        #     form.senior_hs_school_addr_text.data = educational_background.senior_address or ''
        #     form.senior_hs_year_grad.data = educational_background.senior_graduated or ''
        #     form.senior_strand.data = educational_background.senior_track_strand or ''
        # form.tertiary_school_name.data = educational_background.tertiary_school or ''
        # form.tertiary_school_addr_text.data = educational_background.tertiary_address or ''
        # form.tertiary_year_grad.data = educational_background.tertiary_graduated or ''
        # form.tertiary_course.data = educational_background.tertiary_course or ''

    if form.validate_on_submit():
        print("Form is valid")
        # Convert the RFID UID to hexadecimal before saving
        form.rfid_uid.data = convert_to_hex(form.rfid_uid.data)

        # Convert all fields to lowercase and normalize spaces
        for field in form:
            if isinstance(field.data, str):
                # Convert to lowercase
                field.data = field.data.lower()
                # Normalize spaces (reduce multiple spaces to a single space)
                field.data = re.sub(r'\s+', ' ', field.data)

        # # Only hash the password if the password field is not empty
        # if form.password.data:
        #     hashed_pw = generate_password_hash(form.password.data, "pbkdf2:sha256")
        # else:
        #     hashed_pw = student.password_hash  # Use the existing password hash

        # Check for existing email, username, and student number conflicts
        rfid_uid_exists = User.query.filter(User.rfid_uid == form.rfid_uid.data, User.id != user.id).first()
        email_exists = User.query.filter(User.email == form.email.data, User.id != user.id).first()
        # username_exists = User.queSry.filter(User.username == form.username.data, User.id != user.id).first()
        student_number_exists = Student.query.filter(Student.student_number == form.student_number.data,
                                                     Student.user_id != user.id).first()

        if rfid_uid_exists is not None:
            flash('RFID was already used', 'error')
        elif email_exists is not None:
            flash('Email was already registered', 'error')
        # elif username_exists is not None:
        #     flash('Username is already taken', 'error')
        elif student_number_exists is not None:
            flash('Student ID is already in use', 'error')
        else:
            try:
                with db.session.begin_nested():
                    # Convert all fields to lowercase and normalize spaces
                    user.rfid_uid = clean_field(form.rfid_uid.data.lower())
                    # user.username = clean_field(form.username.data.lower())
                    user.f_name = clean_field(form.f_name.data.lower())
                    user.l_name = clean_field(form.l_name.data.lower())
                    user.m_name = clean_field(form.m_name.data.lower())
                    # user.m_initial = clean_field(form.m_initial.data.lower())
                    user.email = clean_field(form.email.data.lower())
                    #                     user.date_of_birth = form.date_of_birth.data
                    #                     user.place_of_birth = clean_field(form.place_of_birth.data.lower())
                    user.gender = clean_field(form.gender.data.lower())
                    #                     user.civil_status = clean_field(form.civil_status.data.lower())
                    #                     user.nationality = clean_field(form.nationality.data.lower())
                    #                     user.citizenship = clean_field(form.citizenship.data.lower())
                    #                     user.religion = clean_field(form.religion.data.lower())
                    #                     user.dialect = clean_field(form.dialect.data.lower())
                    #                     user.tribal_aff = clean_field(form.tribal_aff.data.lower())

                    # Handle profile pic update
                    # if 'profile_pic' in request.files and request.files['profile_pic'].filename != '':
                    #     profile_pic = request.files['profile_pic']
                    #     pic_filename = secure_filename(profile_pic.filename)
                    #     pic_name = str(uuid.uuid1()) + "_" + pic_filename
                    #     user.profile_pic = pic_name
                    #     profile_pic.save(os.path.join(current_app.config['UPLOAD_FOLDER'], pic_name))

                    # # Update ContactInfo
                    # if contact_info:
                    #     contact_info.contact_number = form.contact_number.data
                    #     contact_info.h_city = clean_field(form.home_addr_text.data.lower())
                    #     contact_info.h_barangay = clean_field(form.home_brgy_text.data.lower())
                    #     contact_info.h_house_no = clean_field(form.home_house_no.data.lower())
                    #     contact_info.h_street = clean_field(form.home_street.data.lower())
                    #     contact_info.curr_city = clean_field(form.curr_addr_text.data.lower())
                    #     contact_info.curr_barangay = clean_field(form.curr_brgy_text.data.lower())
                    #     contact_info.curr_house_no = clean_field(form.curr_house_no.data.lower())
                    #     contact_info.curr_street = clean_field(form.curr_street.data.lower())
                    #
                    # # Update FamilyBackground (similar updates for each field)
                    # if family_background:
                    #     family_background.mother_full_name = clean_field(form.mother_full_name.data.lower())
                    #     family_background.mother_educ_attainment = clean_field(
                    #         form.mother_educ_attainment.data.lower())
                    #     family_background.mother_addr = clean_field(form.mother_addr_text.data.lower())
                    #     family_background.mother_brgy = clean_field(form.mother_brgy_text.data.lower())
                    #     family_background.mother_cont_no = form.mother_cont_no.data
                    #     family_background.mother_place_work_or_company_name = clean_field(
                    #         form.mother_place_work_or_company_name.data.lower())
                    #     family_background.mother_occupation = clean_field(form.mother_occupation.data.lower())
                    #     family_background.father_full_name = clean_field(form.father_full_name.data.lower())
                    #     family_background.father_educ_attainment = clean_field(
                    #         form.father_educ_attainment.data.lower())
                    #     family_background.father_addr = clean_field(form.father_addr_text.data.lower())
                    #     family_background.father_brgy = clean_field(form.father_brgy_text.data.lower())
                    #     family_background.father_cont_no = form.father_cont_no.data
                    #     family_background.father_place_work_or_company_name = clean_field(
                    #         form.father_place_work_or_company_name.data.lower())
                    #     family_background.father_occupation = clean_field(form.father_occupation.data.lower())
                    #     family_background.guardian_full_name = clean_field(form.guardian_full_name.data.lower())
                    #     family_background.guardian_educ_attainment = clean_field(
                    #         form.guardian_educ_attainment.data.lower())
                    #     family_background.guardian_addr = clean_field(form.guardian_addr_text.data.lower())
                    #     family_background.guardian_brgy = clean_field(form.guardian_brgy_text.data.lower())
                    #     family_background.guardian_cont_no = form.guardian_cont_no.data
                    #     family_background.guardian_place_work_or_company_name = clean_field(
                    #         form.guardian_place_work_or_company_name.data.lower())
                    #     family_background.guardian_occupation = clean_field(form.guardian_occupation.data.lower())
                    #
                    # # Update EducationalBackground (similar updates for each field)
                    # if educational_background:
                    #     educational_background.elem_school = clean_field(form.elem_school_name.data.lower())
                    #     educational_background.elem_address = clean_field(form.elem_school_addr_text.data.lower())
                    #     educational_background.elem_graduated = form.elem_year_grad.data
                    #     educational_background.junior_school = clean_field(form.junior_hs_school_name.data.lower())
                    #     educational_background.junior_address = clean_field(
                    #         form.junior_hs_school_addr_text.data.lower())
                    #     educational_background.junior_graduated = form.junior_hs_year_grad.data
                    #     educational_background.senior_school = clean_field(form.senior_hs_school_name.data.lower())
                    #     educational_background.senior_address = clean_field(
                    #         form.senior_hs_school_addr_text.data.lower())
                    #     educational_background.senior_graduated = form.senior_hs_year_grad.data
                    #     educational_background.senior_track_strand = clean_field(form.senior_strand.data.lower())
                    # educational_background.tertiary_school = clean_field(form.tertiary_school_name.data.lower())
                    # educational_background.tertiary_address = clean_field(
                    #     form.tertiary_school_addr_text.data.lower())
                    # educational_background.tertiary_graduated = form.tertiary_year_grad.data
                    # educational_background.tertiary_course = clean_field(form.tertiary_course.data.lower())

                    # # Update the password hash only if it's changed
                    # if form.password.data:
                    #     student.password_hash = hashed_pw

                    # Update Student
                    student.student_number = form.student_number.data
                    student.year_level_id = form.year_level_id.data
                    student.section_id = form.section_id.data
                    student.course_id = form.course_id.data
                    student.semester_id = form.semester_id.data

                db.session.commit()
                flash('Student details updated successfully!', 'success')
                return redirect(url_for('student.manage_student'))

            except SQLAlchemyError as e:
                db.session.rollback()

                if isinstance(e.orig, IntegrityError) and "Duplicate entry" in str(e.orig):
                    field_name = str(e.orig).split("'")[3]

                    field_name_map = {
                        'rfid_uid': 'RFID',
                        'email': 'Email',
                        # 'username': 'Username',
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

    return render_template('student/edit_student.html', form=form, student=student)


@student_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
@cspc_acc_required
@admin_required
def delete_student(id):
    student = Student.query.get_or_404(id)
    user = student.user
    try:
        # Delete related attendance records first
        Attendance.query.filter_by(student_id=student.id).delete()

        # # Delete other related records
        # ContactInfo.query.filter_by(user_id=student.user.id).delete()
        # FamilyBackground.query.filter_by(user_id=student.user.id).delete()
        # EducationalBackground.query.filter_by(user_id=student.user.id).delete()

        # Remove student from subjects without deleting subjects
        subjects = student.subjects
        for subject in subjects:
            student.subjects.remove(subject)

        db.session.delete(student)
        db.session.delete(user)
        db.session.commit()

        flash('Student deleted successfully', 'success')
    except SQLAlchemyError as e:
        db.session.rollback()
        flash(f'Error deleting student: {str(e)}', 'error')
    return redirect(url_for('student.manage_student'))


@student_bp.route('/irregular-students')
@login_required
@cspc_acc_required
@admin_required
def irregular_students():
    # Get all students with their course, year level, semester, and enrolled subjects
    students = Student.query.options(
        joinedload(Student.course),
        joinedload(Student.year_level),
        joinedload(Student.semester),
        joinedload(Student.subjects)
    ).all()

    # List to store students with incorrect subject enrollment
    incorrect_enrollments = []

    # Check each student's enrolled subjects
    for student in students:
        # Get correct subjects
        correct_subjects = db.session.query(CourseYearLevelSemesterSubject).filter_by(
            course_id=student.course_id,
            year_level_id=student.year_level_id,
            semester_id=student.semester_id
        ).all()

        correct_subject_ids = {cs.subject_id for cs in correct_subjects}
        enrolled_subject_ids = {subject.id for subject in student.subjects}

        # Find subjects the student is enrolled in that are not in the correct subjects list
        if not enrolled_subject_ids.issubset(correct_subject_ids):
            # Add the correct subjects to the student object for template usage
            student.correct_subjects = [cs.subject for cs in correct_subjects]
            incorrect_enrollments.append(student)

    # Debug: Print or log the students to ensure they are being correctly populated
    print(incorrect_enrollments)  # or use logging if preferred
    for student in incorrect_enrollments:
        print(f"Student ID: {student.student_number}")
        print(f"Full Name: {student.full_name}")
        print(f"Course: {student.course.course_name}")
        print(f"Year Level: {student.year_level.display_name}")
        print(f"Semester: {student.semester.display_name}")
        print(f"Subjects: {[subject.subject_name for subject in student.subjects]}")

    return render_template('student/irregular_student.html', students=incorrect_enrollments)


@student_bp.route("/subject/<int:student_id>", methods=["GET", "POST"])
@login_required
@cspc_acc_required
@admin_required
def manage_students_schedule_subjects(student_id):
    delete_form = DeleteForm()
    student = Student.query.get_or_404(student_id)

    # Query regular subjects matching student's course, year level, and semester
    regular_subjects = Subject.query \
        .join(CourseYearLevelSemesterSubject, Subject.id == CourseYearLevelSemesterSubject.subject_id) \
        .filter(CourseYearLevelSemesterSubject.course_id == student.course_id) \
        .filter(CourseYearLevelSemesterSubject.year_level_id == student.year_level_id) \
        .filter(CourseYearLevelSemesterSubject.semester_id == student.semester_id) \
        .join(student_subject_association, Subject.id == student_subject_association.c.subject_id) \
        .filter(student_subject_association.c.student_id == student_id) \
        .all()

    # Query all subjects the student is enrolled in using the student_subject_association table
    all_subjects = Subject.query \
        .join(student_subject_association, Subject.id == student_subject_association.c.subject_id) \
        .filter(student_subject_association.c.student_id == student_id) \
        .all()

    # Identify irregular subjects by excluding regular subjects
    regular_subject_ids = {sub.id for sub in regular_subjects}
    irregular_subjects = [sub for sub in all_subjects if sub.id not in regular_subject_ids]

    # Get schedule details including faculty for regular subjects
    schedule_details = Schedule.query \
        .join(FacultySubjectSchedule, FacultySubjectSchedule.schedule_id == Schedule.id) \
        .filter(Schedule.subject_id.in_([subject.id for subject in regular_subjects])) \
        .filter(FacultySubjectSchedule.course_id == student.course_id,
                FacultySubjectSchedule.year_level_id == student.year_level_id,
                FacultySubjectSchedule.semester_id == student.semester_id) \
        .filter(Schedule.section_id == student.section_id) \
        .all()

    # Prepare a mapping of subject_id to schedule and faculty details for regular subjects
    schedule_map = {}
    for schedule in schedule_details:
        for faculty_schedule in schedule.faculty_subject_schedules:
            if schedule.subject_id not in schedule_map:
                schedule_map[schedule.subject_id] = []
            formatted_start_time = datetime.strptime(str(schedule.start_time), "%H:%M:%S").strftime("%I:%M %p")
            formatted_end_time = datetime.strptime(str(schedule.end_time), "%H:%M:%S").strftime("%I:%M %p")
            schedule_map[schedule.subject_id].append({
                'formatted_start_time': formatted_start_time,
                'formatted_end_time': formatted_end_time,
                'day': schedule.day.name,
                'faculty_name': faculty_schedule.faculty.full_name
            })

    # Assign the formatted schedule details to each regular subject
    for sub in regular_subjects:
        sub.schedule_details_formatted = schedule_map.get(sub.id, [])

    # The same for irregular subjects, filtering by the student_subject_association's schedule_id
    irregular_schedule_details = Schedule.query \
        .join(student_subject_association, Schedule.id == student_subject_association.c.schedule_id) \
        .filter(student_subject_association.c.student_id == student_id) \
        .filter(Schedule.subject_id.in_([subject.id for subject in irregular_subjects])) \
        .all()

    irregular_schedule_map = {}
    for schedule in irregular_schedule_details:
        for faculty_schedule in schedule.faculty_subject_schedules:
            if schedule.subject_id not in irregular_schedule_map:
                irregular_schedule_map[schedule.subject_id] = []
            formatted_start_time = datetime.strptime(str(schedule.start_time), "%H:%M:%S").strftime("%I:%M %p")
            formatted_end_time = datetime.strptime(str(schedule.end_time), "%H:%M:%S").strftime("%I:%M %p")
            irregular_schedule_map[schedule.subject_id].append({
                'formatted_start_time': formatted_start_time,
                'formatted_end_time': formatted_end_time,
                'day': schedule.day.name,
                'faculty_name': faculty_schedule.faculty.full_name
            })

    for sub in irregular_subjects:
        sub.schedule_details_formatted = irregular_schedule_map.get(sub.id, [])

    return render_template('student/manage_student_subject.html', student=student,
                           regular_subjects=regular_subjects,
                           irregular_subjects=irregular_subjects, delete_form=delete_form)


@student_bp.route('/assign-students', methods=['GET'])
def assign_students():
    try:
        students = Student.query.all()

        for student in students:
            # Get all subjects for the student's course, year level, and semester
            subjects = CourseYearLevelSemesterSubject.query.filter_by(
                course_id=student.course_id,
                year_level_id=student.year_level_id,
                semester_id=student.semester_id
            ).all()

            for subject_entry in subjects:
                # Step 1: Find all schedules for the subject that match the student's section
                schedules = Schedule.query.filter_by(
                    subject_id=subject_entry.subject_id,
                    section_id=student.section_id  # Match the student's section
                ).all()

                if not schedules:
                    # Handle the case where no schedules exist (optional)
                    flash(f"No schedule found for subject {subject_entry.subject.subject_name.title()}", 'warning')
                    continue

                # Step 2: Iterate over all matching schedules and assign them
                for schedule in schedules:
                    # Check if the association already exists for this schedule
                    existing_association = db.session.query(student_subject_association).filter_by(
                        student_id=student.id,
                        subject_id=subject_entry.subject_id,
                        schedule_id=schedule.id
                    ).first()

                    # Step 3: If no association exists, create it
                    if not existing_association:
                        student_subject = student_subject_association.insert().values(
                            student_id=student.id,
                            subject_id=subject_entry.subject_id,
                            schedule_id=schedule.id  # Add the schedule_id
                        )
                        db.session.execute(student_subject)

        db.session.commit()
        flash('Students assigned to subjects successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred: {e}', 'danger')

    return redirect(url_for('student.manage_student'))


@student_bp.route('/faculty_schedules/<int:faculty_id>', methods=['GET'])
def load_faculty_schedules(faculty_id):
    faculty_schedules = db.session.query(
        FacultySubjectSchedule.subject_id,
        FacultySubjectSchedule.section_id,
        FacultySubjectSchedule.course_id,
        FacultySubjectSchedule.year_level_id,
        Schedule.id,  # Use the schedule ID
        Schedule.day,
        Schedule.start_time,
        Schedule.end_time
    ).join(Schedule).filter(
        FacultySubjectSchedule.faculty_id == faculty_id
    ).all()

    schedule_options = []
    for schedule in faculty_schedules:
        subject = Subject.query.get(schedule.subject_id)
        section = Section.query.get(schedule.section_id)
        course = Course.query.get(schedule.course_id)
        year_level = YearLevel.query.get(schedule.year_level_id)

        # Convert Enum (DayOfWeek) to string
        day_of_week = schedule.day.name  # or `schedule.day.value` if using values

        # Construct the display for course, year level, and section (e.g., "BSIT 1B")
        course_year_section = f"{course.course_code.upper()} {year_level.code}{section.display_name}"

        # Construct the display text including subject, day, and time
        display_text = f"{subject.subject_name.title()} - {course_year_section} ({day_of_week}, {schedule.start_time.strftime('%I:%M %p')} - {schedule.end_time.strftime('%I:%M %p')})"

        schedule_options.append({
            'id': schedule.id,  # Add the schedule ID here
            'subject_id': schedule.subject_id,
            'section_id': schedule.section_id,
            'day': day_of_week,  # Use string instead of Enum
            'start_time': schedule.start_time.strftime('%H:%M'),
            'end_time': schedule.end_time.strftime('%H:%M'),
            'display_text': display_text
        })

    return jsonify(schedule_options)


@student_bp.route('/assign_back_subject', methods=['GET', 'POST'])
def assign_back_subject():
    form = AssignBackSubjectForm()

    # Prepend "Please select..." as the first choice for both student and faculty
    form.student_id.choices = [(0, 'Please select...')] + [(student.id, student.full_name.title()) for student in
                                                           Student.query.all()]
    form.faculty_id.choices = [(0, 'Please select...')] + [(faculty.id, faculty.full_name.title()) for faculty in
                                                           Faculty.query.all()]

    # If POST request, retrieve the faculty_id and update schedule_id choices dynamically
    if form.validate_on_submit() or request.method == 'POST':
        faculty_id = form.faculty_id.data
        if faculty_id:
            schedules = db.session.query(Schedule).join(FacultySubjectSchedule).filter(
                FacultySubjectSchedule.faculty_id == faculty_id
            ).all()

            # Update the schedule choices
            form.schedule_id.choices = [
                (schedule.id,
                 f"{schedule.subject.subject_name} ({schedule.day.name} {schedule.start_time.strftime('%H:%M')}-{schedule.end_time.strftime('%H:%M')})")
                for schedule in schedules
            ]
        else:
            form.schedule_id.choices = []
            flash("No schedules found for the selected faculty.", "warning")

        if form.validate_on_submit():
            student_id = form.student_id.data
            schedule_id = form.schedule_id.data  # Get the selected schedule ID

            # Retrieve the schedule using the ID
            schedule = Schedule.query.get(schedule_id)
            if not schedule:
                flash("Selected schedule does not exist.", "error")
                return redirect(url_for('student.assign_back_subject'))

            # Process the assignment
            try:
                student_subject_association_entry = student_subject_association.insert().values(
                    student_id=student_id,
                    subject_id=schedule.subject_id,
                    schedule_id=schedule_id
                )
                db.session.execute(student_subject_association_entry)
                db.session.commit()

                flash('Back subject assigned successfully!', "success")
                return redirect(url_for('student.assign_back_subject'))

            except IntegrityError:
                db.session.rollback()  # Roll back the session to avoid partial commits
                flash("This subject has already been assigned to the student.", "error")
                return redirect(url_for('student.assign_back_subject'))

        else:
            # Flash any form validation errors
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f"Error in {getattr(form, field).label.text}: {error}", "error")

    return render_template('student/assign_back_subject.html', form=form)

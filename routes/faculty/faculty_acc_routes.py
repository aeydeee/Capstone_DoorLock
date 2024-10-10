import os
import re
import uuid
from datetime import datetime, timedelta

import io
import os
import re
import pandas as pd
from fuzzywuzzy import fuzz
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape, GOV_LEGAL
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import TableStyle, Table, Paragraph, Image, SimpleDocTemplate, Spacer

from flask import Blueprint, request, render_template, flash, redirect, url_for, jsonify, abort, session, current_app, \
    make_response, send_file
from flask_login import login_required, current_user, logout_user
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
# from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename

from app import db
from decorators import cspc_acc_required, faculty_required, own_faculty_account_required, check_totp_verified
from models import Faculty, User, Student, Attendance, Schedule, Subject, \
    student_subject_association, faculty_subject_association, Section, FacultySubjectSchedule, Course, YearLevel, \
    Semester
from webforms.attendance_form import SelectScheduleForm
from webforms.delete_form import DeleteForm
from webforms.faculty_acc_form import AttendanceStatusForm
from webforms.faculty_form import FacultyForm

faculty_acc_bp = Blueprint('faculty_acc', __name__)


# EXPORT ROUTES
def export_csv(attendances):
    # Convert attendance records to a list of dictionaries
    attendance_data = [{
        'Student Name': attendance.student_name,
        'Student ID': attendance.student_number,
        'Course Code': attendance.course_code,
        'Year Level': attendance.level_code,
        'Section': attendance.section,
        'Semester': attendance.semester,
        'Subject': attendance.subject_name,
        'Faculty': attendance.faculty_name,
        'Time In': attendance.time_in.strftime("%Y-%m-%d %H:%M:%S") if attendance.time_in else '',
        'Time Out': attendance.time_out.strftime("%Y-%m-%d %H:%M:%S") if attendance.time_out else '',
        'Status': attendance.status
    } for attendance in attendances]

    # Create DataFrame
    df = pd.DataFrame(attendance_data)

    # Export to CSV
    csv_data = df.to_csv(index=False)

    # Create response
    response = make_response(csv_data)
    response.headers["Content-Disposition"] = "attachment; filename=attendance.csv"
    response.headers["Content-Type"] = "text/csv"
    return response


def add_header_footer(canvas, doc, is_first_page, start_date=None, end_date=None):
    canvas.saveState()

    # Header Section - different logic for first page
    if is_first_page:
        # Left side logo
        logo_path = os.path.join(os.getcwd(), 'static', 'images', 'logo', 'cspc.png')
        if os.path.exists(logo_path):
            canvas.drawImage(logo_path, 65, doc.height + 40, width=50, height=50)  # Adjusted logo size and position

        # Left side text
        canvas.setFont("Helvetica", 10)
        canvas.drawString(120, doc.height + 75, "Republic of the Philippines")  # Adjusted header text position
        canvas.setFont("Helvetica-Bold", 12)
        canvas.drawString(120, doc.height + 60, "CAMARINES SUR POLYTECHNIC COLLEGES")
        canvas.setFont("Helvetica", 10)
        canvas.drawString(120, doc.height + 45, "Nabua, Camarines Sur")
        canvas.setFont("Helvetica", 6)
        canvas.drawString(70, doc.height + 30, "ISO 9001:2015")

        # Right side logo
        new_logo_path = os.path.join(os.getcwd(), 'static', 'images', 'logo', 'ccs-logo.png')
        if os.path.exists(new_logo_path):
            canvas.drawImage(new_logo_path, doc.width - 1, doc.height + 40, width=50,
                             height=50)  # Align to match left logo size

        # Right side text (College of Computer Studies)
        canvas.setFont("Helvetica-Bold", 12)
        canvas.drawString(doc.width - 215, doc.height + 60,
                          "COLLEGE OF COMPUTER STUDIES")  # Text aligned to the left of the logo

        # Horizontal line after the header
        canvas.setLineWidth(1)
        canvas.setStrokeColor(colors.black)
        canvas.line(60, doc.height + 25, doc.width + 45, doc.height + 25)  # Draw a horizontal line after the header

    else:
        # Adjusted header for the 2nd and subsequent pages
        canvas.setFont("Helvetica-Bold", 12)
        canvas.drawString(65, doc.height + 60, "CAMARINES SUR POLYTECHNIC COLLEGES, ATTENDANCE RECORD LOGS - CONTINUED")

    # Add the italic footer text
    canvas.setFont("Helvetica-Oblique", 9)  # Setting the font to italic
    canvas.drawString(60, 50, "System-generated report. No Signature required.")  # Adjust the y-position as needed

    # Footer Section with horizontal line
    canvas.setLineWidth(1)
    canvas.setStrokeColor(colors.black)
    canvas.line(60, 40, doc.width + 45, 40)  # Horizontal line for the footer
    canvas.setFont("Helvetica", 10)

    # Format the effectivity date based on the provided start and end dates
    if start_date and end_date:
        effectivity_date = f"From {start_date.strftime('%Y-%m-%d')} - To {end_date.strftime('%Y-%m-%d')}"
    elif start_date:
        effectivity_date = f"From {start_date.strftime('%Y-%m-%d')}"
    elif end_date:
        effectivity_date = f"To {end_date.strftime('%Y-%m-%d')}"
    else:
        effectivity_date = "All records across all dates."

    canvas.drawString(60, 30, effectivity_date)

    # Include current_user.faculty_details.full_name in the footer
    if current_user and hasattr(current_user, 'faculty_details') and current_user.faculty_details:
        faculty_full_name = current_user.faculty_details.full_name
        canvas.drawString(60, 20, f"Prepared by: {faculty_full_name.title()}")

    canvas.drawRightString(doc.width + 45, 30, f"Page {doc.page}")

    canvas.restoreState()


def export_pdf(attendances, selected_columns, start_date=None, end_date=None):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(GOV_LEGAL),
                            leftMargin=0.75 * inch, rightMargin=0.75 * inch,
                            topMargin=1 * inch, bottomMargin=0.75 * inch)

    styles = getSampleStyleSheet()
    elements = []
    elements.append(Spacer(1, 30))  # Spacer to push the title down
    title = Paragraph("<b>ATTENDANCE RECORD LOGS</b>", styles['Title'])
    title.hAlign = 'CENTER'
    elements.append(title)
    elements.append(Spacer(1, 10))

    # Define column mappings for selected columns
    column_mapping = {
        'student_name': 'Student Name',
        'student_number': 'Student ID',
        'subject': 'Subject',
        'date': 'Date',
        'course_section': 'Course & Section',
        'semester': 'Semester',
        'time_in': 'Time In',
        'time_out': 'Time Out',
        'status': 'Status'
    }

    # Create table header based on selected columns
    table_header = [column_mapping[col] for col in selected_columns]
    data = [[Paragraph(cell, styles['Normal']) for cell in table_header]]

    # Populate the table rows based on selected columns
    for attendance in attendances:
        row = []
        if 'student_name' in selected_columns:
            row.append(Paragraph(attendance.student_name.title(), styles['Normal']))
        if 'student_number' in selected_columns:
            row.append(Paragraph(attendance.student_number.title(), styles['Normal']))
        if 'subject' in selected_columns:
            row.append(Paragraph(attendance.subject_name.title(), styles['Normal']))
        if 'date' in selected_columns:
            row.append(
                Paragraph(attendance.time_in.strftime('%m-%d-%Y') if attendance.time_in else '', styles['Normal']))
        if 'course_section' in selected_columns:
            row.append(Paragraph(
                f'{attendance.course_code.upper()} {attendance.level_code}{attendance.section.upper() if attendance.section else ""}',
                styles['Normal']))
        if 'semester' in selected_columns:
            row.append(Paragraph(attendance.semester, styles['Normal']))
        if 'time_in' in selected_columns:
            row.append(
                Paragraph(attendance.time_in.strftime('%I:%M %p') if attendance.time_in else 'N/A', styles['Normal']))
        if 'time_out' in selected_columns:
            row.append(
                Paragraph(attendance.time_out.strftime('%I:%M %p') if attendance.time_out else 'N/A', styles['Normal']))
        if 'status' in selected_columns:
            row.append(Paragraph(attendance.status.upper(), styles['Normal']))
        data.append(row)

    # Define specific column widths for time_in, time_out, and status
    column_widths = {
        'student_name': 180,
        'student_number': 65,
        'subject': 120,
        'date': 70,
        'course_section': 100,
        'semester': 90,
        'time_in': 65,  # Specific width for Time In
        'time_out': 65,  # Specific width for Time Out
        'status': 60  # Specific width for Status
    }

    # Set colWidths dynamically based on selected columns
    col_widths = [column_widths[col] for col in selected_columns]

    # Create the table with the specified column widths
    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.white),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    elements.append(table)

    def on_first_page(canvas, doc):
        add_header_footer(canvas, doc, is_first_page=True, start_date=start_date, end_date=end_date)

    def on_later_pages(canvas, doc):
        add_header_footer(canvas, doc, is_first_page=False, start_date=start_date, end_date=end_date)

    doc.build(elements, onFirstPage=on_first_page, onLaterPages=on_later_pages)

    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name='attendance_records.pdf', mimetype='application/pdf')


@faculty_acc_bp.route('/students')
@login_required
@cspc_acc_required
@faculty_required
@check_totp_verified
def view_students():
    # Query all students joined with necessary tables and filtered by faculty_id
    students = Student.query.join(User, Student.user_id == User.id).join(
        student_subject_association, Student.id == student_subject_association.c.student_id
    ).join(Subject, student_subject_association.c.subject_id == Subject.id).join(
        faculty_subject_association, Subject.id == faculty_subject_association.c.subject_id
    ).join(Faculty, faculty_subject_association.c.faculty_id == Faculty.id).filter(
        Faculty.id == current_user.faculty_details.id
    ).all()

    return render_template('faculty_acc/view_students.html', students=students)


@faculty_acc_bp.route('/instructor/student/<int:student_id>/schedule')
@login_required
def view_student_schedule(student_id):
    # Ensure the current user is a faculty_acc
    if current_user.role != 'faculty':
        return "You are not authorized to view this page.", 403

    student = Student.query.get_or_404(student_id)

    # Fetch the schedule details
    schedule = db.session.query(Schedule).join(Section).filter(Section.id == student.section_id).all()

    return render_template('faculty_acc/schedule.html', schedule=schedule, student=student)


@faculty_acc_bp.route('/students/attendance', methods=['GET', 'POST'])
@login_required
@cspc_acc_required
@faculty_required
@check_totp_verified
def view_attendance():
    # Check for export requests
    export_type = request.args.get('export')

    # Retrieve the selected columns for export
    selected_columns = request.args.getlist('columns')  # Capture selected columns from form

    # Ensure selected_columns is a list and not empty
    if not selected_columns:
        selected_columns = ['student_name', 'student_number', 'subject', 'date', 'course_section', 'semester',
                            'time_in', 'time_out',
                            'status']  # default columns

    faculty = Faculty.query.filter_by(user_id=current_user.id).first()
    subjects = faculty.subjects

    # Get student IDs for subjects taught by this faculty
    student_ids = db.session.query(Student.id).join(student_subject_association).filter(
        student_subject_association.c.subject_id.in_([subject.id for subject in subjects])
    ).distinct().all()
    student_ids = [student_id[0] for student_id in student_ids]

    # Get the start and end date from the query parameters
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    # Parse the date strings into datetime objects
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d') if start_date_str and start_date_str != 'None' else None
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str and end_date_str != 'None' else None

    # Build the initial query to fetch attendance records
    attendances_query = Attendance.query.filter(Attendance.student_id.in_(student_ids))
    if start_date:
        attendances_query = attendances_query.filter(Attendance.time_in >= start_date)
    if end_date:
        end_date = end_date.replace(hour=23, minute=59, second=59)
        attendances_query = attendances_query.filter(Attendance.time_in <= end_date)

    # Filter based on the faculty name or fuzzy match
    exact_match_attendances = attendances_query.filter(Attendance.faculty_name == faculty.full_name).all()

    if exact_match_attendances:
        attendances = exact_match_attendances
    else:
        all_attendances = attendances_query.all()
        attendances = [attendance for attendance in all_attendances if
                       fuzz.ratio(attendance.faculty_name, faculty.full_name) >= 80]

    # Handle export requests with the filtered data
    if export_type in ['csv', 'pdf']:
        if export_type == 'csv':
            return export_csv(attendances)  # Pass filtered attendance
        elif export_type == 'pdf':
            return export_pdf(attendances, selected_columns, start_date=start_date, end_date=end_date
                              )

    form = AttendanceStatusForm()

    # Handle form submission to update attendance status
    if form.validate_on_submit():
        attendance_id = request.form.get('attendance_id')
        attendance = Attendance.query.get(attendance_id)
        if attendance:
            attendance.status = form.status.data
            db.session.commit()
            flash('Attendance status updated successfully', 'success')
        return redirect(url_for('faculty_acc.view_attendance'))

    return render_template('faculty_acc/view_attendance.html', attendances=attendances, form=form,
                           selected_columns=selected_columns)


@faculty_acc_bp.route("/profile/<int:faculty_id>", methods=["GET", "POST"])
@login_required
@cspc_acc_required
@own_faculty_account_required
def faculty_profile(faculty_id):
    # Use the user associated with the email in the session
    faculty = Faculty.query.filter_by(id=faculty_id, user_id=current_user.id).first_or_404()
    user = faculty.user
    form = FacultyForm(faculty_id=faculty.id, obj=user)
    print(request.form)

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

    if request.method == 'POST':
        print(form.errors)  # This will print any validation errors in the form

    if request.method == "GET":
        # Populate the form with existing data, using `or ''` to handle None values
        form.rfid_uid.data = user.rfid_uid or ''

        form.f_name.data = user.f_name or ''
        form.l_name.data = user.l_name or ''
        form.m_name.data = user.m_name or ''

        form.gender.data = user.gender or ''

        # Populate Faculty-specific data
        form.school_id.data = faculty.faculty_number or ''
        form.department.data = faculty.faculty_department or ''
        form.designation.data = faculty.designation or ''

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

        # Check for existing email,  and faculty number conflicts
        rfid_uid_exists = User.query.filter(User.rfid_uid == form.rfid_uid.data, User.id != user.id).first()
        email_exists = User.query.filter(User.email == form.email.data, User.id != user.id).first()
        faculty_number_exists = Faculty.query.filter(Faculty.faculty_number == form.school_id.data,
                                                     Faculty.user_id != user.id).first()
        if rfid_uid_exists is not None:
            flash('RFID is already in use', 'error')
        elif email_exists is not None:
            flash('Email is already in use', 'error')
        # elif username_exists is not None:
        #     flash('Username is already taken', 'error')
        elif faculty_number_exists is not None:
            flash('Faculty Number is already in use', 'error')
        else:
            from sqlalchemy.exc import IntegrityError, SQLAlchemyError

            # Inside your route function
            try:
                with db.session.begin_nested():
                    # Convert all fields to lowercase and normalize spaces
                    user.rfid_uid = clean_field(form.rfid_uid.data.lower())
                    user.f_name = clean_field(form.f_name.data.lower())
                    user.l_name = clean_field(form.l_name.data.lower())
                    user.m_name = clean_field(form.m_name.data.lower())
                    user.gender = clean_field(form.gender.data.lower())

                    # Update Faculty
                    faculty.faculty_number = clean_field(form.school_id.data.lower())
                    faculty.faculty_department = clean_field(form.department.data.lower())
                    faculty.designation = clean_field(form.designation.data.lower())

                db.session.commit()
                flash('Faculty details updated successfully!', 'success')

                # redirect to the two-factor auth page, passing username in session
                session['email'] = user.email
                return redirect(url_for('totp.two_factor_setup'))

            except IntegrityError as e:
                db.session.rollback()
                # Handle duplicate entry errors
                if "Duplicate entry" in str(e.orig):
                    field_name = str(e.orig).split("'")[3]

                    field_name_map = {
                        'rfid_uid': 'RFID',
                        'email': 'Email',
                        'faculty_number': 'Faculty Number',
                    }

                    friendly_field_name = field_name_map.get(field_name, field_name)
                    flash(f"The {friendly_field_name} you entered is already in use. Please use a different value.",
                          'error')
                else:
                    flash('An error occurred while updating the faculty details. Please try again.', 'error')

            except SQLAlchemyError as e:
                db.session.rollback()
                # Handle other SQLAlchemy errors
                flash('A database error occurred. Please try again.', 'error')

            if form.errors:
                for field, errors in form.errors.items():
                    for error in errors:
                        flash(f"Error: {error}", 'error')

    return render_template('faculty_acc/faculty_profile.html', form=form, faculty=faculty)


@faculty_acc_bp.route('/view_schedule/<int:faculty_id>')
@login_required
@cspc_acc_required
@own_faculty_account_required
@check_totp_verified
def view_schedule(faculty_id):
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

    return render_template('faculty_acc/view_schedule.html', faculty=faculty, schedules=schedules)

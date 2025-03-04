import io
import os
import re
import uuid
from datetime import datetime

import numpy as np
import pandas as pd
import pyqrcode

from flask import Blueprint, request, render_template, current_app, flash, redirect, url_for, jsonify, session, abort, \
    send_file, make_response
from flask_login import login_required
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.platypus import TableStyle, Table, Paragraph, Image, SimpleDocTemplate
from werkzeug.utils import secure_filename
from sqlalchemy.exc import IntegrityError

from app import db
from decorators import admin_required, cspc_acc_required
from models import Faculty, User, FacultyCourseSchedule, faculty_course_association, Schedule, \
    student_course_association
from webforms.faculty_form import FacultyForm
from webforms.delete_form import DeleteForm

from sqlalchemy.exc import SQLAlchemyError

from webforms.upload_form import UploadForm

faculty_bp = Blueprint('faculty', __name__)


# EXPORT ROUTES
def export_csv():
    # Retrieve all students
    faculties = Faculty.query.all()

    # Convert faculties to a list of dictionaries
    faculty_data = [{
        'faculty_number': faculty.faculty_number,
        'email': faculty.user.email,
        'name': f"{faculty.user.f_name} {faculty.user.l_name}",
        # Add more fields as necessary
    } for faculty in faculties]

    # Create DataFrame
    df = pd.DataFrame(faculty_data)

    # Export to CSV
    csv_data = df.to_csv(index=False)

    # Create response
    response = make_response(csv_data)
    response.headers["Content-Disposition"] = "attachment; filename=faculties.csv"
    response.headers["Content-Type"] = "text/csv"
    return response


def export_pdf():
    # Retrieve all faculties
    faculties = Faculty.query.all()

    # Create a PDF buffer
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)

    # Set up PDF styles
    styles = getSampleStyleSheet()
    elements = []

    # Correct way to provide the logo path as an absolute path
    logo_path = os.path.join(os.getcwd(), 'static', 'images', 'logo', 'ccs-logo.png')

    if os.path.exists(logo_path):
        # Add a logo at the top
        logo = Image(logo_path, width=100, height=50)  # Adjust size as needed
        elements.append(logo)
    else:
        # Handle case where the logo is missing
        elements.append(Paragraph("Logo not found", styles['Normal']))

    # Add a header
    header = Paragraph("Faculty List", styles['Title'])
    elements.append(header)

    # Prepare data for the table
    data = [['Faculty Number', 'Email', 'Name']]  # Table header
    for faculty in faculties:
        data.append([
            faculty.faculty_number.upper(),
            faculty.user.email,
            f"{faculty.user.f_name.title()} {faculty.user.l_name.title()}"
        ])

    # Create a table and style it
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),  # Header background color
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),  # Header text color
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  # Center align all cells
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Bold font for header
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),  # Padding for header
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),  # Background color for cells
        ('GRID', (0, 0), (-1, -1), 1, colors.black),  # Add grid lines
    ]))

    # Add table to the elements
    elements.append(table)

    # Build the PDF
    doc.build(elements)

    # Move buffer cursor to the beginning
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name='faculties.pdf', mimetype='application/pdf')


@faculty_bp.route('/api/faculty_data', methods=['GET'])
def get_faculty_data():
    faculties = Faculty.query.all()
    data = []
    for faculty in faculties:
        courses = [{"code": subj.course_code.upper(), "name": subj.course_name.title()} for subj in faculty.courses]
        profile_pic = faculty.user.profile_pic if faculty.user.profile_pic else None
        profile_html = (f'<a href="#" data-bs-toggle="modal" data-bs-target="#profileModal{faculty.id}">'
                        f'<img src="{profile_pic}" alt="Profile Picture" style="border-radius: 50%; width: 28px; height: 28px; cursor: pointer;">'
                        '</a>') if profile_pic else "<i class='bx bxs-user-circle'></i>"
        data.append({
            "id": faculty.id,
            "faculty_number": faculty.faculty_number.upper() if faculty.faculty_number else "",
            "full_name": faculty.full_name.title() if faculty.full_name else "",
            "designation": faculty.designation.title() if faculty.designation else "",
            "l_name": faculty.user.l_name.title() if faculty.user.l_name else "",
            "f_name": faculty.user.f_name.title() if faculty.user.f_name else "",
            "m_name": faculty.user.m_name.title() if faculty.user.m_name else "",
            "gender": faculty.user.gender.upper() if faculty.user.gender else "",
            "faculty_department": faculty.faculty_department.upper() if faculty.faculty_department else "",
            "email": faculty.user.email,
            "profile": profile_html,
            "courses": courses
        })
    return jsonify({"data": data})


@faculty_bp.route('/qrcode/<int:faculty_id>')
def faculty_qrcode(faculty_id):
    faculty = Faculty.query.get_or_404(faculty_id)
    if faculty.user.totp_secret is None:
        abort(404)

    # Generate QR code for TOTP using the faculty's secret key
    url = pyqrcode.create(faculty.user.get_totp_uri())
    stream = io.BytesIO()
    url.svg(stream, scale=3)
    return stream.getvalue(), 200, {
        'Content-Type': 'image/svg+xml',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
    }


@faculty_bp.route('/reset_schedules', methods=['POST'])
@login_required
@cspc_acc_required
@admin_required
def faculty_reset_schedules():
    try:
        # Perform bulk delete on FacultyCourseSchedule and faculty_course_association
        db.session.query(FacultyCourseSchedule).delete()
        db.session.execute(faculty_course_association.delete())

        # Manually delete related entries in student_course_association
        db.session.execute(
            student_course_association.delete().where(
                student_course_association.c.schedule_id.isnot(None)
            )
        )

        # Retrieve all schedules and delete them one by one
        schedules = Schedule.query.all()
        for schedule in schedules:
            db.session.delete(schedule)

        db.session.commit()
        flash('Schedule and associated faculty-program links resets successfully', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error occurred: {str(e)}', 'danger')

    # Redirect to the page where the reset button is located (you can change this)
    return redirect(url_for('faculty.manage_faculty'))


@faculty_bp.route('/download_template', methods=['GET'])
@login_required
@cspc_acc_required
@admin_required
def download_template():
    # Define the column names for the template
    columns = ['rfid_uid', 'faculty_number', 'designation', 'faculty_department', 'email', 'f_name', 'l_name', 'm_name',
               'gender',
               ]

    # Create an empty DataFrame with the required columns
    df = pd.DataFrame(columns=columns)

    # Save the DataFrame to a BytesIO object
    output = io.BytesIO()

    # Use xlsxwriter for formatting
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Faculty Template')

        # Get the xlsxwriter workbook and worksheet objects
        workbook = writer.book
        worksheet = writer.sheets['Faculty Template']

        # Define formats for styling
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'center',
            'fg_color': '#4F81BD',
            'font_color': 'white',
            'border': 1
        })

        cell_format = workbook.add_format({
            'border': 1,
            'valign': 'center'
        })

        # Set column widths for better readability
        worksheet.set_column('A:A', 15, cell_format)  # RFID UID
        worksheet.set_column('B:B', 15, cell_format)  # Faculty Number
        worksheet.set_column('C:C', 15, cell_format)  # Designation
        worksheet.set_column('D:D', 20, cell_format)  # Department
        worksheet.set_column('E:E', 30, cell_format)  # Email
        worksheet.set_column('F:F', 20, cell_format)  # First Name
        worksheet.set_column('G:G', 20, cell_format)  # Last Name
        worksheet.set_column('H:H', 15, cell_format)  # Middle Name
        worksheet.set_column('I:I', 10, cell_format)  # Gender

        # Apply the header format to the first row
        for col_num, value in enumerate(df.columns):
            worksheet.write(0, col_num, value, header_format)

    # Set the file pointer back to the start
    output.seek(0)

    # Send the file as an attachment for download
    return send_file(output, as_attachment=True, download_name='faculty_template.xlsx',
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


@faculty_bp.route('/', methods=['GET', 'POST'])
@login_required
@cspc_acc_required
@admin_required
def manage_faculty():
    upload_form = UploadForm()
    delete_form = DeleteForm()

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
                rfid_int = int(rfid_uid)
                rfid_hex = format(rfid_int, '08X')
                rfid_hex = ''.join(reversed([rfid_hex[i:i + 2] for i in range(0, len(rfid_hex), 2)]))
                return rfid_hex
            except ValueError:
                return rfid_uid.lower()

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

                if row['faculty_number'] is None or row['email'] is None:
                    flash(f'Skipping row {index + 1} due to missing essential data.', 'warning')
                    continue

                if 'rfid_uid' in row and row['rfid_uid'] is not None:
                    row['rfid_uid'] = convert_to_hex(row['rfid_uid'])

                rfid_uid_exists = User.query.filter_by(rfid_uid=row['rfid_uid']).first()
                email_exists = User.query.filter_by(email=row['email']).first()
                faculty_number_exists = Faculty.query.filter_by(faculty_number=row['faculty_number']).first()

                if rfid_uid_exists is not None:
                    flash(f"Row {index + 1}: RFID {row['rfid_uid']} is already in use", 'error')
                    error_count += 1
                elif email_exists is not None:
                    flash(f"Row {index + 1}: Email {row['email']} is already registered", 'error')
                    error_count += 1
                elif faculty_number_exists is not None:
                    flash(f"Row {index + 1}: Faculty Number {row['faculty_number']} is already in use", 'error')
                    error_count += 1
                else:
                    try:
                        with db.session.begin_nested():
                            # Create a new User instance
                            user = User(
                                rfid_uid=row['rfid_uid'],
                                # username=row['username'],
                                f_name=row['f_name'],
                                l_name=row['l_name'],
                                m_name=row['m_name'],
                                email=row['email'],
                                role='faculty',
                                gender=row['gender'],

                            )
                            db.session.add(user)
                            db.session.flush()  # Get user.id without committing

                            # Create a new Faculty instance
                            faculty = Faculty(
                                faculty_number=row['faculty_number'],
                                designation=row['designation'],
                                faculty_department=row['faculty_department'],
                                # password_hash=password_hash,  # Use the hashed password
                                user=user  # Link User instance
                            )
                            db.session.add(faculty)

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
                                'faculty_number': 'Faculty Number',
                            }
                            friendly_field_name = field_name_map.get(field_name, field_name)
                            flash(f"Row {index + 1}: The {friendly_field_name} for {row['email']} is already in use.",
                                  'error')
                        else:
                            flash(f'Row {index + 1}: An error occurred while adding {row["email"]}. Please try again.',
                                  'error')

            if success_count > 0:
                flash(f'{success_count} faculties were successfully imported.', 'success')
            if error_count > 0:
                flash(f'{error_count} faculties could not be imported due to errors.', 'danger')

        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'danger')
            print(f"Exception at row {index + 1}: {e}")

    faculties = Faculty.query.all()
    return render_template('faculty/manage_faculty.html', faculties=faculties, upload_form=upload_form,
                           delete_form=delete_form)


@faculty_bp.route("/add", methods=["GET", "POST"])
@login_required
@cspc_acc_required
@admin_required
def add_faculty():
    form = FacultyForm()
    print("Raw form data:", request.form)
    print("Form data before submission:", form.data)

    if form.validate_on_submit():
        def clean_field(field_value):
            # Handle None values before stripping
            return " ".join(field_value.strip().split()) if field_value else ""

        def convert_to_hex(rfid_uid):
            try:
                rfid_int = int(rfid_uid)
                rfid_hex = format(rfid_int, '08X')
                rfid_hex = ''.join(reversed([rfid_hex[i:i + 2] for i in range(0, len(rfid_hex), 2)]))
                return rfid_hex
            except ValueError:
                return rfid_uid.lower() if rfid_uid else ""

        def is_valid_cspc_email(email):
            return email.lower().endswith('@cspc.edu.ph') if email else False

        # Handle all fields with None checks
        rfid_uid = form.rfid_uid.data if form.rfid_uid.data else None  # Set to None if blank
        email = form.email.data if form.email.data is not None else ''
        faculty_number = form.school_id.data if form.school_id.data is not None else ''
        f_name = form.f_name.data if form.f_name.data is not None else ''
        l_name = form.l_name.data if form.l_name.data is not None else ''
        m_name = form.m_name.data if form.m_name.data is not None else ''
        gender = form.gender.data if form.gender.data is not None else ''
        department = form.department.data if form.department.data is not None else ''
        designation = form.designation.data if form.designation.data is not None else ''

        # Convert RFID UID to hexadecimal only if not None
        if rfid_uid:
            rfid_uid = convert_to_hex(rfid_uid)

        # Clean email and validate CSPC domain
        email = clean_field(email.lower())
        if not is_valid_cspc_email(email):
            flash('Email must be from the CSPC domain', 'error')
            return render_template('faculty/add_faculty.html', form=form)

        # Clean other fields
        faculty_number_clean = clean_field(faculty_number.lower())
        f_name_clean = clean_field(f_name.lower())
        l_name_clean = clean_field(l_name.lower())
        m_name_clean = clean_field(m_name.lower())
        gender_clean = clean_field(gender.lower())
        department_clean = clean_field(department.lower())
        designation_clean = clean_field(designation.lower())

        # Check for existing RFID, email, and faculty number
        rfid_uid_exists = User.query.filter_by(rfid_uid=rfid_uid).first() if rfid_uid else None
        email_exists = User.query.filter_by(email=email).first()
        faculty_number_exists = Faculty.query.filter_by(faculty_number=faculty_number_clean).first()

        if rfid_uid_exists:
            flash('RFID was already used', 'error')
        elif email_exists:
            flash('Email was already registered', 'error')
        elif faculty_number_exists:
            flash('Faculty Number is already in use', 'error')
        else:
            try:
                with db.session.begin_nested():
                    # Create User instance
                    user = User(
                        rfid_uid=rfid_uid,  # Will be None if empty
                        f_name=f_name_clean,
                        l_name=l_name_clean,
                        m_name=m_name_clean,
                        email=email,
                        role='faculty',
                        gender=gender_clean
                    )
                    db.session.add(user)
                    db.session.flush()

                    # Add Faculty instance
                    faculty = Faculty(
                        user_id=user.id,
                        faculty_department=department_clean,
                        faculty_number=faculty_number_clean,
                        designation=designation_clean,
                    )
                    db.session.add(faculty)
                    db.session.flush()

                db.session.commit()
                flash('Faculty added successfully!', 'success')
                return redirect(url_for('faculty.add_faculty'))

            except SQLAlchemyError as e:
                db.session.rollback()

                if isinstance(e.orig, IntegrityError) and "Duplicate entry" in str(e.orig):
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
                    flash('An error occurred while adding the faculty. Please try again.', 'error')

    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error in {field}: {error}", 'error')

    return render_template('faculty/add_faculty.html', form=form)


@faculty_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_faculty(id):
    facu = Faculty.query.get_or_404(id)
    user = facu.user
    form = FacultyForm(obj=user)

    def clean_field(field_value):
        return " ".join(field_value.strip().split())

    def convert_to_hex(rfid_uid):
        if not rfid_uid:
            return ""  # Handle blank RFID UID
        try:
            # Remove spaces and convert to int if possible
            rfid_uid = rfid_uid.strip()
            rfid_int = int(rfid_uid)
            rfid_hex = format(rfid_int, '08X')
            # Reverse the byte order
            rfid_hex = ''.join(reversed([rfid_hex[i:i + 2] for i in range(0, len(rfid_hex), 2)]))
            return rfid_hex
        except ValueError:
            return rfid_uid  # Return the original UID if it's not a valid number

    rfid_uid = form.rfid_uid.data if form.rfid_uid.data else None

    # Convert RFID UID to hexadecimal only if not None
    if rfid_uid:
        rfid_uid = convert_to_hex(rfid_uid)

    if request.method == 'GET':
        form.rfid_uid.data = user.rfid_uid.upper() if user.rfid_uid else ''
        form.f_name.data = user.f_name or ''
        form.l_name.data = user.l_name or ''
        form.m_name.data = user.m_name or ''
        form.email.data = user.email or ''
        form.gender.data = user.gender or ''
        form.school_id.data = facu.faculty_number or ''
        form.department.data = facu.faculty_department or ''
        form.designation.data = facu.designation or ''

    if form.validate_on_submit():
        # Clean and convert RFID UID if provided, else set to None
        rfid_uid = form.rfid_uid.data.strip()
        if rfid_uid:
            rfid_uid = convert_to_hex(rfid_uid)
        else:
            rfid_uid = None

        # Check for existing RFID, email, and faculty number (only if RFID is not None)
        rfid_uid_exists = User.query.filter(User.rfid_uid == rfid_uid,
                                            User.id != user.id).first() if rfid_uid else None
        email_exists = User.query.filter(User.email == form.email.data, User.id != user.id).first()
        faculty_number_exists = Faculty.query.filter(Faculty.faculty_number == form.school_id.data,
                                                     Faculty.user_id != user.id).first()

        if rfid_uid_exists:
            flash('RFID is already in use', 'error')
        elif email_exists:
            flash('Email is already in use', 'error')
        elif faculty_number_exists:
            flash('Faculty Number is already in use', 'error')
        else:
            try:
                with db.session.begin_nested():
                    # Assign RFID UID, setting to None if blank
                    user.rfid_uid = rfid_uid if rfid_uid else None
                    user.f_name = clean_field(form.f_name.data.lower())
                    user.l_name = clean_field(form.l_name.data.lower())
                    user.m_name = clean_field(form.m_name.data.lower())
                    user.email = clean_field(form.email.data.lower())
                    user.gender = clean_field(form.gender.data.lower())

                    facu.faculty_number = clean_field(form.school_id.data.lower())
                    facu.faculty_department = clean_field(form.department.data.lower())
                    facu.designation = clean_field(form.designation.data.lower())

                db.session.commit()
                flash('Faculty information has been updated!', 'success')
                return redirect(url_for('faculty.manage_faculty'))

            except SQLAlchemyError as e:
                db.session.rollback()
                if isinstance(e.orig, IntegrityError) and "Duplicate entry" in str(e.orig):
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

    return render_template('faculty/edit_faculty.html', form=form, faculty=facu)


@faculty_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
@cspc_acc_required
@admin_required
def delete_faculty(id):
    faculty = Faculty.query.get_or_404(id)
    user = faculty.user
    try:
        # Manually delete all associated faculty_course_schedule records
        FacultyCourseSchedule.query.filter_by(faculty_id=faculty.id).delete()

        # Now delete the faculty and user
        db.session.delete(faculty)
        db.session.delete(user)
        db.session.commit()

        flash('Faculty deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting faculty: {str(e)}', 'error')
    return redirect(url_for('faculty.manage_faculty'))

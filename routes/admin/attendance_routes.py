from datetime import datetime

from flask import Blueprint, render_template, request, redirect, flash, url_for, make_response, send_file

from flask_login import login_required, current_user

import io
import os

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape, GOV_LEGAL
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import TableStyle, Table, Paragraph, SimpleDocTemplate, Spacer

from app import db
from decorators import cspc_acc_required, admin_required
from models import Attendance
from webforms.faculty_acc_form import AttendanceStatusForm

attendance_bp = Blueprint('attendance', __name__)


def export_csv(attendances):
    # Convert attendance records to a list of dictionaries
    attendance_data = [{
        'Student Name': attendance.student_name,
        'Student ID': attendance.student_number,
        'Program Code': attendance.program_code,
        'Year Level': attendance.level_code,
        'Section': attendance.section,
        'Semester': attendance.semester,
        'Course': attendance.course_name,
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
    if current_user and hasattr(current_user, 'admin_details') and current_user.admin_details:
        faculty_full_name = current_user.admin_details.full_name
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
        'program': 'Course',
        'date': 'Date',
        'program_section': 'Program & Section',
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
        if 'program' in selected_columns:
            row.append(Paragraph(attendance.course_name.title(), styles['Normal']))
        if 'date' in selected_columns:
            row.append(
                Paragraph(attendance.time_in.strftime('%m-%d-%Y') if attendance.time_in else '', styles['Normal']))
        if 'program_section' in selected_columns:
            row.append(Paragraph(
                f'{attendance.program_code.upper()} {attendance.level_code}{attendance.section.upper() if attendance.section else ""}',
                styles['Normal']))
        if 'semester' in selected_columns:
            row.append(Paragraph(attendance.semester, styles['Normal']))
        if 'time_in' in selected_columns:
            row.append(
                Paragraph(attendance.time_in.strftime('%I:%M %p') if attendance.time_in else '', styles['Normal']))
        if 'time_out' in selected_columns:
            row.append(
                Paragraph(attendance.time_out.strftime('%I:%M %p') if attendance.time_out else '', styles['Normal']))
        if 'status' in selected_columns:
            row.append(Paragraph(attendance.status.upper(), styles['Normal']))
        data.append(row)

    # Define specific column widths for time_in, time_out, and status
    column_widths = {
        'student_name': 180,
        'student_number': 65,
        'program': 120,
        'date': 70,
        'program_section': 100,
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


@attendance_bp.route('/attendance', methods=['GET', 'POST'])
@login_required
@cspc_acc_required
@admin_required
def view_attendance():
    # Check for export requests
    export_type = request.args.get('export')

    # Retrieve the selected columns for export
    selected_columns = request.args.getlist('columns')  # Capture selected columns from form

    if not selected_columns:
        selected_columns = ['student_name', 'student_number', 'program', 'date', 'program_section', 'semester',
                            'time_in', 'time_out',
                            'status']  # Default columns

    # Handle date filters from query parameters
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    # Parse the date strings into datetime objects
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d') if start_date_str and start_date_str != 'None' else None
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str and end_date_str != 'None' else None

    # Query for all attendances
    attendances_query = Attendance.query

    # Apply date filters if present
    if start_date:
        attendances_query = attendances_query.filter(Attendance.time_in >= start_date)
    if end_date:
        # Set time to end of the day for the end date filter
        end_date = end_date.replace(hour=23, minute=59, second=59)
        attendances_query = attendances_query.filter(Attendance.time_in <= end_date)

    # Fetch the attendances after applying the filters
    attendances = attendances_query.all()

    # Handle export requests with the filtered data
    if export_type in ['csv', 'pdf']:
        if export_type == 'csv':
            return export_csv(attendances)  # Pass filtered attendance
        elif export_type == 'pdf':
            return export_pdf(attendances, selected_columns, start_date=start_date, end_date=end_date)

    form = AttendanceStatusForm()

    # Handle form submission for updating attendance status
    if form.validate_on_submit():
        attendance_id = request.form.get('attendance_id')
        attendance = Attendance.query.get(attendance_id)
        if attendance:
            attendance.status = form.status.data
            db.session.commit()
            flash('Attendance status updated successfully', 'success')
        return redirect(url_for('attendance.view_attendance'))

    # Render the attendance page with all attendances and form
    return render_template('admin/view_attendance.html', attendances=attendances, form=form,
                           selected_columns=selected_columns)

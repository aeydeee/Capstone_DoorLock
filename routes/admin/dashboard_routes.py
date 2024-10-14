import os
import re
import uuid
from datetime import date, timedelta

from flask import Blueprint, render_template, flash, redirect, url_for, session, current_app, request
from flask_login import current_user, logout_user, login_required
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from werkzeug.utils import secure_filename

from app import db
from decorators import cspc_acc_required, admin_required
from models import Faculty, Attendance, Student, User, Section, Semester, Program, YearLevel
from webforms.student_form import EditStudentForm

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/dashboard')
@login_required
@cspc_acc_required
@admin_required
def dashboard():
    if current_user.role == 'student':
        return redirect(url_for('student_acc.view_student_account_schedule', student_id=current_user.id))
    # Fetch the required data
    total_faculties = Faculty.query.count()
    total_students = Student.query.count()
    total_attendances = Attendance.query.count()
    todays_attendance = Attendance.query.filter(db.func.date(Attendance.time_in) == date.today()).count()

    # Fetch recent attendances
    recent_attendances = Attendance.query.order_by(Attendance.time_in.desc()).limit(5).all()

    past_week_data = {}
    for i in range(7):
        day = date.today() - timedelta(days=i)
        count = Attendance.query.filter(db.func.date(Attendance.time_in) == day).count()
        past_week_data[day.strftime('%b. %d, %Y')] = count

    # Reverse the order to make sure the chart labels are in chronological order
    past_week_data = dict(sorted(past_week_data.items()))

    labels = list(past_week_data.keys())
    data = list(past_week_data.values())
    print(labels)  # should output the list of dates
    print(data)  # should output the corresponding list of attendance counts

    return render_template(
        'admin/dashboard.html',
        total_faculties=total_faculties,
        total_students=total_students,
        total_attendances=total_attendances,
        todays_attendance=todays_attendance,
        recent_attendances=recent_attendances,
        past_week_data=past_week_data,  # Pass the attendance data to the template
        labels=labels, data=data
    )

# @dashboard_bp.route('/dashboard2')
# def dashboard2():
#     return render_template('manage_courses.html')

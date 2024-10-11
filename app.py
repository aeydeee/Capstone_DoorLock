import os

import pyotp
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
from waitress import serve

import atexit

import pymysql
import pytz
import sqlalchemy
from apscheduler.schedulers.background import BackgroundScheduler

from flask import Flask, render_template, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

from flask_ckeditor import CKEditor
from dotenv import load_dotenv
from flask_wtf import CSRFProtect
from sqlalchemy import desc
from werkzeug.security import check_password_hash, generate_password_hash

from config import Config
from utils import check_and_create_enums
from webforms.totp_form import RequestTOTPResetForm

# Load environment variables from .env file
load_dotenv()

db = SQLAlchemy()


def create_app():
    app = Flask(__name__)

    # Load environment variables
    app.config.from_object(Config)

    # Load environment variables
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default_secret_key')

    print("SECRET_KEY:", app.config['SECRET_KEY'])

    ckeditor = CKEditor(app)
    csrf = CSRFProtect(app)
    csrf.init_app(app)

    # db.init_app(app)
    migrate = Migrate(app, db)
    mail = Mail(app)

    from models import User, Attendance, Schedule, FacultyCourseSchedule, Faculty, Course, Program, YearLevel, Section, \
        Semester, FacultySession, ReportLog, student_course_association, delete_null_status_logs, \
        delete_old_faculty_sessions
    from flask import request
    from datetime import datetime, timedelta
    import requests
    from flask_login import LoginManager, login_required, current_user

    from database.google_backup import run_full_backup

    # Flask_Login Stuff
    login_manager = LoginManager()
    login_manager.login_view = 'login.login'
    login_manager.init_app(app)

    # Function for full backup (end of day)
    def trigger_full_backup_job(app):
        with app.app_context():
            app.test_client().get('/trigger-full-backup')

    # Create scheduler
    scheduler = BackgroundScheduler()

    # Pass the app instance to delete_null_status_logs
    scheduler.add_job(func=lambda: delete_null_status_logs(app), trigger="interval", seconds=5)
    scheduler.add_job(func=lambda: delete_old_faculty_sessions(app), trigger="interval", hours=24)

    # Schedule full backups at the end of the day (midnight)
    scheduler.add_job(func=lambda: trigger_full_backup_job(app), trigger="cron", hour=17, minute=4)

    scheduler.start()

    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register Blueprints
    from routes import register_blueprints
    register_blueprints(app)

    def check_and_create_database():
        try:
            # Ensure environment variable 'DB_NAME' is set properly
            db_name = os.environ.get('DB_NAME')
            if not db_name:
                raise ValueError("DB_NAME is not set in environment variables")

            # Connect to MySQL server using pymysql without specifying a database
            connection = pymysql.connect(
                host=os.environ.get('DB_HOST', 'localhost'),
                user=os.environ.get('DB_USERNAME'),
                password=os.environ.get('DB_PASSWORD')
            )
            cursor = connection.cursor()

            # Check if the database exists
            cursor.execute(f"SHOW DATABASES LIKE '{db_name}';")
            result = cursor.fetchone()

            if not result:
                # If database does not exist, create it
                cursor.execute(f"CREATE DATABASE {db_name};")
                print(f"Database '{db_name}' created successfully.")
            else:
                print(f"Database '{db_name}' already exists.")

            # Close connection
            cursor.close()
            connection.close()

            # Update the URI to use the database and initialize SQLAlchemy
            sqlalchemy_uri = f"mysql+pymysql://{os.environ.get('DB_USERNAME')}:{os.environ.get('DB_PASSWORD')}@{os.environ.get('DB_HOST', 'localhost')}/{db_name}"
            app.config['SQLALCHEMY_DATABASE_URI'] = sqlalchemy_uri
            db.init_app(app)

        except pymysql.MySQLError as e:
            print(f"Error: {e}")
        except ValueError as ve:
            print(f"Configuration error: {ve}")

    with app.app_context():
        check_and_create_database()  # Check and create the database if needed

        db.create_all()  # Create all database tables
        from utils import check_and_create_admin
        check_and_create_admin()  # Check and create admin user
        check_and_create_enums()

    ARDUINO_IP = '192.168.50.170'  # Arduino's IP address
    ARDUINO_PORT = 90

    # Function to unlock the door
    def unlock():
        try:
            response = requests.get(f'http://{ARDUINO_IP}:{ARDUINO_PORT}/unlock', timeout=5)
            print(response.text)
            return {'status': 'success', 'response': response.text}
        except requests.exceptions.Timeout:
            print("Request timed out")
            return {'status': 'error', 'message': 'Request timed out'}
        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")
            return {'status': 'error', 'message': str(e)}

    # Function to lock the door
    def lock():
        try:
            response = requests.get(f'http://{ARDUINO_IP}:{ARDUINO_PORT}/lock', timeout=5)
            print(response.text)
            return {'status': 'success', 'response': response.text}
        except requests.exceptions.Timeout:
            print("Request timed out")
            return {'status': 'error', 'message': 'Request timed out'}
        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")
            return {'status': 'error', 'message': str(e)}

    @app.route('/trigger-full-backup')
    def trigger_full_backup():
        run_full_backup()
        return "Full Backup initiated successfully."

    @app.route('/get_role', methods=['POST'])
    @csrf.exempt
    def get_user_role():
        rfid_uid = request.form.get('uid')
        print(f"Received UID: {rfid_uid}")  # Debugging: Print the received UID

        if not rfid_uid:
            print("No UID received. Raw data:", request.get_data(as_text=True))
            return "error", 400

        user = User.query.filter_by(rfid_uid=rfid_uid).first()

        if not user:
            print("User not found for UID:", rfid_uid)
            return "not found", 404

        print(f"User role for UID {rfid_uid}: {user.role}")  # Debugging: Print the user role
        return user.role, 200

    @app.route('/rfid', methods=['POST'])
    @csrf.exempt
    def handle_rfid():
        rfid_uid = request.form.get('uid')
        totp = request.form.get('totp')
        reader_type = request.form.get('reader_type')
        print(f'READER_TYPE {reader_type}')

        # Set timezone to Asia/Manila (Philippine Timezone)
        timezone = pytz.timezone('Asia/Manila')
        response_data = {}
        response_status = 500

        if not rfid_uid:
            print("No UID received. Raw data:", request.get_data(as_text=True))

            lock_response = lock()
            lock_status = lock_response.get('status')

            if lock_status == 'success':
                display_message("No UID received", "lock")
                response_data = {'error': 'UID not received'}
                response_status = 400
            else:
                print("Failed to lock the door")
                display_message("Lock failed", "failed")
                response_data = {'error': 'lock_failed'}
                response_status = 500

        else:
            print(f"Received UID: {rfid_uid}")
            user = User.query.filter_by(rfid_uid=rfid_uid).first()

            if not user:
                print("User not found")

                lock_response = lock()
                lock_status = lock_response.get('status')

                # Log the access attempt in ReportLog
                report_log = ReportLog(action=reader_type, status="Unidentified User")
                db.session.add(report_log)
                db.session.commit()

                if lock_status == 'success':
                    display_message("User not found", "lock")
                    response_data = {'status': 'not found'}
                    response_status = 404
                else:
                    print("Failed to lock the door")
                    display_message("Lock failed", "failed")
                    response_data = {'status': 'lock_failed'}
                    response_status = 500

            else:
                current_time = datetime.now(timezone).time()
                formatted_time = current_time.strftime("%I:%M %p")
                current_day = datetime.now(timezone).strftime('%A')

                # Log the access attempt in ReportLog
                report_log = ReportLog(user_id=user.id, action=reader_type, timestamp=datetime.now(timezone))
                db.session.add(report_log)
                db.session.commit()

                # Admin logic
                if user.role == 'admin':
                    if not totp:
                        print("TOTP required for admin")
                        display_message("TOTP required for admin", "lock")
                        response_data = {'status': 'totp_required'}
                        response_status = 400
                    elif user.verify_totp(totp):
                        print("Admin TOTP verified successfully")
                        display_message("Admin authenticated", "unlock")

                        # Check if admin has already timed in (i.e., report_log has a timestamp)
                        if report_log.timestamp:
                            if reader_type == "out":
                                # Admin has timed in, proceed with time out
                                report_log.time_out = datetime.now(timezone)
                                report_log.status = 'Timed Out'
                                db.session.commit()

                                print("Admin has timed out")
                                display_message("Admin successfully timed out", "unlock")
                                response_data = {'status': 'admin_successfully_timed_out', 'email': user.email}
                                response_status = 200
                            else:
                                # Admin has timed in but is not "out" yet
                                print("Admin is still timed-in")
                                display_message("Admin is still timed-in", "lock")
                                response_data = {'status': 'admin_still_timed_in'}
                                response_status = 400
                        else:
                            # No active session (no timestamp means no prior time-in)
                            print("Admin has not yet timed in")
                            display_message("Admin has not yet timed in", "lock")
                            response_data = {'status': 'no_active_session'}
                            response_status = 400

                        # Attempt to unlock the door if TOTP is verified
                        unlock_response = unlock()
                        unlock_status = unlock_response.get('status')

                        if unlock_status == 'success':
                            formatted_time = datetime.now().strftime('%H:%M:%S')  # Assuming formatted_time variable
                            display_message(f"Door unlocked for admin at {formatted_time}", "unlock")
                            report_log.status = 'Access Granted'
                            db.session.commit()
                            response_data = {'status': 'admin_authenticated', 'email': user.email}
                            response_status = 200
                        else:
                            print("Failed to unlock the door")

                            # Attempt to lock the door after failed unlock
                            lock_response = lock()
                            lock_status = lock_response.get('status')

                            if lock_status == 'success':
                                display_message("Unlock failed, door locked", "lock")
                                response_data = {'status': 'unlock_failed'}
                            else:
                                print("Failed to lock the door")
                                display_message("Lock failed", "fail")
                                response_data = {'status': 'lock_failed'}
                            response_status = 500
                    else:
                        print("Invalid TOTP for admin")

                        # Lock the door after invalid TOTP attempt
                        lock_response = lock()
                        lock_status = lock_response.get('status')

                        if lock_status == 'success':
                            display_message("Invalid TOTP, door locked", "lock")
                            report_log.status = 'Invalid TOTP attempt'
                            db.session.commit()
                            response_data = {'status': 'invalid_totp'}
                            response_status = 403
                        else:
                            print("Failed to lock the door")
                            display_message("Lock failed", "fail")
                            response_data = {'status': 'lock_failed'}
                            response_status = 500

                elif user.role == 'faculty':
                    if not user.faculty_details:
                        print("Faculty details missing for user")
                        display_message("Faculty details missing", "lock")

                        lock_response = lock()
                        lock_status = lock_response.get('status')

                        if lock_status == 'success':
                            display_message("Faculty details missing", "lock")
                            report_log.status = 'Faculty details missing'
                            db.session.commit()
                            response_data = {'error': 'Faculty details missing'}
                            response_status = 400
                        else:
                            print("Failed to lock the door")
                            display_message("Lock failed", "fail")
                            response_data = {'status': 'lock_failed'}
                            response_status = 500

                    else:
                        # Debug: Print current time and day for comparison
                        print(f"Current time: {current_time}")
                        print(f"Current day: {current_day}")

                        # Fetch the latest schedule for the current day
                        user_schedule = Schedule.query.join(FacultyCourseSchedule,
                                                            FacultyCourseSchedule.schedule_id == Schedule.id).filter(
                            FacultyCourseSchedule.faculty_id == user.faculty_details.id,
                            Schedule.start_time <= current_time, Schedule.day == current_day).order_by(
                            desc(Schedule.start_time)).first()  # Fetch only the latest schedule

                        # Check if user_schedule is not None before accessing its attributes
                        if user_schedule and user_schedule.start_time and user_schedule.start_time <= current_time <= (
                                datetime.combine(datetime.today(), user_schedule.end_time) + timedelta(
                            minutes=15)).time():
                            if user_schedule:

                                user_schedule = user_schedule
                                print(
                                    f"Schedule found: {user_schedule.course.course_name} for {user_schedule.section.display_name}")
                                print(f"Scheduled day: {user_schedule.day}")
                                print(f"Scheduled start time: {user_schedule.start_time}")
                                print(f"Scheduled end time: {user_schedule.end_time}")

                                if not totp:
                                    print("TOTP required for faculty")
                                    display_message("TOTP required for faculty", "lock")
                                    response_data = {'status': 'totp_required'}
                                    response_status = 400
                                elif user.verify_totp(totp):
                                    faculty_session = FacultySession.query.filter_by(
                                        faculty_id=user.faculty_details.id,
                                        schedule_id=user_schedule.id,
                                        active=True
                                    ).first()

                                    if faculty_session or reader_type == "out":
                                        if faculty_session:
                                            faculty_session.active = False
                                            db.session.commit()

                                            # Update ReportLog with timeout
                                            report_log.time_out = datetime.now(timezone)
                                            report_log.status = 'Class dismissed'
                                            db.session.commit()

                                            print("Session ended, class dismissed")
                                            display_message("Class dismissed", "unlock")

                                            unlock_response = unlock()
                                            unlock_status = unlock_response.get('status')

                                            if unlock_status == 'success':
                                                display_message("Class dismissed", "unlock")
                                                response_data = {'status': 'class_dismissed', 'email': user.email}
                                                response_status = 200
                                            else:
                                                print("Failed to unlock the door")
                                                display_message("Unlock failed", "fail")

                                                lock_response = lock()
                                                lock_status = lock_response.get('status')

                                                if lock_status == 'success':
                                                    display_message("Unlock failed", "lock")
                                                    response_data = {'status': 'unlock_failed'}
                                                    response_status = 500
                                                else:
                                                    print("Failed to lock the door")
                                                    display_message("Lock failed", "fail")
                                                    response_data = {'status': 'lock_failed'}
                                                    response_status = 500
                                        else:
                                            print("No active session found to end")
                                            display_message("No active session", "lock")

                                            lock_response = lock()
                                            lock_status = lock_response.get('status')

                                            report_log.status = 'No Active session'
                                            db.session.commit()

                                            if lock_status == 'success':
                                                display_message("No active session", "lock")
                                                response_data = {'status': 'no_active_session'}
                                                response_status = 400
                                            else:
                                                print("Failed to lock the door")
                                                display_message("Lock failed", "fail")
                                                response_data = {'status': 'lock_failed'}
                                                response_status = 500

                                    else:
                                        faculty_session = FacultySession(
                                            faculty_id=user.faculty_details.id,
                                            authenticated_time=datetime.now(timezone),
                                            schedule_id=user_schedule.id,
                                            course_id=user_schedule.course_id,
                                            section_id=user_schedule.section_id,
                                            active=True
                                        )
                                        db.session.add(faculty_session)

                                        try:
                                            report_log.status = 'Timed in'
                                            db.session.commit()
                                        except sqlalchemy.orm.exc.StaleDataError:
                                            db.session.rollback()
                                            print("Ignoring stale data error and proceeding.")

                                        print("Faculty authenticated successfully")
                                        display_message("Faculty authenticated", "unlock")

                                        unlock_response = unlock()
                                        unlock_status = unlock_response.get('status')

                                        if unlock_status == 'success':
                                            display_message(
                                                f"Door unlocked at {formatted_time} for {user_schedule.course.course_name.title()} Scheduled at {user_schedule.start_time}",
                                                "unlock")
                                            response_data = {'status': 'faculty_authenticated', 'email': user.email}
                                            response_status = 200
                                        else:
                                            print("Failed to unlock the door")
                                            display_message("Unlock failed", "lock")

                                            lock_response = lock()
                                            lock_status = lock_response.get('status')

                                            if lock_status == 'success':
                                                display_message("Unlock failed", "lock")
                                                response_data = {'status': 'unlock_failed'}
                                                response_status = 500
                                            else:
                                                print("Failed to lock the door")
                                                display_message("Lock failed", "fail")
                                                response_data = {'status': 'lock_failed'}
                                                response_status = 500

                                else:
                                    print("Invalid TOTP for faculty")
                                    display_message("Invalid TOTP, SCAN RFID AGAIN", "lock")
                                    lock_response = lock()
                                    lock_status = lock_response.get('status')

                                    try:
                                        report_log.status = 'Invalid TOTP'
                                        db.session.commit()
                                    except sqlalchemy.orm.exc.StaleDataError:
                                        db.session.rollback()
                                        print("Ignoring stale data error and proceeding.")

                                    if lock_status == 'success':
                                        display_message("Invalid TOTP, SCAN RFID AGAIN", "lock")
                                        response_data = {'status': 'invalid_totp'}
                                        response_status = 403

                                    else:
                                        print("Failed to lock the door")
                                        display_message("Lock failed", "fail")
                                        response_data = {'status': 'lock_failed'}
                                        response_status = 500
                        else:
                            print("Faculty trying to access outside of schedule")

                            lock_response = lock()
                            lock_status = lock_response.get('status')

                            try:
                                report_log.status = 'No Schedule'
                                db.session.commit()
                            except sqlalchemy.orm.exc.StaleDataError:
                                db.session.rollback()
                                print("Ignoring stale data error and proceeding.")

                            if lock_status == 'success':
                                display_message(
                                    f"Faculty is trying to access outside of their schedule. ({user.f_name.title()} {user.l_name.title()}) ",
                                    "lock")
                                response_data = {'status': 'outside_schedule'}
                                response_status = 403
                            else:
                                print("Failed to lock the door")
                                display_message("Lock failed", "fail")
                                response_data = {'status': 'lock_failed'}
                                response_status = 500

                elif user.role == 'student':

                    print("Handling student attendance")
                    if not user.student_details:
                        print("Student details missing for user")
                        display_message("Student details missing", "lock")
                        lock_response = lock()
                        lock_status = lock_response.get('status')
                        report_log.status = 'Student details missing'
                        if lock_status == 'success':
                            display_message("Student details missing", "lock")
                            response_data = {'error': 'Student details missing'}
                            response_status = 400
                        else:
                            print("Failed to lock the door")
                            display_message("Lock failed", "fail")
                            response_data = {'status': 'lock_failed'}
                            response_status = 500
                    else:
                        faculty_session = FacultySession.query.filter_by(
                            active=True
                        ).order_by(FacultySession.authenticated_time.desc()).first()

                        # Query to get the first faculty with an active session
                        faculty = (
                            db.session.query(Faculty)
                            .join(FacultySession, Faculty.id == FacultySession.faculty_id)
                            .filter(FacultySession.active == True)
                            .order_by(FacultySession.authenticated_time.desc())
                            .first()
                        )

                        if not faculty_session:
                            print("No active faculty session found")

                            lock_response = lock()
                            lock_status = lock_response.get('status')
                            try:
                                report_log.status = 'Faculty unauthenticated'
                                db.session.commit()
                            except sqlalchemy.orm.exc.StaleDataError:
                                db.session.rollback()
                                print("Ignoring stale data error and proceeding.")

                            if lock_status == 'success':
                                display_message(f"Faculty is still not yet authenticated, let them in first", "lock")
                                response_data = {'status': 'faculty_not_authenticated'}
                                response_status = 403
                                report_log.status = 'Faculty not entered yet'
                                db.session.commit()

                            else:
                                print("Failed to lock the door")
                                display_message("Lock failed", "fail")
                                response_data = {'status': 'lock_failed'}
                                response_status = 500
                        else:
                            print(f"Found active faculty session: {faculty_session}")
                            authenticated_time = faculty_session.authenticated_time.astimezone(timezone)

                            # Get the schedule
                            schedule = Schedule.query.get(faculty_session.schedule_id)

                            # Combine the date of authenticated_time with schedule.end_time and ensure both are in the same timezone
                            session_end_datetime = datetime.combine(authenticated_time.date(),
                                                                    schedule.end_time).astimezone(timezone)

                            # Add 15 minutes to session_end_datetime to allow for timeout
                            session_end_datetime += timedelta(minutes=15)

                            # Get the current time
                            current_time = datetime.now(timezone)

                            if current_time <= session_end_datetime or reader_type == "out":
                                # Continue the logic

                                schedule_id = faculty_session.schedule_id
                                course_id = faculty_session.course_id
                                section_id = faculty_session.section_id
                                # Verify the student is associated with the program and schedule (regular or irregular)
                                enrolled_in_course = db.session.query(student_course_association).filter_by(
                                    student_id=user.student_details.id,
                                    course_id=course_id,
                                    schedule_id=schedule_id,

                                ).first()

                                if not enrolled_in_course:
                                    print("Student is not authorized for this program or schedule")
                                    display_message("Unauthorized access", "lock")

                                    lock_response = lock()
                                    lock_status = lock_response.get('status')

                                    try:
                                        report_log.status = 'Unauthorized access'
                                        db.session.commit()
                                    except sqlalchemy.orm.exc.StaleDataError:
                                        db.session.rollback()
                                        print("Ignoring stale data error and proceeding.")

                                    if lock_status == 'success':
                                        display_message("Unauthorized access", "lock")
                                        response_data = {'status': 'unauthorized_student'}
                                        response_status = 403
                                    else:
                                        print("Failed to lock the door")
                                        display_message("Lock failed", "fail")
                                        response_data = {'status': 'lock_failed'}
                                        response_status = 500

                                else:
                                    today = datetime.now(timezone).date()
                                    # Fetch the current schedule details
                                    current_schedule = Schedule.query.filter_by(id=faculty_session.schedule_id).first()
                                    attendance = Attendance.query.filter_by(
                                        student_id=user.student_details.id,
                                        course_id=course_id
                                    ).filter(db.func.date(Attendance.time_in) == today).first()

                                    course = Course.query.filter_by(id=course_id).first()
                                    student = user.student_details  # Assuming this already includes student details
                                    student_number = student.student_number  # Assuming this already includes student details
                                    program_code = student.program.program_code  # Assuming program relationship exists
                                    level_code = student.year_level.level_code  # Assuming level relationship exists
                                    section = student.section.display_name  # Assuming section relationship exists
                                    semester = student.semester.display_name  # Assuming semester relationship exists

                                    if reader_type == "in":
                                        if attendance and attendance.time_in:
                                            # Attendance already recorded
                                            print(
                                                f"Attendance already recorded for student {user.email} for this schedule today")

                                            display_message("Attendance already recorded for this schedule today",
                                                            "unlock")

                                            # Update report_log status and commit
                                            try:
                                                report_log.status = 'Attendance already recorded'
                                                db.session.commit()
                                            except sqlalchemy.orm.exc.StaleDataError:
                                                db.session.rollback()
                                                print("Ignoring stale data error and proceeding.")

                                            unlock_response = unlock()
                                            unlock_status = unlock_response.get('status')

                                            if unlock_status == 'success':
                                                display_message(
                                                    f"Attendance already recorded, Door unlocked at {formatted_time}",
                                                    "unlock")
                                                response_data = {'status': 'attendance_already_recorded_today'}
                                                response_status = 200
                                            else:
                                                print("Failed to unlock the door")
                                                display_message("Unlock failed", "lock")

                                                lock_response = lock()
                                                lock_status = lock_response.get('status')

                                                if lock_status == 'success':
                                                    display_message("Unlock failed", "lock")
                                                    response_data = {'status': 'unlock_failed'}
                                                    response_status = 200
                                                else:
                                                    print("Failed to lock the door")
                                                    display_message("Lock failed", "fail")
                                                    response_data = {'status': 'lock_failed'}
                                                    response_status = 500

                                        else:
                                            # Create new attendance record if it doesn't exist
                                            if not attendance:
                                                attendance = Attendance(
                                                    time_in=datetime.now(timezone),
                                                    student_id=user.student_details.id,
                                                    course_id=course_id,
                                                    course_name=course.course_name,
                                                    student_name=f"{student.user.f_name} {student.user.m_name} {student.user.l_name}",
                                                    student_number=student_number,
                                                    program_code=program_code,
                                                    level_code=level_code,
                                                    section=section,
                                                    semester=semester,
                                                    faculty_id=faculty.id,
                                                    faculty_name=f"{faculty.full_name}",
                                                )
                                                db.session.add(attendance)
                                            else:
                                                # Update time_in for existing attendance
                                                attendance.time_in = datetime.now(timezone)

                                            # Update report_log status and commit
                                            try:
                                                report_log.status = 'Attendance recorded'
                                                db.session.commit()
                                            except Exception as e:
                                                db.session.rollback()
                                                print(f"Error updating report log: {str(e)}")

                                            print(
                                                f"Attendance recorded for student {user.email} for this schedule today")
                                            display_message("Attendance recorded for this schedule today", "unlock")

                                            unlock_response = unlock()
                                            unlock_status = unlock_response.get('status')

                                            if unlock_status == 'success':
                                                display_message(
                                                    f"Attendance recorded for this schedule today, Door unlocked at {formatted_time}",
                                                    "unlock")
                                                response_data = {'status': 'attendance_recorded_today'}
                                                response_status = 200
                                            else:
                                                print("Failed to unlock the door")
                                                display_message("Unlock failed", "lock")

                                                lock_response = lock()
                                                lock_status = lock_response.get('status')

                                                if lock_status == 'success':
                                                    display_message("Unlock failed", "lock")
                                                    response_data = {'status': 'unlock_failed'}
                                                    response_status = 200
                                                else:
                                                    print("Failed to lock the door")
                                                    display_message("Lock failed", "fail")
                                                    response_data = {'status': 'lock_failed'}
                                                    response_status = 500

                                    elif reader_type == "out":
                                        if attendance and not attendance.time_out:
                                            attendance.time_out = datetime.now(timezone)
                                            attendance.course_name = course.course_name  # Ensure program name is updated
                                            attendance.student_name = f"{student.user.f_name} {student.user.m_name} {student.user.l_name}"  # Ensure student name is updated
                                            attendance.student_number = student_number,
                                            attendance.program_code = program_code  # Ensure program code is updated
                                            attendance.level_code = level_code  # Ensure level code is updated
                                            attendance.section = section  # Ensure section is updated
                                            attendance.semester = semester  # Ensure semester is updated
                                            report_log.time_out = attendance.time_out  # Update the ReportLog with timeout
                                            report_log.status = 'Time in & out'
                                            db.session.commit()
                                            print(f"Time-out recorded for student {user.email}")
                                            display_message("Time-out recorded", "unlock")

                                            unlock_response = unlock()
                                            unlock_status = unlock_response.get('status')

                                            if unlock_status == 'success':
                                                display_message(
                                                    f"Time-out recorded for {user.f_name.title()} {user.student_details.program_section} Door unlocked at {formatted_time}",
                                                    "unlock")
                                                response_data = {'status': 'checkout_recorded', 'email': user.email}
                                                response_status = 200
                                            else:
                                                print("Failed to unlock the door")
                                                display_message("Unlock failed", "lock")

                                                lock_response = lock()
                                                lock_status = lock_response.get('status')

                                                if lock_status == 'success':
                                                    display_message("Unlock failed", "lock")
                                                    response_data = {'status': 'unlock_failed'}
                                                    response_status = 200
                                                else:
                                                    print("Failed to lock the door")
                                                    display_message("Lock failed", "fail")
                                                    response_data = {'status': 'lock_failed'}
                                                    response_status = 500
                                        else:
                                            print("No time-in found or already timed out")
                                            display_message("No time-in found", "lock")

                                            lock_response = lock()
                                            lock_status = lock_response.get('status')
                                            report_log.status = 'No time-in'
                                            db.session.commit()

                                            if lock_status == 'success':
                                                display_message("No time-in found", "lock")
                                                response_data = {'status': 'no_timein_found_or_already_timed_out'}
                                                response_status = 200
                                            else:
                                                print("Failed to lock the door")
                                                display_message("Lock failed", "fail")
                                                response_data = {'status': 'lock_failed'}
                                                response_status = 500
                            else:
                                print("Faculty authentication expired")
                                display_message("Faculty auth expired", "lock")
                                faculty_session.active = False
                                db.session.commit()
                                lock_response = lock()
                                lock_status = lock_response.get('status')
                                report_log.status = 'Faculty auth expired'
                                db.session.commit()

                                if lock_status == 'success':
                                    display_message("Faculty auth expired", "lock")
                                    response_data = {'status': 'faculty_auth_expired'}
                                    response_status = 200
                                else:
                                    print("Failed to lock the door")
                                    display_message("Lock failed", "fail")
                                    response_data = {'status': 'lock_failed'}
                                    response_status = 500
                else:
                    print(f"Unexpected role for user: {user.role}")
                    display_message("Unexpected role", "lock")

                    lock_response = lock()
                    lock_status = lock_response.get('status')
                    report_log.status = 'Unexpected user role'
                    db.session.commit()

                    if lock_status == 'success':
                        display_message("Unexpected role", "lock")
                        response_data = {'error': 'Unexpected role'}
                        response_status = 400
                    else:
                        print("Failed to lock the door")
                        display_message("Lock failed", "fail")
                        response_data = {'status': 'lock_failed'}
                        response_status = 500

        # Final response
        return response_data, response_status

    # Function to display a message on the LCD
    def display_message(message, message_type):
        try:
            # Replace spaces with %20 for URL encoding
            message = message.replace(' ', '%20')
            # URL encode the message type as well
            message_type = message_type.replace(' ', '%20')
            try:
                response = requests.get(f'http://{ARDUINO_IP}:{ARDUINO_PORT}/display?msg={message}&type={message_type}',
                                        timeout=5)
                print(response.text)
                return {'status': 'success', 'response': response.text}
            except requests.exceptions.Timeout:
                print("Request timed out")
            except requests.exceptions.RequestException as e:
                print(f"An error occurred: {e}")
            print("Message displayed on LCD and matrix")
        except requests.RequestException as e:
            print(f"Error displaying message: {e}")
            return {'status': 'error', 'message': str(e)}

    # Route to render the control page
    @app.route('/control-page')
    @login_required
    def control_page():
        if not current_user.faculty_details:
            return redirect(url_for('faculty_acc.view_students'))  # Redirect to an appropriate page

        # Check if the current user has faculty details
        faculty_id = current_user.faculty_details.id
        if not faculty_id or not current_user.faculty_details:
            flash("Faculty details are not available for the current user", "danger")
            return redirect(url_for('faculty_acc.view_students'))  # Redirect to an appropriate page

        timezone = pytz.timezone('Asia/Manila')
        faculty = Faculty.query.filter_by(id=faculty_id, user_id=current_user.id).first_or_404()

        # Get current day and time
        current_day = datetime.now(timezone).strftime('%A')  # 'Monday', 'Tuesday', etc.
        current_time = datetime.now(timezone).time()

        # Print current day and time for debugging
        print(f"Current day: {current_day}")
        print(f"Current time: {current_time}")

        # Query schedules for the faculty
        schedules = Schedule.query.join(Course, Schedule.course_id == Course.id) \
            .join(FacultyCourseSchedule, Schedule.id == FacultyCourseSchedule.schedule_id) \
            .join(Faculty, FacultyCourseSchedule.faculty_id == Faculty.id) \
            .join(Program, FacultyCourseSchedule.program_id == Program.id) \
            .join(YearLevel, FacultyCourseSchedule.year_level_id == YearLevel.id) \
            .join(Section, FacultyCourseSchedule.section_id == Section.id) \
            .join(Semester, FacultyCourseSchedule.semester_id == Semester.id) \
            .filter(Faculty.id == faculty.id).all()

        # Check if the current time and day is within any of the faculty's scheduled times
        access_allowed = False
        for sched in schedules:
            # Extend the end time by one hour
            extended_end_time = (
                    datetime.combine(datetime.now(timezone), sched.end_time) + timedelta(minutes=15)).time()

            # Print schedule details for debugging
            print(f"Schedule day: {sched.day.name}")
            print(f"Schedule start time: {sched.start_time}")
            print(f"Schedule end time: {sched.end_time}")
            print(f"Extended end time: {extended_end_time}")

            # Compare both the day and time
            if sched.day.name == current_day.upper() and sched.start_time <= current_time <= extended_end_time:
                access_allowed = True
                break

        if not access_allowed:
            flash("Access is not allowed at this time", "danger")
            return redirect(url_for('faculty_acc.view_students'))

        # Render the control page if access is allowed
        return render_template('faculty_acc/lock_control.html')

    # Route to handle the unlock action with schedule check
    @app.route('/unlock', methods=['POST'])
    @login_required
    @csrf.exempt
    def unlock_route():
        result = unlock()
        if result['status'] == 'success':
            flash('Door unlocked successfully', 'success')
        else:
            flash(f"Error unlocking the door: {result['message']}", 'danger')
        return redirect(url_for('control_page'))

    # Route to handle the lock action with schedule check
    @app.route('/lock', methods=['POST'])
    @login_required
    @csrf.exempt
    def lock_route():
        result = lock()
        if result['status'] == 'success':
            flash('Door locked successfully', 'success')
        else:
            flash(f"Error locking the door: {result['message']}", 'danger')
        return redirect(url_for('control_page'))

    # RESET TOTP LOGICS:
    def generate_token(email):
        serializer = URLSafeTimedSerializer(os.environ.get('SECRET_KEY'))
        token = serializer.dumps(email, salt='totp-secret-reset-salt')

        # Find the user and store the hashed token in the database
        user = User.query.filter_by(email=email).first()
        if user:
            user.totp_reset_token = generate_password_hash(token, 'pbkdf2')  # Hashing the token
            user.totp_token_used = False  # Reset the token status
            db.session.commit()

        return token

    def confirm_token(token, expiration=3600):
        serializer = URLSafeTimedSerializer(os.environ.get('SECRET_KEY'))
        try:
            email = serializer.loads(
                token,
                salt='totp-secret-reset-salt',
                max_age=expiration
            )
        except:
            return False

        # Check if the token matches and hasn't been used
        user = User.query.filter_by(email=email).first()
        if not user or not user.totp_reset_token:
            return False

        if user.totp_token_used:
            return False  # The token has already been used

        # Check if the provided token matches the one in the database
        if not check_password_hash(user.totp_reset_token, token):
            return False

        return email

    def send_reset_email(user_email):
        token = generate_token(user_email)
        reset_url = url_for('reset_totp', token=token, _external=True)

        msg = Message('Reset Your TOTP Secret Key',
                      sender=os.environ.get('MAIL_USERNAME'),
                      recipients=[user_email])
        msg.body = f'Click the link to reset your TOTP secret key: {reset_url}'
        mail.send(msg)

    @app.route('/request_totp_reset', methods=['GET', 'POST'])
    @login_required
    def request_totp_reset():
        if not current_user.totp_verified:
            flash(
                'You still haven\'t verified your current TOTP')
            return redirect(url_for('login.login'))
        form = RequestTOTPResetForm()
        if request.method == 'POST':
            # Debugging print statement
            print("POST request received")
            send_reset_email(current_user.email)
            flash('An email has been sent with instructions to reset your TOTP secret key.')
            return redirect(url_for('login.login'))
        return render_template('request_totp_reset.html', form=form)

    @app.route('/reset_totp/<token>', methods=['GET', 'POST'])
    def reset_totp(token):
        email = confirm_token(token)
        if not email:
            flash('The reset link is invalid or has expired.', 'danger')
            return redirect(url_for('login.login'))

        user = User.query.filter_by(email=email).first()
        if user is None:
            flash('User not found.', 'danger')
            return redirect(url_for('login.login'))

        # Ensure the token has not been used
        if user.totp_token_used:
            flash('The reset link has already been used.', 'danger')
            return redirect(url_for('login.login'))

        # Here, generate and update the new TOTP secret key
        user.totp_secret.secret_key = pyotp.random_base32()
        user.totp_verified = False
        user.totp_token_used = True  # Mark the token as used
        db.session.commit()

        flash('Your TOTP secret key has been reset. Please configure your authenticator app again.', 'success')
        return redirect(url_for('login.login'))

    # 400 Error Handler for Bad Requests
    @app.errorhandler(400)
    def bad_request_error(error):
        return render_template('error/400.html', message="The CSRF token has expired."), 400

    # 403 Error Handler
    @app.errorhandler(403)
    def not_found_error(error):
        return render_template('error/403.html'), 403

    # 404 Error Handler
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('error/404.html'), 404

    # 405 Error Handler
    @app.errorhandler(405)
    def not_found_error(error):
        return render_template('error/405.html'), 405

    # 500 Error Handler
    @app.errorhandler(500)
    def internal_error(error):
        return render_template('error/500.html'), 500

    # 503 Error Handler
    @app.errorhandler(503)
    def service_unavailable_error(error):
        return render_template('error/503.html'), 503

    # 504 Error Handler
    @app.errorhandler(504)
    def gateway_timeout_error(error):
        return render_template('error/504.html'), 504

    return app


if __name__ == "__main__":
    app = create_app()

    serve(app, host="0.0.0.0", port=5000)  # Use Waitress instead of app.run()

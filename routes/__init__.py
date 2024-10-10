from routes.admin.course_routes import course_bp
from routes.faculty.faculty_acc_routes import faculty_acc_bp
from routes.student.student_acc_routes import student_acc_bp
from routes.admin.student_routes import student_bp
from routes.admin.subject.subject_routes import subject_bp
from routes.admin.schedule_routes import schedule_bp
from routes.admin.faculty_routes import faculty_bp
from routes.admin.dashboard_routes import dashboard_bp
from .admin.admin_acc_routes import admin_acc_bp
from .admin.admin_routes import admin_bp
from .admin.attendance_routes import attendance_bp
from .admin.report_routes import report_bp
from .admin.subject.add_sub_per_course import add_sub_per_course_bp
from .auth.google_routes import google_bp
from .auth.login_routes import login_bp
from routes.auth.totp_routes import totp_bp


def register_blueprints(app):
    # Auth routes
    app.register_blueprint(google_bp, url_prefix='/google')
    app.register_blueprint(totp_bp, url_prefix='/totp')
    app.register_blueprint(login_bp, url_prefix='/login')

    # Admin routes
    app.register_blueprint(dashboard_bp, url_prefix='/')
    app.register_blueprint(admin_acc_bp, url_prefix='/admin_acc')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(subject_bp, url_prefix='/subjects')
    app.register_blueprint(schedule_bp, url_prefix='/schedules')
    app.register_blueprint(faculty_bp, url_prefix='/faculties')
    app.register_blueprint(student_bp, url_prefix='/students')
    app.register_blueprint(course_bp, url_prefix='/courses')
    app.register_blueprint(report_bp, url_prefix='/reports')
    app.register_blueprint(attendance_bp, url_prefix='/attendances')

    # Admin - Subject routes
    app.register_blueprint(add_sub_per_course_bp, url_prefix='/add_sub_per_course')

    # Instructor routes
    app.register_blueprint(faculty_acc_bp, url_prefix='/faculty_acc')

    # Student routes
    app.register_blueprint(student_acc_bp, url_prefix='/student_acc')

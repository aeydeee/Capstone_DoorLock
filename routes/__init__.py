from .auth_routes import auth_bp
from .instructor_student_routes import instructor_bp
from .student_routes import student_bp
from .subject_routes import subject_bp
from .schedule_routes import schedule_bp
from .faculty_routes import faculty_bp
from .dashboard_routes import dashboard_bp


def register_blueprints(app):
    app.register_blueprint(dashboard_bp, url_prefix='/')
    app.register_blueprint(auth_bp, url_prefix='/auth')

    # Admin routes
    app.register_blueprint(subject_bp, url_prefix='/subjects')
    app.register_blueprint(schedule_bp, url_prefix='/schedules')
    app.register_blueprint(faculty_bp, url_prefix='/faculties')
    app.register_blueprint(student_bp, url_prefix='/students')

    # Instructor routes
    app.register_blueprint(instructor_bp, url_prefix='/instructors')

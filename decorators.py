# decorators.py
from functools import wraps
from flask import redirect, url_for, flash, session
from flask_login import current_user


# Common redirect function for unauthenticated users
def unauthorized_redirect(message, category='danger', redirect_route='login.login'):
    flash(message, category)
    return redirect(url_for(redirect_route))


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            return unauthorized_redirect('You must be an admin to access this page.', 'danger',
                                         'faculty_acc.view_students')
        return f(*args, **kwargs)

    return decorated_function


def cspc_acc_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Debugging print statement to see what is happening
        print(
            f"Current User Authenticated: {current_user.is_authenticated}, Role: {getattr(current_user, 'role', None)}, Email: {getattr(current_user, 'email', None)}")

        if current_user.is_authenticated and current_user.email.split('@')[1] == "cspc.edu.ph":
            return f(*args, **kwargs)
        else:
            flash("Access denied. Faculty members only.", category="error")
            return redirect(url_for('login.login'))  # Redirect to login or another page

    return decorated_function


def faculty_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'faculty':
            return unauthorized_redirect('You must be a faculty to access this page.')
        return f(*args, **kwargs)

    return decorated_function


def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print(f"Checking student access for user: {current_user.email}")
        if not current_user.is_authenticated or current_user.role != 'student':
            flash('Access denied: You do not have permission to view this schedule.', 'error')
            return redirect(url_for('login.login'))

        if current_user.email.split('@')[1] == "my.cspc.edu.ph":
            return f(*args, **kwargs)
        else:
            flash("Access denied. Student members only.", category="error")
            return redirect(url_for('login.login'))

    return decorated_function


def email_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        email = session.get('user_email')
        print(f"Email required: {email}")
        if not email:
            flash("No email found in session.", category="error")
            return redirect(url_for('login.login'))
        return f(*args, **kwargs)

    return decorated_function


def own_student_account_required(f):
    @wraps(f)
    def decorated_function(student_id, *args, **kwargs):
        # Ensure the student_id matches the logged-in student's ID
        if current_user.student_details.id != student_id:
            return unauthorized_redirect('Access denied: You can only view your own account.', 'error', 'login.login')
        return f(student_id, *args, **kwargs)

    return decorated_function


def own_faculty_account_required(f):
    @wraps(f)
    def decorated_function(faculty_id, *args, **kwargs):
        # Ensure the faculty_id matches the logged-in faculty's ID
        if current_user.faculty_details.id != faculty_id:
            return unauthorized_redirect('Access denied: You can only view your own account.', 'error', 'login.login')
        return f(faculty_id, *args, **kwargs)

    return decorated_function


def check_totp_verified(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.totp_verified:
            flash('Please complete the Profile Page and verify your TOTP first!')
            # Check if the user is a faculty or a student and redirect accordingly
            if current_user.role == 'faculty':
                return redirect(url_for('faculty_acc.faculty_profile',
                                        faculty_id=current_user.faculty_details.id))  # Redirect faculty to their profile
            elif current_user.role == 'student':
                return redirect(url_for('student_acc.student_profile',
                                        student_id=current_user.student_details.id))  # Redirect student to their profile
        return f(*args, **kwargs)

    return decorated_function

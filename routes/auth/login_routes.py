from flask import Blueprint, url_for, redirect, flash, session, render_template
from flask_login import current_user, login_required, logout_user, login_user
from werkzeug.security import check_password_hash

from models import User
from webforms.login_form import LoginForm

from fuzzywuzzy import fuzz
from fuzzywuzzy import process

login_bp = Blueprint('login', __name__)


@login_bp.route('/', methods=['POST', 'GET'])
def login():
    """User login route."""
    if current_user.is_authenticated and current_user.student_details:
        student_id = current_user.student_details.id
        return redirect(url_for('student_acc.view_student_account_schedule', student_id=student_id))
    elif current_user.is_authenticated and current_user.role == 'admin':
        return redirect(url_for('dashboard.dashboard'))
    elif current_user.is_authenticated and current_user.role == 'faculty':
        return redirect(url_for('faculty_acc.view_detailed_attendance'))

    form = LoginForm()

    if form.validate_on_submit():
        input_email = form.email.data
        # Fetch all users and their emails
        users = User.query.all()

        # Get the closest email match with a threshold
        email_choices = [user.email for user in users]
        closest_email, match_score = process.extractOne(input_email, email_choices, scorer=fuzz.ratio)

        # Set a threshold for the match score (e.g., 80 means 80% similarity)
        if match_score < 80:
            flash('Invalid email, or totp code.', 'error')
            return redirect(url_for('login.login'))

        # Fetch the user with the closest matching email
        user = User.query.filter_by(email=closest_email).first()
        print(user)

        if user is None:
            flash('Invalid email, or totp code.', 'error')
            return redirect(url_for('login.login'))

        role_details = getattr(user, f"{user.role}_details", None)
        print(role_details)

        if role_details:
            if user.verify_totp(form.totp_code.data):
                login_user(user)
                flash('Successfully logged in!', 'success')
                return redirect(url_for('dashboard.dashboard'))
            else:
                flash('Invalid TOTP code or email.', 'error')
        else:
            flash('Incorrect email details not found.', 'error')

    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error: {error}", 'error')

    return render_template('user/login.html', form=form)


# Create a Logout Page
@login_bp.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    flash('Successfully logged out')
    return redirect(url_for('login.login'))

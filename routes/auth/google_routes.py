import random
import string

from flask import flash, redirect, url_for, session
from flask_login import current_user, login_user, logout_user
from flask_dance.contrib.google import make_google_blueprint
from flask_dance.consumer import oauth_authorized, oauth_error
from flask_dance.consumer.storage.sqla import SQLAlchemyStorage
from sqlalchemy.exc import IntegrityError

from app import db
from models import OAuth, User, Student, Faculty

google_bp = make_google_blueprint(
    scope=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email"],
    storage=SQLAlchemyStorage(OAuth, db.session, user=current_user),
)


# Create/login local user on successful OAuth login
@oauth_authorized.connect_via(google_bp)
def google_logged_in(blueprint, token):
    if not token:
        flash("Failed to log in.", category="error")
        return redirect(url_for('login.login'))

    resp = blueprint.session.get("/oauth2/v3/userinfo")
    if not resp.ok:
        flash("Failed to fetch user info.", category="error")
        return redirect(url_for('login.login'))

    info = resp.json()
    user_id = info["sub"]
    email = info["email"]
    email_domain = email.split('@')[1]

    # Extract profile picture URL and modify to high resolution
    picture = info.get("picture", "")
    if picture:
        picture = picture.replace("=s96-c", "=s400")  # Request higher resolution

    username = email.split('@')[0]  # Extract username

    # Check email domain
    if email_domain not in ["my.cspc.edu.ph", "cspc.edu.ph"]:
        flash("Unauthorized email domain. Access denied.", category="error")
        return redirect(url_for('login.login'))

    role = 'student' if email_domain == "my.cspc.edu.ph" else 'faculty'

    try:
        # Check if user exists
        user = User.query.filter_by(email=email).first()

        if user:
            user.profile_pic = picture

            # Check or create OAuth entry
            oauth = OAuth.query.filter_by(provider=blueprint.name, provider_user_id=user_id).first()
            if oauth is None:
                oauth = OAuth(provider=blueprint.name, provider_user_id=user_id, token=token)
                oauth.user = user
                db.session.add(oauth)
            else:
                oauth.token = token

            db.session.commit()
            login_user(user)
        else:
            # Create new user
            user = User(email=email, role=role, profile_pic=picture)
            db.session.add(user)
            db.session.flush()

            if role == 'student':
                student = Student(user_id=user.id, student_number="Change this!")
                db.session.add(student)
            elif role == 'faculty':
                faculty = Faculty(user_id=user.id, faculty_number="Change this!")
                db.session.add(faculty)

            oauth = OAuth(provider=blueprint.name, provider_user_id=user_id, token=token)
            oauth.user = user
            db.session.add(oauth)

            db.session.commit()
            login_user(user)

    except IntegrityError as e:
        db.session.rollback()
        flash(f"Integrity Error: {str(e.orig)}", category="error")
        return redirect(url_for('login.login'))

    # Redirect to profile page if TOTP not verified
    if not current_user.totp_verified:
        if role == 'student':
            return redirect(url_for('student_acc.student_profile', student_id=current_user.student_details.id))
        elif role == 'faculty':
            return redirect(url_for('faculty_acc.faculty_profile', faculty_id=current_user.faculty_details.id))

    # Store the email in the session
    session['user_email'] = email

    # After the user creation and login process
    if role == 'student':
        if 'student' in locals():
            return redirect(url_for('login.login'))
        elif current_user.totp_verified is False:
            return redirect(url_for('student_acc.student_profile', student_id=current_user.student_details.id))
        else:
            flash("Student account existing already.", category="error")
            return redirect(url_for('login.login'))
    elif role == 'faculty':
        if 'faculty' in locals():
            return redirect(url_for('login.login'))
        elif current_user.totp_verified is False:
            return redirect(url_for('faculty_acc.faculty_profile', faculty_id=current_user.faculty_details.id))
        else:
            flash("Faculty account existing already.", category="error")
            return redirect(url_for('login.login'))

    return False


# Notify on OAuth provider error
@oauth_error.connect_via(google_bp)
def google_error(blueprint, message, response):
    msg = f"OAuth error from {blueprint.name}! message={message} response={response}"
    flash(msg, category="error")

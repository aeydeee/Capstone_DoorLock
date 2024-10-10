from io import BytesIO

import pyqrcode
from flask import Blueprint, redirect, url_for, session, flash, render_template, abort, request

from app import db
from models import User
from webforms.totp_form import TOTPForm

totp_bp = Blueprint('totp', __name__)


@totp_bp.route('/twofactor')
def two_factor_setup():
    form = TOTPForm()
    if 'email' not in session:
        return redirect(url_for('login.login'))

    user = User.query.filter_by(email=session['email']).first()
    if user is None:
        return redirect(url_for('login.login'))

    if user.totp_verified and user.role == 'admin':
        flash('TOTP is already set up. Proceed to your dashboard.', 'info')
        return redirect(url_for('dashboard.dashboard'))
    elif user.totp_verified and user.role == 'faculty':
        flash('TOTP is already set up. Proceed to your account page.', 'info')
        return redirect(url_for('faculty_acc.view_students'))
    elif user.totp_verified:
        flash('TOTP is already set up. Proceed to your account page.', 'info')
        return redirect(url_for('login.login'))

    secret_key = user.totp_secret.secret_key
    return render_template('totp/two-factor-setup.html', secret_key=secret_key, form=form), 200, {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
    }


@totp_bp.route('/verify-totp', methods=['GET', 'POST'])
def verify_totp():
    if 'email' not in session:
        flash('Session expired. Please log in again.', 'danger')
        return redirect(url_for('login.login'))

    user = User.query.filter_by(email=session['email']).first()
    if user is None:
        flash('Invalid session data. Please log in again.', 'danger')
        return redirect(url_for('login.login'))

    form = TOTPForm()

    if request.method == 'POST' and form.validate_on_submit():  # Ensure form validation
        token = form.totp.data

        if user.verify_totp(token):
            # Mark the TOTP setup as complete
            user.totp_verified = True
            db.session.commit()

            # Remove email from session and redirect to dashboard
            del session['email']
            flash('TOTP verified successfully!', 'success')
            return redirect(url_for('login.login'))
        else:
            flash('Invalid TOTP code. Please try again.', 'danger')

    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error: {error}", 'error')

    return render_template('totp/verify-totp.html', form=form)


@totp_bp.route('/qrcode')
def qrcode():
    if 'email' not in session:
        abort(404)
    user = User.query.filter_by(email=session['email']).first()
    if user is None:
        abort(404)

    # render QR code for TOTP
    url = pyqrcode.create(user.get_totp_uri())
    stream = BytesIO()
    url.svg(stream, scale=3)
    return stream.getvalue(), 200, {
        'Content-Type': 'image/svg+xml',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
    }

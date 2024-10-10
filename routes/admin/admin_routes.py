import io
import re

import pyqrcode
from flask import Blueprint, render_template, flash, request, redirect, url_for, abort
from flask_login import login_required, current_user
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from app import db
from decorators import cspc_acc_required, admin_required
from models import Admin, User
from webforms.admin_form import AdminForm
from webforms.delete_form import DeleteForm

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/qrcode/<int:admin_id>')
def admin_qrcode(admin_id):
    admin = Admin.query.get_or_404(admin_id)
    if admin.user.totp_secret is None:
        abort(404)

    # Generate QR code for TOTP using the admin's secret key
    url = pyqrcode.create(admin.user.get_totp_uri())
    stream = io.BytesIO()
    url.svg(stream, scale=3)
    return stream.getvalue(), 200, {
        'Content-Type': 'image/svg+xml',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
    }


@admin_bp.route('/', methods=['GET', 'POST'])
@login_required
@cspc_acc_required
@admin_required
def manage_admin():
    delete_form = DeleteForm()

    admins = Admin.query.all()
    return render_template('admin/manage_admin.html', admins=admins, delete_form=delete_form)


@admin_bp.route("/add", methods=["GET", "POST"])
@login_required
@cspc_acc_required
@admin_required
def add_admin():
    form = AdminForm()
    print("Raw form data:", request.form)
    if form.validate_on_submit():
        def clean_field(field_value):
            return " ".join(field_value.strip().split())

        def convert_to_hex(rfid_uid):
            try:
                # Try to interpret the RFID UID as an integer (which means it's in decimal)
                rfid_int = int(rfid_uid)

                # Convert the integer to a hexadecimal string
                rfid_hex = format(rfid_int, '08X')

                # Adjust the byte order (reverse for little-endian)
                rfid_hex = ''.join(reversed([rfid_hex[i:i + 2] for i in range(0, len(rfid_hex), 2)]))

                return rfid_hex
            except ValueError:
                # If it raises a ValueError, it means rfid_uid is already a valid hexadecimal string
                return rfid_uid.lower()  # Return as lowercase hex

        def is_valid_cspc_email(email):
            """Check if the email ends with '@cspc.edu.ph'."""
            return email.lower().endswith('@cspc.edu.ph')

        rfid_uid = form.rfid_uid.data if form.rfid_uid.data else None  # Set to None if blank

        # Convert RFID UID to hexadecimal only if not None
        if rfid_uid:
            rfid_uid = convert_to_hex(rfid_uid)

        # Check if the email is valid
        email = clean_field(form.email.data.lower())
        if not is_valid_cspc_email(email):
            flash('Email must be from the CSPC domain', 'error')
            return render_template('admin/add_admin.html', form=form)

        # Check for existing email, username, and admin number
        rfid_uid_exists = User.query.filter_by(rfid_uid=rfid_uid).first() if rfid_uid else None
        email_exists = User.query.filter_by(email=clean_field(form.email.data.lower())).first()
        school_id_exists = Admin.query.filter_by(school_id=clean_field(form.school_id.data.lower())).first()

        if rfid_uid_exists:
            flash('RFID was already used', 'error')
        elif email_exists:
            flash('Email was already registered', 'error')
        elif school_id_exists:
            flash('Admin Number is already in use', 'error')
        else:
            try:
                with db.session.begin_nested():
                    # # Hash the password

                    # Create User instance
                    user = User(
                        rfid_uid=rfid_uid,  # Will be None if empty
                        f_name=clean_field(form.f_name.data.lower()),
                        l_name=clean_field(form.l_name.data.lower()),
                        m_name=clean_field(form.m_name.data.lower()),
                        # m_initial=clean_field(form.m_initial.data.lower()),
                        email=clean_field(form.email.data.lower()),
                        role='admin',
                        gender=clean_field(form.gender.data.lower()),

                    )
                    db.session.add(user)
                    db.session.flush()  # Get user.id without committing

                    # Add Admin
                    admin = Admin(
                        user_id=user.id,
                        school_id=clean_field(form.school_id.data.lower()),

                    )
                    db.session.add(admin)
                    db.session.flush()  # Get admin.id without committing

                # Commit the transaction
                db.session.commit()
                flash('Admin added successfully!', 'success')
                return redirect(url_for('admin.add_admin'))

            except SQLAlchemyError as e:
                db.session.rollback()

                if isinstance(e.orig, IntegrityError) and "Duplicate entry" in str(e.orig):
                    field_name = str(e.orig).split("'")[3]
                    # Mapping database columns to user-friendly field names
                    field_name_map = {
                        'rfid_uid': 'RFID',
                        'email': 'Email',
                        # 'username': 'Username',
                        'school_id': 'Admin Number',
                    }
                    # Use the user-friendly name if available, else fall back to the database column name
                    friendly_field_name = field_name_map.get(field_name, field_name)
                    flash(f"The {friendly_field_name} you entered is already in use. Please use a different value.",
                          'error')
                else:
                    flash('An error occurred while adding the admin. Please try again.', 'error')

    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error: {error}", 'error')

    return render_template('admin/add_admin.html', form=form)


@admin_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_admin(id):
    admin = Admin.query.get_or_404(id)
    user = admin.user
    form = AdminForm(obj=user)
    print(request.form)

    def clean_field(field_value):
        return " ".join(field_value.strip().split())

    def convert_to_hex(rfid_uid):
        try:
            # Try to interpret the RFID UID as an integer (which means it's in decimal)
            rfid_int = int(rfid_uid)

            # Convert the integer to a hexadecimal string
            rfid_hex = format(rfid_int, '08X')

            # Adjust the byte order (reverse for little-endian)
            rfid_hex = ''.join(reversed([rfid_hex[i:i + 2] for i in range(0, len(rfid_hex), 2)]))

            return rfid_hex
        except ValueError:
            # If it raises a ValueError, it means rfid_uid is already a valid hexadecimal string
            return rfid_uid.lower()  # Return as uppercase hex

    rfid_uid = form.rfid_uid.data if form.rfid_uid.data else None

    # Convert RFID UID to hexadecimal only if not None
    if rfid_uid:
        rfid_uid = convert_to_hex(rfid_uid)

    if request.method == 'POST':
        print(form.errors)  # This will print any validation errors in the form

    if request.method == 'GET':
        # Populate the form with existing data, using `or ''` to handle None values
        form.rfid_uid.data = user.rfid_uid.upper() if user.rfid_uid else ''

        form.f_name.data = user.f_name or ''
        form.l_name.data = user.l_name or ''
        form.m_name.data = user.m_name or ''

        form.email.data = user.email or ''

        form.gender.data = user.gender or ''

        form.school_id.data = admin.school_id or ''

    if form.validate_on_submit():
        print("Form is valid")
        # Convert the RFID UID to hexadecimal before saving
        form.rfid_uid.data = convert_to_hex(form.rfid_uid.data)

        # Convert all fields to lowercase and normalize spaces
        for field in form:
            if isinstance(field.data, str):
                # Convert to lowercase
                field.data = field.data.lower()
                # Normalize spaces (reduce multiple spaces to a single space)
                field.data = re.sub(r'\s+', ' ', field.data)

        # Check for existing email, username, and admin number conflicts
        rfid_uid_exists = User.query.filter(User.rfid_uid == rfid_uid, User.id != user.id).first() if rfid_uid else None
        email_exists = User.query.filter(User.email == form.email.data, User.id != user.id).first()
        school_id_exists = Admin.query.filter(Admin.school_id == form.school_id.data,
                                              Admin.user_id != user.id).first()
        if rfid_uid_exists is not None:
            flash('RFID is already in use', 'error')
        elif email_exists is not None:
            flash('Email is already in use', 'error')
        elif school_id_exists is not None:
            flash('Admin Number is already in use', 'error')
        else:
            try:
                with db.session.begin_nested():
                    # Convert all fields to lowercase and normalize spaces
                    user.rfid_uid = rfid_uid if rfid_uid else None
                    user.f_name = clean_field(form.f_name.data.lower())
                    user.l_name = clean_field(form.l_name.data.lower())
                    user.m_name = clean_field(form.m_name.data.lower())
                    user.email = clean_field(form.email.data.lower())
                    user.gender = clean_field(form.gender.data.lower())

                    # Update Admin
                    admin.school_id = clean_field(form.school_id.data.lower())

                db.session.commit()
                flash('Admin information has been updated!', 'success')
                return redirect(url_for('admin.manage_admin'))

            except SQLAlchemyError as e:
                db.session.rollback()
                if isinstance(e.orig, IntegrityError) and "Duplicate entry" in str(e.orig):
                    field_name = str(e.orig).split("'")[3]
                    field_name_map = {
                        'rfid_uid': 'RFID',
                        'email': 'Email',
                        # 'username': 'Username',
                        'school_id': 'Admin Number',
                    }

                    friendly_field_name = field_name_map.get(field_name, field_name)
                    flash(f"The {friendly_field_name} you entered is already in use. Please use a different value.",
                          'error')
                else:
                    flash('An error occurred while updating the admin details. Please try again.', 'error')

    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error: {error}", 'error')
    return render_template('admin/edit_admin.html', form=form, admin=admin)


@admin_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
@cspc_acc_required
@admin_required
def delete_admin(id):
    admin = Admin.query.get_or_404(id)
    # Check if the current admin is attempting to delete their own account
    if admin.user.id == current_user.id:
        flash('You cannot delete your own account', 'warning')
        return redirect(url_for('admin.manage_admin'))

    user = admin.user
    try:
        db.session.delete(admin)
        db.session.delete(user)
        db.session.commit()
        flash('Faculty deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting admin', 'error')

    return redirect(url_for('admin.manage_admin'))

import re

from flask import Blueprint, flash, render_template, redirect, url_for, request, session
from flask_login import login_required, current_user
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from app import db
from decorators import cspc_acc_required, admin_required
from models import Admin, User
from webforms.admin_form import AdminForm

admin_acc_bp = Blueprint('admin_acc', __name__)


@admin_acc_bp.route("/profile/<int:admin_id>", methods=["GET", "POST"])
@login_required
@cspc_acc_required
@admin_required
def admin_profile(admin_id):
    # Use the user associated with the email in the session
    admin = Admin.query.filter_by(id=admin_id, user_id=current_user.id).first_or_404()
    user = admin.user
    form = AdminForm(admin_id=admin.id, obj=user)
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
            return rfid_uid.lower()  # Return as lowercase hex

    if request.method == 'POST':
        print(form.errors)  # This will print any validation errors in the form

    if request.method == "GET":
        # Populate the form with existing data, using `or ''` to handle None values
        form.rfid_uid.data = user.rfid_uid or ''
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
        rfid_uid_exists = User.query.filter(User.rfid_uid == form.rfid_uid.data, User.id != user.id).first()
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
                    user.rfid_uid = clean_field(form.rfid_uid.data.lower())
                    user.f_name = clean_field(form.f_name.data.lower())
                    user.l_name = clean_field(form.l_name.data.lower())
                    user.m_name = clean_field(form.m_name.data.lower())
                    user.gender = clean_field(form.gender.data.lower())

                    # Update Admin
                    admin.school_id = clean_field(form.school_id.data.lower())

                db.session.commit()
                flash('Admin details updated successfully!', 'success')

                # redirect to the two-factor auth page, passing username in session
                session['email'] = user.email
                return redirect(url_for('totp.two_factor_setup'))

            except IntegrityError as e:
                db.session.rollback()
                # Handle duplicate entry errors
                if "Duplicate entry" in str(e.orig):
                    field_name = str(e.orig).split("'")[3]
                    field_name_map = {
                        'rfid_uid': 'RFID',
                        'email': 'Email',
                        'school_id': 'School ID',
                    }
                    friendly_field_name = field_name_map.get(field_name, field_name)
                    flash(f"The {friendly_field_name} you entered is already in use. Please use a different value.",
                          'error')
                else:
                    flash('An error occurred while updating the admin details. Please try again.', 'error')

            except SQLAlchemyError as e:
                db.session.rollback()
                # Handle other SQLAlchemy errors
                flash('A database error occurred. Please try again.', 'error')

            if form.errors:
                for field, errors in form.errors.items():
                    # Convert field names to user-friendly versions
                    friendly_field_names = {
                        'rfid_uid': 'RFID',
                        'f_name': 'First Name',
                        'l_name': 'Last Name',
                        'm_name': 'Middle Name',
                        'email': 'Email Address',
                        'gender': 'Gender',
                        'school_id': 'School ID'
                    }
                    field_label = friendly_field_names.get(field, field.capitalize())

                    # Display all validation errors in layman's terms
                    for error in errors:
                        flash(f"{field_label}: {error}. Please try again.", 'error')

    return render_template('admin_acc/admin_profile.html', form=form, admin=admin)

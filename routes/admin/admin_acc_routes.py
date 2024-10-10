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

    # # Initialize variables
    # contact_info = user.contact_info
    # family_background = user.family_background
    # educational_background = user.educational_background
    #
    # # Ensure that the related objects exist
    # if contact_info is None:
    #     contact_info = ContactInfo(user_id=user.id)
    #     db.session.add(contact_info)
    #     db.session.commit()
    #     user.contact_info = contact_info
    #
    # if family_background is None:
    #     family_background = FamilyBackground(user_id=user.id)
    #     db.session.add(family_background)
    #     db.session.commit()
    #     user.family_background = family_background
    #
    # if educational_background is None:
    #     educational_background = EducationalBackground(user_id=user.id)
    #     db.session.add(educational_background)
    #     db.session.commit()
    #     user.educational_background = educational_background

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
        # form.username.data = user.username or ''
        form.f_name.data = user.f_name or ''
        form.l_name.data = user.l_name or ''
        form.m_name.data = user.m_name or ''
        # form.m_initial.data = user.m_initial or ''
        form.email.data = user.email or ''
        #         form.date_of_birth.data = user.date_of_birth or ''
        #         form.place_of_birth.data = user.place_of_birth or ''
        form.gender.data = user.gender or ''
        #         form.civil_status.data = user.civil_status or ''
        #         form.nationality.data = user.nationality or ''
        #         form.citizenship.data = user.citizenship or ''
        #         form.religion.data = user.religion or ''
        #         form.dialect.data = user.dialect or ''
        #         form.tribal_aff.data = user.tribal_aff or ''

        # Populate Admin-specific data
        form.school_id.data = admin.school_id or ''
        # form.password.data = ''

        # # Populate ContactInfo
        # if contact_info:
        #     form.contact_number.data = contact_info.contact_number or ''
        #     form.home_addr_text.data = contact_info.h_city or ''
        #     form.home_brgy_text.data = contact_info.h_barangay or ''
        #     form.home_house_no.data = contact_info.h_house_no or ''
        #     form.home_street.data = contact_info.h_street or ''
        #     form.curr_addr_text.data = contact_info.curr_city or ''
        #     form.curr_brgy_text.data = contact_info.curr_barangay or ''
        #     form.curr_house_no.data = contact_info.curr_house_no or ''
        #     form.curr_street.data = contact_info.curr_street or ''
        #
        # # Populate FamilyBackground
        # if family_background:
        #     form.mother_full_name.data = family_background.mother_full_name or ''
        #     form.mother_educ_attainment.data = family_background.mother_educ_attainment or ''
        #     form.mother_addr_text.data = family_background.mother_addr or ''
        #     form.mother_brgy_text.data = family_background.mother_brgy or ''
        #     form.mother_cont_no.data = family_background.mother_cont_no or ''
        #     form.mother_place_work_or_company_name.data = family_background.mother_place_work_or_company_name or ''
        #     form.mother_occupation.data = family_background.mother_occupation or ''
        #     form.father_full_name.data = family_background.father_full_name or ''
        #     form.father_educ_attainment.data = family_background.father_educ_attainment or ''
        #     form.father_addr_text.data = family_background.father_addr or ''
        #     form.father_brgy_text.data = family_background.father_brgy or ''
        #     form.father_cont_no.data = family_background.father_cont_no or ''
        #     form.father_place_work_or_company_name.data = family_background.father_place_work_or_company_name or ''
        #     form.father_occupation.data = family_background.father_occupation or ''
        #     form.guardian_full_name.data = family_background.guardian_full_name or ''
        #     form.guardian_educ_attainment.data = family_background.guardian_educ_attainment or ''
        #     form.guardian_addr_text.data = family_background.guardian_addr or ''
        #     form.guardian_brgy_text.data = family_background.guardian_brgy or ''
        #     form.guardian_cont_no.data = family_background.guardian_cont_no or ''
        #     form.guardian_place_work_or_company_name.data = family_background.guardian_place_work_or_company_name or ''
        #     form.guardian_occupation.data = family_background.guardian_occupation or ''
        #
        # # Populate EducationalBackground
        # if educational_background:
        #     form.elem_school_name.data = educational_background.elem_school or ''
        #     form.elem_school_addr_text.data = educational_background.elem_address or ''
        #     form.elem_year_grad.data = educational_background.elem_graduated or ''
        #     form.junior_hs_school_name.data = educational_background.junior_school or ''
        #     form.junior_hs_school_addr_text.data = educational_background.junior_address or ''
        #     form.junior_hs_year_grad.data = educational_background.junior_graduated or ''
        #     form.senior_hs_school_name.data = educational_background.senior_school or ''
        #     form.senior_hs_school_addr_text.data = educational_background.senior_address or ''
        #     form.senior_hs_year_grad.data = educational_background.senior_graduated or ''
        #     form.senior_strand.data = educational_background.senior_track_strand or ''
        #     form.tertiary_school_name.data = educational_background.tertiary_school or ''
        #     form.tertiary_school_addr_text.data = educational_background.tertiary_address or ''
        #     form.tertiary_year_grad.data = educational_background.tertiary_graduated or ''
        #     form.tertiary_course.data = educational_background.tertiary_course or ''

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

        # Only hash and update the password if provided
        # if form.password.data:
        #     admin.password_hash = generate_password_hash(form.password.data, "pbkdf2:sha256")

        # Check for existing email, username, and admin number conflicts
        rfid_uid_exists = User.query.filter(User.rfid_uid == form.rfid_uid.data, User.id != user.id).first()
        email_exists = User.query.filter(User.email == form.email.data, User.id != user.id).first()
        # username_exists = User.query.filter(User.username == form.username.data, User.id != user.id).first()
        school_id_exists = Admin.query.filter(Admin.school_id == form.school_id.data,
                                              Admin.user_id != user.id).first()
        if rfid_uid_exists is not None:
            flash('RFID is already in use', 'error')
        elif email_exists is not None:
            flash('Email is already in use', 'error')
        # elif username_exists is not None:
        #     flash('Username is already taken', 'error')
        elif school_id_exists is not None:
            flash('Admin Number is already in use', 'error')
        else:
            try:
                with db.session.begin_nested():
                    # Convert all fields to lowercase and normalize spaces
                    user.rfid_uid = clean_field(form.rfid_uid.data.lower())
                    # user.username = clean_field(form.username.data.lower())
                    user.f_name = clean_field(form.f_name.data.lower())
                    user.l_name = clean_field(form.l_name.data.lower())
                    user.m_name = clean_field(form.m_name.data.lower())
                    user.m_initial = clean_field(form.m_initial.data.lower())
                    user.email = clean_field(form.email.data.lower())
                    user.date_of_birth = form.date_of_birth.data
                    user.place_of_birth = clean_field(form.place_of_birth.data.lower())
                    user.gender = clean_field(form.gender.data.lower())
                    user.civil_status = clean_field(form.civil_status.data.lower())
                    user.nationality = clean_field(form.nationality.data.lower())
                    user.citizenship = clean_field(form.citizenship.data.lower())
                    user.religion = clean_field(form.religion.data.lower())
                    user.dialect = clean_field(form.dialect.data.lower())
                    user.tribal_aff = clean_field(form.tribal_aff.data.lower())

                    # Handle profile pic update
                    # if 'profile_pic' in request.files and request.files['profile_pic'].filename != '':
                    #     profile_pic = request.files['profile_pic']
                    #     pic_filename = secure_filename(profile_pic.filename)
                    #     pic_name = str(uuid.uuid1()) + "_" + pic_filename
                    #     user.profile_pic = pic_name
                    #     profile_pic.save(os.path.join(current_app.config['UPLOAD_FOLDER'], pic_name))

                    # # Update ContactInfo
                    # if contact_info:
                    #     contact_info.contact_number = form.contact_number.data
                    #     contact_info.h_city = clean_field(form.home_addr_text.data.lower())
                    #     contact_info.h_barangay = clean_field(form.home_brgy_text.data.lower())
                    #     contact_info.h_house_no = clean_field(form.home_house_no.data.lower())
                    #     contact_info.h_street = clean_field(form.home_street.data.lower())
                    #     contact_info.curr_city = clean_field(form.curr_addr_text.data.lower())
                    #     contact_info.curr_barangay = clean_field(form.curr_brgy_text.data.lower())
                    #     contact_info.curr_house_no = clean_field(form.curr_house_no.data.lower())
                    #     contact_info.curr_street = clean_field(form.curr_street.data.lower())
                    #
                    # # Update FamilyBackground (similar updates for each field)
                    # if family_background:
                    #     family_background.mother_full_name = clean_field(form.mother_full_name.data.lower())
                    #     family_background.mother_educ_attainment = clean_field(
                    #         form.mother_educ_attainment.data.lower())
                    #     family_background.mother_addr = clean_field(form.mother_addr_text.data.lower())
                    #     family_background.mother_brgy = clean_field(form.mother_brgy_text.data.lower())
                    #     family_background.mother_cont_no = form.mother_cont_no.data
                    #     family_background.mother_place_work_or_company_name = clean_field(
                    #         form.mother_place_work_or_company_name.data.lower())
                    #     family_background.mother_occupation = clean_field(form.mother_occupation.data.lower())
                    #     family_background.father_full_name = clean_field(form.father_full_name.data.lower())
                    #     family_background.father_educ_attainment = clean_field(
                    #         form.father_educ_attainment.data.lower())
                    #     family_background.father_addr = clean_field(form.father_addr_text.data.lower())
                    #     family_background.father_brgy = clean_field(form.father_brgy_text.data.lower())
                    #     family_background.father_cont_no = form.father_cont_no.data
                    #     family_background.father_place_work_or_company_name = clean_field(
                    #         form.father_place_work_or_company_name.data.lower())
                    #     family_background.father_occupation = clean_field(form.father_occupation.data.lower())
                    #     family_background.guardian_full_name = clean_field(form.guardian_full_name.data.lower())
                    #     family_background.guardian_educ_attainment = clean_field(
                    #         form.guardian_educ_attainment.data.lower())
                    #     family_background.guardian_addr = clean_field(form.guardian_addr_text.data.lower())
                    #     family_background.guardian_brgy = clean_field(form.guardian_brgy_text.data.lower())
                    #     family_background.guardian_cont_no = form.guardian_cont_no.data
                    #     family_background.guardian_place_work_or_company_name = clean_field(
                    #         form.guardian_place_work_or_company_name.data.lower())
                    #     family_background.guardian_occupation = clean_field(form.guardian_occupation.data.lower())
                    #
                    # # Update EducationalBackground (similar updates for each field)
                    # if educational_background:
                    #     educational_background.elem_school = clean_field(form.elem_school_name.data.lower())
                    #     educational_background.elem_address = clean_field(form.elem_school_addr_text.data.lower())
                    #     educational_background.elem_graduated = form.elem_year_grad.data
                    #     educational_background.junior_school = clean_field(form.junior_hs_school_name.data.lower())
                    #     educational_background.junior_address = clean_field(
                    #         form.junior_hs_school_addr_text.data.lower())
                    #     educational_background.junior_graduated = form.junior_hs_year_grad.data
                    #     educational_background.senior_school = clean_field(form.senior_hs_school_name.data.lower())
                    #     educational_background.senior_address = clean_field(
                    #         form.senior_hs_school_addr_text.data.lower())
                    #     educational_background.senior_graduated = form.senior_hs_year_grad.data
                    #     educational_background.senior_track_strand = clean_field(form.senior_strand.data.lower())
                    #     educational_background.tertiary_school = clean_field(form.tertiary_school_name.data.lower())
                    #     educational_background.tertiary_address = clean_field(
                    #         form.tertiary_school_addr_text.data.lower())
                    #     educational_background.tertiary_graduated = form.tertiary_year_grad.data
                    #     educational_background.tertiary_course = clean_field(form.tertiary_course.data.lower())

                    # Update the password hash only if it's changed
                    # if form.password.data:
                    #     admin.password_hash = generate_password_hash(form.password.data, "pbkdf2:sha256")

                    # Update Admin
                    admin.school_id = clean_field(form.school_id.data.lower())

                db.session.commit()
                flash('Admin details updated successfully!', 'success')

                # redirect to the two-factor auth page, passing username in session
                session['email'] = user.email
                return redirect(url_for('totp.two_factor_setup'))

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
                    flash('An error occurred while updating the student details. Please try again.', 'error')

    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error: {error}", 'error')

    return render_template('admin_acc/admin_profile.html', form=form, admin=admin)

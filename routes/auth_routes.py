from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import uuid

from models import User, Student, Admin, Faculty, EducationalBackground, FamilyBackground, \
    ContactInfo
from webforms.login_form import LoginForm
from webforms.registration_form import RegistrationForm
from app import db

auth_bp = Blueprint('auth', __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        print("Form data:", form.data)
        user = User.query.filter_by(email=form.email.data).first()
        role = form.role.data.lower()
        if user is None:
            hashed_pw = generate_password_hash(form.password.data, "pbkdf2:sha256")
            user = User(
                rfid_uid=form.rfid_uid.data,
                username=form.username.data,
                f_name=form.f_name.data,
                l_name=form.l_name.data,
                m_name=form.m_name.data,
                m_initial=form.m_initial.data,
                email=form.email.data,
                date_of_birth=form.date_of_birth.data,
                place_of_birth=form.place_of_birth.data,
                role=role,
                gender=form.gender.data,
                civil_status=form.civil_status.data,
                nationality=form.nationality.data,
                citizenship=form.citizenship.data,
                address=form.address.data,
                profile_pic=None,  # Initially set to None, will update later if uploaded
                religion=form.religion.data,
                dialect=form.dialect.data
            )
            db.session.add(user)
            db.session.commit()  # Commit to get the user.id

            if user.id:
                # Check for profile pic
                if 'profile_pic' in request.files and request.files['profile_pic'].filename != '':
                    profile_pic = request.files['profile_pic']
                    pic_filename = secure_filename(profile_pic.filename)
                    pic_name = str(uuid.uuid1()) + "_" + pic_filename
                    user.profile_pic = pic_name
                    profile_pic.save(os.path.join(current_app.config['UPLOAD_FOLDER'], pic_name))
                    db.session.commit()

                # Add ContactInfo
                contact_info = ContactInfo(
                    user_id=user.id,
                    contact_number=form.contact_number.data,
                    h_city=form.h_city.data,
                    h_barangay=form.h_barangay.data,
                    h_house_no=form.h_house_no.data,
                    h_street=form.h_street.data,
                    curr_city=form.curr_city.data,
                    curr_barangay=form.curr_barangay.data,
                    curr_house_no=form.curr_house_no.data,
                    curr_street=form.curr_street.data,
                )
                db.session.add(contact_info)
                db.session.commit()

                # Add FamilyBackground
                family_background = FamilyBackground(
                    user_id=user.id,
                    mother_full_name=form.mother_full_name.data,
                    mother_educ_attainment=form.mother_educ_attainment.data,
                    mother_addr=form.mother_addr.data,
                    mother_brgy=form.mother_brgy.data,
                    mother_cont_no=form.mother_cont_no.data,
                    mother_place_work_or_company_name=form.mother_place_work_or_company_name.data,
                    mother_occupation=form.mother_occupation.data,
                    father_full_name=form.father_full_name.data,
                    father_educ_attainment=form.father_educ_attainment.data,
                    father_addr=form.father_addr.data,
                    father_brgy=form.father_brgy.data,
                    father_cont_no=form.father_cont_no.data,
                    father_place_work_or_company_name=form.father_place_work_or_company_name.data,
                    father_occupation=form.father_occupation.data,
                    guardian_full_name=form.guardian_full_name.data,
                    guardian_educ_attainment=form.guardian_educ_attainment.data,
                    guardian_addr=form.guardian_addr.data,
                    guardian_brgy=form.guardian_brgy.data,
                    guardian_cont_no=form.guardian_cont_no.data,
                    guardian_place_work_or_company_name=form.guardian_place_work_or_company_name.data,
                    guardian_occupation=form.guardian_occupation.data,
                )
                db.session.add(family_background)
                db.session.commit()

                # Add EducationalBackground
                educational_background = EducationalBackground(
                    user_id=user.id,
                    elem_school=form.elem_school.data,
                    elem_address=form.elem_address.data,
                    elem_graduated=form.elem_graduated.data,
                    junior_school=form.junior_school.data,
                    junior_address=form.junior_address.data,
                    junior_graduated=form.junior_graduated.data,
                    senior_school=form.senior_school.data,
                    senior_address=form.senior_address.data,
                    senior_graduated=form.senior_graduated.data,
                    senior_track_strand=form.senior_track_strand.data,
                )
                db.session.add(educational_background)
                db.session.commit()

                # Add role-specific information
                if role == 'student':
                    student = Student(
                        user_id=user.id,
                        student_number=form.student_number.data
                    )
                    db.session.add(student)
                    db.session.commit()

                    # Add course and year details for the student
                    student_course_and_year = StudentCourseAndYear(
                        student_id=student.id,
                        course_name=form.course_name.data,
                        year_level=form.year_level.data,
                        section=form.section.data
                    )
                    db.session.add(student_course_and_year)
                    db.session.commit()

                    flash('Student registered successfully!', 'success')
                elif role == 'faculty':
                    faculty = Faculty(
                        user_id=user.id,
                        faculty_id=form.faculty_id.data,
                        designation=form.designation.data,
                        faculty_department=form.faculty_department.data,
                        password_hash=hashed_pw
                    )
                    db.session.add(faculty)
                    db.session.commit()
                    flash('Faculty registered successfully!', 'success')
                elif role == 'admin':
                    admin = Admin(
                        user_id=user.id,
                        school_id=form.school_id.data,
                        admin_department=form.admin_department.data,
                        password_hash=hashed_pw,
                    )
                    db.session.add(admin)
                    db.session.commit()
                    flash('Admin registered successfully!', 'success')

                return redirect(url_for('auth.register'))
        else:
            flash('Email was already registered', 'error')

    if form.errors:
        print("Form errors:", form.errors)

    return render_template('user/register.html', form=form)


@auth_bp.route('/login', methods=['POST', 'GET'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            print(f"User found: {user.email}, Role: {user.role}")
            if user.role in ['faculty', 'admin']:
                details = user.faculty_details if user.role == 'faculty' else user.admin_details
                if details:
                    print(f"Stored hash: {details.password_hash}")
                    print(f"Password entered: {form.password.data}")
                    if check_password_hash(details.password_hash, form.password.data):
                        login_user(user)
                        flash('Successfully logged in!', 'success')
                        return redirect(url_for('dashboard.dashboard'))
                    else:
                        flash('Woops! Wrong password - Try Again!', 'error')
                else:
                    flash(f'{user.role.capitalize()} details not found', 'error')
            else:
                flash('Invalid role for this login form', 'error')
        else:
            flash('That User Doesn\'t Exist', 'error')
    return render_template('user/login.html', form=form)


# Create a Logout Page
@auth_bp.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    flash('Successfully logged out')
    return redirect(url_for('auth.login'))

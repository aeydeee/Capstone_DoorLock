import os
import uuid

from flask import Blueprint, request, render_template, current_app, flash, redirect, url_for, jsonify
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename

from app import db
from models import Faculty, User, EducationalBackground, FamilyBackground, ContactInfo
from webforms.faculty_form import AddFaculty
from webforms.delete_form import DeleteForm

from sqlalchemy.exc import SQLAlchemyError

faculty_bp = Blueprint('faculty', __name__)


@faculty_bp.route('/api/faculty_data', methods=['GET'])
def get_faculty_data():
    faculties = Faculty.query.all()
    data = []
    for faculty in faculties:
        subjects = [{"code": subj.subject_code, "name": subj.subject_name} for subj in faculty.subjects]
        data.append({
            "id": faculty.id,
            "faculty_number": faculty.faculty_number,
            "full_name": faculty.full_name,
            "designation": faculty.designation,
            "l_name": faculty.user.l_name,
            "f_name": faculty.user.f_name,
            "m_name": faculty.user.m_name,
            "gender": faculty.user.gender,
            "rfid_uid": faculty.user.rfid_uid,
            "email": faculty.user.email,
            "subjects": subjects
        })
    return jsonify({"data": data})


@faculty_bp.route('/')
def manage_faculty():
    delete_form = DeleteForm()
    faculties = Faculty.query.all()

    return render_template('faculty/manage_faculty.html', faculties=faculties,
                           delete_form=delete_form)


@faculty_bp.route("/add", methods=["GET", "POST"])
def add_faculty():
    form = AddFaculty()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None:
            hashed_pw = generate_password_hash(form.password.data, "pbkdf2")
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
                role='faculty',
                gender=form.gender.data,
                civil_status=form.civil_status.data,
                nationality=form.nationality.data,
                citizenship=form.citizenship.data,
                address=form.address.data,
                religion=form.religion.data,
                dialect=form.dialect.data,
                profile_pic=None  # Initially set to None, will update later if uploaded
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
                    curr_street=form.curr_street.data
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
                    guardian_occupation=form.guardian_occupation.data
                )
                db.session.add(family_background)
                db.session.commit()

                # Add EducationalBackground
                educational_background = EducationalBackground(
                    user_id=user.id,
                    elem_school=form.elem_school_name.data,
                    elem_address=form.elem_address.data,
                    elem_graduated=form.elem_year_grad.data,
                    junior_school=form.junior_hs_school_name.data,
                    junior_address=form.junior_hs_address.data,
                    junior_graduated=form.junior_hs_year_grad.data,
                    senior_school=form.senior_hs_school_name.data,
                    senior_address=form.senior_hs_address.data,
                    senior_graduated=form.senior_hs_year_grad.data,
                    senior_track_strand=form.senior_hs_track_strand.data,
                    tertiary_school=form.tertiary_school_name.data,
                    tertiary_address=form.tertiary_school_address.data,
                    tertiary_graduated=form.tertiary_year_grad.data,
                    tertiary_course=form.tertiary_course.data
                )
                db.session.add(educational_background)
                db.session.commit()

                # Add Faculty
                faculty = Faculty(
                    user_id=user.id,
                    faculty_department=form.department.data,
                    faculty_number=form.school_id.data,
                    designation=form.designation.data,
                    password_hash=hashed_pw
                )
                db.session.add(faculty)
                db.session.commit()
                flash('Faculty added successfully!', 'success')

                return redirect(url_for('faculty.add_faculty'))
        else:
            flash('Email was already registered', 'error')

        if form.errors:
            print(form.errors)

    return render_template('faculty/add_faculty.html', form=form)


@faculty_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_faculty(id):
    facu = Faculty.query.get_or_404(id)
    user = facu.user
    form = AddFaculty(obj=user)

    if request.method == 'GET':
        form.school_id.data = facu.faculty_number
        contact_info = user.contact_info
        if contact_info:
            form.contact_number.data = contact_info.contact_number
            form.h_city.data = contact_info.h_city
            form.h_barangay.data = contact_info.h_barangay
            form.h_house_no.data = contact_info.h_house_no
            form.h_street.data = contact_info.h_street
            form.curr_city.data = contact_info.curr_city
            form.curr_barangay.data = contact_info.curr_barangay
            form.curr_house_no.data = contact_info.curr_house_no
            form.curr_street.data = contact_info.curr_street

        family_background = user.family_background
        if family_background:
            form.mother_full_name.data = family_background.mother_full_name
            form.mother_educ_attainment.data = family_background.mother_educ_attainment
            form.mother_addr.data = family_background.mother_addr
            form.mother_brgy.data = family_background.mother_brgy
            form.mother_cont_no.data = family_background.mother_cont_no
            form.mother_place_work_or_company_name.data = family_background.mother_place_work_or_company_name
            form.mother_occupation.data = family_background.mother_occupation
            form.father_full_name.data = family_background.father_full_name
            form.father_educ_attainment.data = family_background.father_educ_attainment
            form.father_addr.data = family_background.father_addr
            form.father_brgy.data = family_background.father_brgy
            form.father_cont_no.data = family_background.father_cont_no
            form.father_place_work_or_company_name.data = family_background.father_place_work_or_company_name
            form.father_occupation.data = family_background.father_occupation
            form.guardian_full_name.data = family_background.guardian_full_name
            form.guardian_educ_attainment.data = family_background.guardian_educ_attainment
            form.guardian_addr.data = family_background.guardian_addr
            form.guardian_brgy.data = family_background.guardian_brgy
            form.guardian_cont_no.data = family_background.guardian_cont_no
            form.guardian_place_work_or_company_name.data = family_background.guardian_place_work_or_company_name
            form.guardian_occupation.data = family_background.guardian_occupation

        educational_background = user.educational_background
        if educational_background:
            form.elem_school_name.data = educational_background.elem_school
            form.elem_address.data = educational_background.elem_address
            form.elem_year_grad.data = educational_background.elem_graduated
            form.junior_hs_school_name.data = educational_background.junior_school
            form.junior_hs_address.data = educational_background.junior_address
            form.junior_hs_year_grad.data = educational_background.junior_graduated
            form.senior_hs_school_name.data = educational_background.senior_school
            form.senior_hs_address.data = educational_background.senior_address
            form.senior_hs_year_grad.data = educational_background.senior_graduated
            form.senior_hs_track_strand.data = educational_background.senior_track_strand
            form.tertiary_school_name.data = educational_background.tertiary_school
            form.tertiary_school_address.data = educational_background.tertiary_address
            form.tertiary_year_grad.data = educational_background.tertiary_graduated
            form.tertiary_course.data = educational_background.tertiary_course

    if form.validate_on_submit():
        user.rfid_uid = form.rfid_uid.data
        user.username = form.username.data
        user.f_name = form.f_name.data
        user.l_name = form.l_name.data
        user.m_name = form.m_name.data
        user.m_initial = form.m_initial.data
        user.email = form.email.data
        user.date_of_birth = form.date_of_birth.data
        user.place_of_birth = form.place_of_birth.data
        user.gender = form.gender.data
        user.civil_status = form.civil_status.data
        user.nationality = form.nationality.data
        user.citizenship = form.citizenship.data
        user.address = form.address.data
        user.religion = form.religion.data
        user.dialect = form.dialect.data

        if 'profile_pic' in request.files and request.files['profile_pic'].filename != '':
            profile_pic = request.files['profile_pic']
            pic_filename = secure_filename(profile_pic.filename)
            pic_name = str(uuid.uuid1()) + "_" + pic_filename
            user.profile_pic = pic_name
            profile_pic.save(os.path.join(current_app.config['UPLOAD_FOLDER'], pic_name))

        contact_info = user.contact_info
        if contact_info:
            contact_info.contact_number = form.contact_number.data
            contact_info.h_city = form.h_city.data
            contact_info.h_barangay = form.h_barangay.data
            contact_info.h_house_no = form.h_house_no.data
            contact_info.h_street = form.h_street.data
            contact_info.curr_city = form.curr_city.data
            contact_info.curr_barangay = form.curr_barangay.data
            contact_info.curr_house_no = form.curr_house_no.data
            contact_info.curr_street = form.curr_street.data

        family_background = user.family_background
        if family_background:
            family_background.mother_full_name = form.mother_full_name.data
            family_background.mother_educ_attainment = form.mother_educ_attainment.data
            family_background.mother_addr = form.mother_addr.data
            family_background.mother_brgy = form.mother_brgy.data
            family_background.mother_cont_no = form.mother_cont_no.data
            family_background.mother_place_work_or_company_name = form.mother_place_work_or_company_name.data
            family_background.mother_occupation = form.mother_occupation.data
            family_background.father_full_name = form.father_full_name.data
            family_background.father_educ_attainment = form.father_educ_attainment.data
            family_background.father_addr = form.father_addr.data
            family_background.father_brgy = form.father_brgy.data
            family_background.father_cont_no = form.father_cont_no.data
            family_background.father_place_work_or_company_name = form.father_place_work_or_company_name.data
            family_background.father_occupation = form.father_occupation.data
            family_background.guardian_full_name = form.guardian_full_name.data
            family_background.guardian_educ_attainment = form.guardian_educ_attainment.data
            family_background.guardian_addr = form.guardian_addr.data
            family_background.guardian_brgy = form.guardian_brgy.data
            family_background.guardian_cont_no = form.guardian_cont_no.data
            family_background.guardian_place_work_or_company_name = form.guardian_place_work_or_company_name.data
            family_background.guardian_occupation = form.guardian_occupation.data

        educational_background = user.educational_background
        if educational_background:
            educational_background.elem_school = form.elem_school_name.data
            educational_background.elem_address = form.elem_address.data
            educational_background.elem_graduated = form.elem_year_grad.data
            educational_background.junior_school = form.junior_hs_school_name.data
            educational_background.junior_address = form.junior_hs_address.data
            educational_background.junior_graduated = form.junior_hs_year_grad.data
            educational_background.senior_school = form.senior_hs_school_name.data
            educational_background.senior_address = form.senior_hs_address.data
            educational_background.senior_graduated = form.senior_hs_year_grad.data
            educational_background.senior_track_strand = form.senior_hs_track_strand.data
            educational_background.tertiary_school = form.tertiary_school_name.data
            educational_background.tertiary_address = form.tertiary_school_address.data
            educational_background.tertiary_graduated = form.tertiary_year_grad.data
            educational_background.tertiary_course = form.tertiary_course.data

        facu.faculty_number = form.school_id.data

        try:
            db.session.commit()
            flash(f'Faculty {user.f_name} {user.l_name} has been updated!', 'success')
            return redirect(url_for('faculty.manage_faculty'))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f'An error occurred while updating the faculty: {str(e)}', 'error')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error in {getattr(form, field).label.text}: {error}", 'danger')
    return render_template('faculty/edit_faculty.html', form=form, faculty=facu)


@faculty_bp.route('/delete/<int:id>', methods=['POST'])
def delete_faculty(id):
    faculty = Faculty.query.get_or_404(id)
    user = faculty.user
    try:
        db.session.delete(faculty)
        db.session.delete(user)
        db.session.commit()
        flash('Faculty deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting faculty', 'error')
    return redirect(url_for('faculty.manage_faculty'))

import os
import uuid

from flask import Blueprint, request, render_template, current_app, flash, redirect, url_for
from flask_login import current_user, login_required
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename

from app import db
from models import Student, User, EducationalBackground, FamilyBackground, ContactInfo, StudentCourseAndYear, Faculty, \
    Subject

from webforms.delete_form import DeleteForm
from webforms.search_form import SearchForm, AssignStudentForm
from webforms.student_form import AddStudent

student_bp = Blueprint('student', __name__)


@student_bp.route('/', methods=['GET', 'POST'])
def manage_student():
    delete_form = DeleteForm()
    assign_form = AssignStudentForm()

    # Populate the subject dropdown with subject name and faculty name
    subjects = Subject.query.all()
    assign_form.subject.choices = [
        (subject.id, f"{subject.subject_name} - {subject.faculty_id}") for subject in subjects
    ]

    # Retrieve all students or filter by course_section
    course_section = request.args.get('course_section', '')
    if course_section:
        students = Student.query.join(StudentCourseAndYear).filter(
            (StudentCourseAndYear.course_name + " " +
             StudentCourseAndYear.year_level + " " +
             StudentCourseAndYear.section) == course_section
        ).all()
    else:
        students = Student.query.all()

    course_sections = [
        f"{sc.course_name} {sc.year_level} {sc.section}"
        for sc in StudentCourseAndYear.query.distinct(
            StudentCourseAndYear.course_name,
            StudentCourseAndYear.year_level,
            StudentCourseAndYear.section
        ).all()
    ]

    return render_template(
        'student/manage_student.html',
        students=students,
        delete_form=delete_form,
        course_sections=course_sections,
        assign_form=assign_form
    )


@student_bp.route('/assign_students_to_subject', methods=['POST'])
def assign_students_to_subject():
    assign_form = AssignStudentForm()
    assign_form.subject.choices = [
        (subject.id, f"{subject.subject_name} - {subject.faculty_id}") for subject in Subject.query.all()
    ]

    if assign_form.validate_on_submit():
        subject_id = assign_form.subject.data
        selected_student_ids = request.form.getlist('student_ids')

        if not selected_student_ids:
            flash('No students selected for assignment.', 'error')
            return redirect(url_for('student.manage_student'))

        subject = Subject.query.get(subject_id)
        if not subject:
            flash('Invalid subject selected.', 'error')
            return redirect(url_for('student.manage_student'))

        for student_id in selected_student_ids:
            student = Student.query.get(student_id)
            if student:
                student.subjects.append(subject)
                db.session.add(student)

        db.session.commit()
        flash('Students successfully assigned to the subject.', 'success')
        return redirect(url_for('student.manage_student'))
    else:
        flash('Form validation failed. Please check your inputs.', 'error')
        return redirect(url_for('student.manage_student'))


@student_bp.route("/add", methods=["GET", "POST"])
def add_student():
    form = AddStudent()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None:
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
                role='student',
                gender=form.gender.data,
                civil_status=form.civil_status.data,
                nationality=form.nationality.data,
                citizenship=form.citizenship.data,
                address=form.address.data,
                religion=form.religion.data,
                dialect=form.dialect.data,
                profile_pic=None
            )
            db.session.add(user)
            db.session.commit()
            if user.id:
                if 'profile_pic' in request.files and request.files['profile_pic'].filename != '':
                    profile_pic = request.files['profile_pic']
                    pic_filename = secure_filename(profile_pic.filename)
                    pic_name = str(uuid.uuid1()) + "_" + pic_filename
                    user.profile_pic = pic_name
                    profile_pic.save(os.path.join(current_app.config['UPLOAD_FOLDER'], pic_name))
                    db.session.commit()

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

                educational_background = EducationalBackground(
                    user_id=user.id,
                    elem_school=form.elem_school_name.data,
                    elem_address=form.elem_school_address.data,
                    elem_graduated=form.elem_year_grad.data,

                    junior_school=form.junior_hs_school_name.data,
                    junior_address=form.junior_hs_school_addr.data,
                    junior_graduated=form.junior_hs_year_grad.data,

                    senior_school=form.senior_hs_school_name.data,
                    senior_address=form.senior_hs_school_addr.data,
                    senior_graduated=form.senior_hs_year_grad.data,
                    senior_track_strand=form.senior_strand.data,

                    tertiary_school=form.tertiary_school_name.data,
                    tertiary_address=form.tertiary_school_addr.data,
                    tertiary_graduated=form.tertiary_year_grad.data,
                    tertiary_course=form.tertiary_course.data,
                )
                db.session.add(educational_background)
                db.session.commit()

                student = Student(
                    user_id=user.id,
                    student_number=form.school_id.data
                )
                db.session.add(student)
                db.session.commit()

                student_course_and_year = StudentCourseAndYear(
                    student_id=student.id,
                    course_name=form.course_name.data,
                    year_level=form.year_level.data,
                    section=form.section.data
                )
                db.session.add(student_course_and_year)
                db.session.commit()
                flash('Student added successfully!', 'success')
                return redirect(url_for('student.add_student'))
        else:
            flash('Email was already registered', 'error')
        if form.errors:
            print(form.errors)
    return render_template('student/add_student.html', form=form)


@student_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_student(id):
    stud = Student.query.get_or_404(id)
    user = stud.user
    form = AddStudent(obj=user)

    if request.method == 'GET':
        student_course_and_year = stud.student_course_and_year
        form.course_name.data = student_course_and_year.course_name
        form.year_level.data = student_course_and_year.year_level
        form.section.data = student_course_and_year.section
        form.school_id.data = stud.student_number

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
            form.elem_school_address.data = educational_background.elem_address
            form.elem_year_grad.data = educational_background.elem_graduated
            form.junior_hs_school_name.data = educational_background.junior_school
            form.junior_hs_school_addr.data = educational_background.junior_address
            form.junior_hs_year_grad.data = educational_background.junior_graduated
            form.senior_hs_school_name.data = educational_background.senior_school
            form.senior_hs_school_addr.data = educational_background.senior_address
            form.senior_hs_year_grad.data = educational_background.senior_graduated
            form.senior_strand.data = educational_background.senior_track_strand
            form.tertiary_school_name.data = educational_background.tertiary_school
            form.tertiary_school_addr.data = educational_background.tertiary_address
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
            educational_background.elem_address = form.elem_school_address.data
            educational_background.elem_graduated = form.elem_year_grad.data
            educational_background.junior_school = form.junior_hs_school_name.data
            educational_background.junior_address = form.junior_hs_school_addr.data
            educational_background.junior_graduated = form.junior_hs_year_grad.data
            educational_background.senior_school = form.senior_hs_school_name.data
            educational_background.senior_address = form.senior_hs_school_addr.data
            educational_background.senior_graduated = form.senior_hs_year_grad.data
            educational_background.senior_track_strand = form.senior_strand.data
            educational_background.tertiary_school = form.tertiary_school_name.data
            educational_background.tertiary_address = form.tertiary_school_addr.data
            educational_background.tertiary_graduated = form.tertiary_year_grad.data
            educational_background.tertiary_course = form.tertiary_course.data

        stud.student_number = form.school_id.data

        student_course_and_year = stud.student_course_and_year
        if student_course_and_year:
            student_course_and_year.course_name = form.course_name.data
            student_course_and_year.year_level = form.year_level.data
            student_course_and_year.section = form.section.data

        try:
            db.session.commit()
            flash(f'Student {user.f_name} {user.l_name} has been updated!', 'success')
            return redirect(url_for('student.manage_student'))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f'An error occurred while updating the student: {str(e)}', 'error')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error in {getattr(form, field).label.text}: {error}", 'danger')
    return render_template('student/edit_student.html', form=form, student=stud)


@student_bp.route('/delete/<int:id>', methods=['POST'])
def delete_student(id):
    student = Student.query.get_or_404(id)
    user = student.user
    try:
        db.session.delete(student)
        db.session.delete(user)
        db.session.commit()
        flash('Student deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting student', 'error')
    return redirect(url_for('student.manage_student'))

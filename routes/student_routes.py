import os
import uuid

from flask import Blueprint, request, render_template, current_app, flash, redirect, url_for
from flask_login import current_user, login_required
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename

from app import db
from models import Student, User, EducationalBackground, FamilyBackground, ContactInfo, Faculty, \
    Subject, Attendance, CourseYearLevelSemesterSubject, Section, Course, YearLevel, Semester, \
    student_subject_association

from webforms.delete_form import DeleteForm
from webforms.search_form import SearchForm, AssignStudentForm
from webforms.student_form import AddStudent, EditStudentForm

student_bp = Blueprint('student', __name__)


@student_bp.route('/', methods=['GET', 'POST'])
def manage_student():
    delete_form = DeleteForm()
    assign_form = AssignStudentForm()

    # Populate the subject dropdown with subject name and faculty names
    subjects = Subject.query.all()
    assign_form.subject.choices = [
        (subject.id, f"{subject.subject_name} - {', '.join(faculty.full_name for faculty in subject.faculties)}")
        for subject in subjects
    ]

    # Retrieve all students or filter by course, year level, and section
    course_section = request.args.get('course_section', '')
    print(f"course_section: {course_section}")  # Debugging line

    if course_section:
        parts = course_section.rsplit(' ', 2)
        print(f"parts: {parts}")  # Debugging line
        if len(parts) == 3:
            course_name, year_level_code, section_name = parts

            # Handle possible prefix in year level
            if year_level_code.startswith('YearLevelEnum.'):
                year_level_code = year_level_code.replace('YearLevelEnum.', '')

            print(
                f"course_name: {course_name}, year_level_code: {year_level_code}, section_name: {section_name}")  # Debugging line

            students = Student.query.join(Course).join(YearLevel).join(Section).filter(
                Course.course_name == course_name.strip(),
                YearLevel.level_code == year_level_code.strip(),
                Section.section_name == section_name.strip()
            ).all()
            print(f"students: {students}")  # Debugging line
        else:
            students = []
    else:
        students = Student.query.all()

    # Generate course sections without 'YearLevelEnum.'
    course_sections = [
        f"{sc.course.course_name} {str(sc.year_level.level_code).replace('YearLevelEnum.', '')} {sc.section.section_name}"
        for sc in Student.query.distinct(
            Student.course_id,
            Student.year_level_id,
            Student.section_id
        ).join(Course).join(YearLevel).join(Section).all()
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
        (subject.id, f"{subject.subject_name} - {', '.join(faculty.full_name for faculty in subject.faculties)}")
        for subject in Subject.query.all()
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
    form.year_level_id.choices = [(y.id, y.level_name) for y in YearLevel.query.all()]
    form.course_id.choices = [(c.id, c.course_name) for c in Course.query.all()]
    form.section_id.choices = [(s.id, s.section_name) for s in Section.query.all()]
    form.semester_id.choices = [(sem.id, sem.semester_name) for sem in Semester.query.all()]

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None:
            try:
                with db.session.begin_nested():
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
                    db.session.flush()  # Get user.id without committing

                    if 'profile_pic' in request.files and request.files['profile_pic'].filename != '':
                        profile_pic = request.files['profile_pic']
                        pic_filename = secure_filename(profile_pic.filename)
                        pic_name = str(uuid.uuid1()) + "_" + pic_filename
                        user.profile_pic = pic_name
                        profile_pic.save(os.path.join(current_app.config['UPLOAD_FOLDER'], pic_name))

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

                    student = Student(
                        student_number=form.student_number.data,
                        year_level_id=form.year_level_id.data,
                        course_id=form.course_id.data,
                        section_id=form.section_id.data,
                        semester_id=form.semester_id.data,
                        user_id=user.id
                    )
                    db.session.add(student)
                    db.session.flush()  # Get student.id without committing

                # Commit the transaction
                db.session.commit()
                flash('Student added successfully!', 'success')
                return redirect(url_for('student.add_student'))

            except SQLAlchemyError as e:
                # Rollback the transaction in case of error
                db.session.rollback()
                flash('An error occurred while adding the student. Please try again.', 'error')
                print(e)
        else:
            flash('Email was already registered', 'error')

    if form.errors:
        print(form.errors)
    return render_template('student/add_student.html', form=form)


@student_bp.route("/student/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit_student(id):
    student = Student.query.get_or_404(id)
    user = student.user

    form = AddStudent()
    form.year_level_id.choices = [(y.id, y.display_name) for y in YearLevel.query.all()]
    form.course_id.choices = [(c.id, c.course_name) for c in Course.query.all()]
    form.section_id.choices = [(s.id, s.section_name) for s in Section.query.all()]
    form.semester_id.choices = [(sem.id, sem.display_name) for sem in Semester.query.all()]

    if request.method == "GET":
        # Pre-populate form fields with the current data
        form.rfid_uid.data = user.rfid_uid
        form.username.data = user.username
        form.f_name.data = user.f_name
        form.l_name.data = user.l_name
        form.m_name.data = user.m_name
        form.m_initial.data = user.m_initial
        form.email.data = user.email
        form.date_of_birth.data = user.date_of_birth
        form.place_of_birth.data = user.place_of_birth
        form.gender.data = user.gender
        form.civil_status.data = user.civil_status
        form.nationality.data = user.nationality
        form.citizenship.data = user.citizenship
        form.address.data = user.address
        form.religion.data = user.religion
        form.dialect.data = user.dialect

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

        form.student_number.data = student.student_number
        form.year_level_id.data = student.year_level_id
        form.course_id.data = student.course_id
        form.section_id.data = student.section_id
        form.semester_id.data = student.semester_id

    if form.validate_on_submit():
        try:
            # Update the user information
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
            user.role = 'student'

            if 'profile_pic' in request.files and request.files['profile_pic'].filename != '':
                profile_pic = request.files['profile_pic']
                pic_filename = secure_filename(profile_pic.filename)
                pic_name = str(uuid.uuid1()) + "_" + pic_filename
                user.profile_pic = pic_name
                profile_pic.save(os.path.join(current_app.config['UPLOAD_FOLDER'], pic_name))

            contact_info = user.contact_info
            if not contact_info:
                contact_info = ContactInfo(user_id=user.id)
                db.session.add(contact_info)
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
            if not family_background:
                family_background = FamilyBackground(user_id=user.id)
                db.session.add(family_background)
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
            if not educational_background:
                educational_background = EducationalBackground(user_id=user.id)
                db.session.add(educational_background)
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

            student.student_number = form.student_number.data
            student.year_level_id = form.year_level_id.data
            student.course_id = form.course_id.data
            student.section_id = form.section_id.data
            student.semester_id = form.semester_id.data

            # Update the student's subjects based on the current course, year level, and semester
            course_id = form.course_id.data
            year_level_id = form.year_level_id.data
            semester_id = form.semester_id.data
            subjects = CourseYearLevelSemesterSubject.query.filter_by(
                course_id=course_id, year_level_id=year_level_id, semester_id=semester_id).all()

            # Clear current subjects and add new ones
            student.subjects = []
            for subject in subjects:
                student.subjects.append(subject.subject)

            db.session.commit()
            flash('Student details updated successfully!', 'success')
            return redirect(url_for('student.manage_student'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error updating student: {str(e)}', 'danger')

    return render_template('student/edit_student.html', form=form, student=student)


@student_bp.route('/delete/<int:id>', methods=['POST'])
def delete_student(id):
    student = Student.query.get_or_404(id)
    user = student.user
    try:
        # Delete related attendance records first
        Attendance.query.filter_by(user_id=user.id).delete()

        # Delete other related records
        CourseYearLevelSemesterSubject.query.filter_by(student_id=student.id).delete()
        ContactInfo.query.filter_by(user_id=user.id).delete()
        FamilyBackground.query.filter_by(user_id=user.id).delete()
        EducationalBackground.query.filter_by(user_id=user.id).delete()

        # Remove student from subjects without deleting subjects
        subjects = student.subjects
        for subject in subjects:
            student.subjects.remove(subject)

        db.session.delete(student)
        db.session.delete(user)
        db.session.commit()

        flash('Student deleted successfully', 'success')
    except SQLAlchemyError as e:
        db.session.rollback()
        flash(f'Error deleting student: {str(e)}', 'error')
    return redirect(url_for('student.manage_student'))


@student_bp.route('/assign-students', methods=['GET'])
def assign_students():
    try:
        students = Student.query.all()

        for student in students:
            subjects = CourseYearLevelSemesterSubject.query.filter_by(
                course_id=student.course_id,
                year_level_id=student.year_level_id,
                semester_id=student.semester_id
            ).all()

            for subject_entry in subjects:
                # Check if the association already exists
                existing_association = db.session.query(student_subject_association).filter_by(
                    student_id=student.id,
                    subject_id=subject_entry.subject_id
                ).first()

                if not existing_association:
                    student_subject = student_subject_association.insert().values(
                        student_id=student.id,
                        subject_id=subject_entry.subject_id
                    )
                    db.session.execute(student_subject)

        db.session.commit()
        flash('Students assigned to subjects successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred: {e}', 'danger')

    return redirect(url_for('student.manage_student'))


@student_bp.route('/view-assign-students', methods=['GET'])
def view_assign_students():
    return render_template('student/assign_students.html')

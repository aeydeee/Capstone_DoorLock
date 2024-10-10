from flask import Blueprint, render_template, redirect, url_for, flash, request

from flask_login import login_required
from sqlalchemy.exc import IntegrityError

from decorators import cspc_acc_required, admin_required
from models import Subject, CourseYearLevelSemesterSubject, Course, YearLevel, Semester, FacultySubjectSchedule, \
    Schedule

from webforms.delete_form import DeleteForm
from webforms.subject_form import SubjectForm, EditSubjectForm, CourseYearLevelSemesterSubjectForm
from app import db

subject_bp = Blueprint('subject', __name__)


@subject_bp.route("/", methods=["GET"])
@login_required
@cspc_acc_required
@admin_required
def subject_lists():
    delete_form = DeleteForm()  # Assuming you have a DeleteForm for handling the delete actions
    subjects = Subject.query.all()  # Fetching all subjects to display

    return render_template('subject/subject_lists.html',
                           subjects=subjects,
                           delete_form=delete_form)


@subject_bp.route("/course_sub_lists", methods=["GET"])
@login_required
@cspc_acc_required
@admin_required
def course_sub_lists():
    delete_form = DeleteForm()  # Form to handle deletion actions
    courses = Course.query.all()  # Fetch all courses for the dropdown filter
    selected_course = request.args.get('course', type=int)  # Get the selected course from query parameters

    # Fetch details of subjects filtered by the selected course
    if selected_course:
        details = CourseYearLevelSemesterSubject.query.filter_by(course_id=selected_course).all()
    else:
        details = CourseYearLevelSemesterSubject.query.all()

    return render_template('subject/course_sub_lists.html',
                           details=details,
                           courses=courses,
                           selected_course=selected_course,
                           delete_form=delete_form)


@subject_bp.route("/delete_subject_detail/<int:detail_id>", methods=["POST"])
@login_required
@cspc_acc_required
@admin_required
def delete_subject_detail(detail_id):
    detail = CourseYearLevelSemesterSubject.query.get_or_404(detail_id)

    try:
        # Reattach the detail object to the session if it was detached
        db.session.add(detail)

        # Now, you can safely access the `subject` attribute
        subject_name = detail.subject.subject_name

        db.session.delete(detail)
        db.session.commit()
        flash(f'Subject {subject_name} deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred: {str(e)}', 'danger')

    return redirect(url_for('subject.course_sub_lists'))


@subject_bp.route('/add_subject', methods=['GET', 'POST'])
@login_required
@cspc_acc_required
@admin_required
def add_subject():
    form = SubjectForm()

    if form.validate_on_submit():
        # Process form data
        subject = Subject(
            subject_name=form.name.data,
            subject_code=form.code.data,
            subject_units=form.units.data
        )

        db.session.add(subject)
        db.session.commit()

        flash('Subject added successfully!')
        return redirect(url_for('subject.add_subject'))

    return render_template('subject/add_subject.html', form=form)


@subject_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@cspc_acc_required
@admin_required
def edit_subject(id):
    subj = Subject.query.get_or_404(id)
    form = EditSubjectForm()

    if request.method == 'GET':
        form.name.data = subj.subject_name
        form.code.data = subj.subject_code
        form.units.data = subj.subject_units

    if form.validate_on_submit():
        # Update the subject object with form data
        subj.subject_name = form.name.data
        subj.subject_code = form.code.data
        subj.subject_units = form.units.data

        db.session.commit()
        flash('Subject has been updated successfully!')
        return redirect(url_for('subject.edit_subject', id=subj.id))

    return render_template('subject/edit_subject.html', form=form, subject=subj)


@subject_bp.route('/delete/<int:id>', methods=['GET', 'POST'])
@login_required
@cspc_acc_required
@admin_required
def delete_subject(id):
    print(f"Request method: {request.method}")
    subject = Subject.query.get(id)

    if not subject:
        print("Subject not found.")
        flash('Subject not found.', 'danger')
        return redirect(url_for('subject.subject_lists'))

    if request.method == 'POST':
        print(f"Deleting associated records for subject: {subject.subject_name}")

        # Manually delete associated faculty_subject_schedule records
        FacultySubjectSchedule.query.filter_by(subject_id=id).delete()

        # Manually delete associated schedules
        Schedule.query.filter_by(subject_id=id).delete()

        # Delete the subject
        print(f"Deleting subject: {subject.subject_name}")
        db.session.delete(subject)
        db.session.commit()

        flash('Subject deleted successfully', 'success')
    else:
        print("Delete request not using POST method")

    return redirect(url_for('subject.subject_lists'))


@subject_bp.route('/manage_subs')
@login_required
@cspc_acc_required
@admin_required
def manage_sub():
    # Assuming you have a Course model
    courses = Course.query.all()
    return render_template('subject/manage_subjects.html', courses=courses)

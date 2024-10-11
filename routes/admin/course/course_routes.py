from flask import Blueprint, render_template, redirect, url_for, flash, request

from flask_login import login_required
from sqlalchemy.exc import IntegrityError

from decorators import cspc_acc_required, admin_required
from models import Course, ProgramYearLevelSemesterCourse, Program, YearLevel, Semester, FacultyCourseSchedule, \
    Schedule

from webforms.delete_form import DeleteForm
from webforms.course_form import CourseForm, EditCourseForm, ProgramYearLevelSemesterCourseForm
from app import db

course_bp = Blueprint('course', __name__)


@course_bp.route("/", methods=["GET"])
@login_required
@cspc_acc_required
@admin_required
def course_lists():
    delete_form = DeleteForm()  # Assuming you have a DeleteForm for handling the delete actions
    courses = Course.query.all()  # Fetching all courses to display

    return render_template('course/course_lists.html',
                           courses=courses,
                           delete_form=delete_form)


@course_bp.route("/program_course_lists", methods=["GET"])
@login_required
@cspc_acc_required
@admin_required
def program_course_lists():
    delete_form = DeleteForm()  # Form to handle deletion actions
    programs = Program.query.all()  # Fetch all programs for the dropdown filter
    selected_program = request.args.get('program', type=int)  # Get the selected program from query parameters

    # Fetch details of courses filtered by the selected program
    if selected_program:
        details = ProgramYearLevelSemesterCourse.query.filter_by(program_id=selected_program).all()
    else:
        details = ProgramYearLevelSemesterCourse.query.all()

    return render_template('course/program_course_lists.html',
                           details=details,
                           programs=programs,
                           selected_program=selected_program,
                           delete_form=delete_form)


@course_bp.route("/delete_course_detail/<int:detail_id>", methods=["POST"])
@login_required
@cspc_acc_required
@admin_required
def delete_course_detail(detail_id):
    detail = ProgramYearLevelSemesterCourse.query.get_or_404(detail_id)

    try:
        # Reattach the detail object to the session if it was detached
        db.session.add(detail)

        # Now, you can safely access the `course` attribute
        course_name = detail.course.course_name

        db.session.delete(detail)
        db.session.commit()
        flash(f'Course {course_name} deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred: {str(e)}', 'danger')

    return redirect(url_for('course.program_course_lists'))


@course_bp.route('/add_course', methods=['GET', 'POST'])
@login_required
@cspc_acc_required
@admin_required
def add_course():
    form = CourseForm()

    if form.validate_on_submit():
        # Process form data
        course = Course(
            course_name=form.name.data,
            course_code=form.code.data,
            course_units=form.units.data
        )

        db.session.add(course)
        db.session.commit()

        flash('Course added successfully!')
        return redirect(url_for('course.add_course'))

    return render_template('course/add_course.html', form=form)


@course_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@cspc_acc_required
@admin_required
def edit_course(id):
    course = Course.query.get_or_404(id)
    form = EditCourseForm()

    if request.method == 'GET':
        form.name.data = course.course_name
        form.code.data = course.course_code
        form.units.data = course.course_units

    if form.validate_on_submit():
        # Update the course object with form data
        course.course_name = form.name.data
        course.course_code = form.code.data
        course.course_units = form.units.data

        db.session.commit()
        flash('Course has been updated successfully!')
        return redirect(url_for('course.edit_course', id=course.id))

    return render_template('course/edit_course.html', form=form, course=course)


@course_bp.route('/delete/<int:id>', methods=['GET', 'POST'])
@login_required
@cspc_acc_required
@admin_required
def delete_course(id):
    print(f"Request method: {request.method}")
    course = Course.query.get(id)

    if not course:
        print("Course not found.")
        flash('Course not found.', 'danger')
        return redirect(url_for('course.course_lists'))

    if request.method == 'POST':
        print(f"Deleting associated records for course: {course.course_name}")

        # Manually delete associated faculty_course_schedule records
        FacultyCourseSchedule.query.filter_by(course_id=id).delete()

        # Manually delete associated schedules
        Schedule.query.filter_by(course_id=id).delete()

        # Delete the course
        print(f"Deleting course: {course.course_name}")
        db.session.delete(course)
        db.session.commit()

        flash('Course deleted successfully', 'success')
    else:
        print("Delete request not using POST method")

    return redirect(url_for('course.course_lists'))


@course_bp.route('/manage_courses')
@login_required
@cspc_acc_required
@admin_required
def manage_course():
    # Assuming you have a Program model
    programs = Program.query.all()
    return render_template('course/manage_courses.html', programs=programs)

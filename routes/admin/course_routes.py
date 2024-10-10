from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_required
from sqlalchemy.exc import IntegrityError

from app import db
from decorators import cspc_acc_required, admin_required
from models import CourseYearLevelSemesterSubject, Semester, YearLevel, Course, Subject, Section, Student
from webforms.delete_form import DeleteForm
from webforms.course_form import CourseForm, YearLevelForm, SemesterForm, SubjectForm, \
    SectionForm, EditSectionForm

course_bp = Blueprint('course', __name__)


@course_bp.route("/", methods=["GET", "POST"])
@login_required
@cspc_acc_required
@admin_required
def manage_course():
    delete_form = DeleteForm()
    course_form = CourseForm(prefix='course')
    section_form = SectionForm(prefix='section')

    # Populate choices for SelectFields
    courses = Course.query.all()

    if request.method == "POST":
        if course_form.submit.data and course_form.validate():
            # Preprocess the course name and course code
            course_name = ' '.join(course_form.course_name.data.strip().lower().split())
            course_code = ' '.join(course_form.course_code.data.strip().lower().split())

            course = Course(course_name=course_name, course_code=course_code)
            try:
                db.session.add(course)
                db.session.commit()
                flash('Course added successfully', 'success')
            except IntegrityError:
                db.session.rollback()
                flash('Error: Duplicate course code.', 'error')
            return redirect(url_for('course.manage_course'))

        elif section_form.submit.data and section_form.validate():
            section_range = section_form.section_range.data
            try:
                if '-' in section_range:  # Handle range
                    start, end = section_range.split('-')
                    start = start.strip().upper()
                    end = end.strip().upper()

                    for char in range(ord(start), ord(end) + 1):
                        section_name = chr(char)
                        section = Section(section_name=section_name)
                        db.session.add(section)
                else:  # Handle single section
                    section_name = section_range.strip().upper()
                    section = Section(section_name=section_name)
                    db.session.add(section)

                db.session.commit()
                flash('Section(s) added successfully', 'success')
            except IntegrityError:
                db.session.rollback()
                flash('Error: Duplicate section name.', 'error')
            except ValueError:
                flash('Invalid section range format. Use A or A-F format.', 'error')

            return redirect(url_for('course.manage_course'))

    sections = Section.query.all()

    return render_template('course/manage_course.html',
                           delete_form=delete_form,
                           course_form=course_form,
                           section_form=section_form,
                           courses=courses,
                           sections=sections)


@course_bp.route("/edit_course/<string:course_type>/<int:course_id>", methods=["GET", "POST"])
@login_required
@cspc_acc_required
@admin_required
def edit_course(course_type, course_id):
    if course_type == "course":
        course = Course.query.get_or_404(course_id)
        form = CourseForm(obj=course, prefix='course')
    elif course_type == "year_level":
        course = YearLevel.query.get_or_404(course_id)
        form = YearLevelForm(obj=course, prefix='year_level')
    elif course_type == "semester":
        course = Semester.query.get_or_404(course_id)
        form = SemesterForm(obj=course, prefix='semester')
    else:
        flash('Invalid course type', 'error')
        return redirect(url_for('course.manage_course'))

    if request.method == "POST" and form.validate():
        if course_type == "course":
            # Preprocess course name and code
            course.course_name = ' '.join(form.course_name.data.strip().lower().split())
            course.course_code = ' '.join(form.course_code.data.strip().lower().split())
        elif course_type == "year_level":
            # Preprocess year level name
            course.level_name = ' '.join(form.level_name.data.strip().lower().split())
        elif course_type == "semester":
            # Preprocess semester name
            course.semester_name = ' '.join(form.semester_name.data.strip().lower().split())

        db.session.commit()
        flash(f'{course_type.replace("_", " ").title()} updated successfully', 'success')
        return redirect(url_for('course.manage_course'))

    return render_template('course/edit_course.html', form=form, course=course, course_type=course_type)


@course_bp.route('/delete_course/<string:course_type>/<int:course_id>', methods=['POST'])
@login_required
@cspc_acc_required
@admin_required
def delete_course(course_type, course_id):
    if course_type == 'course':
        course = Course.query.get_or_404(course_id)
        related_records = CourseYearLevelSemesterSubject.query.filter_by(course_id=course_id).all()
    elif course_type == 'year_level':
        course = YearLevel.query.get_or_404(course_id)
        related_records = CourseYearLevelSemesterSubject.query.filter_by(year_level_id=course_id).all()
    elif course_type == 'semester':
        course = Semester.query.get_or_404(course_id)
        related_records = CourseYearLevelSemesterSubject.query.filter_by(semester_id=course_id).all()
    elif course_type == 'section':
        course = Section.query.get_or_404(course_id)
        related_records = Student.query.filter_by(section_id=course_id).all()
    else:
        flash('Invalid course type', 'error')
        return redirect(url_for('course.manage_course'))

    try:
        for record in related_records:
            db.session.delete(record)
        db.session.delete(course)
        db.session.commit()
        flash(f'{course_type.replace("_", " ").title()} deleted successfully', 'success')
    except IntegrityError:
        db.session.rollback()
        flash(f'Error deleting {course_type.replace("_", " ").title()}. It may be referenced by other records.',
              'error')

    return redirect(url_for('course.manage_course'))

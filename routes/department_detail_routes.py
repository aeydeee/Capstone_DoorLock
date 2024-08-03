from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from sqlalchemy.exc import IntegrityError

from app import db
from models import CourseYearLevelSemesterSubject, Semester, YearLevel, Course, Subject, Section, Student
from webforms.delete_form import DeleteForm
from webforms.department_detail_form import CourseForm, YearLevelForm, SemesterForm, SubjectForm, \
    SectionForm, EditSectionForm

department_bp = Blueprint('department', __name__)


@department_bp.route("/manage_department_detail", methods=["GET", "POST"])
def manage_department_details():
    delete_form = DeleteForm()
    course_form = CourseForm(prefix='course')
    section_form = SectionForm(prefix='section')

    # Populate choices for SelectFields
    courses = Course.query.all()

    if request.method == "POST":
        if course_form.submit.data and course_form.validate():
            course = Course(course_name=course_form.course_name.data, course_code=course_form.course_code.data)
            try:
                db.session.add(course)
                db.session.commit()
                flash('Course added successfully', 'success')
            except IntegrityError:
                db.session.rollback()
                flash('Error: Duplicate course code.', 'error')
            return redirect(url_for('department.manage_department_details'))

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

            return redirect(url_for('department.manage_department_details'))

    sections = Section.query.all()

    return render_template('department/manage_department.html',
                           delete_form=delete_form,
                           course_form=course_form,
                           section_form=section_form,
                           courses=courses,
                           sections=sections)


@department_bp.route("/edit_department/<string:detail_type>/<int:detail_id>", methods=["GET", "POST"])
def edit_department(detail_type, detail_id):
    if detail_type == "course":
        detail = Course.query.get_or_404(detail_id)
        form = CourseForm(obj=detail, prefix='course')
    elif detail_type == "year_level":
        detail = YearLevel.query.get_or_404(detail_id)
        form = YearLevelForm(obj=detail, prefix='year_level')
    elif detail_type == "semester":
        detail = Semester.query.get_or_404(detail_id)
        form = SemesterForm(obj=detail, prefix='semester')
    else:
        flash('Invalid detail type', 'error')
        return redirect(url_for('department.manage_department_details'))

    if request.method == "POST" and form.validate():
        if detail_type == "course":
            detail.course_name = form.course_name.data
            detail.course_code = form.course_code.data
        elif detail_type == "year_level":
            detail.level_name = form.level_name.data
        elif detail_type == "semester":
            detail.semester_name = form.semester_name.data

        db.session.commit()
        flash(f'{detail_type.replace("_", " ").title()} updated successfully', 'success')
        return redirect(url_for('department.manage_department_details'))

    return render_template('department/edit_department.html', form=form, detail=detail, detail_type=detail_type)


@department_bp.route('/delete_department/<string:detail_type>/<int:detail_id>', methods=['POST'])
def delete_department(detail_type, detail_id):
    if detail_type == 'course':
        detail = Course.query.get_or_404(detail_id)
        related_records = CourseYearLevelSemesterSubject.query.filter_by(course_id=detail_id).all()
    elif detail_type == 'year_level':
        detail = YearLevel.query.get_or_404(detail_id)
        related_records = CourseYearLevelSemesterSubject.query.filter_by(year_level_id=detail_id).all()
    elif detail_type == 'semester':
        detail = Semester.query.get_or_404(detail_id)
        related_records = CourseYearLevelSemesterSubject.query.filter_by(semester_id=detail_id).all()
    elif detail_type == 'section':
        detail = Section.query.get_or_404(detail_id)
        related_records = Student.query.filter_by(section_id=detail_id).all()
    else:
        flash('Invalid detail type', 'error')
        return redirect(url_for('department.manage_department_details'))

    try:
        for record in related_records:
            db.session.delete(record)
        db.session.delete(detail)
        db.session.commit()
        flash(f'{detail_type.replace("_", " ").title()} deleted successfully', 'success')
    except IntegrityError:
        db.session.rollback()
        flash(f'Error deleting {detail_type.replace("_", " ").title()}. It may be referenced by other records.',
              'error')

    return redirect(url_for('department.manage_department_details'))

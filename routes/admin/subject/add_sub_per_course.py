import pandas as pd

from flask import Blueprint, flash, redirect, url_for, render_template
from flask_login import login_required

from app import db
from decorators import cspc_acc_required, admin_required
from models import Subject, Course, YearLevelEnum, YearLevel, SemesterEnum, Semester, CourseYearLevelSemesterSubject
from webforms.subject_form import SubjectForm
from webforms.upload_form import UploadForm
from flask import request

add_sub_per_course_bp = Blueprint('add_sub_per_course', __name__)

YEAR_LEVEL_MAPPING = {
    1: 'FIRST_YEAR',
    2: 'SECOND_YEAR',
    3: 'THIRD_YEAR',
    4: 'FOURTH_YEAR'
}


@add_sub_per_course_bp.route('/add_subject/<int:course_id>/<int:year>/<int:sem>', methods=['GET', 'POST'])
@login_required
@cspc_acc_required
@admin_required
def add_subject(course_id, year, sem):
    form = SubjectForm()
    upload_form = UploadForm()  # Use the UploadForm for file uploads

    # Get Course
    course = Course.query.get_or_404(course_id)

    year_level = YearLevel.query.filter_by(level_code=year).first()
    year_level_id = year_level.id if year_level else None

    # Get Semester ID
    semester_code = SemesterEnum.code(f'{"FIRST_SEMESTER" if sem == 1 else "SECOND_SEMESTER"}')
    semester = Semester.query.filter_by(semester_code=semester_code).first()
    semester_id = semester.id if semester else None

    if upload_form.validate_on_submit() and 'file' in request.files:
        file = request.files['file']
        df = None

        if file and file.filename.endswith('.csv'):
            df = pd.read_csv(file)
        elif file and file.filename.endswith('.xlsx'):
            df = pd.read_excel(file)

        if df is not None:
            for index, row in df.iterrows():
                # Process subject name and code
                subject_name = ' '.join(row['subject_name'].strip().lower().split())
                subject_code = ' '.join(row['subject_code'].strip().upper().split())
                subject_units = int(row['subject_units'])  # Ensure units is an integer

                # Check if a subject with the same name or code already exists
                existing_subject = Subject.query.filter(
                    (Subject.subject_name == subject_name) |
                    (Subject.subject_code == subject_code)
                ).first()

                if existing_subject:
                    subject = existing_subject
                    flash(f'Subject "{subject_name}" with this name or code already exists.', 'error')
                else:
                    # Create a new subject
                    subject = Subject(
                        subject_name=subject_name,
                        subject_code=subject_code,
                        subject_units=subject_units
                    )
                    db.session.add(subject)
                    db.session.commit()
                    flash(f'Subject "{subject_name}" added successfully!', 'success')

                # Associate the subject with the course, year level, and semester
                association_exists = CourseYearLevelSemesterSubject.query.filter_by(
                    course_id=course_id,
                    year_level_id=year_level.id,
                    semester_id=semester.id,
                    subject_id=subject.id
                ).first()

                if not association_exists:
                    new_association = CourseYearLevelSemesterSubject(
                        course_id=course_id,
                        year_level_id=year_level.id,
                        semester_id=semester.id,
                        subject_id=subject.id
                    )
                    db.session.add(new_association)
                    db.session.commit()
                    flash(f'Subject "{subject_name}" association added successfully!', 'success')

            return redirect(url_for('add_sub_per_course.add_subject', course_id=course_id, year=year, sem=sem))

    elif form.validate_on_submit():
        # Process subject name and code
        subject_name = ' '.join(form.name.data.strip().lower().split())
        subject_code = ' '.join(form.code.data.strip().upper().split())
        subject_units = form.units.data

        # Check if a subject with the same name or code already exists
        existing_subject = Subject.query.filter(
            (Subject.subject_name == subject_name) |
            (Subject.subject_code == subject_code)
        ).first()

        if existing_subject:
            subject = existing_subject
            flash('Subject with this name or code already exists.', 'error')
        else:
            # Process form data and create a new subject
            subject = Subject(
                subject_name=subject_name,
                subject_code=subject_code,
                subject_units=subject_units
            )
            db.session.add(subject)
            db.session.commit()
            flash('Subject added successfully!', 'success')

        # Associate the subject with the course, year level, and semester
        association_exists = CourseYearLevelSemesterSubject.query.filter_by(
            course_id=course_id,
            year_level_id=year_level.id,
            semester_id=semester.id,
            subject_id=subject.id
        ).first()

        if not association_exists:
            new_association = CourseYearLevelSemesterSubject(
                course_id=course_id,
                year_level_id=year_level.id,
                semester_id=semester.id,
                subject_id=subject.id
            )
            db.session.add(new_association)
            db.session.commit()
            flash('Subject association with course, year level, and semester added successfully!', 'success')

        return redirect(url_for('add_sub_per_course.add_subject', course_id=course_id, year=year, sem=sem))

    return render_template('subject/add_subjects.html', form=form, upload_form=upload_form,
                           course_code=course.course_code,
                           year_level=year_level, semester=semester)

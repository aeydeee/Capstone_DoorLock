import pandas as pd

from flask import Blueprint, flash, redirect, url_for, render_template
from flask_login import login_required

from app import db
from decorators import cspc_acc_required, admin_required
from models import Course, Program, YearLevelEnum, YearLevel, SemesterEnum, Semester, ProgramYearLevelSemesterCourse
from webforms.course_form import CourseForm
from webforms.upload_form import UploadForm
from flask import request

add_course_per_program_bp = Blueprint('add_course_per_program', __name__)

YEAR_LEVEL_MAPPING = {
    1: 'FIRST_YEAR',
    2: 'SECOND_YEAR',
    3: 'THIRD_YEAR',
    4: 'FOURTH_YEAR'
}


@add_course_per_program_bp.route('/add_course/<int:program_id>/<int:year>/<int:sem>', methods=['GET', 'POST'])
@login_required
@cspc_acc_required
@admin_required
def add_course(program_id, year, sem):
    form = CourseForm()
    upload_form = UploadForm()  # Use the UploadForm for file uploads

    # Get Program
    program = Program.query.get_or_404(program_id)

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
            try:
                for index, row in df.iterrows():
                    # Process course name and code
                    course_name = ' '.join(row['course_name'].strip().lower().split())
                    course_code = ' '.join(row['course_code'].strip().upper().split())
                    course_units = int(row['course_units'])  # Ensure units is an integer

                    # Check if a course with the same name or code already exists
                    existing_course = Course.query.filter(
                        (Course.course_name == course_name) |
                        (Course.course_code == course_code)
                    ).first()

                    if existing_course:
                        course = existing_course
                        flash(f'Course "{course_name}" with this name or code already exists.', 'error')
                    else:
                        # Create a new course
                        course = Course(
                            course_name=course_name,
                            course_code=course_code,
                            course_units=course_units
                        )
                        db.session.add(course)
                        db.session.commit()
                        flash(f'Course "{course_name}" added successfully!', 'success')

                    # Associate the course with the program, year level, and semester
                    association_exists = ProgramYearLevelSemesterCourse.query.filter_by(
                        program_id=program_id,
                        year_level_id=year_level.id,
                        semester_id=semester.id,
                        course_id=course.id
                    ).first()

                    if not association_exists:
                        new_association = ProgramYearLevelSemesterCourse(
                            program_id=program_id,
                            year_level_id=year_level.id,
                            semester_id=semester.id,
                            course_id=course.id
                        )
                        db.session.add(new_association)
                        db.session.commit()
                        flash(f'Course "{course_name}" association added successfully!', 'success')

                return redirect(url_for('add_course_per_program.add_course', program_id=program_id, year=year, sem=sem))

            except KeyError as e:
                flash(f'Missing column: {e}. Please make sure the uploaded file contains "course_name", "course_code", and "course_units" columns.', 'error')
            except ValueError:
                flash('Invalid data format in the uploaded file. Please ensure that course units are numeric.', 'error')
            except Exception as e:
                flash(f'An unexpected error occurred: {str(e)}', 'error')

    elif form.validate_on_submit():
        # Process course name and code
        course_name = ' '.join(form.name.data.strip().lower().split())
        course_code = ' '.join(form.code.data.strip().upper().split())
        course_units = form.units.data

        # Check if a course with the same name or code already exists
        existing_course = Course.query.filter(
            (Course.course_name == course_name) |
            (Course.course_code == course_code)
        ).first()

        if existing_course:
            course = existing_course
            flash('Course with this name or code already exists.', 'error')
        else:
            # Process form data and create a new course
            course = Course(
                course_name=course_name,
                course_code=course_code,
                course_units=course_units
            )
            db.session.add(course)
            db.session.commit()
            flash('Course added successfully!', 'success')

        # Associate the course with the program, year level, and semester
        association_exists = ProgramYearLevelSemesterCourse.query.filter_by(
            program_id=program_id,
            year_level_id=year_level.id,
            semester_id=semester.id,
            course_id=course.id
        ).first()

        if not association_exists:
            new_association = ProgramYearLevelSemesterCourse(
                program_id=program_id,
                year_level_id=year_level.id,
                semester_id=semester.id,
                course_id=course.id
            )
            db.session.add(new_association)
            db.session.commit()
            flash('Course association with program, year level, and semester added successfully!', 'success')

        return redirect(url_for('add_course_per_program.add_course', program_id=program_id, year=year, sem=sem))

    return render_template('course/add_courses.html', form=form, upload_form=upload_form,
                           program_code=program.program_code,
                           year_level=year_level, semester=semester)

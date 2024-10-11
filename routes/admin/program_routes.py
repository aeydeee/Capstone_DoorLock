from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_required
from sqlalchemy.exc import IntegrityError

from app import db
from decorators import cspc_acc_required, admin_required
from models import ProgramYearLevelSemesterCourse, Semester, YearLevel, Program, Program, Section, Student
from webforms.delete_form import DeleteForm
from webforms.program_form import ProgramForm, YearLevelForm, SemesterForm, CourseForm, \
    SectionForm, EditSectionForm

program_bp = Blueprint('program', __name__)


@program_bp.route("/", methods=["GET", "POST"])
@login_required
@cspc_acc_required
@admin_required
def manage_program():
    delete_form = DeleteForm()
    program_form = ProgramForm(prefix='program')
    section_form = SectionForm(prefix='section')

    # Populate choices for SelectFields
    programs = Program.query.all()

    if request.method == "POST":
        if program_form.submit.data and program_form.validate():
            # Preprocess the program name and program code
            program_name = ' '.join(program_form.program_name.data.strip().lower().split())
            program_code = ' '.join(program_form.program_code.data.strip().lower().split())

            program = Program(program_name=program_name, program_code=program_code)
            try:
                db.session.add(program)
                db.session.commit()
                flash('Program added successfully', 'success')
            except IntegrityError:
                db.session.rollback()
                flash('Error: Duplicate program code.', 'error')
            return redirect(url_for('program.manage_program'))

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

            return redirect(url_for('program.manage_program'))

    sections = Section.query.all()

    return render_template('program/manage_program.html',
                           delete_form=delete_form,
                           program_form=program_form,
                           section_form=section_form,
                           programs=programs,
                           sections=sections)


@program_bp.route("/edit_program/<string:program_type>/<int:program_id>", methods=["GET", "POST"])
@login_required
@cspc_acc_required
@admin_required
def edit_program(program_type, program_id):
    if program_type == "program":
        program = Program.query.get_or_404(program_id)
        form = ProgramForm(obj=program, prefix='program')
    elif program_type == "year_level":
        program = YearLevel.query.get_or_404(program_id)
        form = YearLevelForm(obj=program, prefix='year_level')
    elif program_type == "semester":
        program = Semester.query.get_or_404(program_id)
        form = SemesterForm(obj=program, prefix='semester')
    else:
        flash('Invalid program type', 'error')
        return redirect(url_for('program.manage_program'))

    if request.method == "POST" and form.validate():
        if program_type == "program":
            # Preprocess program name and code
            program.program_name = ' '.join(form.program_name.data.strip().lower().split())
            program.program_code = ' '.join(form.program_code.data.strip().lower().split())
        elif program_type == "year_level":
            # Preprocess year level name
            program.level_name = ' '.join(form.level_name.data.strip().lower().split())
        elif program_type == "semester":
            # Preprocess semester name
            program.semester_name = ' '.join(form.semester_name.data.strip().lower().split())

        db.session.commit()
        flash(f'{program_type.replace("_", " ").title()} updated successfully', 'success')
        return redirect(url_for('program.manage_program'))

    return render_template('program/edit_program.html', form=form, program=program, program_type=program_type)


@program_bp.route('/delete_program/<string:program_type>/<int:program_id>', methods=['POST'])
@login_required
@cspc_acc_required
@admin_required
def delete_program(program_type, program_id):
    if program_type == 'program':
        program = Program.query.get_or_404(program_id)
        related_records = ProgramYearLevelSemesterCourse.query.filter_by(program_id=program_id).all()
    elif program_type == 'year_level':
        program = YearLevel.query.get_or_404(program_id)
        related_records = ProgramYearLevelSemesterCourse.query.filter_by(year_level_id=program_id).all()
    elif program_type == 'semester':
        program = Semester.query.get_or_404(program_id)
        related_records = ProgramYearLevelSemesterCourse.query.filter_by(semester_id=program_id).all()
    elif program_type == 'section':
        program = Section.query.get_or_404(program_id)
        related_records = Student.query.filter_by(section_id=program_id).all()
    else:
        flash('Invalid program type', 'error')
        return redirect(url_for('program.manage_program'))

    try:
        for record in related_records:
            db.session.delete(record)
        db.session.delete(program)
        db.session.commit()
        flash(f'{program_type.replace("_", " ").title()} deleted successfully', 'success')
    except IntegrityError:
        db.session.rollback()
        flash(f'Error deleting {program_type.replace("_", " ").title()}. It may be referenced by other records.',
              'error')

    return redirect(url_for('program.manage_program'))

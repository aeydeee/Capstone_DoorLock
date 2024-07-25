from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from datetime import datetime
from models import Subject, Faculty, Schedule
from webforms.subject_form import SubjectForm, EditSubjectForm
from app import db

subject_bp = Blueprint('subject', __name__)


@subject_bp.route('/')
def manage_subject():
    # Get the page number from the query parameters, defaulting to page 1
    page = request.args.get('page', 1, type=int)
    per_page = 20  # Number of items per page

    # Query all faculties with their subjects and schedule details, paginated
    faculties = Faculty.query.paginate(page=page, per_page=per_page)

    # Render the HTML template with the fetched data
    return render_template('subject/manage_subject.html', faculties=faculties)


@subject_bp.route('/add_subject', methods=['GET', 'POST'])
def add_subject():
    form = SubjectForm()

    # Fetch faculties from the database
    faculties = Faculty.query.all()
    form.faculty.choices = [(facu.id, facu.full_name) for facu in faculties]

    if form.validate_on_submit():
        # Process form data
        name = form.name.data
        code = form.code.data
        units = form.units.data
        faculty_id = form.faculty.data

        day = form.day.data
        schedule_from = form.schedule_from.data
        schedule_to = form.schedule_to.data

        # Convert to time objects
        schedule_from_time = datetime.combine(datetime.min, schedule_from).time()
        schedule_to_time = datetime.combine(datetime.min, schedule_to).time()

        # Create a new subject
        new_subject = Subject(name=name, code=code, units=units, faculty_id=faculty_id)
        db.session.add(new_subject)
        db.session.commit()  # Commit to get the new_subject ID

        # Create a new schedule linked to the subject
        new_schedule = Schedule(day=day, schedule_from=schedule_from_time, schedule_to=schedule_to_time,
                                subject_id=new_subject.id)
        db.session.add(new_schedule)
        db.session.commit()

        flash('Subject added successfully!')
        return redirect(url_for('subject.add_subject'))

    return render_template('subject/add_subject.html', form=form)


@subject_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_subject(id):
    subj = Subject.query.get_or_404(id)
    form = EditSubjectForm(obj=subj)

    # Fetch faculties from the database and populate choices
    faculties = Faculty.query.all()
    form.faculty.choices = [(facu.id, facu.full_name) for facu in faculties]

    if form.validate_on_submit():
        # Update the subject object with form data
        subj.name = form.name.data
        subj.code = form.code.data
        subj.units = form.units.data
        subj.faculty_id = form.faculty.data

        db.session.commit()
        flash('Subject has been updated successfully!')
        return redirect(url_for('subject.manage_subject'))

    # Fetch the schedule details to display in the form
    schedules = subj.schedule_details

    return render_template('subject/edit_subject.html', form=form, subject=subj, schedules=schedules)

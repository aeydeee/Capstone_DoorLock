from flask import Blueprint, render_template, redirect, url_for, flash, request
from datetime import datetime, timedelta
from models import Schedule, Faculty, Subject
from webforms.schedule_form import ScheduleForm, EditScheduleForm
from app import db

schedule_bp = Blueprint('schedule', __name__)


@schedule_bp.route('/add_schedule', methods=['GET', 'POST'])
def add_schedule():
    form = ScheduleForm()

    # Fetch faculties from the database and populate choices
    faculties = Faculty.query.all()
    form.faculty.choices = [(instr.id, instr.full_name) for instr in faculties]

    # Default to the first faculty if none is selected
    faculty_id = form.faculty.data or (faculties[0].id if faculties else None)

    if faculty_id:
        # Populate subject choices based on the selected faculty
        subjects = Subject.query.filter_by(faculty_id=faculty_id).all()
        form.subject.choices = [(subj.id, subj.name) for subj in subjects]

    if request.method == 'POST':
        # Update subject choices based on the selected faculty
        faculty_id = form.faculty.data
        subjects = Subject.query.filter_by(faculty_id=faculty_id).all()
        form.subject.choices = [(subj.id, subj.name) for subj in subjects]

        # Set default values for schedule_from and schedule_to if not provided
        if 'schedule_from' not in request.form:
            form.schedule_from.data = datetime.now().time()

        if 'schedule_to' not in request.form:
            form.schedule_to.data = (datetime.now() + timedelta(hours=1)).time()

        if form.validate_on_submit():
            # Process form data
            faculty_id = form.faculty.data
            subject_id = form.subject.data
            day = form.day.data
            schedule_from = form.schedule_from.data
            schedule_to = form.schedule_to.data

            # Convert to time objects
            schedule_from_time = datetime.combine(datetime.min, schedule_from).time()
            schedule_to_time = datetime.combine(datetime.min, schedule_to).time()

            # Fetch the existing subject
            existing_subject = Subject.query.get(subject_id)

            if existing_subject:
                # Ensure the subject belongs to the selected faculty
                if existing_subject.faculty_id == int(faculty_id):
                    # Create a new schedule linked to the existing subject
                    new_schedule = Schedule(
                        day=day,
                        schedule_from=schedule_from_time,
                        schedule_to=schedule_to_time,
                        subject_id=existing_subject.id
                    )
                    db.session.add(new_schedule)
                    db.session.commit()

                    flash('Schedule added successfully!', 'success')
                    return redirect(url_for('schedule.add_schedule'))
                else:
                    flash('The selected subject does not belong to the chosen faculty.', 'error')
            else:
                flash('Subject not found.', 'error')

    return render_template('schedule/add_schedule.html', form=form)


@schedule_bp.route('/')
def manage_schedule():
    # Get the page number from the query parameters, defaulting to page 1
    page = request.args.get('page', 1, type=int)
    per_page = 20  # Number of items per page

    # Query all faculties with their subjects and schedule details, paginated
    faculties = Faculty.query.paginate(page=page, per_page=per_page)

    # Render the HTML template with the fetched data
    return render_template('schedule/manage_schedule.html', faculties=faculties)


@schedule_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_schedule(id):
    sched = Schedule.query.get_or_404(id)
    form = EditScheduleForm(obj=sched)

    if form.validate_on_submit():
        # Update the schedule object with form data
        form.populate_obj(sched)

        # Convert to time objects
        schedule_from_time = datetime.combine(datetime.min, form.schedule_from.data).time()
        schedule_to_time = datetime.combine(datetime.min, form.schedule_to.data).time()

        sched.schedule_from = schedule_from_time
        sched.schedule_to = schedule_to_time

        db.session.commit()
        flash('Schedule has been updated successfully!')
        return redirect(url_for('schedule.manage_schedule'))

    return render_template('schedule/edit_schedule.html', form=form, schedule=sched)

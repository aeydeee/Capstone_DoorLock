from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from datetime import datetime, timedelta
from models import Schedule, Faculty, Subject
from webforms.delete_form import DeleteForm
from webforms.schedule_form import ScheduleForm, EditScheduleForm
from app import db

schedule_bp = Blueprint('schedule', __name__)


@schedule_bp.route('/<int:faculty_id>/schedule')
def view_schedule(faculty_id):
    delete_form = DeleteForm()
    faculty = Faculty.query.get_or_404(faculty_id)
    schedule = Schedule.query.filter_by(faculty_id=faculty_id).all()
    return render_template('schedule/view_schedule.html', faculty=faculty, schedule=schedule, delete_form=delete_form)


@schedule_bp.route('/get_subjects/<int:faculty_id>', methods=['GET'])
def get_subjects(faculty_id):
    subjects = Subject.query.filter_by(faculty_id=faculty_id).all()
    subjects_list = [(subj.id, subj.subject_name) for subj in subjects]
    return jsonify(subjects_list)


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
        form.subject.choices = [(subj.id, subj.subject_name) for subj in subjects]

    if request.method == 'POST':
        # Update subject choices based on the selected faculty
        faculty_id = form.faculty.data
        subjects = Subject.query.filter_by(faculty_id=faculty_id).all()
        form.subject.choices = [(subj.id, subj.subject_name) for subj in subjects]

        if form.validate_on_submit():
            # Process form data
            faculty_id = form.faculty.data
            subject_id = form.subject.data
            schedule_day = form.schedule_day.data
            schedule_time_from = form.schedule_time_from.data
            schedule_time_to = form.schedule_time_to.data

            # Fetch the existing subject
            existing_subject = Subject.query.get(subject_id)

            if existing_subject:
                # Ensure the subject belongs to the selected faculty
                if existing_subject.faculty_id == int(faculty_id):
                    # Create a new schedule linked to the existing subject
                    new_schedule = Schedule(
                        schedule_day=schedule_day,
                        schedule_time_from=schedule_time_from,
                        schedule_time_to=schedule_time_to,
                        faculty_id=faculty_id,  # Ensure faculty_id is assigned
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


@schedule_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_schedule(id):
    sched = Schedule.query.get_or_404(id)
    form = EditScheduleForm(obj=sched)

    if form.validate_on_submit():
        # Update the schedule object with form data
        form.populate_obj(sched)

        # Convert to time objects
        schedule_time_from = datetime.combine(datetime.min, form.schedule_time_from.data).time()
        schedule_time_to = datetime.combine(datetime.min, form.schedule_time_to.data).time()

        sched.schedule_time_from = schedule_time_from
        sched.schedule_time_to = schedule_time_to

        db.session.commit()
        flash('Schedule has been updated successfully!')
        return redirect(url_for('schedule.view_schedule', faculty_id=sched.faculty_id))

    return render_template('schedule/edit_schedule.html', form=form, schedule=sched)


@schedule_bp.route('/delete/<int:id>', methods=['POST'])
def delete_schedule(id):
    schedule = Schedule.query.get_or_404(id)
    db.session.delete(schedule)
    db.session.commit()
    flash('Schedule deleted successfully', 'success')
    return redirect(url_for('schedule.view_schedule', faculty_id=schedule.faculty_id))

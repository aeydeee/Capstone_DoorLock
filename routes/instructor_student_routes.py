import os
import uuid

from flask import Blueprint, request, render_template, current_app, flash, redirect, url_for
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename

from app import db
from models import Faculty, User, EducationalBackground, FamilyBackground, ContactInfo, Student
from webforms.delete_form import DeleteForm
from webforms.search_form import SearchForm

from sqlalchemy.exc import SQLAlchemyError

instructor_bp = Blueprint('instructor', __name__)


@instructor_bp.route('/students')
@login_required
def view_students():
    search = SearchForm()
    delete_form = DeleteForm()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search_query = request.args.get('search', '')

    # Filter students by the current user's (faculty) ID
    query = Student.query.join(Student.faculties).filter(Faculty.id == current_user.faculty_details.id)

    if search_query:
        query = query.join(User).filter(
            db.or_(
                User.f_name.ilike(f'%{search_query}%'),
                User.m_name.ilike(f'%{search_query}%'),
                User.l_name.ilike(f'%{search_query}%'),
                User.rfid_uid.ilike(f'%{search_query}%'),
                User.email.ilike(f'%{search_query}%')
            )
        )

    students = query.paginate(page=page, per_page=per_page)

    return render_template('instructor/view_students.html', students=students, search=search, form=delete_form)

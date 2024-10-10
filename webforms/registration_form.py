from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, FileField, PasswordField, SubmitField, IntegerField, DateField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, ValidationError
from flask_wtf.file import FileAllowed

from models import User


class RegistrationForm(FlaskForm):
    rfid_uid = StringField('RFID UID', validators=[DataRequired(), Length(max=100)])
    username = StringField('Username', validators=[Length(max=255)])
    f_name = StringField('First Name', validators=[DataRequired(), Length(max=100)])
    l_name = StringField('Last Name', validators=[DataRequired(), Length(max=100)])
    m_name = StringField('Middle Name', validators=[Length(max=100)])  # Optional Middle Name
    m_initial = StringField('Middle Initial', validators=[Length(max=10)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=100)])
    date_of_birth = DateField('Date of Birth', validators=[DataRequired()])
    place_of_birth = StringField('Place of Birth', validators=[DataRequired(), Length(max=255)])
    role = SelectField('Role', choices=[('student', 'Student'), ('faculty', 'Faculty'), ('admin', 'Admin')],
                       validators=[DataRequired()])
    gender = SelectField('Gender', choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')],
                         validators=[DataRequired()])
    civil_status = StringField('Civil Status', validators=[Length(max=50)])
    nationality = StringField('Nationality', validators=[Length(max=100)])
    citizenship = StringField('Citizenship', validators=[Length(max=100)])
    religion = StringField('Religion', validators=[Length(max=100)])
    dialect = StringField('Dialect', validators=[Length(max=100)])
    tribal_aff = StringField('Tribal Affiliation', validators=[Length(max=100)])
    profile_pic = FileField('Profile Picture')

    # Contact Information
    contact_number = IntegerField('Contact Number', validators=[DataRequired(), Length(min=10, max=15)])
    home_addr = SelectField('Home City', validators=[DataRequired(), Length(max=100)])
    home_brgy = SelectField('Home Barangay', validators=[DataRequired(), Length(max=100)])
    home_house_no = StringField('Home House Number', validators=[DataRequired(), Length(max=100)])
    home_street = StringField('Home Street', validators=[DataRequired(), Length(max=100)])
    curr_addr = SelectField('Current City', validators=[Length(max=100)])
    curr_brgy = SelectField('Current Barangay', validators=[Length(max=100)])
    curr_house_no = StringField('Current House Number', validators=[Length(max=100)])
    curr_street = StringField('Current Street', validators=[Length(max=100)])

    # Family Background
    mother_full_name = StringField('Mother\'s Full Name', validators=[Length(max=255)])
    mother_educ_attainment = StringField('Mother\'s Educational Attainment', validators=[Length(max=255)])
    mother_addr = SelectField('Mother\'s Address', validators=[Length(max=255)])
    mother_brgy = SelectField('Mother\'s Barangay', validators=[Length(max=100)])
    mother_cont_no = IntegerField('Mother\'s Contact Number', validators=[Length(max=15)])
    mother_place_work_or_company_name = StringField('Mother\'s Place of Work or Company Name',
                                                    validators=[Length(max=255)])
    mother_occupation = StringField('Mother\'s Occupation', validators=[Length(max=255)])

    father_full_name = StringField('Father\'s Full Name', validators=[Length(max=255)])
    father_educ_attainment = StringField('Father\'s Educational Attainment', validators=[Length(max=255)])
    father_addr = SelectField('Father\'s Address', validators=[Length(max=255)])
    father_brgy = SelectField('Father\'s Barangay', validators=[Length(max=100)])
    father_cont_no = IntegerField('Father\'s Contact Number', validators=[Length(max=15)])
    father_place_work_or_company_name = StringField('Father\'s Place of Work or Company Name',
                                                    validators=[Length(max=255)])
    father_occupation = StringField('Father\'s Occupation', validators=[Length(max=255)])

    guardian_full_name = StringField('Guardian\'s Full Name', validators=[Length(max=255)])
    guardian_educ_attainment = StringField('Guardian\'s Educational Attainment', validators=[Length(max=255)])
    guardian_addr = SelectField('Guardian\'s Address', validators=[Length(max=255)])
    guardian_brgy = SelectField('Guardian\'s Barangay', validators=[Length(max=100)])
    guardian_cont_no = IntegerField('Guardian\'s Contact Number', validators=[Length(max=15)])
    guardian_place_work_or_company_name = StringField('Guardian\'s Place of Work or Company Name',
                                                      validators=[Length(max=255)])
    guardian_occupation = StringField('Guardian\'s Occupation', validators=[Length(max=255)])

    # Educational Background
    elem_school_name = StringField('Elementary School Name', validators=[Length(max=255)])
    elem_school_addr = SelectField('Elementary School Address', validators=[Length(max=255)])
    elem_year_grad = StringField('Elementary Year Graduated', validators=[Length(max=4)])

    junior_hs_school_name = StringField('Junior High School Name', validators=[Length(max=255)])
    junior_hs_school_addr = SelectField('Junior High School Address', validators=[Length(max=255)])
    junior_hs_year_grad = StringField('Junior High Year Graduated', validators=[Length(max=4)])

    senior_hs_school_name = StringField('Senior High School Name', validators=[Length(max=255)])
    senior_hs_school_addr = SelectField('Senior High School Address', validators=[Length(max=255)])
    senior_hs_year_grad = StringField('Senior High Year Graduated', validators=[Length(max=4)])
    senior_strand = StringField('Senior High School Track/Strand', validators=[Length(max=255)])

    tertiary_school_name = StringField('Tertiary School Name', validators=[Length(max=255)])
    tertiary_school_addr = SelectField('Tertiary School Address', validators=[Length(max=255)])
    tertiary_year_grad = StringField('Tertiary Year Graduated', validators=[Length(max=4)])
    tertiary_course = StringField('Tertiary School Course', validators=[Length(max=255)])

    # Student
    student_number = StringField('School ID', validators=[DataRequired(), Length(max=100)])
    # Course and Year
    course_id = SelectField('Course', coerce=int, validators=[DataRequired()])
    year_level_id = SelectField('Year Level', coerce=int, validators=[DataRequired()])
    section_id = SelectField('Section', coerce=int, validators=[DataRequired()])
    semester_id = SelectField('Semester', coerce=int, validators=[DataRequired()])

    # Faculty fields
    faculty_id = StringField('School ID')
    designation = StringField('Faculty Designation')
    faculty_department = StringField('Faculty Department')

    # Admin fields
    school_id = StringField('School ID')
    admin_department = StringField('Admin Department')

    password = PasswordField('Password', validators=[Optional(), Length(min=8),
                                                     EqualTo('password_2', message='Passwords must match!')])
    password_2 = PasswordField('Confirm Password')

    submit = SubmitField('Register')

    def validate_username(self, username):
        user_object = User.query.filter_by(username=username.data).first()
        if user_object:
            raise ValidationError("Username already exists. Select a different username.")

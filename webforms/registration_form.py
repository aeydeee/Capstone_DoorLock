from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, FileField, PasswordField, SubmitField, IntegerField, DateField
from wtforms.validators import DataRequired, Email, EqualTo
from flask_wtf.file import FileAllowed


class RegistrationForm(FlaskForm):
    # Existing fields
    rfid_uid = StringField('RFID UID', validators=[DataRequired()])
    username = StringField('Username', validators=[DataRequired()])
    f_name = StringField('First Name', validators=[DataRequired()])
    l_name = StringField('Last Name', validators=[DataRequired()])
    m_name = StringField('Middle Name', validators=[DataRequired()])
    m_initial = StringField('Middle Initial', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    date_of_birth = DateField('Date of Birth', validators=[DataRequired()])
    place_of_birth = StringField('Place of Birth', validators=[DataRequired()])
    role = SelectField('Role', choices=[('student', 'Student'), ('faculty', 'Faculty'), ('admin', 'Admin')],
                       validators=[DataRequired()])
    profile_pic = FileField('Profile Picture', validators=[FileAllowed(['jpg', 'jpeg', 'png'], 'Images only!')])
    gender = SelectField('Gender', choices=[('male', 'Male'), ('female', 'Female')], validators=[DataRequired()])
    civil_status = StringField('Civil Status', validators=[DataRequired()])
    nationality = StringField('Nationality', validators=[DataRequired()])
    citizenship = StringField('Citizenship', validators=[DataRequired()])
    address = StringField('Address', validators=[DataRequired()])
    religion = StringField('Religion', validators=[DataRequired()])
    dialect = StringField('Dialect', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])

    # ContactInfo fields
    contact_number = StringField('Contact Number', validators=[DataRequired()])
    h_city = StringField('Home City', validators=[DataRequired()])
    h_barangay = StringField('Home Barangay', validators=[DataRequired()])
    h_house_no = IntegerField('Home House Number', validators=[DataRequired()])
    h_street = StringField('Home Street', validators=[DataRequired()])
    curr_city = StringField('Current City')
    curr_barangay = StringField('Current Barangay')
    curr_house_no = IntegerField('Current House Number')
    curr_street = StringField('Current Street')

    # FamilyBackground fields
    mother_full_name = StringField('Mother Full Name', validators=[DataRequired()])
    mother_educ_attainment = StringField('Mother Education Attainment')
    mother_addr = StringField('Mother Address')
    mother_brgy = StringField('Mother Barangay')
    mother_cont_no = StringField('Mother Contact Number')
    mother_place_work_or_company_name = StringField('Mother Place of Work or Company Name')
    mother_occupation = StringField('Mother Occupation')
    father_full_name = StringField('Father Full Name')
    father_educ_attainment = StringField('Father Education Attainment')
    father_addr = StringField('Father Address')
    father_brgy = StringField('Father Barangay')
    father_cont_no = StringField('Father Contact Number')
    father_place_work_or_company_name = StringField('Father Place of Work or Company Name')
    father_occupation = StringField('Father Occupation')
    guardian_full_name = StringField('Guardian Full Name')
    guardian_educ_attainment = StringField('Guardian Education Attainment')
    guardian_addr = StringField('Guardian Address')
    guardian_brgy = StringField('Guardian Barangay')
    guardian_cont_no = StringField('Guardian Contact Number')
    guardian_place_work_or_company_name = StringField('Guardian Place of Work or Company Name')
    guardian_occupation = StringField('Guardian Occupation')

    # EducationalBackground fields
    elem_school = StringField('Elementary School', validators=[DataRequired()])
    elem_address = StringField('Elementary School Address', validators=[DataRequired()])
    elem_graduated = IntegerField('Elementary Graduation Year', validators=[DataRequired()])
    junior_school = StringField('Junior High School')
    junior_address = StringField('Junior High School Address')
    junior_graduated = IntegerField('Junior High School Graduation Year')
    senior_school = StringField('Senior High School', validators=[DataRequired()])
    senior_address = StringField('Senior High School Address', validators=[DataRequired()])
    senior_graduated = IntegerField('Senior High School Graduation Year', validators=[DataRequired()])
    senior_track_strand = StringField('Senior High School Track/Strand', validators=[DataRequired()])

    # Student fields
    student_number = StringField('School ID')
    course_name = StringField('Course')
    year_level = SelectField('Year Level', choices=[
        (1, 'First Year'),
        (2, 'Second Year'),
        (3, 'Third Year'),
        (4, 'Fourth Year')
    ])
    section = StringField('Section')

    # Faculty fields
    faculty_id = StringField('School ID')
    designation = StringField('Faculty Designation')
    faculty_department = StringField('Faculty Department')

    # Admin fields
    admin_department = StringField('Admin Department')
    school_id = StringField('School ID')

    submit = SubmitField('Register')

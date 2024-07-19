from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from wtforms.fields.choices import SelectField
from wtforms.fields.datetime import DateField
from wtforms.fields.numeric import IntegerField
from wtforms.fields.simple import StringField, SubmitField, PasswordField, EmailField, TextAreaField
from wtforms.validators import DataRequired, EqualTo, Length, Email, Optional


class AddFaculty(FlaskForm):
    rfid_uid = StringField('RFID UID', validators=[DataRequired(), Length(max=100)])
    username = StringField('Username', validators=[DataRequired(), Length(max=255)])
    f_name = StringField('First Name', validators=[DataRequired(), Length(max=100)])
    l_name = StringField('Last Name', validators=[DataRequired(), Length(max=100)])
    m_name = StringField('Middle Name', validators=[DataRequired(), Length(max=100)])
    m_initial = StringField('Middle Initial', validators=[DataRequired(), Length(max=1)])
    school_id = StringField('School ID', validators=[DataRequired(), Length(max=100)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=100)])
    date_of_birth = DateField('Date of Birth', validators=[DataRequired()])
    place_of_birth = StringField('Place of Birth', validators=[DataRequired(), Length(max=255)])
    gender = SelectField('Gender', choices=[('male', 'Male'), ('female', 'Female')], validators=[DataRequired()])
    civil_status = StringField('Civil Status', validators=[DataRequired(), Length(max=100)])
    nationality = StringField('Nationality', validators=[DataRequired(), Length(max=100)])
    citizenship = StringField('Citizenship', validators=[DataRequired(), Length(max=100)])
    address = TextAreaField('Address', validators=[DataRequired(), Length(max=255)])
    profile_pic = FileField('Profile Picture')
    religion = StringField('Religion', validators=[Optional(), Length(max=100)])
    dialect = StringField('Dialect', validators=[Optional(), Length(max=100)])
    contact_number = StringField('Contact Number', validators=[DataRequired(), Length(min=10, max=15)])

    # Contact Info fields
    h_city = StringField('Home City', validators=[Optional(), Length(max=100)])
    h_barangay = StringField('Home Barangay', validators=[Optional(), Length(max=100)])
    h_house_no = StringField('Home House Number', validators=[Optional(), Length(max=100)])
    h_street = StringField('Home Street', validators=[Optional(), Length(max=100)])
    curr_city = StringField('Current City', validators=[Optional(), Length(max=100)])
    curr_barangay = StringField('Current Barangay', validators=[Optional(), Length(max=100)])
    curr_house_no = StringField('Current House Number', validators=[Optional(), Length(max=100)])
    curr_street = StringField('Current Street', validators=[Optional(), Length(max=100)])

    # Family Background fields
    mother_full_name = StringField('Mother\'s Full Name', validators=[Optional(), Length(max=255)])
    mother_educ_attainment = StringField('Mother\'s Educational Attainment', validators=[Optional(), Length(max=255)])
    mother_addr = StringField('Mother\'s Address', validators=[Optional(), Length(max=255)])
    mother_brgy = StringField('Mother\'s Barangay', validators=[Optional(), Length(max=100)])
    mother_cont_no = StringField('Mother\'s Contact Number', validators=[Optional(), Length(min=10, max=15)])
    mother_place_work_or_company_name = StringField('Mother\'s Place of Work/Company Name',
                                                    validators=[Optional(), Length(max=255)])
    mother_occupation = StringField('Mother\'s Occupation', validators=[Optional(), Length(max=255)])
    father_full_name = StringField('Father\'s Full Name', validators=[Optional(), Length(max=255)])
    father_educ_attainment = StringField('Father\'s Educational Attainment', validators=[Optional(), Length(max=255)])
    father_addr = StringField('Father\'s Address', validators=[Optional(), Length(max=255)])
    father_brgy = StringField('Father\'s Barangay', validators=[Optional(), Length(max=100)])
    father_cont_no = StringField('Father\'s Contact Number', validators=[Optional(), Length(min=10, max=15)])
    father_place_work_or_company_name = StringField('Father\'s Place of Work/Company Name',
                                                    validators=[Optional(), Length(max=255)])
    father_occupation = StringField('Father\'s Occupation', validators=[Optional(), Length(max=255)])
    guardian_full_name = StringField('Guardian\'s Full Name', validators=[Optional(), Length(max=255)])
    guardian_educ_attainment = StringField('Guardian\'s Educational Attainment',
                                           validators=[Optional(), Length(max=255)])
    guardian_addr = StringField('Guardian\'s Address', validators=[Optional(), Length(max=255)])
    guardian_brgy = StringField('Guardian\'s Barangay', validators=[Optional(), Length(max=100)])
    guardian_cont_no = StringField('Guardian\'s Contact Number', validators=[Optional(), Length(min=10, max=15)])
    guardian_place_work_or_company_name = StringField('Guardian\'s Place of Work/Company Name',
                                                      validators=[Optional(), Length(max=255)])
    guardian_occupation = StringField('Guardian\'s Occupation', validators=[Optional(), Length(max=255)])

    # Educational Background fields
    elem_school_name = StringField('Elementary School Name',
                                   validators=[Optional(), Length(max=255)])
    elem_address = StringField('Elementary School Address',
                               validators=[Optional(), Length(max=255)])
    elem_year_grad = IntegerField('Elementary Year Graduated',
                                  validators=[Optional()])

    junior_hs_school_name = StringField('Junior High School Name',
                                        validators=[Optional(), Length(max=255)])
    junior_hs_address = StringField('Junior High School Address',
                                    validators=[Optional(), Length(max=255)])
    junior_hs_year_grad = IntegerField('Junior High Year Graduated',
                                       validators=[Optional()])

    senior_hs_school_name = StringField('Senior High School Name',
                                        validators=[Optional(), Length(max=255)])
    senior_hs_address = StringField('Senior High School Address',
                                    validators=[Optional(), Length(max=255)])
    senior_hs_year_grad = IntegerField('Senior High Year Graduated',
                                       validators=[Optional()])
    senior_hs_track_strand = StringField('Senior High Track/Strand',
                                         validators=[Optional(), Length(max=255)])

    tertiary_school_name = StringField('Tertiary School Name',
                                       validators=[Optional(), Length(max=255)])
    tertiary_school_address = StringField('Tertiary School Address',
                                          validators=[Optional(), Length(max=255)])
    tertiary_year_grad = IntegerField('Tertiary Year Graduated',
                                      validators=[Optional()])
    tertiary_course = StringField('Tertiary Course', validators=[Optional(), Length(max=255)])

    designation = StringField('Designation', validators=[DataRequired(), Length(max=255)])
    department = StringField('Department', validators=[DataRequired(), Length(max=255)])
    password = PasswordField('Password', validators=[Optional(), Length(min=8),
                                                     EqualTo('password_2', message='Passwords must match!')])
    password_2 = PasswordField('Confirm Password')
    submit = SubmitField('Register')

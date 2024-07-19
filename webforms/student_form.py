from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from wtforms.fields.choices import SelectField
from wtforms.fields.datetime import DateField
from wtforms.fields.simple import StringField, EmailField, TextAreaField, PasswordField, SubmitField
from wtforms.validators import Optional, DataRequired, Length, Email, EqualTo, NumberRange


class AddStudent(FlaskForm):
    rfid_uid = StringField('RFID UID', validators=[DataRequired(), Length(max=100)])
    username = StringField('Username', validators=[Length(max=255)])
    f_name = StringField('First Name', validators=[DataRequired(), Length(max=100)])
    l_name = StringField('Last Name', validators=[DataRequired(), Length(max=100)])
    m_name = StringField('Middle Name', validators=[DataRequired(), Length(max=100)])
    m_initial = StringField('Middle Initial', validators=[Length(max=10)])
    email = EmailField('Email', validators=[DataRequired(), Email(), Length(max=100)])
    date_of_birth = DateField('Date of Birth', validators=[DataRequired()])
    place_of_birth = StringField('Place of Birth', validators=[DataRequired(), Length(max=255)])
    gender = SelectField('Gender', choices=[('male', 'Male'), ('female', 'Female')], validators=[DataRequired()])
    civil_status = StringField('Civil Status', validators=[Length(max=50)])
    nationality = StringField('Nationality', validators=[Length(max=100)])
    citizenship = StringField('Citizenship', validators=[Length(max=100)])
    address = TextAreaField('Address', validators=[DataRequired(), Length(max=255)])
    religion = StringField('Religion', validators=[Length(max=100)])
    dialect = StringField('Dialect', validators=[Length(max=100)])
    profile_pic = FileField('Profile Picture')

    # Contact Information
    contact_number = StringField('Contact Number', validators=[DataRequired(), Length(min=10, max=15)])
    h_city = StringField('Home City', validators=[DataRequired(), Length(max=100)])
    h_barangay = StringField('Home Barangay', validators=[DataRequired(), Length(max=100)])
    h_house_no = StringField('Home House Number', validators=[DataRequired(), Length(max=100)])
    h_street = StringField('Home Street', validators=[DataRequired(), Length(max=100)])
    curr_city = StringField('Current City', validators=[Length(max=100)])
    curr_barangay = StringField('Current Barangay', validators=[Length(max=100)])
    curr_house_no = StringField('Current House Number', validators=[Length(max=100)])
    curr_street = StringField('Current Street', validators=[Length(max=100)])

    # Family Background
    mother_full_name = StringField('Mother\'s Full Name', validators=[Length(max=255)])
    mother_educ_attainment = StringField('Mother\'s Educational Attainment', validators=[Length(max=255)])
    mother_addr = TextAreaField('Mother\'s Address', validators=[Length(max=255)])
    mother_brgy = StringField('Mother\'s Barangay', validators=[Length(max=100)])
    mother_cont_no = StringField('Mother\'s Contact Number', validators=[Length(max=15)])
    mother_place_work_or_company_name = StringField('Mother\'s Place of Work or Company Name',
                                                    validators=[Length(max=255)])
    mother_occupation = StringField('Mother\'s Occupation', validators=[Length(max=255)])

    father_full_name = StringField('Father\'s Full Name', validators=[Length(max=255)])
    father_educ_attainment = StringField('Father\'s Educational Attainment', validators=[Length(max=255)])
    father_addr = TextAreaField('Father\'s Address', validators=[Length(max=255)])
    father_brgy = StringField('Father\'s Barangay', validators=[Length(max=100)])
    father_cont_no = StringField('Father\'s Contact Number', validators=[Length(max=15)])
    father_place_work_or_company_name = StringField('Father\'s Place of Work or Company Name',
                                                    validators=[Length(max=255)])
    father_occupation = StringField('Father\'s Occupation', validators=[Length(max=255)])

    guardian_full_name = StringField('Guardian\'s Full Name', validators=[Length(max=255)])
    guardian_educ_attainment = StringField('Guardian\'s Educational Attainment', validators=[Length(max=255)])
    guardian_addr = TextAreaField('Guardian\'s Address', validators=[Length(max=255)])
    guardian_brgy = StringField('Guardian\'s Barangay', validators=[Length(max=100)])
    guardian_cont_no = StringField('Guardian\'s Contact Number', validators=[Length(max=15)])
    guardian_place_work_or_company_name = StringField('Guardian\'s Place of Work or Company Name',
                                                      validators=[Length(max=255)])
    guardian_occupation = StringField('Guardian\'s Occupation', validators=[Length(max=255)])

    # Educational Background
    elem_school_name = StringField('Elementary School Name', validators=[Length(max=255)])
    elem_school_address = StringField('Elementary School Address', validators=[Length(max=255)])
    elem_year_grad = StringField('Elementary Year Graduated', validators=[Length(max=4)])

    junior_hs_school_name = StringField('Junior High School Name', validators=[Length(max=255)])
    junior_hs_school_addr = StringField('Junior High School Address', validators=[Length(max=255)])
    junior_hs_year_grad = StringField('Junior High Year Graduated', validators=[Length(max=4)])

    senior_hs_school_name = StringField('Senior High School Name', validators=[Length(max=255)])
    senior_hs_school_addr = StringField('Senior High School Address', validators=[Length(max=255)])
    senior_hs_year_grad = StringField('Senior High Year Graduated', validators=[Length(max=4)])
    senior_strand = StringField('Senior High School Track/Strand', validators=[Length(max=255)])

    tertiary_school_name = StringField('Tertiary School Name', validators=[Length(max=255)])
    tertiary_school_addr = StringField('Tertiary School Address', validators=[Length(max=255)])
    tertiary_year_grad = StringField('Tertiary Year Graduated', validators=[Length(max=4)])
    tertiary_course = StringField('Tertiary School Course', validators=[Length(max=255)])

    # Student
    school_id = StringField('School ID', validators=[DataRequired(), Length(max=100)])

    # Course and Year
    course_name = SelectField('Course',
                              choices=[
                                  ('GENED', 'General Education'),
                                  ('MIT', 'Master of Information Technology'),
                                  ('MEN', 'Master of Engineering'),
                                  ('MAN', 'Master of Arts in Nursing'),
                                  ('BSIT', 'Bachelor of Science in Information Technology'),
                                  ('BSCS', 'Bachelor of Science in Computer Science'),
                                  ('MBM', 'Master in Business Management'),
                                  ('BLIS', 'Bachelor of Library Information Science'),
                                  ('BSIS', 'Bachelor of Science in Information Systems'),
                                  ('BSME', 'Bachelor of Science in Mechanical Engineering'),
                                  ('BSCE', 'Bachelor of Science in Civil Engineering'),
                                  ('BSEE', 'Bachelor of Science in Electrical Engineering'),
                                  ('BSECE', 'Bachelor of Science in Electronics Engineering'),
                                  ('BSMath', 'Bachelor of Science in Mathematics'),
                                  ('BAEL', 'Bachelor of Arts in English Language'),
                                  ('BTVTEFSM',
                                   'Bachelor of Technical-Vocational Teacher Education Major in Food Service Management'),
                                  ('BTVTEET',
                                   'Bachelor of Technical-Vocational Teacher Education Major in Electronics Technology'),
                                  ('BSOA', 'Bachelor of Science in Office Administration'),
                                  ('BSHM', 'Bachelor of Science in Hospitality Management'),
                                  ('BSTM', 'Bachelor of Science in Tourism Management'),
                                  ('BSEM', 'Bachelor of Science in Entrepreneurial Management'),
                                  ('BSM', 'Bachelor of Science in Midwifery'),
                                  ('BSN', 'Bachelor of Science in Nursing')
                              ],
                              validators=[Length(max=255)])
    year_level = SelectField('Year Level',
                             choices=[(1, 'First Year'), (2, 'Second Year'), (3, 'Third Year'), (4, 'Fourth Year'),
                                      (5, 'Fifth Year'), (6, 'Graduate')], coerce=int,
                             validators=[DataRequired(), NumberRange(min=1, max=6)])
    section = StringField('Section', validators=[Length(max=255)])

    submit = SubmitField('Register')

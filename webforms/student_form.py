from flask_login import current_user

from wtforms.validators import ValidationError

from models import YearLevel, Section, Course, Semester, User, Student, DayOfWeek
from webforms.faculty_form import current_year
from webforms.validators import contact_num_length, strong_password

from wtforms import StringField, IntegerField, SelectField, DateField, HiddenField, FileField, SubmitField, EmailField
from wtforms.validators import DataRequired, Length, Optional, Email, NumberRange
from flask_wtf import FlaskForm


def coerce_int_or_none(value):
    if value == '' or value is None:
        return None
    return int(value)


class StudentForm(FlaskForm):
    def none_to_empty_string(value):
        return '' if value is None else value

    rfid_uid = StringField(
        'RFID UID',
        validators=[Length(max=100)],
        filters=[lambda x: x or ''],
        render_kw={"placeholder": "Leave blank if no RFID scanner"}
    )
    f_name = StringField('First Name', validators=[DataRequired(), Length(max=100)], filters=[none_to_empty_string])
    l_name = StringField('Last Name', validators=[DataRequired(), Length(max=100)], filters=[none_to_empty_string])
    m_name = StringField('Middle Name', validators=[Optional(), Length(max=100)], filters=[none_to_empty_string])
    # m_initial = StringField('Middle Initial', validators=[Optional(), Length(max=5)], filters=[none_to_empty_string])
    email = EmailField('Email', validators=[DataRequired(), Email(), Length(max=100)], filters=[none_to_empty_string])
    # date_of_birth = DateField('Date of Birth', validators=[DataRequired()], filters=[none_to_empty_string])
    # place_of_birth = StringField('Place of Birth', validators=[DataRequired(), Length(max=255)],
    #                              filters=[none_to_empty_string])
    gender = SelectField('Gender', choices=[('male', 'Male'), ('female', 'Female')], validators=[DataRequired()],
                         filters=[none_to_empty_string])
    # civil_status = SelectField('Civil Status', choices=[
    #     ('single', 'Single'),
    #     ('married', 'Married'),
    #     ('divorced', 'Divorced'),
    #     ('separated', 'Separated'),
    #     ('widowed', 'Widowed')
    # ], validators=[DataRequired()], filters=[none_to_empty_string])
    # nationality = StringField('Nationality', validators=[DataRequired(), Length(max=100)],
    #                           filters=[none_to_empty_string])
    # citizenship = StringField('Citizenship', validators=[DataRequired(), Length(max=100)],
    #                           filters=[none_to_empty_string])
    # religion = StringField('Religion', validators=[Optional(), Length(max=100)], filters=[none_to_empty_string])
    # dialect = StringField('Dialect', validators=[Optional(), Length(max=100)], filters=[none_to_empty_string])
    # tribal_aff = StringField('Tribal Affiliation', validators=[DataRequired(), Length(max=100)],
    #                          filters=[none_to_empty_string])
    # # profile_pic = FileField('Profile Picture')
    #
    # contact_number = IntegerField('Contact Number', validators=[DataRequired(), contact_num_length])
    # home_addr_text = HiddenField('Home Address Text', validators=[DataRequired()], filters=[none_to_empty_string])
    # home_brgy_text = HiddenField('Home Barangay Text', validators=[DataRequired()], filters=[none_to_empty_string])
    # home_house_no = StringField('Home House Number', validators=[DataRequired(), Length(max=100)],
    #                             filters=[none_to_empty_string])
    # home_street = StringField('Home Street', validators=[DataRequired(), Length(max=100)],
    #                           filters=[none_to_empty_string])
    # curr_addr_text = HiddenField('Current Address Text', validators=[DataRequired()], filters=[none_to_empty_string])
    # curr_brgy_text = HiddenField('Current Barangay Text', validators=[DataRequired()], filters=[none_to_empty_string])
    # curr_house_no = StringField('Current House Number', validators=[DataRequired(), Length(max=100)],
    #                             filters=[none_to_empty_string])
    # curr_street = StringField('Current Street', validators=[DataRequired(), Length(max=100)],
    #                           filters=[none_to_empty_string])
    #
    # mother_full_name = StringField('Mother\'s Full Name', validators=[DataRequired(), Length(max=255)],
    #                                filters=[none_to_empty_string])
    # mother_educ_attainment = StringField('Mother\'s Educational Attainment',
    #                                      validators=[DataRequired(), Length(max=255)], filters=[none_to_empty_string])
    # mother_addr_text = HiddenField('Mother Address Text', validators=[DataRequired()], filters=[none_to_empty_string])
    # mother_brgy_text = HiddenField('Mother Barangay Text', validators=[DataRequired()], filters=[none_to_empty_string])
    # mother_cont_no = IntegerField('Mother\'s Contact Number', validators=[DataRequired(), contact_num_length])
    # mother_place_work_or_company_name = StringField('Mother\'s Place of Work or Company Name',
    #                                                 validators=[Length(max=255)], filters=[none_to_empty_string])
    # mother_occupation = StringField('Mother\'s Occupation', validators=[DataRequired(), Length(max=255)],
    #                                 filters=[none_to_empty_string])
    #
    # father_full_name = StringField('Father\'s Full Name', validators=[Length(max=255)], filters=[none_to_empty_string])
    # father_educ_attainment = StringField('Father\'s Educational Attainment', validators=[Length(max=255)],
    #                                      filters=[none_to_empty_string])
    # father_addr_text = HiddenField('Father Address Text', validators=[DataRequired()], filters=[none_to_empty_string])
    # father_brgy_text = HiddenField('Father Barangay Text', validators=[DataRequired()], filters=[none_to_empty_string])
    # father_cont_no = IntegerField('Father\'s Contact Number', validators=[DataRequired(), contact_num_length])
    # father_place_work_or_company_name = StringField('Father\'s Place of Work or Company Name',
    #                                                 validators=[Length(max=255)], filters=[none_to_empty_string])
    # father_occupation = StringField('Father\'s Occupation', validators=[Length(max=255)],
    #                                 filters=[none_to_empty_string])
    #
    # guardian_full_name = StringField('Guardian\'s Full Name', validators=[Length(max=255)],
    #                                  filters=[none_to_empty_string])
    # guardian_educ_attainment = StringField('Guardian\'s Educational Attainment', validators=[Length(max=255)],
    #                                        filters=[none_to_empty_string])
    # guardian_addr_text = HiddenField('Guardian\'s Address Text', validators=[DataRequired()],
    #                                  filters=[none_to_empty_string])
    # guardian_brgy_text = HiddenField('Guardian\'s Barangay Text', validators=[DataRequired()],
    #                                  filters=[none_to_empty_string])
    # guardian_cont_no = IntegerField('Guardian\'s Contact Number', validators=[DataRequired(), contact_num_length])
    # guardian_place_work_or_company_name = StringField('Guardian\'s Place of Work or Company Name',
    #                                                   validators=[Length(max=255)], filters=[none_to_empty_string])
    # guardian_occupation = StringField('Guardian\'s Occupation', validators=[Length(max=255)],
    #                                   filters=[none_to_empty_string])
    #
    # elem_school_name = StringField('Elementary School Name', validators=[DataRequired(), Length(max=255)],
    #                                filters=[none_to_empty_string])
    # elem_school_addr_text = HiddenField('Elementary School Address Text', validators=[DataRequired()],
    #                                     filters=[none_to_empty_string])
    # elem_year_grad = IntegerField('Elementary Year Graduated',
    #                               validators=[DataRequired(), NumberRange(min=1900, max=current_year)])
    #
    # junior_hs_school_name = StringField('Junior High School Name', validators=[Length(max=255)],
    #                                     filters=[none_to_empty_string])
    # junior_hs_school_addr_text = HiddenField('Junior High School Address Text', validators=[DataRequired()],
    #                                          filters=[none_to_empty_string])
    # junior_hs_year_grad = IntegerField('Junior High Year Graduated',
    #                                    validators=[NumberRange(min=1900, max=current_year)])
    #
    # senior_hs_school_name = StringField('Senior High School Name', validators=[DataRequired(), Length(max=255)],
    #                                     filters=[none_to_empty_string])
    # senior_hs_school_addr_text = HiddenField('Senior High School Address Text', validators=[DataRequired()],
    #                                          filters=[none_to_empty_string])
    # senior_hs_year_grad = IntegerField('Senior High Year Graduated',
    #                                    validators=[NumberRange(min=1900, max=current_year)])
    # senior_strand = StringField('Senior High School Track/Strand', validators=[DataRequired(), Length(max=255)],
    #                             filters=[none_to_empty_string])
    #
    # tertiary_school_name = StringField('Tertiary School Name', validators=[Length(max=255)],
    #                                    filters=[none_to_empty_string])
    # tertiary_school_addr_text = HiddenField('Tertiary School Address Text', validators=[Length(max=255)],
    #                                         filters=[none_to_empty_string])
    # tertiary_year_grad = IntegerField('Tertiary Year Graduated', validators=[NumberRange(min=1900, max=current_year)])
    # tertiary_course = StringField('Tertiary School Course', validators=[Length(max=255)],
    #                               filters=[none_to_empty_string])

    student_number = StringField('School ID', validators=[DataRequired(), Length(max=100)],
                                 filters=[none_to_empty_string])

    course_id = SelectField('Course', coerce=int, validators=[DataRequired()], filters=[none_to_empty_string])
    section_id = SelectField('Section', coerce=int, validators=[DataRequired()], filters=[none_to_empty_string])
    year_level_id = SelectField('Year Level', coerce=int, validators=[DataRequired()], filters=[none_to_empty_string])
    semester_id = SelectField('Semester', coerce=int, validators=[DataRequired()], filters=[none_to_empty_string])

    same_as_home = SelectField(
        'Same as Home Address?',
        choices=[('yes', 'Yes'), ('no', 'No')],
        default='yes'
    )

    submit = SubmitField('Submit')

    # Custom validator for email domain
    def validate_email(self, field):
        if not field.data.endswith('@my.cspc.edu.ph'):
            raise ValidationError('Email must be an @my.cspc.edu.ph address.')


class OptionalPasswordIfAbsent:
    def __init__(self, message=None):
        self.message = message

    def __call__(self, form, field):
        if not current_user.student_details.password_hash and not field.data:
            raise ValidationError(self.message)


class EditStudentForm(FlaskForm):
    def none_to_empty_string(value):
        return '' if value is None else value

    rfid_uid = StringField(
        'RFID UID',
        validators=[Length(max=100)],
        filters=[lambda x: x or ''],
        render_kw={"placeholder": "Leave blank if no RFID scanner"}
    )
    # username = StringField('Username', validators=[DataRequired(), Length(max=255)])
    f_name = StringField('First Name', validators=[DataRequired(), Length(max=100)])
    l_name = StringField('Last Name', validators=[DataRequired(), Length(max=100)])
    m_name = StringField('Middle Name', validators=[Optional(), Length(max=100)])  # Made optional
    # m_initial = StringField('Middle Initial', validators=[Optional(), Length(max=5)])  # Made optional
    email = EmailField('Email', validators=[DataRequired(), Email(), Length(max=100)])
    #     date_of_birth = DateField('Date of Birth', validators=[DataRequired()])
    #     place_of_birth = StringField('Place of Birth', validators=[DataRequired(), Length(max=255)])
    gender = SelectField('Gender', choices=[('male', 'Male'), ('female', 'Female')], validators=[DataRequired()])
    # civil_status = SelectField('Civil Status',
    #                            choices=[
    #                                ('single', 'Single'),
    #                                ('married', 'Married'),
    #                                ('divorced', 'Divorced'),
    #                                ('separated', 'Separated'),
    #                                ('widowed', 'Widowed')
    #                            ],
    #                            validators=[DataRequired()])
    # nationality = StringField('Nationality', validators=[DataRequired(), Length(max=100)])
    # citizenship = StringField('Citizenship', validators=[DataRequired(), Length(max=100)])
    # religion = StringField('Religion', validators=[DataRequired(), Length(max=100)])
    # dialect = StringField('Dialect', validators=[DataRequired(), Length(max=100)])
    # tribal_aff = StringField('Tribal Affiliation', validators=[DataRequired(), Length(max=100)])
    # # profile_pic = FileField('Profile Picture')
    #
    # # Contact Information
    # contact_number = IntegerField('Contact Number', validators=[DataRequired(), contact_num_length])
    # home_addr_text = HiddenField('Home Address Text', validators=[DataRequired()])
    # home_brgy_text = HiddenField('Home Barangay Text', validators=[DataRequired()])
    # home_house_no = StringField('Home House Number', validators=[DataRequired(), Length(max=100)])
    # home_street = StringField('Home Street', validators=[DataRequired(), Length(max=100)])
    # curr_addr_text = HiddenField('Current Address Text', validators=[DataRequired()])
    # curr_brgy_text = HiddenField('Current Barangay Text', validators=[DataRequired()])
    # curr_house_no = StringField('Current House Number', validators=[DataRequired(), Length(max=100)])
    # curr_street = StringField('Current Street', validators=[Length(max=100), DataRequired()])
    #
    # # Family Background
    # mother_full_name = StringField('Mother\'s Full Name', validators=[DataRequired(), Length(max=255)])
    # mother_educ_attainment = StringField('Mother\'s Educational Attainment',
    #                                      validators=[DataRequired(), Length(max=255)])
    # mother_addr_text = HiddenField('Mother Address Text', validators=[DataRequired()])
    # mother_brgy_text = HiddenField('Mother Barangay Text', validators=[DataRequired()])
    # mother_cont_no = IntegerField('Mother\'s Contact Number', validators=[DataRequired(), contact_num_length])
    # mother_place_work_or_company_name = StringField('Mother\'s Place of Work or Company Name',
    #                                                 validators=[Length(max=255)])
    # mother_occupation = StringField('Mother\'s Occupation', validators=[Length(max=255)])
    #
    # father_full_name = StringField('Father\'s Full Name', validators=[Length(max=255)])
    # father_educ_attainment = StringField('Father\'s Educational Attainment', validators=[Length(max=255)])
    # father_addr_text = HiddenField('Father Address Text', validators=[DataRequired()])
    # father_brgy_text = HiddenField('Father Barangay Text', validators=[DataRequired()])
    # father_cont_no = IntegerField('Father\'s Contact Number', validators=[DataRequired(), contact_num_length])
    # father_place_work_or_company_name = StringField('Father\'s Place of Work or Company Name',
    #                                                 validators=[Length(max=255)])
    # father_occupation = StringField('Father\'s Occupation', validators=[Length(max=255)])
    #
    # guardian_full_name = StringField('Guardian\'s Full Name', validators=[Length(max=255)])
    # guardian_educ_attainment = StringField('Guardian\'s Educational Attainment', validators=[Length(max=255)])
    # guardian_addr_text = HiddenField('Guardian\'s Address Text', validators=[DataRequired()])
    # guardian_brgy_text = HiddenField('Guardian\'s Barangay Text', validators=[DataRequired()])
    # guardian_cont_no = IntegerField('Guardian\'s Contact Number',
    #                                 validators=[DataRequired(), contact_num_length])
    # guardian_place_work_or_company_name = StringField('Guardian\'s Place of Work or Company Name',
    #                                                   validators=[Length(max=255)])
    # guardian_occupation = StringField('Guardian\'s Occupation', validators=[Length(max=255)])
    #
    # # Educational Background
    # elem_school_name = StringField('Elementary School Name', validators=[DataRequired(), Length(max=255)])
    # elem_school_addr_text = HiddenField('Elementary School Address Text', validators=[DataRequired()])
    # elem_year_grad = IntegerField('Elementary Year Graduated',
    #                               validators=[DataRequired(), NumberRange(min=1900, max=current_year)])
    #
    # junior_hs_school_name = StringField('Junior High School Name', validators=[Length(max=255)])
    # junior_hs_school_addr_text = HiddenField('Junior High School Address Text', validators=[DataRequired()])
    # junior_hs_year_grad = IntegerField('Junior High Year Graduated',
    #                                    validators=[NumberRange(min=1900, max=current_year)])
    #
    # senior_hs_school_name = StringField('Senior High School Name', validators=[DataRequired(), Length(max=255)])
    # senior_hs_school_addr_text = HiddenField('Senior High School Address Text', validators=[DataRequired()])
    # senior_hs_year_grad = IntegerField('Senior High Year Graduated',
    #                                    validators=[NumberRange(min=1900, max=current_year)])
    # senior_strand = StringField('Senior High School Track/Strand', validators=[DataRequired(), Length(max=255)])
    #
    # tertiary_school_name = StringField('Tertiary School Name', validators=[Length(max=255)])
    # tertiary_school_addr_text = HiddenField('Tertiary School Address Text', validators=[Length(max=255)])
    # tertiary_year_grad = IntegerField('Tertiary Year Graduated', validators=[NumberRange(min=1900, max=current_year)])
    # tertiary_course = StringField('Tertiary School Course', validators=[Length(max=255)])

    # Student
    student_number = StringField('School ID', validators=[DataRequired(), Length(max=100)])
    # password = PasswordField('Password', validators=[
    #     OptionalPasswordIfAbsent(message='Password is required if none exists.'),
    #     EqualTo('password_2', message='Passwords must match!'),
    # ])
    # password_2 = PasswordField('Confirm Password', validators=[Optional(), strong_password])

    # Course and Year
    course_id = SelectField('Course', coerce=coerce_int_or_none, validators=[DataRequired()])
    section_id = SelectField('Section', coerce=coerce_int_or_none, validators=[DataRequired()])
    year_level_id = SelectField('Year Level', coerce=coerce_int_or_none, validators=[DataRequired()])
    semester_id = SelectField('Semester', coerce=coerce_int_or_none, validators=[DataRequired()])

    same_as_home = SelectField(
        'Same as Home Address?',
        choices=[('yes', 'Yes'), ('no', 'No')],
        default='yes'
    )

    submit = SubmitField('Submit')

    def __init__(self, *args, **kwargs):
        super(EditStudentForm, self).__init__(*args, **kwargs)
        self.course_id.choices = [(0, 'Please select a course')] + [(c.id, c.course_name) for c in Course.query.all()]
        self.section_id.choices = [(0, 'Please select a section')] + [(s.id, s.section_name) for s in
                                                                      Section.query.all()]
        self.year_level_id.choices = [(0, 'Please select a year level')] + [(yl.id, yl.display_name) for yl in
                                                                            YearLevel.query.all()]
        self.semester_id.choices = [(0, 'Please select a semester')] + [(s.id, s.display_name) for s in
                                                                        Semester.query.all()]
        # if current_user.student_details.password_hash:
        #     self.password.flags.hidden = True  # Hide the password field if password_hash exists
        # else:
        #     self.password.flags.hidden = False  # Show the password field if no password_hash

    def validate_course_id(self, field):
        if field.data == 0:
            raise ValidationError('Please select a valid course.')

    def validate_section_id(self, field):
        if field.data == 0:
            raise ValidationError('Please select a valid section.')

    def validate_year_level_id(self, field):
        if field.data == 0:
            raise ValidationError('Please select a valid year level.')

    def validate_semester_id(self, field):
        if field.data == 0:
            raise ValidationError('Please select a valid semester.')

        # Custom validator for email domain

    def validate_email(self, field):
        if not field.data.endswith('@my.cspc.edu.ph'):
            raise ValidationError('Email must be an @my.cspc.edu.ph address.')


class AssignBackSubjectForm(FlaskForm):
    student_id = SelectField('Student', coerce=int, choices=[(0, 'Please select...')])
    faculty_id = SelectField('Faculty', coerce=int, choices=[(0, 'Please select...')])
    schedule_id = SelectField('Subject Schedule', coerce=str, choices=[])  # The dynamically loaded field
    submit = SubmitField('Assign')

    def validate_student_id(self, field):
        if field.data == 0:
            raise ValidationError('Please select a valid student.')

    def validate_faculty_id(self, field):
        if field.data == 0:
            raise ValidationError('Please select a valid faculty.')

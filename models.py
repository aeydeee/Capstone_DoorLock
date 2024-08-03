import enum
from datetime import datetime, timedelta, date

from sqlalchemy import event, Enum
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

from app import db

# Create an association table for the many-to-many relationship between students and subjects
student_subject_association = db.Table('student_subject',
                                       db.Column('student_id', db.Integer,
                                                 db.ForeignKey('student.id', ondelete='CASCADE'), primary_key=True),
                                       db.Column('subject_id', db.Integer,
                                                 db.ForeignKey('course_subjects.id', ondelete='CASCADE'),
                                                 primary_key=True)
                                       )

faculty_subject_association = db.Table('faculty_subject',
                                       db.Column('faculty_id', db.Integer,
                                                 db.ForeignKey('faculty.id', ondelete='CASCADE'), primary_key=True),
                                       db.Column('subject_id', db.Integer,
                                                 db.ForeignKey('course_subjects.id', ondelete='CASCADE'),
                                                 primary_key=True)
                                       )


class TOTPSecret(db.Model):
    __tablename__ = 'totp_secret'
    id = db.Column(db.Integer, primary_key=True)
    secret_key = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    user = db.relationship('User', back_populates='totp_secret')


class Course(db.Model):
    __tablename__ = 'course'
    id = db.Column(db.Integer, primary_key=True)
    course_name = db.Column(db.String(255), nullable=False, unique=True)
    course_code = db.Column(db.String(255), nullable=False, unique=True)
    students = db.relationship('Student', back_populates='course')


class YearLevelEnum(enum.Enum):
    FIRST_YEAR = (1, 'First Year')
    SECOND_YEAR = (2, 'Second Year')
    THIRD_YEAR = (3, 'Third Year')
    FOURTH_YEAR = (4, 'Fourth Year')

    @classmethod
    def choices(cls):
        return [(choice.name, choice.value[1]) for choice in cls]

    @classmethod
    def code(cls, name):
        return cls[name].value[0]


class YearLevel(db.Model):
    __tablename__ = 'year_level'
    id = db.Column(db.Integer, primary_key=True)
    level_name = db.Column(db.Enum(YearLevelEnum), nullable=False, unique=True)
    level_code = db.Column(db.Integer, nullable=False, unique=True)
    students = db.relationship('Student', back_populates='year_level')

    @property
    def display_name(self):
        return self.level_name.value[1]

    @property
    def code(self):
        return self.level_name.value[0]


class SemesterEnum(enum.Enum):
    FIRST_SEMESTER = (1, 'First Semester')
    SECOND_SEMESTER = (2, 'Second Semester')
    SUMMER_TERM = (3, 'Summer Term')

    @classmethod
    def choices(cls):
        return [(choice.name, choice.value[1]) for choice in cls]

    @classmethod
    def code(cls, name):
        return cls[name].value[0]


class Semester(db.Model):
    __tablename__ = 'semester'
    id = db.Column(db.Integer, primary_key=True)
    semester_name = db.Column(db.Enum(SemesterEnum), nullable=False, unique=True)
    semester_code = db.Column(db.Integer, nullable=False, unique=True)
    students = db.relationship('Student', back_populates='semester')

    @property
    def display_name(self):
        return self.semester_name.value[1]

    @property
    def code(self):
        return self.semester_name.value[0]


class Section(db.Model):
    __tablename__ = 'section'
    id = db.Column(db.Integer, primary_key=True)
    section_name = db.Column(db.String(255), nullable=False, unique=True)
    students = db.relationship('Student', back_populates='section')
    schedules = db.relationship('Schedule', back_populates='section', cascade="all, delete-orphan")


class Subject(db.Model):
    __tablename__ = 'course_subjects'
    id = db.Column(db.Integer, primary_key=True)
    subject_code = db.Column(db.String(255), nullable=False, unique=True)
    subject_name = db.Column(db.String(255), nullable=False)
    subject_units = db.Column(db.String(255), nullable=False)

    # Define the many-to-many relationship to faculties
    faculties = db.relationship('Faculty', secondary=faculty_subject_association, back_populates='subjects')

    # Define the relationship to schedules and students
    schedule_details = db.relationship('Schedule', back_populates='subject', cascade="all, delete-orphan")
    students = db.relationship('Student', secondary=student_subject_association, back_populates='subjects')


class CourseYearLevelSemesterSubject(db.Model):
    __tablename__ = 'course_year_level_semester_subject'
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id', ondelete='CASCADE'), nullable=False)
    year_level_id = db.Column(db.Integer, db.ForeignKey('year_level.id', ondelete='CASCADE'), nullable=False)
    semester_id = db.Column(db.Integer, db.ForeignKey('semester.id', ondelete='CASCADE'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('course_subjects.id', ondelete='CASCADE'), nullable=False)

    course = db.relationship('Course', backref='course_year_level_semester_subjects')
    year_level = db.relationship('YearLevel', backref='course_year_level_semester_subjects')
    semester = db.relationship('Semester', backref='course_year_level_semester_subjects')
    subject = db.relationship('Subject', backref='course_year_level_semester_subjects')

    __table_args__ = (
        db.UniqueConstraint('course_id', 'year_level_id', 'semester_id', 'subject_id',
                            name='_course_year_semester_subject_uc'),
    )


class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    rfid_uid = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(255), nullable=False)
    f_name = db.Column(db.String(100), nullable=False)
    l_name = db.Column(db.String(100), nullable=False)
    m_name = db.Column(db.String(100), nullable=False)
    m_initial = db.Column(db.String(5), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    date_of_birth = db.Column(db.Date, nullable=False)
    place_of_birth = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum('student', 'faculty', 'admin'), nullable=False)
    gender = db.Column(db.Enum('male', 'female'), nullable=False)
    civil_status = db.Column(db.String(15), nullable=False)
    nationality = db.Column(db.String(50), nullable=False)
    citizenship = db.Column(db.String(50), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    profile_pic = db.Column(db.String(255))
    religion = db.Column(db.String(255), nullable=False)
    dialect = db.Column(db.String(255), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.now)

    # Define relationships with string references
    contact_info = db.relationship('ContactInfo', backref='user', uselist=False, cascade="all, delete-orphan")
    student_details = db.relationship('Student', backref='user', uselist=False, cascade="all, delete-orphan")
    faculty_details = db.relationship('Faculty', backref='user', uselist=False, cascade="all, delete-orphan")
    admin_details = db.relationship('Admin', backref='user', uselist=False, cascade="all, delete-orphan")
    family_background = db.relationship('FamilyBackground', backref='user', uselist=False, cascade="all, delete-orphan")
    educational_background = db.relationship('EducationalBackground', backref='user', uselist=False,
                                             cascade="all, delete-orphan")
    totp_secret = db.relationship('TOTPSecret', back_populates='user', uselist=False, cascade="all, delete-orphan")


class ContactInfo(db.Model):
    __tablename__ = 'contact_information'
    id = db.Column(db.Integer, primary_key=True)
    contact_number = db.Column(db.String(255), nullable=False)
    h_city = db.Column(db.String(255), nullable=False)
    h_barangay = db.Column(db.String(255), nullable=False)
    h_house_no = db.Column(db.Integer, nullable=False)
    h_street = db.Column(db.String(255), nullable=False)
    curr_city = db.Column(db.String(255))
    curr_barangay = db.Column(db.String(255))
    curr_house_no = db.Column(db.Integer)
    curr_street = db.Column(db.String(255))

    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)


class FamilyBackground(db.Model):
    __tablename__ = 'user_family_background'
    id = db.Column(db.Integer, primary_key=True)
    mother_full_name = db.Column(db.String(255), nullable=False)
    mother_educ_attainment = db.Column(db.String(255))
    mother_addr = db.Column(db.String(255))
    mother_brgy = db.Column(db.String(255))
    mother_cont_no = db.Column(db.String(255))
    mother_place_work_or_company_name = db.Column(db.String(255))
    mother_occupation = db.Column(db.String(255))

    father_full_name = db.Column(db.String(255))
    father_educ_attainment = db.Column(db.String(255))
    father_addr = db.Column(db.String(255))
    father_brgy = db.Column(db.String(255))
    father_cont_no = db.Column(db.String(255))
    father_place_work_or_company_name = db.Column(db.String(255))
    father_occupation = db.Column(db.String(255))

    guardian_full_name = db.Column(db.String(255))
    guardian_educ_attainment = db.Column(db.String(255))
    guardian_addr = db.Column(db.String(255))
    guardian_brgy = db.Column(db.String(255))
    guardian_cont_no = db.Column(db.String(255))
    guardian_place_work_or_company_name = db.Column(db.String(255))
    guardian_occupation = db.Column(db.String(255))

    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)


class EducationalBackground(db.Model):
    __tablename__ = 'user_educational_background'
    id = db.Column(db.Integer, primary_key=True)
    elem_school = db.Column(db.String(255), nullable=False)
    elem_address = db.Column(db.String(255), nullable=False)
    elem_graduated = db.Column(db.Integer, nullable=False)

    junior_school = db.Column(db.String(255))
    junior_address = db.Column(db.String(255))
    junior_graduated = db.Column(db.Integer)

    senior_school = db.Column(db.String(255), nullable=False)
    senior_address = db.Column(db.String(255), nullable=False)
    senior_graduated = db.Column(db.Integer, nullable=False)
    senior_track_strand = db.Column(db.String(255), nullable=False)

    tertiary_school = db.Column(db.String(255), nullable=False)
    tertiary_address = db.Column(db.String(255), nullable=False)
    tertiary_graduated = db.Column(db.String(255), nullable=False)
    tertiary_course = db.Column(db.String(255), nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)


class Student(db.Model):
    __tablename__ = 'student'
    id = db.Column(db.Integer, primary_key=True)
    student_number = db.Column(db.String(255), unique=True, nullable=False)
    year_level_id = db.Column(db.Integer, db.ForeignKey('year_level.id', ondelete='CASCADE'), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('section.id', ondelete='CASCADE'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id', ondelete='CASCADE'), nullable=False)
    semester_id = db.Column(db.Integer, db.ForeignKey('semester.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)

    year_level = db.relationship('YearLevel', back_populates='students')
    section = db.relationship('Section', back_populates='students')
    course = db.relationship('Course', back_populates='students')
    semester = db.relationship('Semester', back_populates='students')
    subjects = db.relationship('Subject', secondary=student_subject_association, back_populates='students')
    attendances = db.relationship('Attendance', back_populates='student', cascade="all, delete-orphan")

    @property
    def full_name(self):
        return f"{self.user.f_name} {self.user.m_name} {self.user.l_name}"

    @property
    def course_section(self):
        return f"{self.course.course_code} {self.year_level.level_code}{self.section.section_name}"


class Admin(db.Model):
    __tablename__ = 'admin'
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.String(100), nullable=False, unique=True)
    admin_department = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(128))

    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)

    @property
    def password(self):
        raise AttributeError('Password is not a readable attribute!')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)


class Faculty(db.Model):
    __tablename__ = 'faculty'
    id = db.Column(db.Integer, primary_key=True)
    faculty_number = db.Column(db.String(100), nullable=False, unique=True)
    designation = db.Column(db.String(255), nullable=False)
    faculty_department = db.Column(db.String(255), nullable=False)
    password_hash = db.Column(db.String(128))

    # Define the many-to-many relationship to subjects
    subjects = db.relationship('Subject', secondary=faculty_subject_association, back_populates='faculties')

    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)

    @property
    def password(self):
        raise AttributeError('Password is not a readable attribute!')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def full_name(self):
        return f"{self.user.f_name} {self.user.m_name} {self.user.l_name}"


class DayOfWeek(enum.Enum):
    SUNDAY = "Sunday"
    MONDAY = "Monday"
    TUESDAY = "Tuesday"
    WEDNESDAY = "Wednesday"
    THURSDAY = "Thursday"
    FRIDAY = "Friday"
    SATURDAY = "Saturday"


class Schedule(db.Model):
    __tablename__ = 'schedule'
    id = db.Column(db.Integer, primary_key=True)
    day = db.Column(Enum(DayOfWeek), nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)

    subject_id = db.Column(db.Integer, db.ForeignKey('course_subjects.id', ondelete='CASCADE'), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('section.id', ondelete='CASCADE'), nullable=False)

    subject = db.relationship('Subject', back_populates='schedule_details')
    section = db.relationship('Section', back_populates='schedules')

    __table_args__ = (
        db.UniqueConstraint('day', 'start_time', 'end_time', 'subject_id', 'section_id',
                            name='_schedule_unique_constraint'),
    )


class FacultySubjectSchedule(db.Model):
    __tablename__ = 'faculty_subject_schedule'
    id = db.Column(db.Integer, primary_key=True)
    faculty_id = db.Column(db.Integer, db.ForeignKey('faculty.id', ondelete='CASCADE'), nullable=False)
    schedule_id = db.Column(db.Integer, db.ForeignKey('schedule.id', ondelete='CASCADE'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('course_subjects.id', ondelete='CASCADE'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id', ondelete='CASCADE'), nullable=False)
    year_level_id = db.Column(db.Integer, db.ForeignKey('year_level.id', ondelete='CASCADE'), nullable=False)
    semester_id = db.Column(db.Integer, db.ForeignKey('semester.id', ondelete='CASCADE'), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('section.id', ondelete='CASCADE'), nullable=False)

    faculty = db.relationship('Faculty', backref='faculty_subject_schedules')
    schedule = db.relationship('Schedule', backref='faculty_subject_schedules')
    subject = db.relationship('Subject', backref='faculty_subject_schedules')
    course = db.relationship('Course', backref='faculty_subject_schedules')
    year_level = db.relationship('YearLevel', backref='faculty_subject_schedules')
    semester = db.relationship('Semester', backref='faculty_subject_schedules')
    section = db.relationship('Section', backref='faculty_subject_schedules')

    __table_args__ = (
        db.UniqueConstraint('faculty_id', 'schedule_id', 'subject_id', 'course_id', 'year_level_id', 'semester_id',
                            'section_id', name='_faculty_schedule_subject_course_year_semester_section_uc'),
    )


class Attendance(db.Model):
    __tablename__ = 'attendance'
    id = db.Column(db.Integer, primary_key=True)
    time_in = db.Column(db.DateTime, nullable=False)
    time_out = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.Enum('present', 'absent', 'late'), nullable=False)

    student_id = db.Column(db.Integer, db.ForeignKey('student.id', ondelete='CASCADE'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('course_subjects.id', ondelete='CASCADE'))

    student = db.relationship('Student', back_populates='attendances')
    subject = db.relationship('Subject', backref='attendances')

    def check_lateness(self):
        current_day = self.time_in.strftime('%A').lower()
        schedule = Schedule.query.filter_by(subject_id=self.subject_id, schedule_day=current_day).first()

        if schedule:
            scheduled_start_time = datetime.combine(self.time_in.date(), schedule.schedule_time_from)
            if self.time_in > (scheduled_start_time + timedelta(minutes=15)):
                self.status = 'late'
            else:
                self.status = 'present'
        else:
            self.status = 'absent'

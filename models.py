import base64
import enum
import os

import onetimepass

from datetime import datetime, timedelta, date

import pytz
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin
from sqlalchemy import Enum
from flask_login import UserMixin

from app import db

# Set timezone to Asia/Manila (Philippine Timezone)
timezone = pytz.timezone('Asia/Manila')

# Create an association table for the many-to-many relationship between students and subjects
student_subject_association = db.Table('student_subject_association',
                                       db.Column('student_id', db.Integer, db.ForeignKey('student.id')),
                                       db.Column('subject_id', db.Integer, db.ForeignKey('course_subjects.id')),
                                       db.Column('schedule_id', db.Integer, db.ForeignKey('schedule.id')),
                                       # Add schedule_id
                                       db.PrimaryKeyConstraint('student_id', 'subject_id', 'schedule_id')
                                       # Make sure it's part of the primary key
                                       )

faculty_subject_association = db.Table('faculty_subject',
                                       db.Column('faculty_id', db.Integer,
                                                 db.ForeignKey('faculty.id', ondelete='CASCADE'), primary_key=True),
                                       db.Column('subject_id', db.Integer,
                                                 db.ForeignKey('course_subjects.id', ondelete='CASCADE'),
                                                 primary_key=True)
                                       )


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


class SectionEnum(enum.Enum):
    A = (1, 'A')
    B = (2, 'B')
    C = (3, 'C')
    D = (4, 'D')
    E = (5, 'E')
    F = (6, 'F')
    G = (7, 'G')
    H = (8, 'H')
    I = (9, 'I')
    J = (10, 'J')
    K = (11, 'K')
    L = (12, 'L')
    M = (13, 'M')

    @classmethod
    def choices(cls):
        return [(choice.name, choice.value[1]) for choice in cls]

    @classmethod
    def code(cls, name):
        return cls[name].value[0]


class Section(db.Model):
    __tablename__ = 'section'
    id = db.Column(db.Integer, primary_key=True)
    section_name = db.Column(db.Enum(SectionEnum), nullable=False, unique=True)
    section_code = db.Column(db.Integer, nullable=False, unique=True)
    students = db.relationship('Student', back_populates='section')
    schedules = db.relationship('Schedule', back_populates='section', cascade="all, delete-orphan")

    @property
    def display_name(self):
        return self.section_name.value[1]

    @property
    def code(self):
        return self.section_name.value[0]


class Subject(db.Model):
    __tablename__ = 'course_subjects'
    id = db.Column(db.Integer, primary_key=True)
    subject_name = db.Column(db.String(255), nullable=False)
    subject_code = db.Column(db.String(255), nullable=False, unique=True)
    subject_units = db.Column(db.String(255), nullable=False)

    faculties = db.relationship('Faculty', secondary=faculty_subject_association, back_populates='subjects')
    schedule_details = db.relationship('Schedule', back_populates='subject', cascade="all, delete-orphan")
    students = db.relationship('Student', secondary=student_subject_association, back_populates='subjects')

    # Add overlaps parameter to resolve the conflict
    course_year_level_semester_subjects = db.relationship('CourseYearLevelSemesterSubject', backref='course_subject',
                                                          cascade='all, delete-orphan',
                                                          overlaps="course_subject, course_year_level_subjects")


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

    # Add back_populates to link the subject and course_year_level_semester_subjects relationships
    subject = db.relationship('Subject', back_populates='course_year_level_semester_subjects',
                              overlaps="course_subject,course_year_level_semester_subjects")

    __table_args__ = (
        db.UniqueConstraint('course_id', 'year_level_id', 'semester_id', 'subject_id',
                            name='_course_year_semester_subject_uc'),
    )


class TOTPSecret(db.Model):
    __tablename__ = 'totp_secret'
    id = db.Column(db.Integer, primary_key=True)
    secret_key = db.Column(db.String(16), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    user = db.relationship('User', back_populates='totp_secret')


class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    rfid_uid = db.Column(db.String(100), unique=True, nullable=True)
    # username = db.Column(db.String(255), nullable=False, unique=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    role = db.Column(db.Enum('student', 'faculty', 'admin'), nullable=False)
    f_name = db.Column(db.String(100))
    m_name = db.Column(db.String(100))
    l_name = db.Column(db.String(100))
    gender = db.Column(db.Enum('male', 'female'))
    profile_pic = db.Column(db.String(255))
    date_created = db.Column(db.DateTime, default=lambda: datetime.now(timezone))
    totp_verified = db.Column(db.Boolean, default=False)
    totp_reset_token = db.Column(db.String(255), nullable=True)
    totp_token_used = db.Column(db.Boolean, default=False)

    # Define relationships with string references
    student_details = db.relationship('Student', backref='user', uselist=False, cascade="all, delete-orphan")
    faculty_details = db.relationship('Faculty', backref='user', uselist=False, cascade="all, delete-orphan")
    admin_details = db.relationship('Admin', backref='user', uselist=False, cascade="all, delete-orphan")
    report_log = db.relationship('ReportLog', backref='user', cascade="all, delete-orphan")
    totp_secret = db.relationship('TOTPSecret', back_populates='user', uselist=False, cascade="all, delete-orphan")

    # Establish a one-to-many relationship with OAuth
    oauth = db.relationship('OAuth', back_populates='user', cascade='all, delete-orphan', passive_deletes=True)

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.totp_secret is None:
            # Generate a random 10-byte secret
            random_bytes = os.urandom(10)

            # Convert to base32 for Google Authenticator
            secret_base32 = base64.b32encode(random_bytes).decode('utf-8')

            # Create TOTPSecret with both base32 and hex secrets
            self.totp_secret = TOTPSecret(secret_key=secret_base32)
            db.session.add(self.totp_secret)

    def get_totp_uri(self):
        if self.totp_secret is None:
            raise ValueError("TOTP secret is not initialized")
        return 'otpauth://totp/{0}?secret={1}&issuer=CSPC-TechNinjas' \
            .format(self.email, self.totp_secret.secret_key)

    def verify_totp(self, token):
        if self.totp_secret is None:
            return False
        return onetimepass.valid_totp(token, self.totp_secret.secret_key)


class OAuth(OAuthConsumerMixin, db.Model):
    provider_user_id = db.Column(db.String(256), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id, ondelete='CASCADE'), nullable=False)
    user = db.relationship(User, back_populates='oauth')


class Student(db.Model):
    __tablename__ = 'student'
    id = db.Column(db.Integer, primary_key=True)
    student_number = db.Column(db.String(255), nullable=False)
    year_level_id = db.Column(db.Integer, db.ForeignKey('year_level.id', ondelete='CASCADE'))
    section_id = db.Column(db.Integer, db.ForeignKey('section.id', ondelete='CASCADE'))
    course_id = db.Column(db.Integer, db.ForeignKey('course.id', ondelete='CASCADE'))
    semester_id = db.Column(db.Integer, db.ForeignKey('semester.id', ondelete='CASCADE'))
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
        return f"{self.course.course_code} {self.year_level.level_code}{self.section.display_name}"


class Admin(db.Model):
    __tablename__ = 'admin'
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.String(100), nullable=False, unique=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)

    @property
    def full_name(self):
        return f"{self.user.f_name} {self.user.m_name} {self.user.l_name}"


class Faculty(db.Model):
    __tablename__ = 'faculty'
    id = db.Column(db.Integer, primary_key=True)
    faculty_number = db.Column(db.String(100), nullable=False)
    designation = db.Column(db.String(255))
    faculty_department = db.Column(db.String(255))
    # password_hash = db.Column(db.String(128))

    # Define the many-to-many relationship to subjects
    subjects = db.relationship('Subject', secondary=faculty_subject_association, back_populates='faculties')

    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)

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
    status = db.Column(db.Enum('present', 'absent', 'late'))

    # Student details
    student_id = db.Column(db.Integer, db.ForeignKey('student.id', ondelete='SET NULL'), nullable=True)
    student_number = db.Column(db.String(255), nullable=True)
    student_name = db.Column(db.String(255), nullable=False)
    course_code = db.Column(db.String(100), nullable=False)
    level_code = db.Column(db.String(100), nullable=False)
    section = db.Column(db.String(100), nullable=False)
    semester = db.Column(db.String(100), nullable=False)

    # Subject details
    subject_id = db.Column(db.Integer, db.ForeignKey('course_subjects.id', ondelete='SET NULL'), nullable=True)
    subject_name = db.Column(db.String(255), nullable=False)

    # Faculty details
    faculty_id = db.Column(db.Integer, db.ForeignKey('faculty.id', ondelete='SET NULL'), nullable=True)
    faculty_name = db.Column(db.String(255), nullable=False)

    # Relationships
    student = db.relationship('Student', back_populates='attendances', passive_deletes=True)
    subject = db.relationship('Subject', backref='attendances', passive_deletes=True)
    faculty = db.relationship('Faculty', backref='attendances', passive_deletes=True)

    def __init__(self, time_in, student_id, subject_id, **kwargs):
        super().__init__(time_in=time_in, student_id=student_id, subject_id=subject_id, **kwargs)
        self.status = self.check_lateness()

    def check_lateness(self):
        # Define your desired timezone
        tz = pytz.timezone('Asia/Manila')  # Example timezone

        current_day = self.time_in.strftime('%A').lower()
        schedule = Schedule.query.filter_by(subject_id=self.subject_id, day=current_day).first()

        if schedule:
            scheduled_start_time = datetime.combine(self.time_in.date(), schedule.start_time).astimezone(tz)
            scheduled_end_time = datetime.combine(self.time_in.date(), schedule.end_time).astimezone(tz)
            time_in_aware = self.time_in.astimezone(tz)

            if time_in_aware > scheduled_end_time:
                return 'late'
            elif time_in_aware > (scheduled_start_time + timedelta(minutes=15)):
                return 'late'
            else:
                return 'present'
        else:
            return 'late'


class ReportLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(50))  # 'in' or 'out'
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone))
    time_out = db.Column(db.DateTime, nullable=True)  # Only for 'out' actions
    status = db.Column(db.String(50))  # 'accepted' or 'denied'

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)


def delete_null_status_logs(app):
    with app.app_context():
        threshold_time = datetime.now(timezone) - timedelta(seconds=20)
        logs_to_delete = ReportLog.query.filter(ReportLog.status.is_(None), ReportLog.timestamp < threshold_time).all()

        for log in logs_to_delete:
            db.session.delete(log)

        db.session.commit()


class FacultySession(db.Model):
    __tablename__ = 'faculty_sessions'
    id = db.Column(db.Integer, primary_key=True)
    authenticated_time = db.Column(db.DateTime, default=lambda: datetime.now(timezone))
    active = db.Column(db.Boolean, default=True, nullable=False)

    faculty_id = db.Column(db.Integer, db.ForeignKey('faculty.id'), nullable=False)
    schedule_id = db.Column(db.Integer, db.ForeignKey('schedule.id', ondelete='CASCADE'))
    subject_id = db.Column(db.Integer, db.ForeignKey('course_subjects.id'), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('section.id'), nullable=False)

    def deactivate(self):
        self.active = False
        db.session.commit()


def delete_old_faculty_sessions(app):
    with app.app_context():
        one_week_ago = datetime.now(timezone) - timedelta(weeks=1)
        old_sessions = FacultySession.query.filter(FacultySession.authenticated_time < one_week_ago).all()

        for session in old_sessions:
            db.session.delete(session)

        db.session.commit()

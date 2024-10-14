import base64
import enum
import os

import onetimepass

from datetime import datetime, timedelta, date

import pytz
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin
from sqlalchemy import Enum, and_
from flask_login import UserMixin
from sqlalchemy.orm import joinedload

from app import db

# Set timezone to Asia/Manila (Philippine Timezone)
timezone = pytz.timezone('Asia/Manila')

# Create an association table for the many-to-many relationship between students and courses
student_course_association = db.Table('student_course_association',
                                      db.Column('student_id', db.Integer, db.ForeignKey('student.id')),
                                      db.Column('course_id', db.Integer, db.ForeignKey('program_courses.id')),
                                      db.Column('schedule_id', db.Integer, db.ForeignKey('schedule.id')),
                                      # Add schedule_id
                                      db.PrimaryKeyConstraint('student_id', 'course_id', 'schedule_id')
                                      # Make sure it's part of the primary key
                                      )

faculty_course_association = db.Table('faculty_course',
                                      db.Column('faculty_id', db.Integer,
                                                db.ForeignKey('faculty.id', ondelete='CASCADE'), primary_key=True),
                                      db.Column('course_id', db.Integer,
                                                db.ForeignKey('program_courses.id', ondelete='CASCADE'),
                                                primary_key=True)
                                      )


class EnrollmentHistory(db.Model):
    __tablename__ = 'enrollment_history'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id', ondelete='CASCADE'), nullable=False)
    school_year_id = db.Column(db.Integer, db.ForeignKey('school_year.id', ondelete='CASCADE'), nullable=False)
    program_id = db.Column(db.Integer, db.ForeignKey('program.id', ondelete='CASCADE'), nullable=False)
    year_level_id = db.Column(db.Integer, db.ForeignKey('year_level.id', ondelete='CASCADE'), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('section.id', ondelete='CASCADE'), nullable=False)
    semester_id = db.Column(db.Integer, db.ForeignKey('semester.id', ondelete='CASCADE'), nullable=False)
    enrollment_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone), nullable=False)

    # Store snapshots of student details
    student_number = db.Column(db.String(255), nullable=False)
    program_code = db.Column(db.String(255), nullable=False)
    year_level_code = db.Column(db.Integer, nullable=False)
    section_code = db.Column(db.Integer, nullable=False)

    @property
    def full_name(self):
        # Assuming you can access the student model if needed
        student = Student.query.get(self.student_id)
        return f"{student.user.f_name} {student.user.m_name} {student.user.l_name}"

    @property
    def program_section(self):
        return f"{self.program.program_code} {self.year_level.level_code}{self.section.display_name}"


class SchoolYear(db.Model):
    __tablename__ = 'school_year'
    id = db.Column(db.Integer, primary_key=True)
    year_label = db.Column(db.String(9), nullable=False, unique=True)  # e.g., "2023-2024"

    students = db.relationship('Student', back_populates='school_year', cascade="all, delete-orphan")


class Program(db.Model):
    __tablename__ = 'program'
    id = db.Column(db.Integer, primary_key=True)
    program_name = db.Column(db.String(255), nullable=False, unique=True)
    program_code = db.Column(db.String(255), nullable=False, unique=True)
    students = db.relationship('Student', back_populates='program')


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


class Course(db.Model):
    __tablename__ = 'program_courses'
    id = db.Column(db.Integer, primary_key=True)
    course_name = db.Column(db.String(255), nullable=False)
    course_code = db.Column(db.String(255), nullable=False, unique=True)
    course_units = db.Column(db.String(255), nullable=False)

    faculties = db.relationship('Faculty', secondary=faculty_course_association, back_populates='courses')
    schedule_details = db.relationship('Schedule', back_populates='course', cascade="all, delete-orphan")
    students = db.relationship('Student', secondary=student_course_association, back_populates='courses')

    # Add overlaps parameter to resolve the conflict
    program_year_level_semester_courses = db.relationship('ProgramYearLevelSemesterCourse', backref='program_course',
                                                          cascade='all, delete-orphan',
                                                          overlaps="program_course, program_year_level_courses")


class ProgramYearLevelSemesterCourse(db.Model):
    __tablename__ = 'program_year_level_semester_course'
    id = db.Column(db.Integer, primary_key=True)
    program_id = db.Column(db.Integer, db.ForeignKey('program.id', ondelete='CASCADE'), nullable=False)
    year_level_id = db.Column(db.Integer, db.ForeignKey('year_level.id', ondelete='CASCADE'), nullable=False)
    semester_id = db.Column(db.Integer, db.ForeignKey('semester.id', ondelete='CASCADE'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('program_courses.id', ondelete='CASCADE'), nullable=False)

    program = db.relationship('Program', backref='program_year_level_semester_courses')
    year_level = db.relationship('YearLevel', backref='program_year_level_semester_courses')
    semester = db.relationship('Semester', backref='program_year_level_semester_courses')

    # Add back_populates to link the course and program_year_level_semester_courses relationships
    course = db.relationship('Course', back_populates='program_year_level_semester_courses',
                             overlaps="program_course,program_year_level_semester_courses")

    __table_args__ = (
        db.UniqueConstraint('program_id', 'year_level_id', 'semester_id', 'course_id',
                            name='_program_year_semester_course_uc'),
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
    program_id = db.Column(db.Integer, db.ForeignKey('program.id', ondelete='CASCADE'))
    semester_id = db.Column(db.Integer, db.ForeignKey('semester.id', ondelete='CASCADE'))
    school_year_id = db.Column(db.Integer, db.ForeignKey('school_year.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)

    school_year = db.relationship('SchoolYear', back_populates='students')
    year_level = db.relationship('YearLevel', back_populates='students')
    section = db.relationship('Section', back_populates='students')
    program = db.relationship('Program', back_populates='students')
    semester = db.relationship('Semester', back_populates='students')
    courses = db.relationship('Course', secondary=student_course_association, back_populates='students')
    attendances = db.relationship('Attendance', back_populates='student', cascade="all, delete-orphan")

    @property
    def full_name(self):
        return f"{self.user.f_name} {self.user.m_name} {self.user.l_name}"

    @property
    def program_section(self):
        return f"{self.program.program_code} {self.year_level.level_code}{self.section.display_name}"


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

    # Define the many-to-many relationship to courses
    courses = db.relationship('Course', secondary=faculty_course_association, back_populates='faculties')

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

    course_id = db.Column(db.Integer, db.ForeignKey('program_courses.id', ondelete='CASCADE'), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('section.id', ondelete='CASCADE'), nullable=False)

    course = db.relationship('Course', back_populates='schedule_details')
    section = db.relationship('Section', back_populates='schedules')

    __table_args__ = (
        db.UniqueConstraint('day', 'start_time', 'end_time', 'course_id', 'section_id',
                            name='_schedule_unique_constraint'),
    )


class FacultyCourseSchedule(db.Model):
    __tablename__ = 'faculty_course_schedule'
    id = db.Column(db.Integer, primary_key=True)
    faculty_id = db.Column(db.Integer, db.ForeignKey('faculty.id', ondelete='CASCADE'), nullable=False)
    schedule_id = db.Column(db.Integer, db.ForeignKey('schedule.id', ondelete='CASCADE'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('program_courses.id', ondelete='CASCADE'), nullable=False)
    program_id = db.Column(db.Integer, db.ForeignKey('program.id', ondelete='CASCADE'), nullable=False)
    year_level_id = db.Column(db.Integer, db.ForeignKey('year_level.id', ondelete='CASCADE'), nullable=False)
    semester_id = db.Column(db.Integer, db.ForeignKey('semester.id', ondelete='CASCADE'), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('section.id', ondelete='CASCADE'), nullable=False)

    faculty = db.relationship('Faculty', backref='faculty_course_schedules')
    schedule = db.relationship('Schedule', backref='faculty_course_schedules')
    course = db.relationship('Course', backref='faculty_course_schedules')
    program = db.relationship('Program', backref='faculty_course_schedules')
    year_level = db.relationship('YearLevel', backref='faculty_course_schedules')
    semester = db.relationship('Semester', backref='faculty_course_schedules')
    section = db.relationship('Section', backref='faculty_course_schedules')

    __table_args__ = (
        db.UniqueConstraint('faculty_id', 'schedule_id', 'course_id', 'program_id', 'year_level_id', 'semester_id',
                            'section_id', name='_faculty_schedule_course_program_year_semester_section_uc'),
    )


class Attendance(db.Model):
    __tablename__ = 'attendance'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=lambda: datetime.now(timezone), nullable=False)
    time_in = db.Column(db.DateTime, nullable=True)
    time_out = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.Enum('present', 'absent', 'late', 'excuse'))

    # Student details
    student_id = db.Column(db.Integer, db.ForeignKey('student.id', ondelete='SET NULL'), nullable=True)
    student_number = db.Column(db.String(255), nullable=True)
    student_name = db.Column(db.String(255), nullable=False)
    program_code = db.Column(db.String(100), nullable=False)
    level_code = db.Column(db.String(100), nullable=False)
    section = db.Column(db.String(100), nullable=False)
    semester = db.Column(db.String(100), nullable=False)
    school_year = db.Column(db.String(100), nullable=False)

    # Course details
    course_id = db.Column(db.Integer, db.ForeignKey('program_courses.id', ondelete='SET NULL'), nullable=True)
    course_name = db.Column(db.String(255), nullable=False)

    # Attendance details
    schedule_id = db.Column(db.Integer, db.ForeignKey('schedule.id', ondelete='SET NULL'), nullable=True)

    # Faculty details
    faculty_id = db.Column(db.Integer, db.ForeignKey('faculty.id', ondelete='SET NULL'), nullable=True)
    faculty_name = db.Column(db.String(255), nullable=False)

    # Relationships
    student = db.relationship('Student', back_populates='attendances', passive_deletes=True)
    course = db.relationship('Course', backref='attendances', passive_deletes=True)
    faculty = db.relationship('Faculty', backref='attendances', passive_deletes=True)

    def __init__(self, time_in, student_id, course_id, **kwargs):
        super().__init__(time_in=time_in, student_id=student_id, course_id=course_id, **kwargs)

        # Only check lateness if time_in is not None
        if time_in is not None:
            self.status = self.check_lateness()
        else:
            self.status = 'absent'  # Explicitly mark as absent if no time_in

    def check_lateness(self):

        # Only check lateness if time_in is not None
        if self.time_in is None:
            return None

        current_day = self.time_in.strftime('%A').lower()
        schedule = Schedule.query.filter_by(course_id=self.course_id, day=current_day).first()

        if schedule:
            scheduled_start_time = datetime.combine(self.time_in.date(), schedule.start_time).astimezone(timezone)
            scheduled_end_time = datetime.combine(self.time_in.date(), schedule.end_time).astimezone(timezone)
            time_in_aware = self.time_in.astimezone(timezone)

            # Check if the student is late based on schedule and grace period+
            if time_in_aware >= scheduled_end_time:
                return 'absent'
            elif time_in_aware > scheduled_end_time:
                return 'late'
            elif time_in_aware > (scheduled_start_time + timedelta(minutes=15)):  # Example grace period of 15 mins
                return 'late'
        else:
            return 'absent'  # If no schedule exists for the day, treat as absent or handle as appropriate


def record_absent_students(app):
    with app.app_context():
        current_time = datetime.now(timezone)
        current_day = current_time.strftime('%A')

        # Query the latest schedule based on the current day and end_time
        latest_schedule = Schedule.query.filter(
            Schedule.day == current_day.upper(),
            Schedule.end_time <= current_time.timetz()
        ).order_by(Schedule.end_time.desc()).first()

        if latest_schedule:
            # Get all faculty-course schedules related to this latest schedule
            faculty_course_schedules = FacultyCourseSchedule.query.filter_by(schedule_id=latest_schedule.id).all()

            for faculty_course_schedule in faculty_course_schedules:
                faculty_id = faculty_course_schedule.faculty_id
                course_id = faculty_course_schedule.course_id
                section_id = faculty_course_schedule.section_id
                semester_id = faculty_course_schedule.semester_id
                schedule_id = faculty_course_schedule.schedule_id

                # print(f'Processing: {faculty_course_schedule}')

                # Query students assigned to this course and schedule with no attendance for this schedule
                students = (
                    Student.query
                    .join(Student.courses)  # Join Student with courses
                    .join(Course.schedule_details)  # Join Course with schedule details
                    .filter(
                        Student.section_id == section_id,  # Filter by section
                        Student.semester_id == semester_id,  # Filter by semester
                        Course.id == course_id,  # Filter by course ID
                        Schedule.id == schedule_id  # Filter by schedule ID
                    )
                    .outerjoin(
                        Attendance,
                        and_(
                            Attendance.course_id == course_id,
                            Attendance.student_id == Student.id,
                            Attendance.schedule_id == schedule_id  # Ensure match with schedule
                        )
                    )
                    .filter(Attendance.id == None)  # Select only students with no attendance
                    .all()
                )

                # print(f'Students with no attendance: {students}')

                # Track if any new attendance records were added
                new_records = False

                # Record absences for students who did not attend
                for student in students:
                    attendance = Attendance(
                        time_in=None,  # No time_in as they did not attend
                        time_out=None,  # No time_out since they didn't attend
                        status='absent',  # Mark as absent
                        student_id=student.id,
                        course_id=course_id,
                        faculty_id=faculty_id,
                        schedule_id=schedule_id,  # Ensure schedule ID is tracked
                        student_number=student.student_number,
                        student_name=student.full_name,
                        course_name=latest_schedule.course.course_name,
                        faculty_name=faculty_course_schedule.faculty.full_name,
                        program_code=student.program.program_code,
                        level_code=student.year_level.level_code,
                        section=student.section.display_name,
                        semester=student.semester.display_name,
                        school_year=student.school_year.year_label
                    )
                    db.session.add(attendance)
                    new_records = True

                # Commit only if new attendance records were added
                if new_records:
                    db.session.commit()
                    # print(f'Attendance recorded for schedule {schedule_id}')


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
    course_id = db.Column(db.Integer, db.ForeignKey('program_courses.id'), nullable=False)
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

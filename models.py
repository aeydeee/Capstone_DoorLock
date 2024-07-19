from datetime import datetime, timedelta

from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

from app import db

# Create an association table for the many-to-many relationship
student_faculty_association = db.Table('student_faculty',
                                       db.Column('student_id', db.Integer,
                                                 db.ForeignKey('student.id', ondelete='CASCADE'), primary_key=True),
                                       db.Column('faculty_id', db.Integer,
                                                 db.ForeignKey('faculty.id', ondelete='CASCADE'), primary_key=True)
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
    student_number = db.Column(db.String(100), nullable=False, unique=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)

    student_course_and_year = db.relationship('StudentCourseAndYear', backref='student', uselist=False,
                                              cascade="all, delete-orphan")

    # Define the relationship to faculties through the association table
    faculties = db.relationship('Faculty', secondary=student_faculty_association, back_populates='students')

    @property
    def full_name(self):
        return f"{self.user.f_name} {self.user.m_name} {self.user.l_name}"

    @property
    def course_section(self):
        return f"{self.student_course_and_year.course_name} {self.student_course_and_year.year_level}{self.student_course_and_year.section}"


class StudentCourseAndYear(db.Model):
    __tablename__ = 'student_course_and_year'
    id = db.Column(db.Integer, primary_key=True)
    course_name = db.Column(db.String(50), nullable=False)
    year_level = db.Column(db.String(50), nullable=False)
    section = db.Column(db.String(50), nullable=False)

    student_id = db.Column(db.Integer, db.ForeignKey('student.id', ondelete='CASCADE'), nullable=False)


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
    faculty_id = db.Column(db.String(100), nullable=False, unique=True)
    designation = db.Column(db.String(255), nullable=False)
    faculty_department = db.Column(db.String(255), nullable=False)
    password_hash = db.Column(db.String(128))

    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)

    subjects_details = db.relationship('Subject', backref='faculty', cascade="all, delete-orphan")

    # Define the relationship to students through the association table
    students = db.relationship('Student', secondary=student_faculty_association, back_populates='faculties')

    @property
    def password(self):
        raise AttributeError('Password is not a readable attribute!')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def full_name(self):
        return f"{self.user.f_name} {self.user.m_name} {self.user.l_name}"


class Subject(db.Model):
    __tablename__ = 'course_subjects'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    code = db.Column(db.String(255), nullable=False)
    units = db.Column(db.Integer)

    schedule_details = db.relationship('Schedule', back_populates='subject_details', cascade="all, delete-orphan")

    faculty_id = db.Column(db.Integer, db.ForeignKey('faculty.id', ondelete='CASCADE'), nullable=False)


class Schedule(db.Model):
    __tablename__ = 'open_lab_schedules'
    id = db.Column(db.Integer, primary_key=True)
    day = db.Column(db.Enum('sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'),
                    nullable=False)
    schedule_from = db.Column(db.Time, nullable=False)
    schedule_to = db.Column(db.Time, nullable=False)

    subject_id = db.Column(db.Integer, db.ForeignKey('course_subjects.id', ondelete='CASCADE'), nullable=False)
    subject_details = db.relationship('Subject', back_populates='schedule_details')


class Attendance(db.Model):
    __tablename__ = 'attendance'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('course_subjects.id', ondelete='CASCADE'), nullable=False)
    time_in = db.Column(db.DateTime, nullable=False)
    time_out = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.Enum('present', 'absent', 'late'), nullable=False)

    user = db.relationship('User', backref='attendances')
    subject = db.relationship('Subject', backref='attendances')

    def check_lateness(self):
        current_day = self.time_in.strftime('%A').lower()
        schedule = Schedule.query.filter_by(subject_id=self.subject_id, day=current_day).first()

        if schedule:
            scheduled_start_time = datetime.combine(self.time_in.date(), schedule.schedule_from)
            if self.time_in > (scheduled_start_time + timedelta(minutes=15)):
                self.status = 'late'
            else:
                self.status = 'present'
        else:
            self.status = 'absent'

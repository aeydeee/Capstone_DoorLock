from sqlalchemy.orm import joinedload


def check_and_create_admin():
    # Delayed import to avoid circular import issues
    from app import db
    from models import User, Admin

    # Check if an admin user exists
    admin_exists = User.query.options(joinedload(User.admin_details)).filter(User.admin_details != None).first()
    print(admin_exists)
    if not admin_exists:
        # Create a new admin user
        admin_user = User(
            email='admin@cspc.edu.ph',
            role='admin',
            f_name='Admin',
            l_name='User',
        )

        # Create the associated Admin details
        admin_details = Admin(
            school_id='ADMIN001',
            user=admin_user,
            # PBKDF2 with SHA256
        )

        # Add to the session and commit
        db.session.add(admin_user)
        db.session.add(admin_details)
        db.session.commit()

        print("Admin user created successfully")
    else:
        print("Admin user already exists")


def check_and_create_enums():
    from app import db
    from models import YearLevelEnum, YearLevel, SemesterEnum, Semester, SectionEnum, Section

    # Check and create YearLevel entries
    for enum_value in YearLevelEnum:
        if not YearLevel.query.filter_by(level_name=enum_value).first():
            year_level = YearLevel(level_name=enum_value, level_code=enum_value.value[0])
            db.session.add(year_level)

    # Check and create Semester entries
    for enum_value in SemesterEnum:
        if not Semester.query.filter_by(semester_name=enum_value).first():
            semester = Semester(semester_name=enum_value, semester_code=enum_value.value[0])
            db.session.add(semester)

    # Check and create Section entries
    for enum_value in SectionEnum:
        if not Section.query.filter_by(section_name=enum_value).first():
            section = Section(section_name=enum_value, section_code=enum_value.value[0])
            db.session.add(section)

    # Commit the changes to the database
    db.session.commit()

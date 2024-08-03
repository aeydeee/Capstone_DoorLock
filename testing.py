from app import db, create_app
from models import Semester, SemesterEnum

# Create an application context
app = create_app()
with app.app_context():
    # Create entries for each semester
    semesters = [
        Semester(semester_name=SemesterEnum.FIRST_SEMESTER, semester_code=SemesterEnum.FIRST_SEMESTER.value[0]),
        Semester(semester_name=SemesterEnum.SECOND_SEMESTER, semester_code=SemesterEnum.SECOND_SEMESTER.value[0]),
        Semester(semester_name=SemesterEnum.SUMMER_TERM, semester_code=SemesterEnum.SUMMER_TERM.value[0])
    ]

    # Add to the session and commit
    db.session.add_all(semesters)
    db.session.commit()

from app import db, create_app
from models import Section, SectionEnum

# Create an application context
app = create_app()
with app.app_context():
    # Create entries for each section
    sections = [
        Section(section_name=SectionEnum.A, section_code=SectionEnum.A.value[0]),
        Section(section_name=SectionEnum.B, section_code=SectionEnum.B.value[0]),
        Section(section_name=SectionEnum.C, section_code=SectionEnum.C.value[0]),
        Section(section_name=SectionEnum.D, section_code=SectionEnum.D.value[0]),
        Section(section_name=SectionEnum.E, section_code=SectionEnum.E.value[0]),
        Section(section_name=SectionEnum.F, section_code=SectionEnum.F.value[0]),
        Section(section_name=SectionEnum.G, section_code=SectionEnum.G.value[0]),
        Section(section_name=SectionEnum.H, section_code=SectionEnum.H.value[0]),
        Section(section_name=SectionEnum.I, section_code=SectionEnum.I.value[0]),
        Section(section_name=SectionEnum.J, section_code=SectionEnum.J.value[0]),
        Section(section_name=SectionEnum.K, section_code=SectionEnum.K.value[0]),
        Section(section_name=SectionEnum.L, section_code=SectionEnum.L.value[0]),
        Section(section_name=SectionEnum.M, section_code=SectionEnum.M.value[0])
    ]

    # Add to the session and commit
    db.session.add_all(sections)
    db.session.commit()

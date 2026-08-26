"""
Seeds the database with starter content: real school info scraped from
the live site (name, contact details, About/Admissions copy), a standard
Nigerian curriculum for Academics, and clearly-labeled placeholder entries
for Staff/Gallery/News/Events wherever we don't have real content yet.

Design decision: this exists as a management command — not a one-off shell
script — so that (a) it's version-controlled and reviewable like any other
code, (b) any developer or the school's own staff can rebuild a fresh dev
database with one command, and (c) it's fully idempotent (safe to re-run;
uses get_or_create/update throughout) rather than creating duplicates.

Usage:
    python manage.py seed_demo_data
"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.academics.models import AcademicsPage, Department, Subject
from apps.gallery.models import GalleryAlbum, GalleryPhoto
from apps.news_events.models import Event, NewsPost
from apps.pages.models import (
    AboutPage,
    AdmissionsPage,
    AdmissionStep,
    CoreValue,
    SchoolInfo,
)
from apps.staff.models import StaffMember


class Command(BaseCommand):
    help = "Seed the database with starter content (real school info + placeholder demo data)."

    def handle(self, *args, **options):
        self.seed_school_info()
        self.seed_about()
        self.seed_admissions()
        self.seed_academics()
        self.seed_staff()
        self.seed_gallery()
        self.seed_news()
        self.seed_events()
        self.stdout.write(self.style.SUCCESS("Demo data seeded successfully."))

    # ----------------------------------------------------------------
    def seed_school_info(self):
        info = SchoolInfo.load()
        info.school_name = "Mater Domini Schools"
        info.tagline = "Academic excellence and moral formation, Ogboja Ogoja."
        info.address = "Mater Domini Schools, Ogboja, Ogoja, Cross River State"
        info.main_office_phone = "07039173271"
        info.admissions_phone = "08065480166"
        info.emergency_phone = "08065480166"
        info.email = "info@materdominischool.com.ng"
        info.result_portal_url = "https://materdominischools.llms.sch.ng/"
        info.save()

    def seed_about(self):
        about = AboutPage.load()
        about.history = (
            "Mater Domini Schools, Ogboja Ogoja is a Catholic co-educational institution "
            "founded by the Catholic Diocese of Ogoja in 2017, starting as Mater Domini "
            "International Nursery and Primary School under the permission of the Bishop of "
            "Ogoja, Most Rev. Dr. Donatus Edet Akpan, and facilitated by the then Diocesan "
            "Education Board Secretary, Rev. Fr. Joseph Monkom Ayima.\n\n"
            "In 2022, under the leadership of Rev. Fr. Simon Peter Ogar Ibu, the secondary "
            "section was approved by the Cross River State Ministry of Education and the "
            "school adopted its current name, Mater Domini Schools, Ogboja Ogoja, open to "
            "all eligible learners irrespective of tribe, tongue, nationality, or religion."
        )
        about.mission = (
            "Mater Domini Schools is committed to academic excellence, character "
            "development, and holistic education — providing a well-structured curriculum, "
            "instilling strong moral values, and encouraging extracurricular activities for "
            "a balanced learning experience."
        )
        about.vision = (
            "To nurture students morally, intellectually, and in every sphere of human "
            "formation — producing graduates able to stand the test of time in all areas "
            "of human endeavour."
        )
        about.administrator_name = "Rev. Fr. Peter Ogar Ibu"
        about.administrator_title = "School Administrator"
        about.administrator_message = (
            "May the name of the undivided Trinity be praised both now and forever more. "
            "Mater Domini Schools, Ogboja Ogoja is a co-educational institution established "
            "by the Catholic Diocese of Ogoja, superlatively staffed with quality and "
            "qualified teachers who are disposed, available, sacrificial, and ever ready."
        )
        about.save()

        for i, (title, desc) in enumerate([
            ("Academic Excellence", "A rigorous, well-structured curriculum equipping students to excel academically and beyond."),
            ("Strong Moral Values", "Discipline, responsibility, and strong ethical foundations rooted in our Catholic identity."),
            ("Holistic Development", "Sports, music, arts, and leadership programs supporting the whole child."),
            ("Safe, Supportive Community", "A secure and inclusive environment where every learner feels valued."),
        ]):
            CoreValue.objects.get_or_create(title=title, defaults={"description": desc, "order": i})

    def seed_admissions(self):
        adm = AdmissionsPage.load()
        adm.intro = (
            "Enrolling at Mater Domini Schools Ogboja Ogoja is open to all eligible learners "
            "irrespective of tribe, tongue, nationality, or religion, from creche through "
            "senior secondary."
        )
        adm.requirements = (
            "Completed application form\n"
            "Birth certificate or age declaration\n"
            "Passport photographs\n"
            "Previous school report (for transfer students)\n"
            "Transfer/testimonial letter (for transfer students)"
        )
        adm.save()

        for i, (title, desc) in enumerate([
            ("Submit an Inquiry", "Fill out the form below with your child's details and your contact information."),
            ("School Visit", "Our admissions office will invite you for a tour and an informal chat."),
            ("Assessment", "Prospective students meet with staff for a brief placement assessment."),
            ("Enrollment", "Complete registration and documentation to secure your child's place."),
        ]):
            AdmissionStep.objects.get_or_create(title=title, defaults={"description": desc, "order": i})

    def seed_academics(self):
        page = AcademicsPage.load()
        page.intro = (
            "Mater Domini Schools follows the Nigerian national curriculum across Junior "
            "and Senior Secondary levels, combining core academic subjects with "
            "values-based and vocational learning."
        )
        page.junior_secondary_overview = (
            "JSS1 to JSS3 students follow a broad common curriculum covering sciences, "
            "humanities, languages, and practical/vocational subjects, building the "
            "foundation for specialization at the senior level."
        )
        page.senior_secondary_overview = (
            "From SS1, students choose a track — Science, Arts, or Commercial — alongside "
            "compulsory core subjects, preparing them for WASSCE/NECO examinations and "
            "tertiary education."
        )
        page.save()

        # (department name, description, order): [(subject, level, track), ...]
        curriculum = {
            ("Sciences", "Physical, biological, and applied sciences.", 0): [
                ("Basic Science", "junior", ""),
                ("Biology", "senior", "science"),
                ("Chemistry", "senior", "science"),
                ("Physics", "senior", "science"),
            ],
            ("Mathematics", "Core and further mathematics.", 1): [
                ("Mathematics", "junior", ""),
                ("Mathematics", "senior", "core"),
                ("Further Mathematics", "senior", "science"),
            ],
            ("Languages", "English and French language studies.", 2): [
                ("English Language", "junior", ""),
                ("French", "junior", ""),
                ("English Language", "senior", "core"),
                ("Literature in English", "senior", "arts"),
                ("French", "senior", "arts"),
            ],
            ("Humanities & Social Sciences", "History, Government, Geography, and Civic Education.", 3): [
                ("Social Studies", "junior", ""),
                ("Civic Education", "junior", ""),
                ("Civic Education", "senior", "core"),
                ("Geography", "senior", "science"),
                ("Geography", "senior", "arts"),
                ("Government", "senior", "arts"),
                ("History", "senior", "arts"),
            ],
            ("Business Studies", "Commerce, Accounting, and Economics.", 4): [
                ("Basic Business Studies", "junior", ""),
                ("Commerce", "senior", "commercial"),
                ("Financial Accounting", "senior", "commercial"),
                ("Economics", "senior", "commercial"),
                ("Office Practice", "senior", "commercial"),
            ],
            ("Religious & Moral Studies", "Christian Religious Studies and moral formation.", 5): [
                ("Christian Religious Studies", "junior", ""),
                ("Christian Religious Studies", "senior", "arts"),
            ],
            ("Creative, Technical & Vocational", "Cultural/Creative Arts, Basic Technology, Agricultural Science, ICT, and Home Economics.", 6): [
                ("Cultural and Creative Arts", "junior", ""),
                ("Basic Technology", "junior", ""),
                ("Agricultural Science", "junior", ""),
                ("Computer Studies/ICT", "junior", ""),
                ("Home Economics", "junior", ""),
                ("Agricultural Science", "senior", "science"),
                ("Computer Science", "senior", "science"),
                ("Fine Arts", "senior", "arts"),
                ("Trade/Entrepreneurship Subject", "senior", "commercial"),
            ],
            ("Physical & Health Education", "Sports and health education.", 7): [
                ("Physical and Health Education", "junior", ""),
            ],
        }

        for (dept_name, dept_desc, dept_order), subjects in curriculum.items():
            department, _ = Department.objects.get_or_create(
                name=dept_name, defaults={"description": dept_desc, "order": dept_order}
            )
            for subj_name, level, track in subjects:
                Subject.objects.get_or_create(
                    name=subj_name, department=department, level=level, track=track
                )

    def seed_staff(self):
        sciences = Department.objects.filter(name="Sciences").first()
        mathematics = Department.objects.filter(name="Mathematics").first()
        languages = Department.objects.filter(name="Languages").first()

        # Real: the Administrator, whose message we already have from About.
        StaffMember.objects.get_or_create(
            full_name="Rev. Fr. Peter Ogar Ibu",
            defaults={
                "role_title": "School Administrator",
                "category": "management",
                "bio": "Oversees the overall direction, mission, and daily operations of the school.",
                "order": 0,
            },
        )

        # Placeholders — clearly bracketed so they're never mistaken for real people.
        placeholders = [
            ("[Placeholder Name]", "Vice Principal (Academics)", "management", None,
             "Placeholder profile — replace with the real Vice Principal (Academics) details from the admin panel.", 1),
            ("[Placeholder Name]", "Vice Principal (Administration)", "management", None,
             "Placeholder profile — replace with the real Vice Principal (Administration) details from the admin panel.", 2),
            ("[Placeholder Staff]", "School Bursar", "non_teaching", None,
             "Placeholder profile — replace with real staff bio and photo from the admin panel.", 0),
            ("[Placeholder Staff]", "Front Desk / Admissions Officer", "non_teaching", None,
             "Placeholder profile — replace with real staff bio and photo from the admin panel.", 1),
            ("[Placeholder Teacher]", "Head of Sciences Department", "teaching", sciences,
             "Placeholder profile — replace with real staff bio and photo from the admin panel.", 0),
            ("[Placeholder Teacher]", "Mathematics Teacher", "teaching", mathematics,
             "Placeholder profile — replace with real staff bio and photo from the admin panel.", 1),
            ("[Placeholder Teacher]", "English Language Teacher", "teaching", languages,
             "Placeholder profile — replace with real staff bio and photo from the admin panel.", 2),
            ("[Placeholder Teacher]", "Basic Science Teacher (JSS)", "teaching", sciences,
             "Placeholder profile — replace with real staff bio and photo from the admin panel.", 3),
        ]
        for full_name, role_title, category, department, bio, order in placeholders:
            StaffMember.objects.get_or_create(
                full_name=full_name,
                role_title=role_title,
                defaults={
                    "category": category,
                    "department": department,
                    "bio": bio,
                    "order": order,
                },
            )

    def seed_gallery(self):
        entries = [
            ("Front Gate & Signage", "campus", "The school entrance along the Ogboja road."),
            ("Classroom Block", "campus", "One of the Junior Secondary classroom blocks."),
            ("Science Practical Session", "academics", "Students during a Basic Science practical."),
            ("Inter-House Sports", "sports", "Annual inter-house sports competition."),
            ("Cultural Day", "events", "Students in traditional attire for Cultural Day."),
            ("Sunday Mass", "spiritual", "The school community at weekly Mass."),
        ]

        for i, (title, category, caption) in enumerate(entries):
            album, _ = GalleryAlbum.objects.get_or_create(
                title=title,
                defaults={
                    "category": category,
                    "caption": caption,
                    "order": i,
                },
            )

            # Create one placeholder slide for albums that do not yet
            # have any uploaded photographs. Real photographs can be
            # added later from the Django admin.
            if not album.photos.exists():
                GalleryPhoto.objects.create(
                    album=album,
                    caption=caption,
                    order=0,
                )

    def seed_news(self):
        today = timezone.now().date()
        posts = [
            (
                "Mater Domini Schools Resumes for New Academic Session",
                "Students and staff return as the new academic session begins with a renewed focus on academic excellence.",
                "[Sample News Post] The school community gathered this week as students resumed for the new academic "
                "session. The administration used the opening assembly to reaffirm the school's commitment to "
                "academic excellence and moral formation for the term ahead. Replace this post with real school "
                "news from the admin panel.",
                today - timedelta(days=3),
            ),
            (
                "Inter-House Sports Competition Announced",
                "The annual inter-house sports competition returns this term, with four houses competing for the trophy.",
                "[Sample News Post] Mater Domini Schools will host its annual inter-house sports competition this "
                "term. All four houses will compete across track and field events. Replace this post with real "
                "school news from the admin panel.",
                today - timedelta(days=10),
            ),
            (
                "WASSCE Preparation Classes Begin for SS3",
                "Extra preparation classes have started for SS3 students ahead of this year's WASSCE examinations.",
                "[Sample News Post] The academics department has begun extra preparation classes for SS3 students "
                "ahead of the West African Senior School Certificate Examination. Replace this post with real "
                "school news from the admin panel.",
                today - timedelta(days=18),
            ),
        ]
        for title, excerpt, body, published_date in posts:
            NewsPost.objects.get_or_create(
                title=title,
                defaults={"excerpt": excerpt, "body": body, "published_date": published_date},
            )

    def seed_events(self):
        now = timezone.now().replace(minute=0, second=0, microsecond=0)
        events = [
            (
                "Inter-House Sports Competition",
                "[Sample Event] Annual inter-house sports competition — replace with real event details from the admin panel.",
                "School Sports Field",
                now + timedelta(days=14, hours=8),
            ),
            (
                "First Term Parent-Teacher Meeting",
                "[Sample Event] Parents and guardians meet with teachers to review first-term progress — replace with "
                "real event details from the admin panel.",
                "School Main Hall",
                now + timedelta(days=25, hours=10),
            ),
            (
                "Cultural Day Celebration",
                "[Sample Event] Students celebrate Nigeria's diverse cultures with traditional attire and performances "
                "— replace with real event details from the admin panel.",
                "School Assembly Ground",
                now - timedelta(days=20, hours=-9),
            ),
        ]
        for title, description, location, start_datetime in events:
            Event.objects.get_or_create(
                title=title,
                defaults={
                    "description": description,
                    "location": location,
                    "start_datetime": start_datetime,
                },
            )

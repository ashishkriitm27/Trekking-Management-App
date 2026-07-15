from datetime import date, timedelta

from app import app
from application.database import db
from application.models import User, Trek


with app.app_context():

    # ---------------- USERS ---------------- #

    users = []

    for i in range(1, 31):
        users.append(
            User(
                username=f"user{i}",
                email=f"user{i}@gmail.com",
                password="123",
                type="user",
                is_approved=True,
                is_blacklist=False
            )
        )

    db.session.add_all(users)

    # ---------------- STAFF ---------------- #

    staffs = []

    for i in range(1, 11):
        staffs.append(
            User(
                username=f"staff{i}",
                email=f"staff{i}@gmail.com",
                password="123",
                type="staff",
                is_approved=True,
                is_blacklist=False
            )
        )

    db.session.add_all(staffs)

    db.session.commit()

    # ---------------- TREKS ---------------- #

    trek_data = [
        ("Kedarkantha Trek", "Uttarakhand", "Easy", 6, 40),
        ("Hampta Pass Trek", "Himachal Pradesh", "Moderate", 5, 35),
        ("Valley of Flowers", "Uttarakhand", "Easy", 4, 50),
        ("Sandakphu Trek", "West Bengal", "Moderate", 7, 30),
        ("Goechala Trek", "Sikkim", "Hard", 8, 25),
    ]

    today = date.today()

    treks = []

    for i, (name, location, difficulty, duration, slots) in enumerate(trek_data):

        start = today + timedelta(days=(i + 1) * 10)
        end = start + timedelta(days=duration - 1)

        treks.append(
            Trek(
                name=name,
                location=location,
                difficulty=difficulty,
                duration=duration,
                total_slot=slots,
                available_slot=slots,
                status="Open",
                start_date=start,
                end_date=end,
                staff_id=None
            )
        )

    db.session.add_all(treks)
    db.session.commit()

    print("=" * 50)
    print("Dummy data inserted successfully!")
    print("30 Users Added")
    print("10 Staff Added")
    print("5 Treks Added")
    print("No Staff Assigned to Any Trek")
    print("=" * 50)
from .database import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    email = db.Column(db.String(200), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # User, Admin, Staff
    is_approved = db.Column(db.Boolean, default=False)
    is_blacklist = db.Column(db.Boolean, default=False)

    # Relationships
    bookings = db.relationship('Booking', backref='user', lazy=True)
    assigned_treks = db.relationship(
        'Trek',
        back_populates='staff',
        foreign_keys='Trek.staff_id',
        lazy=True
    )


class Trek(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    difficulty = db.Column(db.String(20), nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    total_slot = db.Column(db.Integer, nullable=False)
    available_slot = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Open')
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)

    staff_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=True
    )

    # Relationships
    staff = db.relationship(
        'User',
        back_populates='assigned_treks',
        foreign_keys=[staff_id]
    )

    bookings = db.relationship(
        'Booking',
        backref='trek',
        lazy=True
    )


class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=False
    )
    trek_id = db.Column(
        db.Integer,
        db.ForeignKey('trek.id'),
        nullable=False
    )
    booking_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Booked')
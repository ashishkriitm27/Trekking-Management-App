#Imports
from flask import render_template, redirect, request, session, url_for, flash
from flask import current_app as app
from werkzeug.security import check_password_hash, generate_password_hash
from .models import *
from .database import db
from sqlalchemy import or_

from datetime import datetime

# Routes

#Home Routes


@app.route('/')
def home():
    return redirect('/login')

#login, registration and logout routes

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        # Find user by email only
        user = User.query.filter_by(
            email=email
        ).first()

        # Check email and hashed password
        if not user or not check_password_hash(user.password, password):
            flash(
                'Invalid email or password.',
                'danger'
            )
            return redirect('/login')

        if user.is_blacklist:
            flash(
                'Your account has been blacklisted. Contact Admin.',
                'danger'
            )
            return redirect('/login')

        if user.type == 'staff' and not user.is_approved:
            flash(
                'Your account is awaiting admin approval.',
                'warning'
            )
            return redirect('/login')

        session['user_id'] = user.id
        session['username'] = user.username
        session['role'] = user.type

        if user.type == 'admin':
            return redirect('/admin_dashboard')

        elif user.type == 'staff':
            return redirect('/staff_dashboard')

        else:
            return redirect('/user_dashboard')

    return render_template('login.html')


#Log out
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect('/login')

# Registration Route

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        username = request.form['username']
        email = request.form['email']

        password = request.form['password']
        confirm = request.form['confirm_password']

        user_type = request.form.get('type', 'user')

        if password != confirm:
            flash(
                'Confirm password is not the same as password.',
                'danger'
            )
            return redirect('/register')

        existing_user = User.query.filter_by(
            email=email
        ).first()

        if existing_user:
            flash(
                'Email is already registered.',
                'danger'
            )
            return redirect('/register')

        # Hash the password before storing
        hashed_password = generate_password_hash(password)

        new_user = User(
            username=username,
            email=email,
            password=hashed_password,
            type=user_type
        )

        db.session.add(new_user)
        db.session.commit()

        if user_type == 'staff':
            flash(
                'Registration successful! Please wait for admin approval.',
                'success'
            )
            return redirect('/login')

        flash(
            'Registration successful! Please log in.',
            'success'
        )

        return redirect('/login')

    return render_template('register.html')

# Comman Dashbaord routes(for navigation purpose)
@app.route('/dashboard')
def dashboard():

    if 'user_id' not in session:
        return redirect('/login')

    role = session.get('role')

    if role == 'admin':
        return redirect('/admin_dashboard')

    elif role == 'staff':
        return redirect('/staff_dashboard')

    else:
        return redirect('/user_dashboard')
  
#Update profile

@app.route('/profile', methods=['GET', 'POST'])
def profile():

    if 'user_id' not in session:
        return redirect('/login')

    user = User.query.get_or_404(session['user_id'])

    if request.method == 'POST':

        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        existing_user = User.query.filter(
            User.username == username,
            User.id != user.id
        ).first()

        if existing_user:
            flash('Username already exists.', 'danger')
            return redirect(request.url)

        existing_email = User.query.filter(
            User.email == email,
            User.id != user.id
        ).first()

        if existing_email:
            flash('Email already exists.', 'danger')
            return redirect(request.url)

        user.username = username
        user.email = email

        if password:
            user.password = password

        db.session.commit()

        flash('Profile updated successfully.', 'success')

        if session.get('role') == 'staff':
            return redirect('/staff_dashboard')

        elif session.get('role') == 'admin':
            return redirect('/admin_dashboard')

        else:
            return redirect('/dashboard')

    return render_template(
        'profile.html',
        user=user
    )
    
# -------------ADMIN Routes--------------

#Admin dashbaord

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    if session.get('role') != 'admin':
        return redirect('/login')

    total_users = User.query.filter_by(type = 'user').count()
    total_staff = User.query.filter_by(type = 'staff').count()
    pending_staff = User.query.filter_by(type = 'staff', is_approved =False).count()
    total_treks = Trek.query.count()
    total_bookings =Booking.query.filter_by(status='Booked').count()
    recent_bookings = Booking.query.order_by(Booking.id.desc()).limit(5).all()
    
    #Chart
    
    chart_labels = [
    'Treks',
    'Users',
    'Staff',
    'Bookings'
]

    chart_data = [
        total_treks,
        total_users,
        total_staff,
        total_bookings
    ]
    
    return render_template(
    'admin_dashboard.html',
    username=session.get('username'),
    total_users=total_users,
    total_staff=total_staff,
    pending_staff=pending_staff,
    total_treks=total_treks,
    total_bookings=total_bookings,
    recent_bookings=recent_bookings,

    chart_labels=chart_labels,
    chart_data=chart_data
    )
    
# Admin manage User

@app.route('/admin/users')
def admin_users():

    if 'user_id' not in session:
        return redirect('/login')

    if session.get('role') != 'admin':
        return redirect('/login')

    search = request.args.get('search', '').strip()

    query = User.query.filter(User.type == 'user')

    if search:
        query = query.filter(
            or_(
                User.username.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%')
            )
        )

    users = query.order_by(User.username).all()

    return render_template(
        'admin_users.html',
        users=users,
        search=search
    )
    
# Admin blacklist or ublacklist user

@app.route('/admin/blacklist_staff/<int:id>')
def blacklist_staff(id):

    if 'user_id' not in session:
        return redirect('/login')

    if session.get('role') != 'admin':
        return redirect('/login')

    staff = User.query.get_or_404(id)
    staff.is_blacklist = True
    db.session.commit()
    flash('Staff has been blacklisted.', 'warning')
    return redirect('/admin/staff')

@app.route('/admin/unblacklist_user/<int:id>')
def unblacklist_user(id):

    if 'user_id' not in session:
        return redirect('/login')

    if session.get('role') != 'admin':
        return redirect('/login')

    user = User.query.get_or_404(id)
    user.is_blacklist = False
    db.session.commit()
    flash('User removed from blacklist.', 'success')
    return redirect('/admin/users')

# Admin manage staff

@app.route('/admin/staff')
def admin_staff():

    if 'user_id' not in session:
        return redirect('/login')

    if session.get('role') != 'admin':
        return redirect('/login')

    search = request.args.get('search', '').strip()

    if search:

        staffs = User.query.filter(
            User.type == 'staff',
            db.or_(
                User.username.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%')
            )
        ).all()

    else:

        staffs = User.query.filter_by(
            type='staff'
        ).order_by(User.username)

    return render_template(
        'admin_staff.html',
        staffs=staffs,
        search=search
    )

# Admin manage pending staff

@app.route('/admin/pending_staff')
def pending_staff():

    if 'user_id' not in session:
        return redirect('/login')

    if session.get('role') != 'admin':
        return redirect('/login')

    staffs = User.query.filter_by(
        type='staff',
        is_approved=False
    ).all()

    return render_template(
        'pending_staff.html',
        staffs=staffs
    )

# Admin approve pending staff


@app.route('/admin/approve_staff/<int:id>')
def approve_staff(id):

    if 'user_id' not in session:
        return redirect('/login')

    if session.get('role') != 'admin':
        return redirect('/login')

    staff = User.query.get_or_404(id)
    staff.is_approved = True
    db.session.commit()
    flash('Staff approved successfully.', 'success')
    return redirect('/admin/pending_staff')

# Admin reject pending staff

@app.route('/admin/reject_staff/<int:id>')
def reject_staff(id):

    if 'user_id' not in session:
        return redirect('/login')

    if session.get('role') != 'admin':
        return redirect('/login')

    staff = User.query.get_or_404(id)

    db.session.delete(staff)
    db.session.commit()

    flash('Staff request rejected successfully.', 'success')

    return redirect('/admin/pending_staff')

# Admin view trek

@app.route('/admin/treks')
def admin_treks():

    if 'user_id' not in session:
        return redirect('/login')

    if session.get('role') != 'admin':
        return redirect('/login')

    # Search Text
    search = request.args.get('search', '').strip()

    if search:

        treks = Trek.query.filter(
            db.or_(
                Trek.name.ilike(f"%{search}%"),
                Trek.location.ilike(f"%{search}%")
            )
        ).all()

    else:

        treks = Trek.query.all()

    # Approved Staff
    staffs = User.query.filter_by(
    type='staff',
    is_approved=True,
    is_blacklist=False
    ).all()

    return render_template(
        'admin_treks.html',
        treks=treks,
        staffs=staffs,
        search=search
    )    

# Add treak

@app.route('/admin/add_trek', methods=['GET', 'POST'])
def add_trek():

    if 'user_id' not in session:
        return redirect('/login')

    if session.get('role') != 'admin':
        return redirect('/login')

    if request.method == 'POST':

        name = request.form['name']
        location = request.form['location']
        difficulty = request.form['difficulty']
        duration = int(request.form['duration'])
        total_slot = int(request.form['total_slot'])

        start = datetime.strptime(
            request.form['start_date'],
            '%Y-%m-%d'
        ).date()

        end = datetime.strptime(
            request.form['end_date'],
            '%Y-%m-%d'
        ).date()
        from datetime import date

        # Validate dates
        if end < start:
            flash(
                'End Date cannot be before Start Date.',
                'danger'
            )
            return redirect('/admin/add_trek')

        if total_slot <= 0:
            flash(
                'Total Slots must be greater than 0.',
                'danger'
            )
            return redirect('/admin/add_trek')

        trek = Trek(
            name=name,
            location=location,
            difficulty=difficulty,
            duration=duration,
            total_slot=total_slot,
            available_slot=total_slot,
            start_date=start,
            end_date=end,
            status='Open'
        )

        db.session.add(trek)
        db.session.commit()

        flash(
            'Trek Added Successfully.',
            'success'
        )

        return redirect('/admin/treks')

    return render_template('add_trek.html')


@app.route('/admin/edit_trek/<int:id>', methods=['GET', 'POST'])
def edit_trek(id):

    if 'user_id' not in session:
        return redirect('/login')

    if session.get('role') != 'admin':
        return redirect('/login')

    trek = Trek.query.get_or_404(id)

    staffs = User.query.filter_by(
        type='staff',
        is_approved=True,
        is_blacklist=False
    ).all()

    if request.method == 'POST':

        trek.name = request.form['name'].strip()
        trek.location = request.form['location'].strip()
        trek.difficulty = request.form['difficulty']
        trek.duration = int(request.form['duration'])
        trek.status = request.form['status']

        new_total_slot = int(request.form['total_slot'])

        # Count only active bookings
        booked = Booking.query.filter_by(
            trek_id=trek.id,
            status='Booked'
        ).count()

        if new_total_slot < booked:
            flash(
                f'Total slots cannot be less than booked participants ({booked}).',
                'danger'
            )
            return redirect(request.url)

        trek.total_slot = new_total_slot
        trek.available_slot = new_total_slot - booked

        staff_id = request.form.get('staff_id')

        if staff_id:
            staff = User.query.filter_by(
                id=int(staff_id),
                type='staff',
                is_approved=True,
                is_blacklist=False
            ).first()

            trek.staff_id = staff.id if staff else None
        else:
            trek.staff_id = None

        db.session.commit()

        flash(
            'Trek updated successfully.',
            'success'
        )

        return redirect('/admin/treks')

    return render_template(
        'edit_trek.html',
        trek=trek,
        staffs=staffs
    )
#Delete treak


@app.route('/admin/delete_trek/<int:id>')
def delete_trek(id):

    if 'user_id' not in session:
        return redirect('/login')

    if session.get('role') != 'admin':
        return redirect('/login')

    trek = Trek.query.get_or_404(id)
    booking = Booking.query.filter_by(trek_id=id).first()
    if booking:
        flash('This trek cannot be deleted because booking history exists. Change its status instead.','warning')
        return redirect('/admin/treks')
    db.session.delete(trek)
    db.session.commit()
    flash('Trek deleted successfully.', 'success')
    return redirect('/admin/treks')

# Admin booking history
@app.route('/admin/bookings')
def admin_bookings():

    if 'user_id' not in session:
        return redirect('/login')

    if session.get('role') != 'admin':
        return redirect('/login')

    admin = User.query.get(session['user_id'])

    if not admin:
        session.clear()
        return redirect('/login')

    bookings = Booking.query.order_by(
        Booking.booking_date.desc(),
        Booking.id.desc()
    ).all()

    return render_template(
        'admin_bookings.html',
        bookings=bookings
    )
    
#Admin trek details

@app.route('/admin/trek/<int:trek_id>')
def admin_trek_details(trek_id):

    if 'user_id' not in session:
        return redirect('/login')

    if session.get('role') != 'admin':
        return redirect('/login')

    admin = User.query.get(session['user_id'])

    if not admin:
        session.clear()
        return redirect('/login')

    trek = Trek.query.get_or_404(trek_id)

    bookings = Booking.query.filter(
    Booking.trek_id == trek.id,
    Booking.status.in_(["Booked", "Completed"])
    ).order_by(
        Booking.booking_date.desc(),
        Booking.id.desc()
    ).all()

    total_participants = len(bookings)

    booked_count = Booking.query.filter_by(
        trek_id=trek.id,
        status='Booked'
    ).count()

    completed_count = Booking.query.filter_by(
        trek_id=trek.id,
        status='Completed'
    ).count()

    cancelled_count = Booking.query.filter_by(
        trek_id=trek.id,
        status='Cancelled'
    ).count()

    return render_template(
        'admin_trek_details.html',
        trek=trek,
        bookings=bookings,
        total_participants=total_participants,
        booked_count=booked_count,
        completed_count=completed_count,
        cancelled_count=cancelled_count
    )


# -------------STAFF Routes--------------

#Staff dashbaord

@app.route('/staff_dashboard')
def staff_dashboard():

    if 'user_id' not in session:
        return redirect('/login')

    if session.get('role') != 'staff':
        return redirect('/login')

    # Blacklist check
    staff = User.query.get(session['user_id'])
    if not staff or staff.is_blacklist:
        session.clear()
        flash('Your account has been blacklisted.', 'danger')
        return redirect('/login')

    treks = Trek.query.filter_by(
        staff_id=session['user_id']
    ).all()

    total_treks = len(treks)

    open_treks = Trek.query.filter_by(
        staff_id=session['user_id'],
        status='Open'
    ).count()

    total_participants = Booking.query.join(Trek).filter(
        Trek.staff_id == session['user_id'],
        Booking.status == 'Booked'
    ).count()

    chart_labels = []
    chart_data = []

    for trek in treks:

        participant_count = Booking.query.filter_by(
            trek_id=trek.id,
            status='Booked'
        ).count()

        chart_labels.append(trek.name)
        chart_data.append(participant_count)

    return render_template(
        'staff_dashboard.html',
        treks=treks,
        total_treks=total_treks,
        open_treks=open_treks,
        total_participants=total_participants,
        chart_labels=chart_labels,
        chart_data=chart_data
    )
    
# Staff manage treks

@app.route('/staff/manage_trek/<int:trek_id>', methods=['GET', 'POST'])
def manage_trek(trek_id):

    if 'user_id' not in session:
        return redirect('/login')

    if session.get('role') != 'staff':
        return redirect('/login')
    

    trek = Trek.query.filter_by(
        id=trek_id,
        staff_id=session['user_id']
    ).first_or_404()

    booked_count = Booking.query.filter_by(
        trek_id=trek.id,
        status='Booked'
    ).count()

    if request.method == 'POST':

        new_available = int(request.form['available_slots'])

        # Cannot exceed total slots assigned by Admin
        if new_available > trek.total_slot:
            flash(
                f'Available slots cannot exceed Total Slots ({trek.total_slot}).',
                'danger'
            )
            return redirect(request.url)

        # Cannot be less than booked participants
        if new_available < booked_count:
            flash(
                f'Available slots cannot be less than Booked Participants ({booked_count}).',
                'danger'
            )
            return redirect(request.url)

        trek.available_slot = new_available
        trek.status = request.form['status']

        # If trek completed, complete all active bookings
        if trek.status == 'Completed':

            bookings = Booking.query.filter_by(
                trek_id=trek.id,
                status='Booked'
            ).all()

            for booking in bookings:
                booking.status = 'Completed'

        db.session.commit()

        flash(
            'Trek details updated successfully.',
            'success'
        )

        return redirect('/staff_dashboard')

    bookings = Booking.query.filter_by(
        trek_id=trek.id,
        status='Booked'
    ).all()

    return render_template(
        'manage_trek.html',
        trek=trek,
        bookings=bookings,
        count=booked_count
    )    
# ---------------- USER DASHBOARD ---------------- #
@app.route('/user_dashboard')
def user_dashboard():

    if 'user_id' not in session:
        return redirect('/login')

    if session.get('role') != 'user':
        return redirect('/login')

    # Check if user is blacklisted
    user = User.query.get(session['user_id'])

    if not user or user.is_blacklist:
        session.clear()
        flash('Your account has been blacklisted.', 'danger')
        return redirect('/login')

    # ---------------- Search & Filters ---------------- #

    search = request.args.get('search', '').strip()
    difficulty = request.args.get('difficulty', '').strip()
    location = request.args.get('location', '').strip()

    query = Trek.query.filter(
        Trek.status == 'Open',
        Trek.available_slot > 0
    )

    if search:
        query = query.filter(
            Trek.name.ilike(f'%{search}%')
        )

    if difficulty:
        query = query.filter(
            Trek.difficulty == difficulty
        )

    if location:
        query = query.filter(
            Trek.location.ilike(f'%{location}%')
        )

    treks = query.all()

    # ---------------- Dashboard Cards ---------------- #

    total_bookings = Booking.query.filter_by(
        user_id=session['user_id']
    ).count()

    upcoming_treks = Booking.query.join(Trek).filter(
        Booking.user_id == session['user_id'],
        Booking.status == 'Booked',
        Trek.status == 'Open'
    ).count()

    available_treks = Trek.query.filter(
        Trek.status == 'Open',
        Trek.available_slot > 0
    ).count()

    # ---------------- Pie Chart ---------------- #

    booked_count = Booking.query.filter_by(
        user_id=session['user_id'],
        status='Booked'
    ).count()

    completed_count = Booking.query.filter_by(
        user_id=session['user_id'],
        status='Completed'
    ).count()

    cancelled_count = Booking.query.filter_by(
        user_id=session['user_id'],
        status='Cancelled'
    ).count()

    status_labels = [
        'Booked',
        'Completed',
        'Cancelled'
    ]

    status_data = [
        booked_count,
        completed_count,
        cancelled_count
    ]

    # ---------------- Participants Chart ---------------- #

    trek_labels = []
    participant_data = []
    added_treks = set()

    my_bookings = Booking.query.filter_by(
        user_id=session['user_id'],
        status='Booked'
    ).all()

    for booking in my_bookings:

        trek = Trek.query.get(booking.trek_id)

        if trek and trek.id not in added_treks:

            participant_count = Booking.query.filter_by(
                trek_id=trek.id,
                status='Booked'
            ).count()

            trek_labels.append(trek.name)
            participant_data.append(participant_count)

            added_treks.add(trek.id)

    return render_template(
        'user_dashboard.html',
        username=user.username,
        treks=treks,

        total_bookings=total_bookings,
        upcoming_treks=upcoming_treks,
        available_treks=available_treks,

        search=search,
        difficulty=difficulty,
        location=location,

        status_labels=status_labels,
        status_data=status_data,

        trek_labels=trek_labels,
        participant_data=participant_data
    )
    if difficulty:
        query = query.filter(
            Trek.difficulty == difficulty
        )

    if location:
        query = query.filter(
            Trek.location.ilike(f'%{location}%')
        )

    treks = query.all()


    # Dashboard Cards


    # Total Booking History
    total_bookings = Booking.query.filter_by(
        user_id=session['user_id']
    ).count()

    # Only Active Upcoming Bookings
    upcoming_treks = Booking.query.join(Trek).filter(
        Booking.user_id == session['user_id'],
        Booking.status == 'Booked',
        Trek.status == 'Open'
    ).count()

    available_treks = Trek.query.filter_by(
        status='Open'
    ).count()

    # Pie Chart


    booked_count = Booking.query.filter_by(
        user_id=session['user_id'],
        status='Booked'
    ).count()

    completed_count = Booking.query.filter_by(
        user_id=session['user_id'],
        status='Completed'
    ).count()

    cancelled_count = Booking.query.filter_by(
        user_id=session['user_id'],
        status='Cancelled'
    ).count()

    status_labels = [
        'Booked',
        'Completed',
        'Cancelled'
    ]

    status_data = [
        booked_count,
        completed_count,
        cancelled_count
    ]

    # Participants Chart


    trek_labels = []
    participant_data = []
    added_treks = set()

    my_bookings = Booking.query.filter_by(
        user_id=session['user_id'],
        status='Booked'
    ).all()

    for booking in my_bookings:

        trek = Trek.query.get(booking.trek_id)

        if trek and trek.id not in added_treks:

            participant_count = Booking.query.filter_by(
                trek_id=trek.id,
                status='Booked'
            ).count()

            trek_labels.append(trek.name)
            participant_data.append(participant_count)

            added_treks.add(trek.id)

    return render_template(
        'user_dashboard.html',
        username=session.get('username'),
        treks=treks,

        total_bookings=total_bookings,
        upcoming_treks=upcoming_treks,
        available_treks=available_treks,

        search=search,
        difficulty=difficulty,
        location=location,

        status_labels=status_labels,
        status_data=status_data,

        trek_labels=trek_labels,
        participant_data=participant_data
    )

#Book trek

@app.route('/book_trek/<int:trek_id>')
def book_trek(trek_id):

    if 'user_id' not in session:
        return redirect('/login')

    if session.get('role') != 'user':
        return redirect('/login')

    user = User.query.get(session['user_id'])

    if not user:
        session.clear()
        return redirect('/login')

    if user.is_blacklist:
        flash(
            'Your account is blacklisted. Cannot book trek.',
            'danger'
        )
        return redirect('/user_dashboard')

    trek = Trek.query.get_or_404(trek_id)

    if trek.status != 'Open':
        flash(
            'Cannot book trek. Trek is not open.',
            'warning'
        )
        return redirect('/user_dashboard')

    if trek.staff_id is None:
        flash(
            'This trek has no assigned staff yet.',
            'warning'
        )
        return redirect('/user_dashboard')

    if trek.available_slot <= 0:
        flash(
            'No slots available.',
            'warning'
        )
        return redirect('/user_dashboard')

    booking = Booking.query.filter_by(
        user_id=user.id,
        trek_id=trek.id,
        status='Booked'
    ).first()

    if booking:
        flash(
            'You have already booked this trek.',
            'info'
        )
        return redirect('/user_dashboard')

    new_booking = Booking(
        user_id=user.id,
        trek_id=trek.id,
        booking_date=datetime.today().date(),
        status='Booked'
    )

    db.session.add(new_booking)

    trek.available_slot -= 1

    db.session.commit()

    flash(
        'Booking Successful!',
        'success'
    )

    return redirect('/my_bookings')


# User my booking

@app.route('/my_bookings')
def my_bookings():

    if 'user_id' not in session:
        return redirect('/login')

    if session.get('role') != 'user':
        return redirect('/login')

    user = User.query.get(session['user_id'])

    if not user or user.is_blacklist:
        session.clear()
        flash('Your account has been blacklisted.', 'danger')
        return redirect('/login')

    booking_status = request.args.get('booking_status', '').strip()
    trek_status = request.args.get('trek_status', '').strip()

    query = Booking.query.join(Trek).filter(
        Booking.user_id == user.id
    )

    if booking_status:
        query = query.filter(
            Booking.status == booking_status
        )

    if trek_status:
        query = query.filter(
            Trek.status == trek_status
        )

    bookings = query.order_by(
        Booking.id.desc()
    ).all()

    return render_template(
        'my_bookings.html',
        bookings=bookings,
        booking_status=booking_status,
        trek_status=trek_status
    )

#User trek details

@app.route('/trek/<int:trek_id>')
def trek_details(trek_id):

    if 'user_id' not in session:
        return redirect('/login')

    if session.get('role') != 'user':
        return redirect('/login')

    user = User.query.get(session['user_id'])

    if not user or user.is_blacklist:
        session.clear()
        flash('Your account has been blacklisted.', 'danger')
        return redirect('/login')

    trek = Trek.query.get_or_404(trek_id)

    if trek.status != 'Open':
        flash(
            'This trek is not available.',
            'warning'
        )
        return redirect('/user_dashboard')

    already_booked = Booking.query.filter_by(
        user_id=user.id,
        trek_id=trek.id,
        status='Booked'
    ).first()

    return render_template(
        'trek_details.html',
        trek=trek,
        already_booked=already_booked
    )

#User booking trek details

@app.route('/booking/<int:booking_id>')
def booking_details(booking_id):

    if 'user_id' not in session:
        return redirect('/login')

    if session.get('role') != 'user':
        return redirect('/login')

    user = User.query.get(session['user_id'])

    if not user or user.is_blacklist:
        session.clear()
        flash(
            'Your account has been blacklisted.',
            'danger'
        )
        return redirect('/login')

    booking = Booking.query.filter_by(
        id=booking_id,
        user_id=user.id
    ).first_or_404()

    return render_template(
        'booking_details.html',
        booking=booking
    )
#User cancel trek

@app.route('/cancel_booking/<int:booking_id>')
def cancel_booking(booking_id):

    if 'user_id' not in session:
        return redirect('/login')

    if session.get('role') != 'user':
        return redirect('/login')

    user = User.query.get(session['user_id'])

    if not user or user.is_blacklist:
        session.clear()
        flash(
            'Your account has been blacklisted.',
            'danger'
        )
        return redirect('/login')

    booking = Booking.query.filter_by(
        id=booking_id,
        user_id=user.id
    ).first_or_404()

    if booking.status != 'Booked':
        flash(
            'Booking cannot be cancelled.',
            'warning'
        )
        return redirect('/my_bookings')

    trek = booking.trek

    booking.status = 'Cancelled'

    booking.trek.available_slot += 1

    db.session.commit()

    flash(
        'Booking cancelled successfully.',
        'success'
    )

    return redirect('/my_bookings')



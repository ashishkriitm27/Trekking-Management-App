from flask import render_template, redirect, request, session, url_for, flash
from flask import current_app as app
from .models import *
from .database import db

from datetime import datetime
# Home Route

@app.route('/')
def home():
    return redirect('/login')

# Login Route

@app.route('/login', methods=['GET', 'POST'])
def login():

    # Process login form submission
    if request.method == 'POST':

        # Get user credentials from the form
        email = request.form['email']
        password = request.form['password']

        # Find user with matching email and password
        user = User.query.filter_by(email=email, password=password).first()

        # Invalid credentials
        if not user:
            flash('Invalid email or password.', 'danger')
            return redirect('/login')

        # Prevent blacklisted users from logging in
        if user.is_blacklist:
            flash('Your account has been blacklisted. Contact Admin.', 'danger')
            return redirect('/login')

        # Staff members must be approved by the admin
        if user.type == 'staff' and not user.is_approved:
            flash('Your account is awaiting admin approval.', 'warning')
            return redirect('/login')

        # Store logged-in user information in the session
        session['user_id'] = user.id
        session['username'] = user.username
        session['role'] = user.type

        # Redirect users based on their role
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

    # Process registration form submission
    if request.method == 'POST':

        # Get registration details from the form
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confrim = request.form['confirm_password']
        user_type = request.form.get('type', 'user')

        # Check if passwords match
        if password != confrim:
            flash('Confirm password is not the same as password.', 'danger')
            return redirect('/register')

        # Check if email already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email is already registered.', 'danger')
            return redirect('/register')

        # Create a new user account
        new_user = User(
            username=username,
            email=email,
            password=password,
            type=user_type
        )

        # Save the new user to the database
        db.session.add(new_user)
        db.session.commit()

        # Staff accounts require admin approval
        if user_type == 'staff':
            flash('Registration successful! Please wait for admin approval.', 'success')
            return redirect('/login')

        # Regular users can log in immediately
        flash('Registration successful! Please log in.', 'success')
        return redirect('/login')

    return render_template('register.html')
#Dashboard
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
    
# -------------Admin--------------
#Dashabord
@app.route('/admin_dashboard')
def admin_dashbaord():
    if 'user_id' not in session:
        return redirect('/login')
    if session.get('role') != 'admin':
        return redirect('/login')

    total_users = User.query.filter_by(type = 'user').count()
    total_staff = User.query.filter_by(type = 'staff').count()
    pending_staff = User.query.filter_by(type = 'staff', is_approved =False).count()
    total_treks = Trek.query.count()
    total_bookings = Booking.query.count()
    recent_bookings = Booking.query.order_by(Booking.id.desc()).limit(7).all()
    
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
    
#Manage User

@app.route('/admin/users')
def admin_users():
    if 'user_id' not in session:
        return redirect('/login')
    if session.get('role') != 'admin':
        return redirect('/login')
    
    search = request.args.get('search','').strip()
    
    if search:
        users = User.query.filter(User.type =='user',
                                  db.or_(
                                      User.username.ilike(f'${search}'),
                                      User.email.ilike(f'${search}'),
                                  )).all()
    else:
        users = User.query.filter_by(
            type='user'
        ).all()
    
    return render_template(
        'admin_users.html',
        users=users,
        search=search
    )

#Manage Staff

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
        ).all()

    return render_template(
        'admin_staff.html',
        staffs=staffs,
        search=search
    )
#View all
@app.route('/admin/all')
def admin_all():

    if 'user_id' not in session:
        return redirect('/login')

    if session.get('role') != 'admin':
        return redirect('/login')

    search = request.args.get('search', '').strip()

    if search:

        us = User.query.filter(
            User.type != 'admin',
            db.or_(
                User.username.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%')
            )
        ).all()

    else:

        us = User.query.filter(
            User.type.in_(['user', 'staff'])
        ).all()

    return render_template(
        'admin_remove.html',
        us=us,
        search=search
    )

#Pedning Staff and  Approve Staff

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

#Blacklist and Unblack

    
@app.route('/admin/blacklist_user/<int:id>')
def blacklist_user(id):

    if 'user_id' not in session:
        return redirect('/login')

    if session.get('role') != 'admin':
        return redirect('/login')

    user = User.query.get_or_404(id)
    user.is_blacklist = True
    db.session.commit()
    flash('User has been blacklisted.', 'warning')
    return redirect('/admin/users')



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


@app.route('/admin/unblacklist_staff/<int:id>')
def unblacklist_staff(id):

    if 'user_id' not in session:
        return redirect('/login')

    if session.get('role') != 'admin':
        return redirect('/login')

    staff = User.query.get_or_404(id)

    staff.is_blacklist = False

    db.session.commit()
    flash('Staff removed from blacklist.', 'success')
    return redirect('/admin/staff')



#View treak

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
        is_approved=True
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

    # Allow only logged-in admins
    if 'user_id' not in session:
        return redirect('/login')

    if session.get('role') != 'admin':
        return redirect('/login')

    if request.method == 'POST':

        # Get form data
        name = request.form['name']
        location = request.form['location']
        difficulty = request.form['difficulty']
        duration = int(request.form['duration'])
        slot = int(request.form['available_slot'])

        start = datetime.strptime(
            request.form['start_date'],
            '%Y-%m-%d'
        ).date()

        end = datetime.strptime(
            request.form['end_date'],
            '%Y-%m-%d'
        ).date()

        # Validate dates
        if end < start:
            flash(
                'End Date cannot be before Start Date.',
                'danger'
            )
            return redirect('/admin/add_trek')

        # Validate available slots
        if slot <= 0:
            flash(
                'Available Slots must be greater than 0.',
                'danger'
            )
            return redirect('/admin/add_trek')

        # Create a new trek
        trek = Trek(
            name=name,
            location=location,
            difficulty=difficulty,
            duration=duration,
            available_slot=slot,
            start_date=start,
            end_date=end
        )

        db.session.add(trek)
        db.session.commit()

        flash(
            'Trek Added Successfully.',
            'success'
        )

        return redirect('/admin/treks')

    return render_template('add_trek.html')


#Edit trek
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
        trek.name = request.form['name']
        trek.location = request.form['location']
        trek.difficulty = request.form['difficulty']
        trek.duration = int(request.form['duration'])
        trek.available_slot = int(request.form['available_slot'])
        staff_id = request.form.get('staff_id',)
        trek.staff_id = int(staff_id) if staff_id else None
        db.session.commit()
        flash('Trek updated successfully.', 'success')
        return redirect('/admin/treks')
    return render_template('edit_trek.html', trek=trek, staffs=staffs)

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
        flash('Cannot delete trek: existing bookings found.', 'warning')
        return redirect('/admin/treks')
    db.session.delete(trek)
    db.session.commit()
    flash('Trek deleted successfully.', 'success')
    return redirect('/admin/treks')

# Staff Routes

@app.route('/staff_dashboard')
def staff_dashboard():

    if 'user_id' not in session:
        return redirect('/login')

    if session.get('role') != 'staff':
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
        Trek.staff_id == session['user_id']
    ).count()

    #  Chart Data

    chart_labels = []
    chart_data = []

    for trek in treks:

        participant_count = Booking.query.filter_by(
            trek_id=trek.id
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

    if request.method == 'POST':

        new_slot = int(request.form['available_slots'])

        if new_slot > trek.available_slot:
            flash('You cannot increase slots assigned by Admin.', 'danger')
            return redirect(request.url)

        trek.available_slot = new_slot
        trek.status = request.form['status']

        # If trek is completed, mark all bookings as completed
        if trek.status == 'Completed':

            bookings = Booking.query.filter_by(
                trek_id=trek.id,
                status='Booked'
            ).all()

            for booking in bookings:
                booking.status = 'Completed'

        db.session.commit()

        flash('Trek details updated.', 'success')
        return redirect('/staff_dashboard')

    bookings = Booking.query.filter_by(
        trek_id=trek.id
    ).all()

    count = Booking.query.filter_by(
        trek_id=trek.id
    ).count()

    return render_template(
        'manage_trek.html',
        trek=trek,
        bookings=bookings,
        count=count
    )    
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
    
# ---------------- USER DASHBOARD ---------------- #
@app.route('/user_dashboard')
def user_dashboard():

    if 'user_id' not in session:
        return redirect('/login')

    if session.get('role') != 'user':
        return redirect('/login')

    # Search & Filters
    search = request.args.get('search', '').strip()
    difficulty = request.args.get('difficulty', '').strip()
    location = request.args.get('location', '').strip()

    query = Trek.query.filter_by(status='Open')

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

    # Dashboard Statistics
    total_bookings = Booking.query.filter_by(
        user_id=session['user_id']
    ).count()

    upcoming_treks = Booking.query.join(Trek).filter(
        Booking.user_id == session['user_id'],
        Trek.status == 'Open'
    ).count()

    available_treks = Trek.query.filter_by(
        status='Open'
    ).count()

    # Charts
    #  Pie Chart 

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

    # Bar Chart 
    trek_labels = []
    participant_data = []

    my_bookings = Booking.query.filter_by(
        user_id=session['user_id']
    ).all()

    for booking in my_bookings:

        trek = Trek.query.get(booking.trek_id)

        if trek:

            participant_count = Booking.query.filter_by(
                trek_id=trek.id
            ).count()

            trek_labels.append(trek.name)
            participant_data.append(participant_count)


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
        booking_date=datetime.today().date()
    )

    db.session.add(new_booking)

    trek.available_slot -= 1

    db.session.commit()

    flash(
        'Booking Successful!',
        'success'
    )

    return redirect('/my_bookings')


@app.route('/my_bookings')
def my_bookings():

    if 'user_id' not in session:
        return redirect('/login')

    bookings = Booking.query.filter_by(
        user_id=session['user_id']
    ).all()

    return render_template(
        'my_bookings.html',
        bookings=bookings
    )
    
@app.route('/trek/<int:trek_id>')
def trek_details(trek_id):

    if 'user_id' not in session:
        return redirect('/login')

    if session.get('role') != 'user':
        return redirect('/login')

    trek = Trek.query.get_or_404(trek_id)

    already_booked = Booking.query.filter_by(
        user_id=session['user_id'],
        trek_id=trek.id,
        status='Booked'
    ).first()

    return render_template(
        'trek_details.html',
        trek=trek,
        already_booked=already_booked
    )
@app.route('/booking/<int:booking_id>')
def booking_details(booking_id):

    if 'user_id' not in session:
        return redirect('/login')

    if session.get('role') != 'user':
        return redirect('/login')

    booking = Booking.query.filter_by(
        id=booking_id,
        user_id=session['user_id']
    ).first_or_404()

    return render_template(
        'booking_details.html',
        booking=booking
    )
@app.route('/cancel_booking/<int:booking_id>')
def cancel_booking(booking_id):

    if 'user_id' not in session:
        return redirect('/login')

    if session.get('role') != 'user':
        return redirect('/login')

    booking = Booking.query.filter_by(
        id=booking_id,
        user_id=session['user_id']
    ).first_or_404()

    if booking.status != 'Booked':
        flash(
            'Booking cannot be cancelled.',
            'warning'
        )
        return redirect('/my_bookings')

    booking.status = 'Cancelled'

    booking.trek.available_slot += 1

    db.session.commit()

    flash(
        'Booking cancelled successfully.',
        'success'
    )

    return redirect('/my_bookings')


# ---------------- ADMIN BOOKING HISTORY ---------------- #

@app.route('/admin/bookings')
def admin_bookings():

    if 'user_id' not in session:
        return redirect('/login')

    if session.get('role') != 'admin':
        return redirect('/login')

    bookings = Booking.query.order_by(
        Booking.booking_date.desc()
    ).all()

    return render_template(
        'admin_bookings.html',
        bookings=bookings
    )
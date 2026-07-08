from flask import render_template, redirect, request, session, url_for, flash
from flask import current_app as app
from .models import *
from .database import db

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
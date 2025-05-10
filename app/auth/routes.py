# app/auth/routes.py
from flask import render_template, redirect, request, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFProtect
from datetime import datetime
import cv2
from . import auth
from .forms import LoginForm, RegistrationForm, RequestResetPasswordForm, ResetPasswordForm
from .models import User, Alert, Farm, FarmImage, SensorData
from .. import db
from ..utils.email import send_email

csrf = CSRFProtect()

@auth.route('/')
def index():
    return render_template('auth/index.html')

@auth.route('/home')
@login_required
def home():
    farms = current_user.farms.all()
    alerts = Alert.query.filter_by(user_id=current_user.id).order_by(Alert.created_at.desc()).limit(5).all()
    return render_template('auth/home.html', farms=farms, alerts=alerts)



@auth.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    if current_user.is_authenticated:
        return redirect(url_for('auth.home'))  # Redirect authenticated user to the home page

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            user.last_login = datetime.utcnow()
            db.session.commit()

            flash('Login successful! Welcome back.', 'success')
            return redirect(url_for('auth.home'))  # Redirect to home view

        # Flash error and suggest password reset
        flash('Invalid email or password. Please try again or '
              '<a href="{}">reset your password</a>.'.format(url_for('auth.reset_password_request')),
              'danger')

    return render_template('auth/home.html', form=form)




@auth.route('/logout')
@login_required
def logout():
    """Handle user logout"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))


@auth.route('/register', methods=['GET', 'POST'])
@csrf.exempt
def register():
    """Handle user registration"""
    if current_user.is_authenticated:
        flash("You're already logged in.", "info")
        return redirect(url_for('auth.home'))

    form = RegistrationForm()
    if form.validate_on_submit():
        # Create new user
        user = User(
            email=form.email.data.lower(),
            username=form.username.data,
            password=form.password.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            phone_number=form.phone_number.data,
            user_type=form.user_type.data,
            is_approved=False  # Default to not approved
        )

        db.session.add(user)
        db.session.commit()

        # Flash registration success message
        flash('Registration successful! Please log in.', 'success')

        # Redirect to login page
        return redirect(url_for('auth.login'))

    return render_template('auth/auth.html', form=form)

@auth.route('/farms')
@login_required
def list_farms():
    farms = current_user.farms.all()
    return render_template('auth/farms.html', farms=farms)

@auth.route('/farm/<int:farm_id>')
@login_required
def view_farm(farm_id):
    farm = Farm.query.get_or_404(farm_id)
    if farm.owner != current_user:
        flash("Unauthorized access", "danger")
        return redirect(url_for('auth.list_farms'))
    return render_template('auth/farm_detail.html', farm=farm)

@auth.route('/farm/<int:farm_id>/upload_image', methods=['GET', 'POST'])
@login_required
def upload_farm_image(farm_id):
    farm = Farm.query.get_or_404(farm_id)
    if farm.owner != current_user:
        flash("Unauthorized access", "danger")
        return redirect(url_for('auth.home'))

    if request.method == 'POST':
        # Replace this with the actual RTSP/HTTP stream URL of the farm camera
        camera_url = "rtsp://camera_ip_address/live"

        cap = cv2.VideoCapture(camera_url)
        success, frame = cap.read()
        cap.release()

        if success:
            timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
            filename = f'farm_{farm_id}_{timestamp}.jpg'
            path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            cv2.imwrite(path, frame)

            new_image = FarmImage(
                filename=filename,
                path=path,
                farm_id=farm.id,
                user_id=current_user.id,
                image_type=request.form.get('image_type', 'live_feed')
            )
            db.session.add(new_image)
            db.session.commit()
            flash("Live image captured from camera and uploaded", "success")
            return redirect(url_for('auth.view_farm', farm_id=farm_id))
        else:
            flash("Failed to capture image from camera", "danger")

    return render_template('auth/upload_image.html', farm=farm)
@auth.route('/farm/<int:farm_id>/sensor')
@login_required
def sensor_data(farm_id):
    farm = Farm.query.get_or_404(farm_id)
    if farm.owner != current_user:
        flash("Unauthorized access", "danger")
        return redirect(url_for('auth.home'))

    data = SensorData.query.filter_by(farm_id=farm_id).order_by(SensorData.timestamp.desc()).all()
    return render_template('auth/sensor_data.html', farm=farm, data=data)

@auth.route('/alerts')
@login_required
def alerts():
    all_alerts = Alert.query.filter_by(user_id=current_user.id).order_by(Alert.created_at.desc()).all()
    return render_template('auth/alerts.html', alerts=all_alerts)

@auth.route('/alert/<int:alert_id>/read', methods=['POST'])
@login_required
def mark_alert_as_read(alert_id):
    alert = Alert.query.get_or_404(alert_id)
    if alert.user_id != current_user.id:
        flash("Unauthorized access", "danger")
        return redirect(url_for('auth.home'))

    alert.is_read = True
    db.session.commit()
    flash("Alert marked as read", "success")
    return redirect(url_for('auth.alerts'))



@auth.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    """Handle password reset request"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RequestResetPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user:
            token = user.generate_reset_token()
            send_email(
                user.email,
                'Reset Your Password',
                'auth/email/reset_password',
                user=user,
                token=token
            )
        flash('An email with instructions to reset your password has been sent to you.', 'info')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password_request.html', form=form)


@auth.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Handle password reset with token"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = ResetPasswordForm()
    if form.validate_on_submit():
        if User.reset_password(token, form.password.data):
            db.session.commit()
            flash('Your password has been updated.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('The reset link is invalid or has expired.', 'danger')
            return redirect(url_for('auth.reset_password_request'))
    
    return render_template('auth/reset_password.html', form=form)


@auth.route('/profile')
@login_required
def profile():
    """Display user profile"""
    return render_template('auth/profile.html')
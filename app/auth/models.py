# app/auth/models.py
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager

class Role(db.Model):
    """Role model for different user types (admin, farmer)"""
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')
    
    def __init__(self, **kwargs):
        super(Role, self).__init__(**kwargs)
        if self.permissions is None:
            self.permissions = 0
    
    @staticmethod
    def insert_roles():
        roles = {
            'Farmer': [Permission.VIEW_DATA, Permission.UPLOAD_DATA],
            'Admin': [Permission.VIEW_DATA, Permission.UPLOAD_DATA, 
                     Permission.APPROVE_USERS, Permission.ADMIN]
        }
        default_role = 'Farmer'
        
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.reset_permissions()
            for perm in roles[r]:
                role.add_permission(perm)
            role.default = (role.name == default_role)
            db.session.add(role)
        db.session.commit()
    
    def add_permission(self, perm):
        if not self.has_permission(perm):
            self.permissions += perm
    
    def remove_permission(self, perm):
        if self.has_permission(perm):
            self.permissions -= perm
    
    def reset_permissions(self):
        self.permissions = 0
    
    def has_permission(self, perm):
        return self.permissions & perm == perm
    
    def __repr__(self):
        return f'<Role {self.name}>'


class Permission:
    """Permissions for different user roles"""
    VIEW_DATA = 1
    UPLOAD_DATA = 2
    APPROVE_USERS = 4
    ADMIN = 8


class User(UserMixin, db.Model):
    """User model for authentication and authorization"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    phone_number = db.Column(db.String(20))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    is_approved = db.Column(db.Boolean, default=False)
    farms = db.relationship('Farm', backref='owner', lazy='dynamic')
    sensor_data = db.relationship('SensorData', backref='user', lazy='dynamic')
    farm_images = db.relationship('FarmImage', backref='user', lazy='dynamic')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == 'admin@farmeye.com':  # Default admin
                self.role = Role.query.filter_by(name='Admin').first()
                self.is_approved = True
            else:
                self.role = Role.query.filter_by(default=True).first()
    
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')
        
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def can(self, perm):
        return self.role is not None and self.role.has_permission(perm)
    
    def is_admin(self):
        return self.can(Permission.ADMIN)
    
    def is_farmer(self):
        return self.role.name == 'Farmer'
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def __repr__(self):
        return f'<User {self.username}>'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# app/farm/models.py
from datetime import datetime
from app import db
import os

class Farm(db.Model):
    """Farm model for storing farm details"""
    __tablename__ = 'farms'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    location = db.Column(db.String(200))
    size_acres = db.Column(db.Float)
    crop_type = db.Column(db.String(100))
    description = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    images = db.relationship('FarmImage', backref='farm', lazy='dynamic')
    sensor_data = db.relationship('SensorData', backref='farm', lazy='dynamic')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, 
                           onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Farm {self.name}>'


class FarmImage(db.Model):
    """Model for storing farm images that will be processed by ML models"""
    __tablename__ = 'farm_images'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255))
    path = db.Column(db.String(255))
    image_type = db.Column(db.String(50))  # e.g., 'soil', 'crop', 'pest'
    processed = db.Column(db.Boolean, default=False)
    processing_results = db.Column(db.Text)  # JSON or text results from ML model
    farm_id = db.Column(db.Integer, db.ForeignKey('farms.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<FarmImage {self.filename}>'


class SensorData(db.Model):
    """Model for storing sensor data from IoT devices"""
    __tablename__ = 'sensor_data'
    
    id = db.Column(db.Integer, primary_key=True)
    sensor_type = db.Column(db.String(50))  # e.g., 'soil_moisture', 'temperature'
    value = db.Column(db.Float)
    unit = db.Column(db.String(20))  # e.g., 'celsius', '%', 'pH'
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    farm_id = db.Column(db.Integer, db.ForeignKey('farms.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    def __repr__(self):
        return f'<SensorData {self.sensor_type}: {self.value} {self.unit}>'


class Alert(db.Model):
    """Model for storing alerts based on sensor data or image analysis"""
    __tablename__ = 'alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    alert_type = db.Column(db.String(50))  # e.g., 'pest_detected', 'low_moisture'
    message = db.Column(db.Text)
    severity = db.Column(db.String(20))  # e.g., 'low', 'medium', 'high'
    is_read = db.Column(db.Boolean, default=False)
    farm_id = db.Column(db.Integer, db.ForeignKey('farms.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Alert {self.alert_type}: {self.severity}>'
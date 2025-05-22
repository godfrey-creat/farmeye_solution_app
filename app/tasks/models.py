from datetime import datetime
from app import db

class TaskCategory(db.Model):
    __tablename__ = 'task_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.Text)
    color = db.Column(db.String(7), nullable=False)  # Hex color code
    icon = db.Column(db.String(32))  # Font Awesome icon name
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship with backref to Task
    tasks = db.relationship('Task', backref=db.backref('category', lazy='joined'), lazy='dynamic')
    
    def __repr__(self):
        return f'<TaskCategory {self.name}>'
    
    def to_dict(self):
        """Convert category to dictionary for API responses"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'color': self.color,
            'icon': self.icon,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def get_default_categories(cls):
        """Get or create default task categories"""
        default_categories = [
            {'name': 'Weeding', 'color': '#28a745', 'icon': 'fa-leaf'},
            {'name': 'Irrigating', 'color': '#007bff', 'icon': 'fa-tint'},
            {'name': 'Land Preparation', 'color': '#6c757d', 'icon': 'fa-tractor'},
            {'name': 'Harvesting', 'color': '#ffc107', 'icon': 'fa-shopping-basket'},
            {'name': 'Pruning', 'color': '#17a2b8', 'icon': 'fa-cut'},
        ]
        
        categories = []
        for cat_data in default_categories:
            category = cls.query.filter_by(name=cat_data['name']).first()
            if not category:
                category = cls(**cat_data)
                db.session.add(category)
            categories.append(category)
        
        db.session.commit()
        return categories

class TaskRecurrence(db.Model):
    __tablename__ = 'task_recurrences'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    recurrence_type = db.Column(db.String(16))  # daily, weekly, monthly, custom
    recurrence_interval = db.Column(db.Integer, default=1)  # every X days/weeks/etc.
    recurrence_days = db.Column(db.String(32))  # for weekly: "0,1,4" (Sun,Mon,Thu)
    recurrence_end_type = db.Column(db.String(16), default='never')  # never, on_date, after_count
    recurrence_end_date = db.Column(db.DateTime)
    recurrence_count = db.Column(db.Integer)  # number of occurrences
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<TaskRecurrence {self.recurrence_type}>'
    
    def to_dict(self):
        """Convert recurrence to dictionary for API responses"""
        return {
            'id': self.id,
            'task_id': self.task_id,
            'recurrence_type': self.recurrence_type,
            'recurrence_interval': self.recurrence_interval,
            'recurrence_days': self.recurrence_days,
            'recurrence_end_type': self.recurrence_end_type,
            'recurrence_end_date': self.recurrence_end_date.isoformat() if self.recurrence_end_date else None,
            'recurrence_count': self.recurrence_count,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class Task(db.Model):
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    task_type = db.Column(db.String(32), nullable=False)  # Weeding, Irrigating, Land Preparation, etc.
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime)
    is_all_day = db.Column(db.Boolean, default=True)
    status = db.Column(db.String(20), default='pending')  # pending, in_progress, completed
    priority = db.Column(db.String(20), default='medium')  # low, medium, high
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign Keys
    farm_id = db.Column(db.Integer, db.ForeignKey('farms.id'), nullable=False)
    field_id = db.Column(db.Integer, db.ForeignKey('fields.id'))
    category_id = db.Column(db.Integer, db.ForeignKey('task_categories.id'))
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relationships
    farm = db.relationship('Farm', backref=db.backref('tasks', lazy='dynamic'))
    field = db.relationship('Field', backref=db.backref('tasks', lazy='dynamic'))
    assignee = db.relationship('User', foreign_keys=[assigned_to], 
                              backref=db.backref('assigned_tasks', lazy='dynamic'))
    creator = db.relationship('User', foreign_keys=[created_by], 
                             backref=db.backref('created_tasks', lazy='dynamic'))
    recurrence = db.relationship('TaskRecurrence', backref='task', uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Task {self.id}: {self.title}>'
    
    def to_dict(self):
        """Convert task to dictionary for API responses"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'task_type': self.task_type,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'is_all_day': self.is_all_day,
            'status': self.status,
            'priority': self.priority,
            'farm_id': self.farm_id,
            'field_id': self.field_id,
            'category_id': self.category_id,
            'assigned_to': self.assigned_to,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'is_recurring': self.recurrence is not None,
            'category': self.category.to_dict() if self.category else None,
            'recurrence': self.recurrence.to_dict() if self.recurrence else None
        }
    
    @staticmethod
    def get_tasks_by_date_range(start_date, end_date, farm_id=None, field_id=None, user_id=None):
        """Get tasks within a date range with optional filters"""
        query = Task.query.filter(
            ((Task.start_date >= start_date) & (Task.start_date <= end_date)) |
            ((Task.end_date >= start_date) & (Task.end_date <= end_date)) |
            ((Task.start_date <= start_date) & (Task.end_date >= end_date))
        )
        
        if farm_id:
            query = query.filter(Task.farm_id == farm_id)
        
        if field_id:
            query = query.filter(Task.field_id == field_id)
            
        if user_id:
            query = query.filter((Task.assigned_to == user_id) | (Task.created_by == user_id))
            
        return query.order_by(Task.start_date).all() 
# scripts/seed_data.py

from app import create_app, db
from app.auth.models import User
from app.farm.models import (
    Farm, SensorData, FarmImage, Alert,
    FarmStage, PestControl, PestAction
)
from datetime import datetime, timedelta
from app.tasks.models import TaskCategory, Task, TaskRecurrence
from app.auth.models import User
from app.farm.models import Farm, Field
from datetime import datetime, timedelta
import random

def seed_data():
    """Add initial seed data to the database"""
    print("Starting database seeding...")

    # Create a test user if none exists
    user = User.query.filter_by(email='test@example.com').first()
    if not user:
        user = User(
            email='test@example.com',
            username='testuser',
            first_name='Test',
            last_name='User',
            password='password123',  # This will be hashed automatically
            phone_number='1234567890',
            user_type='small-scale',
            region='nairobi',
            is_approved=True
        )
        db.session.add(user)
        db.session.commit()
        print("Created test user.")

    # Create a farm if none exists
    farm = Farm.query.filter_by(user_id=user.id).first()
    if not farm:
        farm = Farm(
            name='Green Valley Farm',
            location='-1.286389,36.817223',  # Example coordinates for Nairobi
            size_acres=10.5,
            crop_type='Corn',
            description='A small corn farm in Nairobi',
            user_id=user.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.session.add(farm)
        db.session.commit()
        print("Created farm.")

    # Add farm stage if none exists
    farm_stage = FarmStage.query.filter_by(farm_id=farm.id, status='Active').first()
    if not farm_stage:
        farm_stage = FarmStage(
            farm_id=farm.id,
            stage_name='Vegetative',
            start_date=datetime.utcnow() - timedelta(days=28),
            status='Active',
            description='Vegetative growth phase of corn'
        )
        db.session.add(farm_stage)
        db.session.commit()
        print("Created farm stage.")

    # Add sensor data if none exists
    sensor_data = SensorData.query.filter_by(farm_id=farm.id).first()
    if not sensor_data:
        # Add 20 days of moisture data
        for i in range(20):
            reading_date = datetime.utcnow() - timedelta(days=19-i)
            moisture_value = 60 + (i % 5)  # Values between 60 and 64

            moisture_data = SensorData(
                sensor_type='soil_moisture',
                value=moisture_value,
                unit='%',
                timestamp=reading_date,
                farm_id=farm.id,
                user_id=user.id
            )
            db.session.add(moisture_data)

            # Also add temperature data
            temp_value = 22 + (i % 8)  # Values between 22 and 29
            temp_data = SensorData(
                sensor_type='temperature',
                value=temp_value,
                unit='°C',
                timestamp=reading_date,
                farm_id=farm.id,
                user_id=user.id
            )
            db.session.add(temp_data)

        db.session.commit()
        print("Added sensor data.")

    # Add alerts if none exist
    alerts = Alert.query.filter_by(farm_id=farm.id).all()
    if not alerts:
        alert1 = Alert(
            farm_id=farm.id,
            user_id=user.id,
            created_at=datetime.utcnow() - timedelta(hours=2),
            alert_type='Pest Detection',
            message='Corn earworm detected in sector 4. Immediate action recommended to prevent crop damage.',
            status='Active',
            severity='High',
            is_read=False
        )
        db.session.add(alert1)

        alert2 = Alert(
            farm_id=farm.id,
            user_id=user.id,
            created_at=datetime.utcnow() - timedelta(hours=4),
            alert_type='Irrigation Needed',
            message='Moisture levels dropping in sector 2. Schedule irrigation within the next 24 hours.',
            status='Active',
            severity='Medium',
            is_read=False
        )
        db.session.add(alert2)

        alert3 = Alert(
            farm_id=farm.id,
            user_id=user.id,
            created_at=datetime.utcnow() - timedelta(hours=12),
            alert_type='Weather Advisory',
            message='Heavy rain expected in 36 hours. Consider delaying fertilizer application until after rainfall.',
            status='Active',
            severity='Low',
            is_read=False
        )
        db.session.add(alert3)

        db.session.commit()
        print("Added alerts.")

    # Add pest detections if none exist
    pest_detections = PestControl.query.filter_by(farm_id=farm.id).all()
    if not pest_detections:
        pest = PestControl(
            farm_id=farm.id,
            pest_name='Corn Earworm',
            detection_date=datetime.utcnow() - timedelta(days=1),
            severity='High',
            location_in_farm='Sector 4',
            description='Multiple corn earworm larvae detected on corn ears.',
            status='Active',
            detected_by='Manual'
        )
        db.session.add(pest)
        db.session.commit()

        # Add a pest action
        action = PestAction(
            pest_control_id=pest.id,
            action_type='Chemical',
            action_name='Apply Organic Pesticide',
            description='Apply BT spray to affected areas.',
            scheduled_date=datetime.utcnow() + timedelta(days=1),
            status='Scheduled',
            user_id=user.id
        )
        db.session.add(action)
        db.session.commit()
        print("Added pest detection and action.")

    print("Database seeding completed successfully!")

def seed_task_categories():
    """Create default task categories"""
    return TaskCategory.get_default_categories()

def seed_sample_tasks(num_tasks=10):
    """Create sample tasks for testing"""
    # Get users, farms, and fields
    users = User.query.all()
    if not users:
        print("No users found. Please run user seeding first.")
        return
        
    farms = Farm.query.all()
    if not farms:
        print("No farms found. Please run farm seeding first.")
        return
    
    categories = seed_task_categories()
    
    # Task types corresponding to categories
    task_types = [cat.name for cat in categories]
    
    # Status options
    statuses = ['pending', 'in_progress', 'completed']
    priorities = ['low', 'medium', 'high']
    
    # Create random tasks
    for i in range(num_tasks):
        # Select random farm and user
        farm = random.choice(farms)
        user = random.choice(users)
        
        # Get fields for this farm
        fields = Field.query.filter_by(farm_id=farm.id).all()
        field = random.choice(fields) if fields else None
        
        # Set random dates within next 30 days
        start_days_offset = random.randint(1, 30)
        duration_days = random.randint(0, 3)
        
        start_date = datetime.utcnow() + timedelta(days=start_days_offset)
        end_date = start_date + timedelta(days=duration_days) if duration_days > 0 else None
        
        # Select random task type and category
        task_type_index = random.randint(0, len(task_types) - 1)
        task_type = task_types[task_type_index]
        category = categories[task_type_index]
        
        # Create task
        task = Task(
            title=f"{task_type} - {'Farm' if not field else field.name}",
            description=f"Sample {task_type.lower()} task for testing.",
            task_type=task_type,
            start_date=start_date,
            end_date=end_date,
            is_all_day=bool(random.randint(0, 1)),
            status=random.choice(statuses),
            priority=random.choice(priorities),
            farm_id=farm.id,
            field_id=field.id if field else None,
            category_id=category.id,
            assigned_to=user.id,
            created_by=user.id
        )
        
        db.session.add(task)
        
        # Add recurrence for some tasks
        if random.random() < 0.3:  # 30% chance of recurring
            recurrence = TaskRecurrence(
                recurrence_type=random.choice(['daily', 'weekly', 'monthly']),
                recurrence_interval=random.randint(1, 3),
                recurrence_days=','.join([str(d) for d in random.sample(range(7), k=random.randint(1, 3))]) if random.random() < 0.5 else None,
                recurrence_end_type=random.choice(['never', 'on_date', 'after_count']),
                recurrence_end_date=datetime.utcnow() + timedelta(days=90) if random.random() < 0.5 else None,
                recurrence_count=random.randint(5, 20) if random.random() < 0.5 else None
            )
            task.recurrence = recurrence
    
    db.session.commit()
    print(f"Created {num_tasks} sample tasks.")


# Run this function when the script is executed directly
if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        seed_data()
        seed_task_categories()
        seed_sample_tasks(20)

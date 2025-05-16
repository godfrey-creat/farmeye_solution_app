# scripts/seed_data.py

from app import create_app, db
from app.auth.models import User
from app.farm.models import (
    Farm, SensorData, FarmImage, Alert,
    FarmStage, PestControl, PestAction
)
from datetime import datetime, timedelta

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

# Run this function when the script is executed directly
if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        seed_data()
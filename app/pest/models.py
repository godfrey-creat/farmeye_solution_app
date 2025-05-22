from datetime import datetime
from app import db

class GrowthStage(db.Model):
    __tablename__ = 'growth_stages'
    
    id = db.Column(db.Integer, primary_key=True)
    farm_id = db.Column(db.Integer, db.ForeignKey('farms.id'), nullable=False)
    stage_name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    recommended_tasks = db.Column(db.Text)  # JSON string of recommended tasks
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship with Farm
    farm = db.relationship('Farm', backref='growth_stages', lazy=True)
    
    def get_recommended_tasks(self):
        """Get recommended tasks for this growth stage"""
        if not self.recommended_tasks:
            return []
        try:
            import json
            return json.loads(self.recommended_tasks)
        except:
            return []
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'farm_id': self.farm_id,
            'stage_name': self.stage_name,
            'description': self.description,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'notes': self.notes,
            'recommended_tasks': self.get_recommended_tasks(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<GrowthStage {self.stage_name} for Farm {self.farm_id}>' 
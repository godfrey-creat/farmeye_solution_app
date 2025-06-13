from app import db

class AdvisoryRecommendation(db.Model):
    __tablename__ = 'advisory_recommendations'
    id = db.Column(db.Integer, primary_key=True)
    farm_id = db.Column(db.Integer, db.ForeignKey('farm.id'), nullable=False)
    action = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(32), default='Medium')
    due = db.Column(db.String(64))
    reasoning = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    def __repr__(self):
        return f"<AdvisoryRecommendation {self.action} (Farm {self.farm_id})>"
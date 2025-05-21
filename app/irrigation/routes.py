from flask import render_template, jsonify, request
from flask_login import login_required
from datetime import datetime, timedelta
import random  # For demo data, replace with actual sensor data in production

from app.irrigation import irrigation  # Import the blueprint instead of creating it


@irrigation.route("/dashboard")
@login_required
def dashboard():
    return render_template("irrigation/dashboard.html", active_page="irrigation")


@irrigation.route("/api/water-usage")
@login_required
def water_usage():
    # Demo data - replace with actual database queries
    today_usage = random.randint(2000, 3000)
    last_week = random.randint(2200, 2800)
    change = ((today_usage - last_week) / last_week) * 100

    return jsonify(
        {
            "today": today_usage,
            "change": round(change, 1),
            "trend": "down" if change < 0 else "up",
        }
    )


@irrigation.route("/api/zones")
@login_required
def get_zones():
    # Demo data - replace with database queries
    zones = [
        {
            "id": 1,
            "name": "Wheat Field",
            "status": "active",
            "moisture": 68,
            "last_watered": "2h ago",
        },
        {
            "id": 2,
            "name": "Vegetable Garden",
            "status": "scheduled",
            "moisture": 52,
            "last_watered": "1d ago",
        },
        {
            "id": 3,
            "name": "Corn Field",
            "status": "inactive",
            "moisture": 70,
            "last_watered": "6h ago",
        },
    ]
    return jsonify(zones)


@irrigation.route("/api/schedule")
@login_required
def get_schedule():
    # Demo data - replace with database queries
    now = datetime.now()
    schedule = [
        {
            "zone_id": 3,
            "zone_name": "Corn Field",
            "type": "Irrigation",
            "scheduled_time": (now + timedelta(days=1))
            .replace(hour=6, minute=0)
            .isoformat(),
        },
        {
            "zone_id": 2,
            "zone_name": "Vegetable Garden",
            "type": "Maintenance",
            "scheduled_time": (now + timedelta(days=1))
            .replace(hour=14, minute=0)
            .isoformat(),
        },
        {
            "zone_id": 1,
            "zone_name": "Wheat Field",
            "type": "Irrigation",
            "scheduled_time": (now + timedelta(days=2))
            .replace(hour=7, minute=0)
            .isoformat(),
        },
    ]
    return jsonify(schedule)


@irrigation.route("/api/metrics")
@login_required
def get_metrics():
    # Demo data - replace with actual calculations
    return jsonify(
        {"water_efficiency": 92, "cost_per_gallon": 0.015, "coverage_rating": 95}
    )


@irrigation.route("/api/schedule", methods=["POST"])
@login_required
def create_schedule():
    data = request.json
    # TODO: Implement schedule creation logic
    return jsonify({"status": "success", "message": "Schedule created"})

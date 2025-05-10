from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from . import pest
from ..farm.models import Farm, PestControl, PestAction, FarmStage, LaborTask
from .. import db
from datetime import datetime

@pest.route('/dashboard')
@login_required
def dashboard():
    """Pest control dashboard"""
    farm = Farm.query.filter_by(user_id=current_user.id).first()
    
    if not farm:
        flash('Please add a farm first', 'warning')
        return redirect(url_for('main.index'))
    
    # Get pest detections for this farm
    pest_detections = PestControl.query.filter_by(farm_id=farm.id).order_by(PestControl.detection_date.desc()).all()
    
    # Get farm stages
    farm_stages = FarmStage.query.filter_by(farm_id=farm.id).order_by(FarmStage.start_date.desc()).all()
    
    # Get recent pest actions
    recent_actions = PestAction.query.join(PestControl).filter(
        PestControl.farm_id == farm.id
    ).order_by(PestAction.scheduled_date.desc()).limit(5).all()
    
    # Common pests based on the crop type (this would typically come from a database or API)
    common_pests = get_common_pests_for_crop(farm.crop_type)
    
    return render_template('dashboard/pest_control.html',
                          farm=farm,
                          pest_detections=pest_detections,
                          farm_stages=farm_stages,
                          recent_actions=recent_actions,
                          common_pests=common_pests,
                          active_page='pest_control')

@pest.route('/add_pest_detection', methods=['POST'])
@login_required
def add_pest_detection():
    """Add a new pest detection"""
    farm = Farm.query.filter_by(user_id=current_user.id).first()
    
    if not farm:
        flash('Please add a farm first', 'warning')
        return redirect(url_for('main.index'))
    
    pest_name = request.form.get('pest_name')
    severity = request.form.get('severity', 'Medium')
    location_in_farm = request.form.get('location_in_farm', '')
    description = request.form.get('description', '')
    
    if not pest_name:
        flash('Pest name is required', 'error')
        return redirect(url_for('pest.dashboard'))
    
    new_detection = PestControl(
        farm_id=farm.id,
        pest_name=pest_name,
        severity=severity,
        location_in_farm=location_in_farm,
        description=description,
        status='Active',
        detected_by='Manual'
    )
    
    db.session.add(new_detection)
    db.session.commit()
    
    flash(f'Pest detection for {pest_name} has been added', 'success')
    return redirect(url_for('pest.dashboard'))

@pest.route('/add_pest_action/<int:pest_id>', methods=['POST'])
@login_required
def add_pest_action(pest_id):
    """Add a new action for a pest detection"""
    pest_detection = PestControl.query.get_or_404(pest_id)
    farm = Farm.query.get_or_404(pest_detection.farm_id)
    
    # Verify ownership
    if farm.user_id != current_user.id:
        flash('Unauthorized access', 'error')
        return redirect(url_for('main.index'))
    
    action_name = request.form.get('action_name')
    action_type = request.form.get('action_type')
    description = request.form.get('description', '')
    scheduled_date_str = request.form.get('scheduled_date')
    
    if not action_name or not action_type:
        flash('Action name and type are required', 'error')
        return redirect(url_for('pest.dashboard'))
    
    # Parse scheduled date if provided
    scheduled_date = None
    if scheduled_date_str:
        try:
            scheduled_date = datetime.strptime(scheduled_date_str, '%Y-%m-%d')
        except ValueError:
            flash('Invalid date format', 'error')
            return redirect(url_for('pest.dashboard'))
    
    new_action = PestAction(
        pest_control_id=pest_id,
        action_name=action_name,
        action_type=action_type,
        description=description,
        scheduled_date=scheduled_date,
        status='Scheduled',
        user_id=current_user.id
    )
    
    db.session.add(new_action)
    db.session.commit()
    
    flash(f'Action "{action_name}" has been scheduled', 'success')
    return redirect(url_for('pest.dashboard'))

@pest.route('/update_farm_stage', methods=['POST'])
@login_required
def update_farm_stage():
    """Update or add a farm stage"""
    farm = Farm.query.filter_by(user_id=current_user.id).first()
    
    if not farm:
        flash('Please add a farm first', 'warning')
        return redirect(url_for('main.index'))
    
    stage_name = request.form.get('stage_name')
    description = request.form.get('description', '')
    
    if not stage_name:
        flash('Stage name is required', 'error')
        return redirect(url_for('pest.dashboard'))
    
    # Check if there's an active stage
    active_stage = FarmStage.query.filter_by(farm_id=farm.id, status='Active').first()
    
    # If an active stage exists, mark it as completed
    if active_stage:
        active_stage.status = 'Completed'
        active_stage.end_date = datetime.utcnow()
    
    # Create a new stage
    new_stage = FarmStage(
        farm_id=farm.id,
        stage_name=stage_name,
        description=description,
        status='Active'
    )
    
    db.session.add(new_stage)
    db.session.commit()
    
    flash(f'Farm stage updated to {stage_name}', 'success')
    return redirect(url_for('pest.dashboard'))

@pest.route('/add_labor_task', methods=['POST'])
@login_required
def add_labor_task():
    """Add a new labor task"""
    farm = Farm.query.filter_by(user_id=current_user.id).first()
    
    if not farm:
        flash('Please add a farm first', 'warning')
        return redirect(url_for('main.index'))
    
    task_name = request.form.get('task_name')
    description = request.form.get('description', '')
    assigned_to = request.form.get('assigned_to', '')
    priority = request.form.get('priority', 'Medium')
    stage_id = request.form.get('stage_id')
    
    if not task_name:
        flash('Task name is required', 'error')
        return redirect(url_for('pest.dashboard'))
    
    new_task = LaborTask(
        farm_id=farm.id,
        task_name=task_name,
        description=description,
        assigned_to=assigned_to,
        priority=priority,
        status='Pending'
    )
    
    if stage_id and stage_id.isdigit():
        stage = FarmStage.query.get(int(stage_id))
        if stage and stage.farm_id == farm.id:
            new_task.stage_id = int(stage_id)
    
    db.session.add(new_task)
    db.session.commit()
    
    flash(f'Labor task "{task_name}" has been added', 'success')
    return redirect(url_for('pest.dashboard'))

def get_common_pests_for_crop(crop_type):
    """Get common pests for a specific crop type
    This would typically query a database or API, but we'll use a simple lookup for now
    """
    pest_lookup = {
        'Corn': [
            {'name': 'Corn Earworm', 'severity': 'High', 'image': 'corn_earworm.jpg', 'description': 'Attacks corn ears and kernels, causing significant damage to yield.'},
            {'name': 'European Corn Borer', 'severity': 'High', 'image': 'corn_borer.jpg', 'description': 'Bores into stalks, disrupting water and nutrient transport.'},
            {'name': 'Corn Rootworm', 'severity': 'Medium', 'image': 'rootworm.jpg', 'description': 'Damages root systems, leading to lodging and reduced uptake of nutrients.'},
            {'name': 'Armyworm', 'severity': 'Medium', 'image': 'armyworm.jpg', 'description': 'Feeds on foliage, can rapidly defoliate plants.'}
        ],
        'Wheat': [
            {'name': 'Hessian Fly', 'severity': 'High', 'image': 'hessian_fly.jpg', 'description': 'Damages stems, causing plants to break and lodge.'},
            {'name': 'Wheat Stem Sawfly', 'severity': 'Medium', 'image': 'sawfly.jpg', 'description': 'Larvae bore into stems, weakening plants and causing lodging.'},
            {'name': 'Aphids', 'severity': 'Medium', 'image': 'aphids.jpg', 'description': 'Suck plant sap and can transmit viral diseases.'}
        ],
        'Soybean': [
            {'name': 'Soybean Aphid', 'severity': 'Medium', 'image': 'soybean_aphid.jpg', 'description': 'Sucks plant sap, reducing vigor and yield.'},
            {'name': 'Bean Leaf Beetle', 'severity': 'Medium', 'image': 'bean_beetle.jpg', 'description': 'Feeds on leaves, pods, and can transmit bean pod mottle virus.'},
            {'name': 'Soybean Cyst Nematode', 'severity': 'High', 'image': 'cyst_nematode.jpg', 'description': 'Damages roots, reducing water and nutrient uptake.'}
        ],
        'Rice': [
            {'name': 'Rice Water Weevil', 'severity': 'High', 'image': 'rice_weevil.jpg', 'description': 'Larvae feed on roots, reducing yield and plant vigor.'},
            {'name': 'Rice Stem Borer', 'severity': 'High', 'image': 'stem_borer.jpg', 'description': 'Bores into stems, causing "whitehead" and empty panicles.'},
            {'name': 'Rice Leafhopper', 'severity': 'Medium', 'image': 'leafhopper.jpg', 'description': 'Sucks sap and can transmit viral diseases.'}
        ],
        'Cotton': [
            {'name': 'Boll Weevil', 'severity': 'High', 'image': 'boll_weevil.jpg', 'description': 'Damages cotton bolls, severely reducing yield.'},
            {'name': 'Cotton Aphid', 'severity': 'Medium', 'image': 'cotton_aphid.jpg', 'description': 'Sucks plant sap and produces honeydew that leads to sooty mold.'},
            {'name': 'Pink Bollworm', 'severity': 'High', 'image': 'pink_bollworm.jpg', 'description': 'Larvae feed inside bolls, damaging lint and seeds.'}
        ]
    }
    
    # Default pests if crop type not found in our lookup
    default_pests = [
        {'name': 'Aphids', 'severity': 'Medium', 'image': 'aphids.jpg', 'description': 'Common sap-sucking pests that affect many crops.'},
        {'name': 'Spider Mites', 'severity': 'Medium', 'image': 'spider_mites.jpg', 'description': 'Tiny pests that cause stippling and yellowing of leaves.'},
        {'name': 'Caterpillars', 'severity': 'High', 'image': 'caterpillars.jpg', 'description': 'Voracious leaf-eaters that can quickly defoliate plants.'},
        {'name': 'Thrips', 'severity': 'Low', 'image': 'thrips.jpg', 'description': 'Small insects that damage leaves and flowers by scraping surface cells.'}
    ]
    
    return pest_lookup.get(crop_type, default_pests) 
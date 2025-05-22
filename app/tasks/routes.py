from flask import jsonify, request, current_app, abort
from flask_login import login_required, current_user
from app import db
from app.tasks import task
from app.tasks.models import Task, TaskCategory, TaskRecurrence
from app.farm.models import Farm, Field
from app.decorators import require_farm_registration
from datetime import datetime, timedelta
import json

# Utility functions
def parse_date_param(date_str, default=None):
    """Parse date string from request parameters"""
    if not date_str:
        return default
    try:
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except ValueError:
        return default

# Task CRUD operations
@task.route('/api/tasks', methods=['GET'])
@login_required
@require_farm_registration
def get_tasks():
    """Get tasks for the current user's farms with filtering options"""
    # Parse filter parameters
    start_date = parse_date_param(request.args.get('start_date'), 
                                  default=datetime.utcnow() - timedelta(days=7))
    end_date = parse_date_param(request.args.get('end_date'), 
                               default=datetime.utcnow() + timedelta(days=30))
    farm_id = request.args.get('farm_id', type=int)
    field_id = request.args.get('field_id', type=int)
    status = request.args.get('status')
    task_type = request.args.get('task_type')
    category_id = request.args.get('category_id', type=int)
    
    # Start with base query
    query = Task.query
    
    # Apply date range filter
    query = query.filter(
        ((Task.start_date >= start_date) & (Task.start_date <= end_date)) |
        ((Task.end_date >= start_date) & (Task.end_date <= end_date)) |
        ((Task.start_date <= start_date) & (Task.end_date >= end_date))
    )
    
    # Apply user permissions filter - only show tasks for farms user has access to
    farms_query = Farm.query.filter_by(user_id=current_user.id)
    farm_ids = [farm.id for farm in farms_query.all()]
    
    if farm_id and farm_id in farm_ids:
        # Filter by specific farm if requested
        query = query.filter(Task.farm_id == farm_id)
    else:
        # Otherwise filter to only show tasks from user's farms
        query = query.filter(Task.farm_id.in_(farm_ids))
    
    # Apply additional filters if provided
    if field_id:
        query = query.filter(Task.field_id == field_id)
    
    if status:
        query = query.filter(Task.status == status)
    
    if task_type:
        query = query.filter(Task.task_type == task_type)
    
    if category_id:
        query = query.filter(Task.category_id == category_id)
    
    # Order by start date
    tasks = query.order_by(Task.start_date).all()
    
    # Format response
    return jsonify({
        'status': 'success',
        'count': len(tasks),
        'tasks': [task.to_dict() for task in tasks]
    })

@task.route('/api/tasks', methods=['POST'])
@login_required
@require_farm_registration
def create_task():
    """Create a new task"""
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['title', 'start_date', 'task_type', 'farm_id']
    for field in required_fields:
        if field not in data:
            return jsonify({'status': 'error', 'message': f'Missing required field: {field}'}), 400
    
    # Validate farm permission
    farm = Farm.query.get(data['farm_id'])
    if not farm or farm.user_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'Farm not found or access denied'}), 403
    
    # Parse dates
    try:
        start_date = datetime.fromisoformat(data['start_date'].replace('Z', '+00:00'))
        end_date = None
        if 'end_date' in data and data['end_date']:
            end_date = datetime.fromisoformat(data['end_date'].replace('Z', '+00:00'))
    except ValueError:
        return jsonify({'status': 'error', 'message': 'Invalid date format'}), 400
    
    # Create new task
    new_task = Task(
        title=data['title'],
        description=data.get('description', ''),
        task_type=data['task_type'],
        start_date=start_date,
        end_date=end_date,
        is_all_day=data.get('is_all_day', True),
        status=data.get('status', 'pending'),
        priority=data.get('priority', 'medium'),
        farm_id=data['farm_id'],
        field_id=data.get('field_id'),
        category_id=data.get('category_id'),
        assigned_to=data.get('assigned_to', current_user.id),
        created_by=current_user.id
    )
    
    db.session.add(new_task)
    
    # Handle recurrence if specified
    if 'recurrence' in data and data['recurrence']:
        recurrence_data = data['recurrence']
        recurrence = TaskRecurrence(
            recurrence_type=recurrence_data.get('recurrence_type', 'daily'),
            recurrence_interval=recurrence_data.get('recurrence_interval', 1),
            recurrence_days=recurrence_data.get('recurrence_days'),
            recurrence_end_type=recurrence_data.get('recurrence_end_type', 'never'),
            recurrence_count=recurrence_data.get('recurrence_count')
        )
        
        # Parse recurrence end date if provided
        if 'recurrence_end_date' in recurrence_data and recurrence_data['recurrence_end_date']:
            try:
                recurrence.recurrence_end_date = datetime.fromisoformat(
                    recurrence_data['recurrence_end_date'].replace('Z', '+00:00')
                )
            except ValueError:
                pass  # Use default if invalid
        
        new_task.recurrence = recurrence
    
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': 'Task created successfully',
        'task': new_task.to_dict()
    }), 201

@task.route('/api/tasks/<int:task_id>', methods=['GET'])
@login_required
def get_task(task_id):
    """Get a specific task by ID"""
    task = Task.query.get_or_404(task_id)
    
    # Verify permission (user owns the farm)
    farm = Farm.query.get(task.farm_id)
    if not farm or farm.user_id != current_user.id:
        abort(403)
    
    return jsonify({
        'status': 'success',
        'task': task.to_dict()
    })

@task.route('/api/tasks/<int:task_id>', methods=['PUT'])
@login_required
def update_task(task_id):
    """Update an existing task"""
    task_obj = Task.query.get_or_404(task_id)
    
    # Verify permission (user owns the farm)
    farm = Farm.query.get(task_obj.farm_id)
    if not farm or farm.user_id != current_user.id:
        abort(403)
    
    data = request.get_json()
    
    # Update basic fields
    if 'title' in data:
        task_obj.title = data['title']
    
    if 'description' in data:
        task_obj.description = data['description']
    
    if 'task_type' in data:
        task_obj.task_type = data['task_type']
    
    if 'status' in data:
        task_obj.status = data['status']
    
    if 'priority' in data:
        task_obj.priority = data['priority']
    
    if 'is_all_day' in data:
        task_obj.is_all_day = data['is_all_day']
    
    if 'category_id' in data:
        task_obj.category_id = data['category_id']
    
    if 'field_id' in data:
        # Validate field belongs to the farm
        if data['field_id']:
            field = Field.query.get(data['field_id'])
            if not field or field.farm_id != task_obj.farm_id:
                return jsonify({'status': 'error', 'message': 'Invalid field ID'}), 400
        task_obj.field_id = data['field_id']
    
    if 'assigned_to' in data:
        task_obj.assigned_to = data['assigned_to']
    
    # Update dates
    if 'start_date' in data:
        try:
            task_obj.start_date = datetime.fromisoformat(data['start_date'].replace('Z', '+00:00'))
        except ValueError:
            return jsonify({'status': 'error', 'message': 'Invalid start date format'}), 400
    
    if 'end_date' in data:
        if data['end_date']:
            try:
                task_obj.end_date = datetime.fromisoformat(data['end_date'].replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'status': 'error', 'message': 'Invalid end date format'}), 400
        else:
            task_obj.end_date = None
    
    # Update recurrence if provided
    if 'recurrence' in data:
        if data['recurrence']:
            recurrence_data = data['recurrence']
            
            # Create or update recurrence
            if not task_obj.recurrence:
                task_obj.recurrence = TaskRecurrence()
            
            task_obj.recurrence.recurrence_type = recurrence_data.get('recurrence_type', 'daily')
            task_obj.recurrence.recurrence_interval = recurrence_data.get('recurrence_interval', 1)
            task_obj.recurrence.recurrence_days = recurrence_data.get('recurrence_days')
            task_obj.recurrence.recurrence_end_type = recurrence_data.get('recurrence_end_type', 'never')
            task_obj.recurrence.recurrence_count = recurrence_data.get('recurrence_count')
            
            # Parse recurrence end date if provided
            if 'recurrence_end_date' in recurrence_data:
                if recurrence_data['recurrence_end_date']:
                    try:
                        task_obj.recurrence.recurrence_end_date = datetime.fromisoformat(
                            recurrence_data['recurrence_end_date'].replace('Z', '+00:00')
                        )
                    except ValueError:
                        pass  # Use existing if invalid
                else:
                    task_obj.recurrence.recurrence_end_date = None
        else:
            # Remove recurrence if set to null/false
            if task_obj.recurrence:
                db.session.delete(task_obj.recurrence)
    
    # Save changes
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': 'Task updated successfully',
        'task': task_obj.to_dict()
    })

@task.route('/api/tasks/<int:task_id>', methods=['DELETE'])
@login_required
def delete_task(task_id):
    """Delete a task"""
    task_obj = Task.query.get_or_404(task_id)
    
    # Verify permission (user owns the farm)
    farm = Farm.query.get(task_obj.farm_id)
    if not farm or farm.user_id != current_user.id:
        abort(403)
    
    db.session.delete(task_obj)
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': 'Task deleted successfully'
    })

# Add these routes to app/tasks/routes.py

@task.route('/api/task-categories', methods=['GET'])
@login_required
def get_task_categories():
    """Get all task categories"""
    categories = TaskCategory.query.all()
    
    return jsonify({
        'status': 'success',
        'categories': [category.to_dict() for category in categories]
    })

@task.route('/api/task-categories', methods=['POST'])
@login_required
def create_task_category():
    """Create a new task category"""
    data = request.get_json()
    
    # Validate required fields
    if not data.get('name') or not data.get('color'):
        return jsonify({'status': 'error', 'message': 'Name and color are required'}), 400
    
    # Check for duplicate names
    existing = TaskCategory.query.filter_by(name=data['name']).first()
    if existing:
        return jsonify({'status': 'error', 'message': 'Category with this name already exists'}), 400
    
    # Create new category
    new_category = TaskCategory(
        name=data['name'],
        color=data['color'],
        description=data.get('description', ''),
        icon=data.get('icon', '')
    )
    
    db.session.add(new_category)
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': 'Category created successfully',
        'category': new_category.to_dict()
    }), 201

@task.route('/api/task-categories/<int:category_id>', methods=['PUT'])
@login_required
def update_task_category(category_id):
    """Update a task category"""
    category = TaskCategory.query.get_or_404(category_id)
    data = request.get_json()
    
    # Update fields if provided
    if 'name' in data:
        # Check for duplicate names
        existing = TaskCategory.query.filter_by(name=data['name']).first()
        if existing and existing.id != category_id:
            return jsonify({'status': 'error', 'message': 'Category with this name already exists'}), 400
        category.name = data['name']
    
    if 'color' in data:
        category.color = data['color']
    
    if 'description' in data:
        category.description = data['description']
    
    if 'icon' in data:
        category.icon = data['icon']
    
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': 'Category updated successfully',
        'category': category.to_dict()
    })

@task.route('/api/task-categories/<int:category_id>', methods=['DELETE'])
@login_required
def delete_task_category(category_id):
    """Delete a task category"""
    category = TaskCategory.query.get_or_404(category_id)
    
    # Check if category is in use
    tasks_using_category = Task.query.filter_by(category_id=category_id).count()
    if tasks_using_category > 0:
        return jsonify({
            'status': 'error', 
            'message': f'Cannot delete category that is used by {tasks_using_category} tasks'
        }), 400
    
    db.session.delete(category)
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': 'Category deleted successfully'
    })

# Add these routes to app/tasks/routes.py

@task.route('/api/tasks/upcoming', methods=['GET'])
@login_required
@require_farm_registration
def get_upcoming_tasks():
    """Get upcoming tasks for dashboard display"""
    # Get farm IDs for current user
    farms_query = Farm.query.filter_by(user_id=current_user.id)
    farm_ids = [farm.id for farm in farms_query.all()]
    
    # Number of days to look ahead
    days = request.args.get('days', default=7, type=int)
    
    # Get upcoming tasks
    start_date = datetime.utcnow()
    end_date = start_date + timedelta(days=days)
    
    tasks = Task.query.filter(
        Task.farm_id.in_(farm_ids),
        Task.start_date >= start_date,
        Task.start_date <= end_date,
        Task.status != 'completed'
    ).order_by(Task.start_date).all()
    
    return jsonify({
        'status': 'success',
        'days_ahead': days,
        'count': len(tasks),
        'tasks': [task.to_dict() for task in tasks]
    })

@task.route('/api/tasks/statistics', methods=['GET'])
@login_required
@require_farm_registration
def get_task_statistics():
    """Get task statistics for dashboard"""
    # Get farm IDs for current user
    farm_id = request.args.get('farm_id', type=int)
    
    # Filter by farm if specified, otherwise use all user's farms
    if farm_id:
        farm = Farm.query.get(farm_id)
        if not farm or farm.user_id != current_user.id:
            return jsonify({'status': 'error', 'message': 'Farm not found or access denied'}), 403
        farm_ids = [farm_id]
    else:
        farms_query = Farm.query.filter_by(user_id=current_user.id)
        farm_ids = [farm.id for farm in farms_query.all()]
    
    # Date ranges
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)
    next_week_end = today + timedelta(days=7)
    
    # Get task counts by status
    pending_count = Task.query.filter(
        Task.farm_id.in_(farm_ids),
        Task.status == 'pending'
    ).count()
    
    in_progress_count = Task.query.filter(
        Task.farm_id.in_(farm_ids),
        Task.status == 'in_progress'
    ).count()
    
    completed_count = Task.query.filter(
        Task.farm_id.in_(farm_ids),
        Task.status == 'completed'
    ).count()
    
    # Tasks due today
    due_today_count = Task.query.filter(
        Task.farm_id.in_(farm_ids),
        Task.start_date >= today,
        Task.start_date < tomorrow,
        Task.status != 'completed'
    ).count()
    
    # Tasks due this week
    due_this_week_count = Task.query.filter(
        Task.farm_id.in_(farm_ids),
        Task.start_date >= tomorrow,
        Task.start_date < next_week_end,
        Task.status != 'completed'
    ).count()
    
    # Tasks by type (for pie chart)
    task_types_query = db.session.query(
        Task.task_type, 
        db.func.count(Task.id)
    ).filter(
        Task.farm_id.in_(farm_ids)
    ).group_by(Task.task_type).all()
    
    task_types = [{'name': task_type, 'count': count} for task_type, count in task_types_query]
    
    # Return statistics
    return jsonify({
        'status': 'success',
        'counts': {
            'pending': pending_count,
            'in_progress': in_progress_count,
            'completed': completed_count,
            'total': pending_count + in_progress_count + completed_count,
            'due_today': due_today_count,
            'due_this_week': due_this_week_count
        },
        'task_types': task_types
    })

# Add these routes to app/tasks/routes.py

@task.route('/api/growth-stages', methods=['GET'])
@login_required
@require_farm_registration
def get_growth_stages():
    """Get growth stages for a farm or all user farms"""
    from app.pest.models import GrowthStage  # Import here to avoid circular imports
    
    farm_id = request.args.get('farm_id', type=int)
    
    # Verify permissions
    if farm_id:
        farm = Farm.query.get(farm_id)
        if not farm or farm.user_id != current_user.id:
            return jsonify({'status': 'error', 'message': 'Farm not found or access denied'}), 403
        
        # Get growth stages for specified farm
        stages = GrowthStage.query.filter_by(farm_id=farm_id).all()
    else:
        # Get farms user has access to
        farms = Farm.query.filter_by(user_id=current_user.id).all()
        farm_ids = [farm.id for farm in farms]
        
        # Get growth stages for all user's farms
        stages = GrowthStage.query.filter(GrowthStage.farm_id.in_(farm_ids)).all()
    
    # Format response
    formatted_stages = []
    for stage in stages:
        stage_dict = {
            'id': stage.id,
            'farm_id': stage.farm_id,
            'stage_name': stage.stage_name,
            'start_date': stage.start_date.isoformat() if hasattr(stage, 'start_date') and stage.start_date else None,
            'end_date': stage.end_date.isoformat() if hasattr(stage, 'end_date') and stage.end_date else None,
            'notes': stage.notes if hasattr(stage, 'notes') else None,
            'recommended_tasks': stage.get_recommended_tasks() if hasattr(stage, 'get_recommended_tasks') else []
        }
        formatted_stages.append(stage_dict)
    
    return jsonify({
        'status': 'success',
        'count': len(formatted_stages),
        'growth_stages': formatted_stages
    })

@task.route('/api/tasks/recommended', methods=['GET'])
@login_required
@require_farm_registration
def get_recommended_tasks():
    """Get task recommendations based on growth stages"""
    from app.pest.models import GrowthStage  # Import here to avoid circular imports
    
    farm_id = request.args.get('farm_id', type=int)
    if not farm_id:
        return jsonify({'status': 'error', 'message': 'Farm ID is required'}), 400
    
    # Verify permissions
    farm = Farm.query.get(farm_id)
    if not farm or farm.user_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'Farm not found or access denied'}), 403
    
    # Get current growth stages for farm
    current_date = datetime.utcnow()
    stages = GrowthStage.query.filter(
        GrowthStage.farm_id == farm_id,
        GrowthStage.start_date <= current_date,
        (GrowthStage.end_date >= current_date) | (GrowthStage.end_date == None)
    ).all()
    
    # Get recommended tasks from all active growth stages
    recommended_tasks = []
    for stage in stages:
        if hasattr(stage, 'get_recommended_tasks'):
            stage_tasks = stage.get_recommended_tasks()
            if stage_tasks:
                for task in stage_tasks:
                    # Add stage context to task
                    task['growth_stage'] = stage.stage_name
                    task['growth_stage_id'] = stage.id
                    recommended_tasks.append(task)
    
    # Get existing tasks to avoid duplicates
    existing_tasks = Task.query.filter(
        Task.farm_id == farm_id,
        Task.start_date >= current_date,
        Task.status != 'completed'
    ).all()
    
    existing_task_types = [task.task_type for task in existing_tasks]
    
    # Filter out recommendations that already have active tasks
    filtered_recommendations = [
        task for task in recommended_tasks 
        if task.get('task_type') not in existing_task_types
    ]
    
    return jsonify({
        'status': 'success',
        'count': len(filtered_recommendations),
        'recommended_tasks': filtered_recommendations
    })

@task.errorhandler(404)
def not_found_error(error):
    return jsonify({
        'status': 'error',
        'message': 'Resource not found'
    }), 404

@task.errorhandler(403)
def forbidden_error(error):
    return jsonify({
        'status': 'error',
        'message': 'You do not have permission to access this resource'
    }), 403

@task.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    current_app.logger.error(f'Internal server error: {error}')
    return jsonify({
        'status': 'error',
        'message': 'Internal server error'
    }), 500


from flask_login import login_required

from app.decorators import require_farm_registration


@task.route('/api/tasks', methods=['GET'])
@login_required
@require_farm_registration
def get_tasks():
    """Get tasks for the current user's farms"""
    # Get query parameters and apply filters
    # Return formatted task data


@task.route('/api/tasks', methods=['POST'])
@login_required
@require_farm_registration
def create_task():
    """Create a new task"""
    # Validate input
    # Create task record
    # Handle recurrence if specified
    # Return task data

@task.route('/api/tasks/<int:task_id>', methods=['PUT'])
@login_required
@require_farm_registration
def update_task(task_id):
    """Update a task"""
    # Validate ownership
    # Update task fields
    # Return updated task data

@task.route('/api/tasks/<int:task_id>', methods=['DELETE'])
@login_required
@require_farm_registration
def delete_task(task_id):
    """Delete a task"""
    # Validate ownership
    # Delete task record
    # Return success response

@task.route('/api/growth-stages', methods=['GET'])
@login_required
@require_farm_registration
def get_growth_stages():
    """Get growth stages for the current user's farms"""
    # Apply farm filter if specified
    # Return growth stage data
    
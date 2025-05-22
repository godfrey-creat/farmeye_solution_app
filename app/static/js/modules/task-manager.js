/**
 * Task Manager
 * Main controller for task creation, editing, and management
 */
import store from '../store/index.js';

class TaskManager {
  constructor(options = {}) {
    this.options = {
      enableAnalytics: true,
      enableRecurrence: true,
      enableBulkActions: true,
      ...options
    };
    
    // State
    this.isInitialized = false;
    this.activeModal = null;
    this.selectedTasks = new Set();
    
    // Store subscription
    this.unsubscribe = null;
    
    // Initialize
    this.initialize();
  }
  
  /**
   * Initialize task manager
   */
  initialize() {
    if (this.isInitialized) return;
    
    // Subscribe to store changes
    this.unsubscribe = store.subscribe(action => {
      this.handleStoreUpdate(action);
    });
    
    // Create task management modals and components
    this.createTaskManagementStructure();
    
    // Setup global event listeners
    this.setupGlobalEventListeners();
    
    this.isInitialized = true;
    console.log('Task manager initialized');
  }
  
  /**
   * Create task management HTML structure
   */
  createTaskManagementStructure() {
    // Create task editor modal
    this.createTaskEditorModal();
    
    // Create analytics dashboard modal
    if (this.options.enableAnalytics) {
      this.createAnalyticsDashboard();
    }
    
    // Create bulk actions toolbar
    if (this.options.enableBulkActions) {
      this.createBulkActionsToolbar();
    }
    
    // Create task templates modal
    this.createTaskTemplatesModal();
  }
  
  /**
   * Create task editor modal
   */
  createTaskEditorModal() {
    const modalHTML = `
      <div class="modal-overlay" id="task-editor-modal" style="display: none;">
        <div class="modal-container task-editor-modal">
          <div class="modal-header">
            <h3 id="task-editor-title">Create New Task</h3>
            <button class="btn-close" onclick="taskManager.closeModal('task-editor-modal')">
              <i class="fas fa-times"></i>
            </button>
          </div>
          
          <div class="modal-body">
            <form id="task-editor-form" class="task-form">
              <!-- Basic Task Information -->
              <div class="form-section">
                <h4>Task Details</h4>
                
                <div class="form-row">
                  <div class="form-group">
                    <label for="task-title">Title *</label>
                    <input type="text" id="task-title" name="title" required 
                           placeholder="Enter task title" maxlength="64">
                    <div class="field-error"></div>
                  </div>
                </div>
                
                <div class="form-row">
                  <div class="form-group">
                    <label for="task-description">Description</label>
                    <textarea id="task-description" name="description" 
                              placeholder="Enter task description" rows="3"></textarea>
                  </div>
                </div>
                
                <div class="form-row">
                  <div class="form-group">
                    <label for="task-type">Task Type *</label>
                    <select id="task-type" name="task_type" required>
                      <option value="">Select task type</option>
                      <option value="Weeding">Weeding</option>
                      <option value="Irrigating">Irrigating</option>
                      <option value="Land Preparation">Land Preparation</option>
                      <option value="Harvesting">Harvesting</option>
                      <option value="Pruning">Pruning</option>
                      <option value="Fertilizing">Fertilizing</option>
                      <option value="Pest Control">Pest Control</option>
                      <option value="Soil Testing">Soil Testing</option>
                      <option value="Equipment Maintenance">Equipment Maintenance</option>
                      <option value="Other">Other</option>
                    </select>
                    <div class="field-error"></div>
                  </div>
                  
                  <div class="form-group">
                    <label for="task-category">Category</label>
                    <select id="task-category" name="category_id">
                      <option value="">Select category</option>
                      <!-- Categories will be populated dynamically -->
                    </select>
                  </div>
                </div>
                
                <div class="form-row">
                  <div class="form-group">
                    <label for="task-priority">Priority</label>
                    <select id="task-priority" name="priority">
                      <option value="low">Low</option>
                      <option value="medium" selected>Medium</option>
                      <option value="high">High</option>
                    </select>
                  </div>
                  
                  <div class="form-group">
                    <label for="task-status">Status</label>
                    <select id="task-status" name="status">
                      <option value="pending" selected>Pending</option>
                      <option value="in_progress">In Progress</option>
                      <option value="completed">Completed</option>
                    </select>
                  </div>
                </div>
              </div>
              
              <!-- Location and Assignment -->
              <div class="form-section">
                <h4>Location & Assignment</h4>
                
                <div class="form-row">
                  <div class="form-group">
                    <label for="task-farm">Farm *</label>
                    <select id="task-farm" name="farm_id" required>
                      <option value="">Select farm</option>
                      <!-- Farms will be populated dynamically -->
                    </select>
                    <div class="field-error"></div>
                  </div>
                  
                  <div class="form-group">
                    <label for="task-field">Field</label>
                    <select id="task-field" name="field_id">
                      <option value="">Select field (optional)</option>
                      <!-- Fields will be populated based on selected farm -->
                    </select>
                  </div>
                </div>
                
                <div class="form-row">
                  <div class="form-group">
                    <label for="task-assigned-to">Assigned To</label>
                    <select id="task-assigned-to" name="assigned_to">
                      <option value="">Assign to someone (optional)</option>
                      <!-- Users will be populated dynamically -->
                    </select>
                  </div>
                </div>
              </div>
              
              <!-- Scheduling -->
              <div class="form-section">
                <h4>Scheduling</h4>
                
                <div class="form-row">
                  <div class="form-group">
                    <label for="task-start-date">Start Date *</label>
                    <input type="date" id="task-start-date" name="start_date" required>
                    <div class="field-error"></div>
                  </div>
                  
                  <div class="form-group">
                    <label for="task-end-date">End Date</label>
                    <input type="date" id="task-end-date" name="end_date">
                  </div>
                </div>
                
                <div class="form-row">
                  <div class="form-group">
                    <div class="checkbox-group">
                      <input type="checkbox" id="task-all-day" name="is_all_day" checked>
                      <label for="task-all-day">All Day Task</label>
                    </div>
                  </div>
                </div>
                
                <div class="time-fields" id="task-time-fields" style="display: none;">
                  <div class="form-row">
                    <div class="form-group">
                      <label for="task-start-time">Start Time</label>
                      <input type="time" id="task-start-time" name="start_time">
                    </div>
                    
                    <div class="form-group">
                      <label for="task-end-time">End Time</label>
                      <input type="time" id="task-end-time" name="end_time">
                    </div>
                  </div>
                </div>
              </div>
              
              <!-- Recurrence -->
              <div class="form-section" id="recurrence-section">
                <h4>
                  <div class="checkbox-group">
                    <input type="checkbox" id="task-recurring" name="is_recurring">
                    <label for="task-recurring">Recurring Task</label>
                  </div>
                </h4>
                
                <div class="recurrence-options" id="recurrence-options" style="display: none;">
                  <div class="form-row">
                    <div class="form-group">
                      <label for="recurrence-type">Repeat</label>
                      <select id="recurrence-type" name="recurrence_type">
                        <option value="daily">Daily</option>
                        <option value="weekly">Weekly</option>
                        <option value="monthly">Monthly</option>
                        <option value="custom">Custom</option>
                      </select>
                    </div>
                    
                    <div class="form-group">
                      <label for="recurrence-interval">Every</label>
                      <input type="number" id="recurrence-interval" name="recurrence_interval" 
                             min="1" max="365" value="1">
                    </div>
                  </div>
                  
                  <div class="form-row" id="weekly-days" style="display: none;">
                    <div class="form-group full-width">
                      <label>Repeat on days</label>
                      <div class="day-selector">
                        <div class="day-option">
                          <input type="checkbox" id="day-0" name="recurrence_days" value="0">
                          <label for="day-0">Sun</label>
                        </div>
                        <div class="day-option">
                          <input type="checkbox" id="day-1" name="recurrence_days" value="1">
                          <label for="day-1">Mon</label>
                        </div>
                        <div class="day-option">
                          <input type="checkbox" id="day-2" name="recurrence_days" value="2">
                          <label for="day-2">Tue</label>
                        </div>
                        <div class="day-option">
                          <input type="checkbox" id="day-3" name="recurrence_days" value="3">
                          <label for="day-3">Wed</label>
                        </div>
                        <div class="day-option">
                          <input type="checkbox" id="day-4" name="recurrence_days" value="4">
                          <label for="day-4">Thu</label>
                        </div>
                        <div class="day-option">
                          <input type="checkbox" id="day-5" name="recurrence_days" value="5">
                          <label for="day-5">Fri</label>
                        </div>
                        <div class="day-option">
                          <input type="checkbox" id="day-6" name="recurrence_days" value="6">
                          <label for="day-6">Sat</label>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <div class="form-row">
                    <div class="form-group">
                      <label for="recurrence-end-type">End</label>
                      <select id="recurrence-end-type" name="recurrence_end_type">
                        <option value="never">Never</option>
                        <option value="on_date">On date</option>
                        <option value="after_count">After occurrences</option>
                      </select>
                    </div>
                    
                    <div class="form-group" id="recurrence-end-date-group" style="display: none;">
                      <label for="recurrence-end-date">End Date</label>
                      <input type="date" id="recurrence-end-date" name="recurrence_end_date">
                    </div>
                    
                    <div class="form-group" id="recurrence-count-group" style="display: none;">
                      <label for="recurrence-count">Occurrences</label>
                      <input type="number" id="recurrence-count" name="recurrence_count" 
                             min="1" max="365" placeholder="Number of times">
                    </div>
                  </div>
                </div>
              </div>
              
              <!-- Weather Integration -->
              <div class="form-section">
                <h4>Weather Considerations</h4>
                
                <div class="weather-info" id="task-weather-info">
                  <!-- Weather information will be populated dynamically -->
                </div>
                
                <div class="form-row">
                  <div class="form-group">
                    <div class="checkbox-group">
                      <input type="checkbox" id="weather-dependent" name="weather_dependent">
                      <label for="weather-dependent">Weather dependent task</label>
                    </div>
                    <small class="help-text">System will suggest rescheduling if weather conditions are unsuitable</small>
                  </div>
                </div>
              </div>
              
              <!-- Growth Stage Integration -->
              <div class="form-section">
                <h4>Growth Stage Context</h4>
                
                <div class="growth-stage-info" id="task-growth-stage-info">
                  <!-- Growth stage information will be populated dynamically -->
                </div>
                
                <div class="recommended-tasks" id="recommended-tasks" style="display: none;">
                  <h5>Recommended Tasks for Current Growth Stage</h5>
                  <div class="recommendation-list">
                    <!-- Recommendations will be populated dynamically -->
                  </div>
                </div>
              </div>
            </form>
          </div>
          
          <div class="modal-footer">
            <div class="footer-actions">
              <button type="button" class="btn-secondary" onclick="taskManager.closeModal('task-editor-modal')">
                Cancel
              </button>
              <button type="button" class="btn-secondary" id="save-as-template">
                Save as Template
              </button>
              <button type="submit" form="task-editor-form" class="btn-primary" id="save-task-btn">
                <span class="btn-text">Create Task</span>
                <span class="btn-loading" style="display: none;">
                  <i class="fas fa-spinner fa-spin"></i> Saving...
                </span>
              </button>
            </div>
          </div>
        </div>
      </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    // Setup task editor event listeners
    this.setupTaskEditorListeners();
  }
  
  /**
   * Setup task editor event listeners
   */
  setupTaskEditorListeners() {
    const form = document.getElementById('task-editor-form');
    const allDayCheckbox = document.getElementById('task-all-day');
    const recurringCheckbox = document.getElementById('task-recurring');
    const recurrenceType = document.getElementById('recurrence-type');
    const recurrenceEndType = document.getElementById('recurrence-end-type');
    const farmSelect = document.getElementById('task-farm');
    const startDateInput = document.getElementById('task-start-date');
    
    // Form submission
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      this.handleTaskSubmit();
    });
    
    // All-day checkbox
    allDayCheckbox.addEventListener('change', (e) => {
      const timeFields = document.getElementById('task-time-fields');
      timeFields.style.display = e.target.checked ? 'none' : 'block';
    });
    
    // Recurring checkbox
    recurringCheckbox.addEventListener('change', (e) => {
      const recurrenceOptions = document.getElementById('recurrence-options');
      recurrenceOptions.style.display = e.target.checked ? 'block' : 'none';
    });
    
    // Recurrence type change
    recurrenceType.addEventListener('change', (e) => {
      const weeklyDays = document.getElementById('weekly-days');
      weeklyDays.style.display = e.target.value === 'weekly' ? 'block' : 'none';
    });
    
    // Recurrence end type change
    recurrenceEndType.addEventListener('change', (e) => {
      const endDateGroup = document.getElementById('recurrence-end-date-group');
      const countGroup = document.getElementById('recurrence-count-group');
      
      endDateGroup.style.display = e.target.value === 'on_date' ? 'block' : 'none';
      countGroup.style.display = e.target.value === 'after_count' ? 'block' : 'none';
    });
    
    // Farm selection change
    farmSelect.addEventListener('change', (e) => {
      this.loadFieldsForFarm(e.target.value);
      this.loadGrowthStageInfo(e.target.value);
    });
    
    // Start date change
    startDateInput.addEventListener('change', (e) => {
      this.loadWeatherInfo(e.target.value);
      this.updateGrowthStageContext(e.target.value);
    });
    
    // Save as template
    document.getElementById('save-as-template').addEventListener('click', () => {
      this.saveAsTemplate();
    });
  }
  
  /**
   * Show task editor modal
   */
  showTaskEditor(taskData = null, dateContext = null) {
    const modal = document.getElementById('task-editor-modal');
    const title = document.getElementById('task-editor-title');
    const saveBtn = document.getElementById('save-task-btn');
    const form = document.getElementById('task-editor-form');
    
    // Reset form
    form.reset();
    this.clearFormErrors();
    
    // Set default values
    this.setDefaultFormValues(dateContext);
    
    // Load dynamic data
    this.loadFormData();
    
    if (taskData) {
      // Editing existing task
      title.textContent = 'Edit Task';
      saveBtn.querySelector('.btn-text').textContent = 'Update Task';
      this.populateFormWithTaskData(taskData);
    } else {
      // Creating new task
      title.textContent = 'Create New Task';
      saveBtn.querySelector('.btn-text').textContent = 'Create Task';
    }
    
    // Show modal
    modal.style.display = 'block';
    this.activeModal = 'task-editor-modal';
    
    // Focus first input
    setTimeout(() => {
      document.getElementById('task-title').focus();
    }, 100);
  }
  
  /**
   * Load form data (farms, categories, etc.)
   */
  async loadFormData() {
    try {
      // Load farms
      const farms = store.farm?.farms || [];
      const farmSelect = document.getElementById('task-farm');
      
      farmSelect.innerHTML = '<option value="">Select farm</option>';
      farms.forEach(farm => {
        farmSelect.innerHTML += `<option value="${farm.id}">${farm.name}</option>`;
      });
      
      // Set active farm if available
      if (store.farm?.activeFarmId) {
        farmSelect.value = store.farm.activeFarmId;
        this.loadFieldsForFarm(store.farm.activeFarmId);
      }
      
      // Load categories
      const categories = store.tasks?.categories || [];
      const categorySelect = document.getElementById('task-category');
      
      categorySelect.innerHTML = '<option value="">Select category</option>';
      categories.forEach(category => {
        categorySelect.innerHTML += `
          <option value="${category.id}" data-color="${category.color}">
            ${category.name}
          </option>
        `;
      });
      
    } catch (error) {
      console.error('Error loading form data:', error);
    }
  }
  
  /**
   * Load fields for selected farm
   */
  async loadFieldsForFarm(farmId) {
    if (!farmId) return;
    
    try {
      const fields = store.farm?.getFieldsByFarmId(parseInt(farmId)) || [];
      const fieldSelect = document.getElementById('task-field');
      
      fieldSelect.innerHTML = '<option value="">Select field (optional)</option>';
      fields.forEach(field => {
        fieldSelect.innerHTML += `<option value="${field.id}">${field.name}</option>`;
      });
      
      // Set active field if available
      if (store.farm?.activeFieldId) {
        fieldSelect.value = store.farm.activeFieldId;
      }
      
    } catch (error) {
      console.error('Error loading fields:', error);
    }
  }
  
  /**
   * Load weather information for date
   */
  async loadWeatherInfo(dateStr) {
    if (!dateStr) return;
    
    const weatherContainer = document.getElementById('task-weather-info');
    
    try {
      const date = new Date(dateStr);
      const weather = store.weather?.getWeatherForDate(date);
      
      if (weather) {
        weatherContainer.innerHTML = `
          <div class="weather-card">
            <div class="weather-icon">
              <i class="fas fa-${this.getWeatherIcon(weather.conditions)}"></i>
            </div>
            <div class="weather-details">
              <div class="weather-condition">${weather.conditions}</div>
              <div class="weather-temp">${weather.temperature}°C</div>
              <div class="weather-rain">Rain: ${weather.precipitation_probability}%</div>
              <div class="weather-wind">Wind: ${weather.wind_speed} km/h</div>
            </div>
          </div>
        `;
      } else {
        weatherContainer.innerHTML = `
          <div class="weather-unavailable">
            <i class="fas fa-cloud"></i>
            <span>Weather data not available for this date</span>
          </div>
        `;
      }
    } catch (error) {
      console.error('Error loading weather info:', error);
      weatherContainer.innerHTML = '';
    }
  }
  
  /**
   * Load growth stage context
   */
  async loadGrowthStageInfo(farmId) {
    if (!farmId) return;
    
    const growthStageContainer = document.getElementById('task-growth-stage-info');
    const recommendedContainer = document.getElementById('recommended-tasks');
    
    try {
      const startDate = document.getElementById('task-start-date').value;
      if (!startDate) return;
      
      const date = new Date(startDate);
      const stage = store.growth?.getStageForDate(date, parseInt(farmId));
      
      if (stage) {
        growthStageContainer.innerHTML = `
          <div class="growth-stage-card">
            <div class="stage-header">
              <h5>${stage.stage_name}</h5>
              <span class="stage-duration">
                ${new Date(stage.start_date).toLocaleDateString()} - 
                ${stage.end_date ? new Date(stage.end_date).toLocaleDateString() : 'Ongoing'}
              </span>
            </div>
            ${stage.notes ? `<p class="stage-notes">${stage.notes}</p>` : ''}
          </div>
        `;
        
        // Load recommended tasks
        const recommendations = store.growth?.getRecommendedTasksForStage(stage.id) || [];
        if (recommendations.length > 0) {
          const recommendationList = document.querySelector('.recommendation-list');
          recommendationList.innerHTML = recommendations.map(task => `
            <div class="recommendation-item">
              <span class="rec-task-type">${task.task_type || task}</span>
              <button class="btn-small btn-primary" onclick="taskManager.applyRecommendation('${task.task_type || task}')">
                Apply
              </button>
            </div>
          `).join('');
          
          recommendedContainer.style.display = 'block';
        } else {
          recommendedContainer.style.display = 'none';
        }
      } else {
        growthStageContainer.innerHTML = `
          <div class="no-growth-stage">
            <i class="fas fa-seedling"></i>
            <span>No active growth stage for this date</span>
          </div>
        `;
        recommendedContainer.style.display = 'none';
      }
    } catch (error) {
      console.error('Error loading growth stage info:', error);
      growthStageContainer.innerHTML = '';
      recommendedContainer.style.display = 'none';
    }
  }
  
  /**
   * Handle task form submission
   */
  async handleTaskSubmit() {
    const form = document.getElementById('task-editor-form');
    const saveBtn = document.getElementById('save-task-btn');
    const btnText = saveBtn.querySelector('.btn-text');
    const btnLoading = saveBtn.querySelector('.btn-loading');
    
    try {
      // Show loading state
      btnText.style.display = 'none';
      btnLoading.style.display = 'inline-block';
      saveBtn.disabled = true;
      
      // Validate form
      if (!this.validateTaskForm()) {
        return;
      }
      
      // Collect form data
      const taskData = this.collectTaskFormData();
      
      // Check if editing or creating
      const taskId = form.dataset.taskId;
      
      if (taskId) {
        // Update existing task
        await store.tasks.updateTask(parseInt(taskId), taskData);
        this.showNotification('Task updated successfully', 'success');
      } else {
        // Create new task
        await store.tasks.createTask(taskData);
        this.showNotification('Task created successfully', 'success');
      }
      
      // Close modal
      this.closeModal('task-editor-modal');
      
    } catch (error) {
      console.error('Error saving task:', error);
      this.showNotification('Error saving task: ' + error.message, 'error');
    } finally {
      // Reset button state
      btnText.style.display = 'inline-block';
      btnLoading.style.display = 'none';
      saveBtn.disabled = false;
    }
  }
  
  /**
   * Validate task form
   */
  validateTaskForm() {
    let isValid = true;
    
    // Clear previous errors
    this.clearFormErrors();
    
    // Required fields validation
    const requiredFields = [
      { id: 'task-title', message: 'Title is required' },
      { id: 'task-type', message: 'Task type is required' },
      { id: 'task-farm', message: 'Farm selection is required' },
      { id: 'task-start-date', message: 'Start date is required' }
    ];
    
    requiredFields.forEach(field => {
      const element = document.getElementById(field.id);
      if (!element.value.trim()) {
        this.showFieldError(field.id, field.message);
        isValid = false;
      }
    });
    
    // Date validation
    const startDate = document.getElementById('task-start-date').value;
    const endDate = document.getElementById('task-end-date').value;
    
    if (startDate && endDate && new Date(endDate) < new Date(startDate)) {
      this.showFieldError('task-end-date', 'End date cannot be before start date');
      isValid = false;
    }
    
    // Recurrence validation
    const isRecurring = document.getElementById('task-recurring').checked;
    if (isRecurring) {
      const recurrenceEndType = document.getElementById('recurrence-end-type').value;
      
      if (recurrenceEndType === 'on_date') {
        const endDate = document.getElementById('recurrence-end-date').value;
        if (!endDate) {
          this.showFieldError('recurrence-end-date', 'End date is required for date-based recurrence');
          isValid = false;
        } else if (new Date(endDate) <= new Date(startDate)) {
          this.showFieldError('recurrence-end-date', 'Recurrence end date must be after start date');
          isValid = false;
        }
      }
      
      if (recurrenceEndType === 'after_count') {
        const count = document.getElementById('recurrence-count').value;
        if (!count || parseInt(count) < 1) {
          this.showFieldError('recurrence-count', 'Number of occurrences must be at least 1');
          isValid = false;
        }
      }
      
      // Weekly recurrence validation
      const recurrenceType = document.getElementById('recurrence-type').value;
      if (recurrenceType === 'weekly') {
        const selectedDays = document.querySelectorAll('input[name="recurrence_days"]:checked');
        if (selectedDays.length === 0) {
          this.showNotification('Please select at least one day for weekly recurrence', 'warning');
          isValid = false;
        }
      }
    }
    
    return isValid;
  }
  
  /**
   * Collect task form data
   */
  collectTaskFormData() {
    const form = document.getElementById('task-editor-form');
    const formData = new FormData(form);
    
    // Basic task data
    const taskData = {
      title: formData.get('title'),
      description: formData.get('description'),
      task_type: formData.get('task_type'),
      priority: formData.get('priority'),
      status: formData.get('status'),
      farm_id: parseInt(formData.get('farm_id')),
      field_id: formData.get('field_id') ? parseInt(formData.get('field_id')) : null,
      category_id: formData.get('category_id') ? parseInt(formData.get('category_id')) : null,
      assigned_to: formData.get('assigned_to') ? parseInt(formData.get('assigned_to')) : null,
      is_all_day: document.getElementById('task-all-day').checked
    };
    
    // Handle dates and times
    const startDate = formData.get('start_date');
    const endDate = formData.get('end_date');
    const startTime = formData.get('start_time');
    const endTime = formData.get('end_time');
    
    if (taskData.is_all_day) {
      taskData.start_date = startDate;
      taskData.end_date = endDate || null;
    } else {
      taskData.start_date = startTime ? `${startDate}T${startTime}` : startDate;
      taskData.end_date = endDate ? (endTime ? `${endDate}T${endTime}` : endDate) : null;
    }
    
    // Handle recurrence
    const isRecurring = document.getElementById('task-recurring').checked;
    if (isRecurring) {
      const recurrenceData = {
        recurrence_type: formData.get('recurrence_type'),
        recurrence_interval: parseInt(formData.get('recurrence_interval')),
        recurrence_end_type: formData.get('recurrence_end_type')
      };
      
      // Weekly days
      if (recurrenceData.recurrence_type === 'weekly') {
        const selectedDays = Array.from(document.querySelectorAll('input[name="recurrence_days"]:checked'))
          .map(cb => cb.value);
        recurrenceData.recurrence_days = selectedDays.join(',');
      }
      
      // End conditions
      if (recurrenceData.recurrence_end_type === 'on_date') {
        recurrenceData.recurrence_end_date = formData.get('recurrence_end_date');
      } else if (recurrenceData.recurrence_end_type === 'after_count') {
        recurrenceData.recurrence_count = parseInt(formData.get('recurrence_count'));
      }
      
      taskData.recurrence = recurrenceData;
    }
    
    return taskData;
  }
  
  /**
   * Show field error
   */
  showFieldError(fieldId, message) {
    const field = document.getElementById(fieldId);
    const errorElement = field.parentNode.querySelector('.field-error');
    
    field.classList.add('error');
    if (errorElement) {
      errorElement.textContent = message;
      errorElement.style.display = 'block';
    }
  }
  
  /**
   * Clear form errors
   */
  clearFormErrors() {
    document.querySelectorAll('.field-error').forEach(error => {
      error.textContent = '';
      error.style.display = 'none';
    });
    
    document.querySelectorAll('.error').forEach(field => {
      field.classList.remove('error');
    });
  }
  
  /**
   * Show notification
   */
  showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
      <div class="notification-content">
        <i class="fas fa-${this.getNotificationIcon(type)}"></i>
        <span>${message}</span>
      </div>
      <button class="notification-close" onclick="this.parentNode.remove()">
        <i class="fas fa-times"></i>
      </button>
    `;
    
    // Add to page
    let container = document.getElementById('notification-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'notification-container';
      container.className = 'notification-container';
      document.body.appendChild(container);
    }
    
    container.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
      if (notification.parentNode) {
        notification.remove();
      }
    }, 5000);
  }
  
  /**
   * Get notification icon
   */
  getNotificationIcon(type) {
    const icons = {
      success: 'check-circle',
      error: 'exclamation-circle',
      warning: 'exclamation-triangle',
      info: 'info-circle'
    };
    return icons[type] || 'info-circle';
  }
  
  /**
   * Get weather icon
   */
  getWeatherIcon(condition) {
    const icons = {
      'Clear': 'sun',
      'Clouds': 'cloud',
      'Rain': 'rain',
      'Snow': 'snowflake',
      'Thunderstorm': 'bolt'
    };
    return icons[condition] || 'cloud';
  }
  
  /**
   * Close modal
   */
  closeModal(modalId) {
    const modal = document.getElementById(modalId);
    modal.style.display = 'none';
    this.activeModal = null;
    
    // Reset form if it's the task editor
    if (modalId === 'task-editor-modal') {
      const form = document.getElementById('task-editor-form');
      form.reset();
      form.removeAttribute('data-task-id');
      this.clearFormErrors();
    }
  }
  
  /**
   * Handle store updates
   */
  handleStoreUpdate(action) {
    switch (action.type) {
      case 'TASK_CREATED':
      case 'TASK_UPDATED':
      case 'TASK_DELETED':
        // Refresh analytics if visible
        if (this.options.enableAnalytics) {
          this.refreshAnalytics();
        }
        break;
        
      case 'ACTIVE_FARM_CHANGED':
        // Update form options if modal is open
        if (this.activeModal === 'task-editor-modal') {
          this.loadFormData();
        }
        break;
    }
  }
  
  /**
   * Setup global event listeners
   */
  setupGlobalEventListeners() {
    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
      // Escape to close modals
      if (e.key === 'Escape' && this.activeModal) {
        this.closeModal(this.activeModal);
      }
      
      // Ctrl+N for new task
      if (e.ctrlKey && e.key === 'n' && !this.activeModal) {
        e.preventDefault();
        this.showTaskEditor();
      }
    });
    
    // Click outside modal to close
    document.addEventListener('click', (e) => {
      if (e.target.classList.contains('modal-overlay')) {
        this.closeModal(this.activeModal);
      }
    });
  }
  
  /**
   * Public API methods
   */
  
  // Create new task
  createTask(dateContext = null) {
    this.showTaskEditor(null, dateContext);
  }
  
  // Edit existing task
  editTask(taskId) {
    const task = store.tasks?.getTaskById(taskId);
    if (task) {
      this.showTaskEditor(task);
    }
  }
  
  // Delete task
  async deleteTask(taskId) {
    if (confirm('Are you sure you want to delete this task?')) {
      try {
        await store.tasks.deleteTask(taskId);
        this.showNotification('Task deleted successfully', 'success');
      } catch (error) {
        this.showNotification('Error deleting task: ' + error.message, 'error');
      }
    }
  }
  
  // Toggle task status
  async toggleTaskStatus(taskId) {
    try {
      const task = store.tasks?.getTaskById(taskId);
      if (!task) return;
      
      const newStatus = task.status === 'completed' ? 'pending' : 'completed';
      await store.tasks.updateTask(taskId, { status: newStatus });
      
      this.showNotification(`Task marked as ${newStatus}`, 'success');
    } catch (error) {
      this.showNotification('Error updating task status: ' + error.message, 'error');
    }
  }
  
  // Apply recommendation
  applyRecommendation(taskType) {
    const taskTypeField = document.getElementById('task-type');
    taskTypeField.value = taskType;
    
    // Trigger change event to update other fields
    taskTypeField.dispatchEvent(new Event('change'));
    
    this.showNotification(`Applied recommendation: ${taskType}`, 'success');
  }
  
  /**
   * Create bulk actions toolbar
   */
  createBulkActionsToolbar() {
    const toolbarHTML = `
      <div class="bulk-actions-toolbar" id="bulk-actions-toolbar" style="display: none;">
        <div class="toolbar-content">
          <div class="selected-count">
            <span id="selected-tasks-count">0</span> tasks selected
          </div>
          <div class="action-buttons">
            <button class="btn-secondary" onclick="taskManager.bulkUpdateStatus('pending')">
              <i class="fas fa-clock"></i> Mark Pending
            </button>
            <button class="btn-secondary" onclick="taskManager.bulkUpdateStatus('in_progress')">
              <i class="fas fa-spinner"></i> Mark In Progress
            </button>
            <button class="btn-secondary" onclick="taskManager.bulkUpdateStatus('completed')">
              <i class="fas fa-check"></i> Mark Completed
            </button>
            <button class="btn-danger" onclick="taskManager.bulkDelete()">
              <i class="fas fa-trash"></i> Delete Selected
            </button>
          </div>
          <button class="btn-close" onclick="taskManager.hideBulkActionsToolbar()">
            <i class="fas fa-times"></i>
          </button>
        </div>
      </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', toolbarHTML);
  }

  /**
   * Show bulk actions toolbar
   */
  showBulkActionsToolbar() {
    const toolbar = document.getElementById('bulk-actions-toolbar');
    if (toolbar) {
      toolbar.style.display = 'block';
      this.updateSelectedTasksCount();
    }
  }

  /**
   * Hide bulk actions toolbar
   */
  hideBulkActionsToolbar() {
    const toolbar = document.getElementById('bulk-actions-toolbar');
    if (toolbar) {
      toolbar.style.display = 'none';
      this.selectedTasks.clear();
      this.updateSelectedTasksCount();
    }
  }

  /**
   * Update selected tasks count
   */
  updateSelectedTasksCount() {
    const countElement = document.getElementById('selected-tasks-count');
    if (countElement) {
      countElement.textContent = this.selectedTasks.size;
    }
  }

  /**
   * Bulk update task status
   */
  async bulkUpdateStatus(status) {
    if (this.selectedTasks.size === 0) return;
    
    try {
      const updates = Array.from(this.selectedTasks).map(taskId => 
        store.tasks.updateTask(taskId, { status })
      );
      
      await Promise.all(updates);
      this.showNotification(`Updated ${this.selectedTasks.size} tasks to ${status}`, 'success');
      this.hideBulkActionsToolbar();
    } catch (error) {
      this.showNotification('Error updating tasks: ' + error.message, 'error');
    }
  }

  /**
   * Bulk delete tasks
   */
  async bulkDelete() {
    if (this.selectedTasks.size === 0) return;
    
    if (confirm(`Are you sure you want to delete ${this.selectedTasks.size} tasks?`)) {
      try {
        const deletions = Array.from(this.selectedTasks).map(taskId => 
          store.tasks.deleteTask(taskId)
        );
        
        await Promise.all(deletions);
        this.showNotification(`Deleted ${this.selectedTasks.size} tasks`, 'success');
        this.hideBulkActionsToolbar();
      } catch (error) {
        this.showNotification('Error deleting tasks: ' + error.message, 'error');
      }
    }
  }
  
  /**
   * Cleanup
   */
  destroy() {
    if (this.unsubscribe) {
      this.unsubscribe();
    }
    
    // Remove modals
    const modals = ['task-editor-modal', 'analytics-dashboard', 'bulk-actions-toolbar'];
    modals.forEach(modalId => {
      const modal = document.getElementById(modalId);
      if (modal) {
        modal.remove();
      }
    });
    
    console.log('Task manager destroyed');
  }
  
  /**
   * Create analytics dashboard modal
   */
  createAnalyticsDashboard() {
    const modalHTML = `
      <div class="modal-overlay" id="task-analytics-modal" style="display: none;">
        <div class="modal-container task-analytics-modal">
          <div class="modal-header">
            <h3>Task Analytics</h3>
            <button class="btn-close" onclick="taskManager.closeModal('task-analytics-modal')">
              <i class="fas fa-times"></i>
            </button>
          </div>
          
          <div class="modal-body">
            <div class="analytics-grid">
              <!-- Task Completion Rate -->
              <div class="analytics-card">
                <h4>Task Completion Rate</h4>
                <div class="analytics-value" id="completion-rate">--</div>
                <div class="analytics-chart" id="completion-chart"></div>
              </div>
              
              <!-- Task Distribution -->
              <div class="analytics-card">
                <h4>Task Distribution</h4>
                <div class="analytics-chart" id="distribution-chart"></div>
              </div>
              
              <!-- Upcoming Tasks -->
              <div class="analytics-card">
                <h4>Upcoming Tasks</h4>
                <div class="analytics-list" id="upcoming-tasks-list"></div>
              </div>
              
              <!-- Task Categories -->
              <div class="analytics-card">
                <h4>Task Categories</h4>
                <div class="analytics-chart" id="categories-chart"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    `;
    
    // Add modal to document
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    // Initialize charts when modal is shown
    const modal = document.getElementById('task-analytics-modal');
    modal.addEventListener('show', () => {
      this.updateAnalyticsCharts();
    });
  }
  
  /**
   * Update analytics charts with current data
   */
  updateAnalyticsCharts() {
    const state = store.getState();
    const tasks = state.tasks.items;
    
    // Update completion rate
    const completedTasks = tasks.filter(t => t.status === 'completed').length;
    const totalTasks = tasks.length;
    const completionRate = totalTasks > 0 ? (completedTasks / totalTasks * 100).toFixed(1) : 0;
    document.getElementById('completion-rate').textContent = `${completionRate}%`;
    
    // Update task distribution
    const distributionData = this.calculateTaskDistribution(tasks);
    this.updateDistributionChart(distributionData);
    
    // Update upcoming tasks
    const upcomingTasks = this.getUpcomingTasks(tasks);
    this.updateUpcomingTasksList(upcomingTasks);
    
    // Update categories
    const categoryData = this.calculateCategoryDistribution(tasks);
    this.updateCategoriesChart(categoryData);
  }
  
  /**
   * Calculate task distribution by status
   */
  calculateTaskDistribution(tasks) {
    const distribution = {
      pending: 0,
      in_progress: 0,
      completed: 0
    };
    
    tasks.forEach(task => {
      distribution[task.status] = (distribution[task.status] || 0) + 1;
    });
    
    return distribution;
  }
  
  /**
   * Get upcoming tasks
   */
  getUpcomingTasks(tasks) {
    const today = new Date();
    return tasks
      .filter(task => {
        const taskDate = new Date(task.start_date);
        return taskDate >= today && task.status !== 'completed';
      })
      .sort((a, b) => new Date(a.start_date) - new Date(b.start_date))
      .slice(0, 5);
  }
  
  /**
   * Calculate category distribution
   */
  calculateCategoryDistribution(tasks) {
    const distribution = {};
    
    tasks.forEach(task => {
      const category = task.category || 'Uncategorized';
      distribution[category] = (distribution[category] || 0) + 1;
    });
    
    return distribution;
  }
  
  /**
   * Update distribution chart
   */
  updateDistributionChart(data) {
    // Implementation depends on your charting library
    console.log('Updating distribution chart with:', data);
  }
  
  /**
   * Update upcoming tasks list
   */
  updateUpcomingTasksList(tasks) {
    const listElement = document.getElementById('upcoming-tasks-list');
    if (!listElement) return;
    
    listElement.innerHTML = tasks.map(task => `
      <div class="upcoming-task">
        <div class="task-title">${task.title}</div>
        <div class="task-date">${new Date(task.start_date).toLocaleDateString()}</div>
      </div>
    `).join('');
  }
  
  /**
   * Update categories chart
   */
  updateCategoriesChart(data) {
    // Implementation depends on your charting library
    console.log('Updating categories chart with:', data);
  }

  /**
   * Create task templates modal
   */
  createTaskTemplatesModal() {
    // Check if modal already exists
    if (document.getElementById('task-templates-modal')) {
      return;
    }

    const modalHTML = `
      <div class="modal-overlay" id="task-templates-modal" style="display: none;">
        <div class="modal-container">
          <div class="modal-header">
            <h3>Task Templates</h3>
            <button class="btn-close" onclick="taskManager.closeModal('task-templates-modal')">
              <i class="fas fa-times"></i>
            </button>
          </div>
          
          <div class="modal-body">
            <div class="templates-section">
              <div class="section-header">
                <h4>Quick Start Templates</h4>
                <button class="btn-secondary btn-sm" onclick="taskManager.createCustomTemplate()">
                  <i class="fas fa-plus"></i> Create Template
                </button>
              </div>
              
              <div class="task-templates-grid" id="templates-grid">
                <!-- Templates will be loaded here -->
              </div>
            </div>
          </div>
        </div>
      </div>
    `;

    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    // Load default templates
    this.loadTaskTemplates();
  }

  /**
   * Load task templates
   */
  loadTaskTemplates() {
    const grid = document.getElementById('templates-grid');
    if (!grid) return;

    // Default templates
    const templates = [
      {
        id: 'weeding',
        title: 'Weekly Weeding',
        type: 'Weeding',
        description: 'Regular weeding schedule for crop maintenance',
        recurrence: 'weekly'
      },
      {
        id: 'irrigation',
        title: 'Irrigation Check',
        type: 'Irrigating',
        description: 'Daily irrigation system monitoring',
        recurrence: 'daily'
      },
      {
        id: 'fertilizer',
        title: 'Fertilizer Application',
        type: 'Fertilizing',
        description: 'Monthly fertilizer application schedule',
        recurrence: 'monthly'
      },
      {
        id: 'harvest',
        title: 'Harvest Planning',
        type: 'Harvesting',
        description: 'Harvest preparation and execution',
        recurrence: 'none'
      }
    ];

    grid.innerHTML = templates.map(template => `
      <div class="template-card" onclick="taskManager.useTemplate('${template.id}')">
        <div class="template-header">
          <h5 class="template-title">${template.title}</h5>
          <span class="template-type">${template.type}</span>
        </div>
        <p class="template-description">${template.description}</p>
        <div class="template-meta">
          <small><i class="fas fa-repeat"></i> ${template.recurrence}</small>
        </div>
      </div>
    `).join('');
  }

  /**
   * Create custom template from current task
   */
  createCustomTemplate() {
    // Get current task form data
    const form = document.getElementById('task-editor-form');
    if (!form) {
      this.showNotification('Please create a task first to save as template', 'warning');
      return;
    }

    // Save current task as template
    this.saveAsTemplate();
    
    // Close task editor and show templates
    this.closeModal('task-editor-modal');
    this.showTaskTemplates();
  }

  /**
   * Use task template
   */
  useTemplate(templateId) {
    // Apply template to new task
    this.createTask();
    
    // Template-specific logic would go here
    console.log('Using template:', templateId);
    
    // Close templates modal
    this.closeModal('task-templates-modal');
  }

  /**
   * Show task templates modal
   */
  showTaskTemplates() {
    const modal = document.getElementById('task-templates-modal');
    if (modal) {
      modal.style.display = 'block';
      this.activeModal = 'task-templates-modal';
    }
  }
}

// Export for use in other modules
export default TaskManager;

// Global instance for backward compatibility
window.TaskManager = TaskManager;
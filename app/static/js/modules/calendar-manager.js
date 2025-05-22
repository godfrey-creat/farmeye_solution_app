/**
 * Calendar Manager
 * Main controller for calendar views and task visualization
 */
import store from '../store/index.js';

class CalendarManager {
  constructor(containerId, options = {}) {
    this.containerId = containerId;
    this.container = document.getElementById(containerId);
    
    if (!this.container) {
      throw new Error(`Container with ID '${containerId}' not found`);
    }
    
    // Calendar state
    this.currentView = options.view || 'month'; // month, week, day, list, gantt
    this.currentDate = options.startDate || new Date();
    this.selectedDate = new Date();
    this.selectedTaskId = null;
    
    // View options
    this.showGrowthStages = options.showGrowthStages !== false;
    this.showWeatherInfo = options.showWeatherInfo !== false;
    this.allowTaskCreation = options.allowTaskCreation !== false;
    
    // Store subscription
    this.unsubscribe = null;
    
    // Event handlers
    this.eventHandlers = {};
    
    // Initialize
    this.initialize();
  }
  
  /**
   * Initialize calendar manager
   */
  initialize() {
    // Subscribe to store changes
    this.unsubscribe = store.subscribe(action => {
      this.handleStoreUpdate(action);
    });
    
    // Create calendar structure
    this.createCalendarStructure();
    
    // Setup event listeners
    this.setupEventListeners();
    
    // Initial render
    this.render();
    
    console.log('Calendar manager initialized');
  }
  
  /**
   * Handle store updates
   */
  handleStoreUpdate(action) {
    switch (action.type) {
      case 'TASKS_LOADED':
      case 'TASK_CREATED':
      case 'TASK_UPDATED':
      case 'TASK_DELETED':
        this.renderCalendarEvents();
        break;
        
      case 'GROWTH_STAGES_LOADED':
        if (this.showGrowthStages) {
          this.renderGrowthStages();
        }
        break;
        
      case 'ACTIVE_FARM_CHANGED':
        this.handleFarmChange(action.payload);
        break;
        
      case 'TASK_FILTER_CHANGED':
        this.render();
        break;
        
      case 'WEATHER_FORECAST_LOADED':
        if (this.showWeatherInfo) {
          this.renderWeatherInfo();
        }
        break;
    }
  }
  
  /**
   * Create calendar HTML structure
   */
  createCalendarStructure() {
    this.container.innerHTML = `
      <div class="calendar-container">
        <!-- Calendar Header -->
        <div class="calendar-header">
          <div class="calendar-controls">
            <div class="date-navigation">
              <button class="btn-nav" id="calendar-prev">
                <i class="fas fa-chevron-left"></i>
              </button>
              <div class="current-date-display">
                <h3 id="calendar-date-title"></h3>
              </div>
              <button class="btn-nav" id="calendar-next">
                <i class="fas fa-chevron-right"></i>
              </button>
              <button class="btn-today" id="calendar-today">Today</button>
            </div>
            
            <div class="view-controls">
              <div class="view-toggle-group">
                <button class="view-toggle active" data-view="month">Month</button>
                <button class="view-toggle" data-view="week">Week</button>
                <button class="view-toggle" data-view="day">Day</button>
                <button class="view-toggle" data-view="list">List</button>
                <button class="view-toggle" data-view="gantt">Gantt</button>
              </div>
            </div>
            
            <div class="calendar-actions">
              <button class="btn-primary" id="add-task-btn">
                <i class="fas fa-plus"></i> Add Task
              </button>
              <button class="btn-secondary" id="filter-tasks-btn">
                <i class="fas fa-filter"></i> Filter
              </button>
            </div>
          </div>
          
          <!-- Task Filter Panel (initially hidden) -->
          <div class="task-filter-panel" id="task-filter-panel" style="display: none;">
            <div class="filter-controls">
              <div class="filter-group">
                <label>Status:</label>
                <select id="filter-status">
                  <option value="all">All</option>
                  <option value="pending">Pending</option>
                  <option value="in_progress">In Progress</option>
                  <option value="completed">Completed</option>
                </select>
              </div>
              
              <div class="filter-group">
                <label>Task Type:</label>
                <select id="filter-task-type">
                  <option value="all">All Types</option>
                </select>
              </div>
              
              <div class="filter-group">
                <label>Category:</label>
                <select id="filter-category">
                  <option value="all">All Categories</option>
                </select>
              </div>
              
              <div class="filter-group">
                <label>Field:</label>
                <select id="filter-field">
                  <option value="all">All Fields</option>
                </select>
              </div>
              
              <div class="filter-actions">
                <button class="btn-secondary" id="clear-filters">Clear</button>
                <button class="btn-primary" id="apply-filters">Apply</button>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Calendar Content -->
        <div class="calendar-content">
          <!-- Calendar Grid (Month/Week/Day views) -->
          <div class="calendar-grid" id="calendar-grid">
            <!-- Calendar grid will be rendered here -->
          </div>
          
          <!-- List View -->
          <div class="calendar-list-view" id="calendar-list-view" style="display: none;">
            <!-- Task list will be rendered here -->
          </div>
          
          <!-- Gantt Chart View -->
          <div class="calendar-gantt-view" id="calendar-gantt-view" style="display: none;">
            <!-- Gantt chart will be rendered here -->
          </div>
        </div>
        
        <!-- Task Detail Panel -->
        <div class="task-detail-panel" id="task-detail-panel" style="display: none;">
          <div class="task-detail-content">
            <!-- Task details will be rendered here -->
          </div>
        </div>
        
        <!-- Legend -->
        <div class="calendar-legend">
          <div class="legend-section">
            <h4>Task Categories</h4>
            <div class="legend-items" id="category-legend">
              <!-- Category legend items will be rendered here -->
            </div>
          </div>
          
          <div class="legend-section" id="growth-stage-legend" style="display: none;">
            <h4>Growth Stages</h4>
            <div class="legend-items" id="stage-legend">
              <!-- Growth stage legend items will be rendered here -->
            </div>
          </div>
        </div>
      </div>
    `;
  }
  
  /**
   * Setup event listeners
   */
  setupEventListeners() {
    // Date navigation
    document.getElementById('calendar-prev').addEventListener('click', () => {
      this.navigateDate(-1);
    });
    
    document.getElementById('calendar-next').addEventListener('click', () => {
      this.navigateDate(1);
    });
    
    document.getElementById('calendar-today').addEventListener('click', () => {
      this.goToToday();
    });
    
    // View toggles
    document.querySelectorAll('.view-toggle').forEach(button => {
      button.addEventListener('click', (e) => {
        this.setView(e.target.dataset.view);
      });
    });
    
    // Task actions
    document.getElementById('add-task-btn').addEventListener('click', () => {
      this.showTaskEditor();
    });
    
    document.getElementById('filter-tasks-btn').addEventListener('click', () => {
      this.toggleFilterPanel();
    });
    
    // Filter controls
    document.getElementById('apply-filters').addEventListener('click', () => {
      this.applyFilters();
    });
    
    document.getElementById('clear-filters').addEventListener('click', () => {
      this.clearFilters();
    });
    
    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
      this.handleKeyboardShortcuts(e);
    });
  }
  
  /**
   * Render calendar
   */
  render() {
    // Update date title
    this.updateDateTitle();
    
    // Show appropriate view
    this.showView(this.currentView);
    
    // Render calendar content based on current view
    switch (this.currentView) {
      case 'month':
        this.renderMonthView();
        break;
      case 'week':
        this.renderWeekView();
        break;
      case 'day':
        this.renderDayView();
        break;
      case 'list':
        this.renderListView();
        break;
      case 'gantt':
        this.renderGanttView();
        break;
    }
    
    // Render legend
    this.renderLegend();
    
    // Render growth stages if enabled
    if (this.showGrowthStages) {
      this.renderGrowthStages();
    }
    
    // Render weather info if enabled
    if (this.showWeatherInfo) {
      this.renderWeatherInfo();
    }
  }
  
  /**
   * Render month view
   */
  renderMonthView() {
    const grid = document.getElementById('calendar-grid');
    const startOfMonth = new Date(this.currentDate.getFullYear(), this.currentDate.getMonth(), 1);
    const endOfMonth = new Date(this.currentDate.getFullYear(), this.currentDate.getMonth() + 1, 0);
    
    // Calculate calendar grid (6 weeks)
    const startOfCalendar = new Date(startOfMonth);
    startOfCalendar.setDate(startOfCalendar.getDate() - startOfCalendar.getDay());
    
    const endOfCalendar = new Date(startOfCalendar);
    endOfCalendar.setDate(endOfCalendar.getDate() + 41); // 6 weeks * 7 days - 1
    
    // Create calendar grid HTML
    let calendarHTML = `
      <div class="calendar-month-grid">
        <div class="calendar-weekdays">
          <div class="weekday">Sun</div>
          <div class="weekday">Mon</div>
          <div class="weekday">Tue</div>
          <div class="weekday">Wed</div>
          <div class="weekday">Thu</div>
          <div class="weekday">Fri</div>
          <div class="weekday">Sat</div>
        </div>
        <div class="calendar-days">
    `;
    
    // Generate calendar days
    const currentDateObj = new Date(startOfCalendar);
    
    for (let week = 0; week < 6; week++) {
      calendarHTML += '<div class="calendar-week">';
      
      for (let day = 0; day < 7; day++) {
        const isCurrentMonth = currentDateObj.getMonth() === this.currentDate.getMonth();
        const isToday = this.isSameDate(currentDateObj, new Date());
        const isSelected = this.isSameDate(currentDateObj, this.selectedDate);
        
        const dayClasses = [
          'calendar-day',
          !isCurrentMonth ? 'other-month' : '',
          isToday ? 'today' : '',
          isSelected ? 'selected' : ''
        ].filter(Boolean).join(' ');
        
        calendarHTML += `
          <div class="${dayClasses}" data-date="${currentDateObj.toISOString()}">
            <div class="day-header">
              <span class="day-number">${currentDateObj.getDate()}</span>
              <div class="day-weather" id="weather-${currentDateObj.toISOString().split('T')[0]}">
                <!-- Weather info will be rendered here -->
              </div>
            </div>
            <div class="day-content" id="day-${currentDateObj.toISOString().split('T')[0]}">
              <!-- Tasks will be rendered here -->
            </div>
            <div class="day-growth-stage" id="stage-${currentDateObj.toISOString().split('T')[0]}">
              <!-- Growth stage info will be rendered here -->
            </div>
          </div>
        `;
        
        currentDateObj.setDate(currentDateObj.getDate() + 1);
      }
      
      calendarHTML += '</div>';
    }
    
    calendarHTML += '</div></div>';
    grid.innerHTML = calendarHTML;
    
    // Add click listeners to days
    grid.querySelectorAll('.calendar-day').forEach(dayElement => {
      dayElement.addEventListener('click', (e) => {
        const date = new Date(e.currentTarget.dataset.date);
        this.selectDate(date);
      });
      
      dayElement.addEventListener('dblclick', (e) => {
        const date = new Date(e.currentTarget.dataset.date);
        this.showTaskEditor(date);
      });
    });
    
    // Render tasks for visible dates
    this.renderCalendarEvents();
  }
  
  /**
   * Render week view
   */
  renderWeekView() {
    const grid = document.getElementById('calendar-grid');
    const startOfWeek = this.getStartOfWeek(this.currentDate);
    const endOfWeek = new Date(startOfWeek);
    endOfWeek.setDate(endOfWeek.getDate() + 6);
    
    let weekHTML = `
      <div class="calendar-week-grid">
        <div class="week-header">
    `;
    
    // Generate week header
    const currentDateObj = new Date(startOfWeek);
    
    for (let day = 0; day < 7; day++) {
      const isToday = this.isSameDate(currentDateObj, new Date());
      const isSelected = this.isSameDate(currentDateObj, this.selectedDate);
      
      weekHTML += `
        <div class="week-day-header ${isToday ? 'today' : ''} ${isSelected ? 'selected' : ''}" 
             data-date="${currentDateObj.toISOString()}">
          <div class="day-name">${this.getDayName(currentDateObj, 'short')}</div>
          <div class="day-number">${currentDateObj.getDate()}</div>
          <div class="day-weather" id="weather-${currentDateObj.toISOString().split('T')[0]}">
            <!-- Weather info will be rendered here -->
          </div>
        </div>
      `;
      
      currentDateObj.setDate(currentDateObj.getDate() + 1);
    }
    
    weekHTML += '</div><div class="week-content">';
    
    // Generate time slots (24 hours)
    for (let hour = 0; hour < 24; hour++) {
      weekHTML += `
        <div class="time-slot" data-hour="${hour}">
          <div class="time-label">${this.formatHour(hour)}</div>
          <div class="time-columns">
      `;
      
      for (let day = 0; day < 7; day++) {
        const slotDate = new Date(startOfWeek);
        slotDate.setDate(slotDate.getDate() + day);
        slotDate.setHours(hour, 0, 0, 0);
        
        weekHTML += `
          <div class="time-column" data-date="${slotDate.toISOString()}" data-hour="${hour}" data-day="${day}">
            <!-- Events will be rendered here -->
          </div>
        `;
      }
      
      weekHTML += '</div></div>';
    }
    
    weekHTML += '</div></div>';
    grid.innerHTML = weekHTML;
    
    // Add event listeners
    this.setupWeekViewListeners();
    
    // Render tasks
    this.renderCalendarEvents();
  }
  
  /**
   * Render day view
   */
  renderDayView() {
    const grid = document.getElementById('calendar-grid');
    const selectedDate = new Date(this.currentDate);
    
    let dayHTML = `
      <div class="calendar-day-grid">
        <div class="day-header">
          <h3>${this.formatDate(selectedDate, 'full')}</h3>
          <div class="day-weather" id="weather-${selectedDate.toISOString().split('T')[0]}">
            <!-- Weather info will be rendered here -->
          </div>
          <div class="day-growth-stage" id="stage-${selectedDate.toISOString().split('T')[0]}">
            <!-- Growth stage info will be rendered here -->
          </div>
        </div>
        <div class="day-content">
    `;
    
    // Generate hourly time slots
    for (let hour = 0; hour < 24; hour++) {
      const slotDate = new Date(selectedDate);
      slotDate.setHours(hour, 0, 0, 0);
      
      dayHTML += `
        <div class="time-slot" data-hour="${hour}">
          <div class="time-label">${this.formatHour(hour)}</div>
          <div class="time-content" data-date="${slotDate.toISOString()}" data-hour="${hour}">
            <!-- Events will be rendered here -->
          </div>
        </div>
      `;
    }
    
    dayHTML += '</div></div>';
    grid.innerHTML = dayHTML;
    
    // Add event listeners
    this.setupDayViewListeners();
    
    // Render tasks
    this.renderCalendarEvents();
  }
  
  /**
   * Render list view
   */
  renderListView() {
    const listView = document.getElementById('calendar-list-view');
    
    // Get tasks for current filter
    const tasks = store.tasks ? store.tasks.tasks : [];
    
    // Group tasks by date
    const groupedTasks = this.groupTasksByDate(tasks);
    
    let listHTML = '<div class="task-list-container">';
    
    // Sort dates
    const sortedDates = Object.keys(groupedTasks).sort();
    
    for (const dateStr of sortedDates) {
      const date = new Date(dateStr);
      const tasksForDate = groupedTasks[dateStr];
      
      listHTML += `
        <div class="task-date-group">
          <div class="date-header">
            <h3>${this.formatDate(date, 'medium')}</h3>
            <span class="task-count">${tasksForDate.length} task${tasksForDate.length !== 1 ? 's' : ''}</span>
          </div>
          <div class="task-list">
      `;
      
      // Sort tasks by start time
      tasksForDate.sort((a, b) => new Date(a.start_date) - new Date(b.start_date));
      
      for (const task of tasksForDate) {
        const category = store.tasks?.categories.find(cat => cat.id === task.category_id);
        
        listHTML += `
          <div class="task-list-item" data-task-id="${task.id}">
            <div class="task-indicator" style="background-color: ${category?.color || '#3788d8'}"></div>
            <div class="task-content">
              <div class="task-header">
                <span class="task-title">${task.title}</span>
                <span class="task-status status-${task.status}">${task.status}</span>
              </div>
              <div class="task-details">
                <span class="task-time">${this.formatTaskTime(task)}</span>
                <span class="task-type">${task.task_type}</span>
                ${task.priority !== 'medium' ? `<span class="task-priority priority-${task.priority}">${task.priority}</span>` : ''}
              </div>
              ${task.description ? `<div class="task-description">${task.description}</div>` : ''}
            </div>
            <div class="task-actions">
              <button class="btn-icon" onclick="calendarManager.editTask(${task.id})">
                <i class="fas fa-edit"></i>
              </button>
              <button class="btn-icon" onclick="calendarManager.toggleTaskStatus(${task.id})">
                <i class="fas fa-check"></i>
              </button>
            </div>
          </div>
        `;
      }
      
      listHTML += '</div></div>';
    }
    
    if (sortedDates.length === 0) {
      listHTML += `
        <div class="empty-state">
          <i class="fas fa-calendar-check"></i>
          <h3>No tasks found</h3>
          <p>No tasks match your current filter criteria.</p>
          <button class="btn-primary" onclick="calendarManager.showTaskEditor()">
            <i class="fas fa-plus"></i> Add Your First Task
          </button>
        </div>
      `;
    }
    
    listHTML += '</div>';
    listView.innerHTML = listHTML;
    
    // Add click listeners to task items
    listView.querySelectorAll('.task-list-item').forEach(item => {
      item.addEventListener('click', (e) => {
        if (!e.target.closest('.task-actions')) {
          const taskId = parseInt(item.dataset.taskId);
          this.selectTask(taskId);
        }
      });
    });
  }
  
  /**
   * Render Gantt chart view
   */
  renderGanttView() {
    const ganttView = document.getElementById('calendar-gantt-view');
    
    // Get tasks for Gantt chart
    const tasks = store.tasks ? store.tasks.tasks : [];
    
    // Import and use Gantt chart module
    import('./gantt-chart.js').then(({ default: GanttChart }) => {
      const ganttChart = new GanttChart(ganttView, {
        tasks: tasks,
        startDate: this.getGanttStartDate(),
        endDate: this.getGanttEndDate(),
        onTaskClick: (task) => this.selectTask(task.id),
        onTaskUpdate: (task, updates) => this.updateTask(task.id, updates)
      });
      
      ganttChart.render();
    });
  }
  
  /**
   * Render calendar events (tasks)
   */
  renderCalendarEvents() {
    if (!store.tasks || !store.tasks.tasks) {
      return;
    }
    
    const tasks = store.tasks.tasks;
    
    // Clear existing events
    document.querySelectorAll('.task-event').forEach(event => event.remove());
    
    // Render tasks based on current view
    switch (this.currentView) {
      case 'month':
        this.renderMonthEvents(tasks);
        break;
      case 'week':
        this.renderWeekEvents(tasks);
        break;
      case 'day':
        this.renderDayEvents(tasks);
        break;
    }
  }
  
  /**
   * Render calendar legend
   */
  renderLegend() {
    // Render category legend
    const categoryLegend = document.getElementById('category-legend');
    if (categoryLegend) {
      const categories = store.tasks?.categories || [];
      categoryLegend.innerHTML = categories.map(category => `
        <div class="legend-item">
          <div class="legend-color" style="background-color: ${category.color}"></div>
          <span>${category.name}</span>
        </div>
      `).join('');
    }

    // Render growth stage legend if enabled
    const growthStageLegend = document.getElementById('growth-stage-legend');
    const stageLegend = document.getElementById('stage-legend');
    if (this.showGrowthStages && growthStageLegend && stageLegend) {
      const stages = store.growth?.stages || [];
      if (stages.length > 0) {
        growthStageLegend.style.display = 'block';
        stageLegend.innerHTML = stages.map(stage => `
          <div class="legend-item">
            <div class="legend-color" style="background-color: ${stage.color || '#6c757d'}"></div>
            <span>${stage.stage_name}</span>
          </div>
        `).join('');
      } else {
        growthStageLegend.style.display = 'none';
      }
    }
  }
  
  /**
   * Render events for month view
   */
  renderMonthEvents(tasks) {
    tasks.forEach(task => {
      const taskDate = new Date(task.start_date);
      const dateStr = taskDate.toISOString().split('T')[0];
      const dayContainer = document.getElementById(`day-${dateStr}`);
      
      if (dayContainer) {
        const category = store.tasks?.categories.find(cat => cat.id === task.category_id);
        
        const eventElement = document.createElement('div');
        eventElement.className = `task-event priority-${task.priority} status-${task.status}`;
        eventElement.dataset.taskId = task.id;
        eventElement.style.backgroundColor = category?.color || '#3788d8';
        
        eventElement.innerHTML = `
          <div class="event-content">
            <span class="event-title">${task.title}</span>
            <span class="event-time">${task.is_all_day ? 'All day' : this.formatTime(taskDate)}</span>
          </div>
        `;
        
        // Add click listener
        eventElement.addEventListener('click', (e) => {
          e.stopPropagation();
          this.selectTask(task.id);
        });
        
        dayContainer.appendChild(eventElement);
      }
    });
  }
  
  /**
   * Render events for week view
   */
  renderWeekEvents(tasks) {
    tasks.forEach(task => {
      const startDate = new Date(task.start_date);
      const endDate = task.end_date ? new Date(task.end_date) : startDate;
      
      if (task.is_all_day) {
        // Render all-day event
        this.renderAllDayEvent(task, startDate, endDate);
      } else {
        // Render timed event
        this.renderTimedEvent(task, startDate, endDate);
      }
    });
  }
  
  /**
   * Render events for day view
   */
  renderDayEvents(tasks) {
    const selectedDate = this.currentDate;
    
    tasks.forEach(task => {
      const taskDate = new Date(task.start_date);
      
      // Only show tasks for selected date
      if (this.isSameDate(taskDate, selectedDate)) {
        const hour = taskDate.getHours();
        const timeContent = document.querySelector(`.time-content[data-hour="${hour}"]`);
        
        if (timeContent) {
          const category = store.tasks?.categories.find(cat => cat.id === task.category_id);
          
          const eventElement = document.createElement('div');
          eventElement.className = `task-event priority-${task.priority} status-${task.status}`;
          eventElement.dataset.taskId = task.id;
          eventElement.style.backgroundColor = category?.color || '#3788d8';
          
          eventElement.innerHTML = `
            <div class="event-content">
              <span class="event-title">${task.title}</span>
              <span class="event-time">${this.formatTaskTime(task)}</span>
              <span class="event-type">${task.task_type}</span>
            </div>
          `;
          
          // Add click listener
          eventElement.addEventListener('click', (e) => {
            e.stopPropagation();
            this.selectTask(task.id);
          });
          
          timeContent.appendChild(eventElement);
        }
      }
    });
  }
  
  /**
   * Render growth stages
   */
  renderGrowthStages() {
    if (!store.growth || !store.growth.stages) {
      return;
    }

    const stages = store.growth.stages;
    const fields = store.fields || [];

    // Clear existing growth stage indicators
    document.querySelectorAll('.day-growth-stage').forEach(el => el.innerHTML = '');

    // For each field, render its growth stages
    fields.forEach(field => {
      if (!field.growth_stages) return;

      // Get the current growth stage for this field
      const currentStage = field.growth_stages.find(stage => {
        const stageDate = new Date(stage.date);
        return stageDate <= new Date() && 
               (!stage.end_date || new Date(stage.end_date) >= new Date());
      });

      if (!currentStage) return;

      // Find the stage definition
      const stageDef = stages.find(s => s.id === currentStage.stage_id);
      if (!stageDef) return;

      // Render the growth stage indicator for the current date
      const dateStr = new Date().toISOString().split('T')[0];
      const stageContainer = document.getElementById(`stage-${dateStr}`);
      
      if (stageContainer) {
        const stageElement = document.createElement('div');
        stageElement.className = 'growth-stage-indicator';
        stageElement.style.backgroundColor = stageDef.color || '#6c757d';
        
        stageElement.innerHTML = `
          <div class="stage-content">
            <span class="stage-name">${stageDef.stage_name}</span>
            <span class="field-name">${field.name}</span>
          </div>
        `;

        // Add tooltip with more details
        stageElement.title = `
          Field: ${field.name}
          Stage: ${stageDef.stage_name}
          Started: ${new Date(currentStage.date).toLocaleDateString()}
          ${currentStage.end_date ? `Ends: ${new Date(currentStage.end_date).toLocaleDateString()}` : ''}
          ${stageDef.description ? `\nDescription: ${stageDef.description}` : ''}
        `;

        stageContainer.appendChild(stageElement);
      }

      // If we have a forecast, render future stages
      if (field.growth_forecast) {
        field.growth_forecast.forEach(forecast => {
          const forecastDate = new Date(forecast.date);
          const dateStr = forecastDate.toISOString().split('T')[0];
          const stageContainer = document.getElementById(`stage-${dateStr}`);
          
          if (stageContainer) {
            const stageDef = stages.find(s => s.id === forecast.stage_id);
            if (!stageDef) return;

            const stageElement = document.createElement('div');
            stageElement.className = 'growth-stage-indicator forecast';
            stageElement.style.backgroundColor = stageDef.color || '#6c757d';
            stageElement.style.opacity = '0.6'; // Make forecast stages appear faded
            
            stageElement.innerHTML = `
              <div class="stage-content">
                <span class="stage-name">${stageDef.stage_name}</span>
                <span class="field-name">${field.name}</span>
                <span class="forecast-label">Forecast</span>
              </div>
            `;

            // Add tooltip with forecast details
            stageElement.title = `
              Field: ${field.name}
              Forecasted Stage: ${stageDef.stage_name}
              Expected Date: ${forecastDate.toLocaleDateString()}
              ${stageDef.description ? `\nDescription: ${stageDef.description}` : ''}
              ${forecast.confidence ? `\nConfidence: ${forecast.confidence}%` : ''}
            `;

            stageContainer.appendChild(stageElement);
          }
        });
      }
    });
  }
  
  /**
   * Utility methods
   */
  
  isSameDate(date1, date2) {
    return date1.toDateString() === date2.toDateString();
  }
  
  getStartOfWeek(date) {
    const startOfWeek = new Date(date);
    startOfWeek.setDate(date.getDate() - date.getDay());
    startOfWeek.setHours(0, 0, 0, 0);
    return startOfWeek;
  }
  
  formatDate(date, format = 'medium') {
    const options = {
      short: { month: 'short', day: 'numeric' },
      medium: { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' },
      full: { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' }
    };
    
    return date.toLocaleDateString('en-US', options[format] || options.medium);
  }
  
  formatTime(date) {
    return date.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    });
  }
  
  formatHour(hour) {
    const date = new Date();
    date.setHours(hour, 0, 0, 0);
    return this.formatTime(date);
  }
  
  getDayName(date, format = 'long') {
    const options = { weekday: format };
    return date.toLocaleDateString('en-US', options);
  }
  
  formatTaskTime(task) {
    const startDate = new Date(task.start_date);
    
    if (task.is_all_day) {
      return 'All day';
    }
    
    if (task.end_date) {
      const endDate = new Date(task.end_date);
      return `${this.formatTime(startDate)} - ${this.formatTime(endDate)}`;
    }
    
    return this.formatTime(startDate);
  }
  
  /**
   * Navigation methods
   */
  
  navigateDate(direction) {
    const newDate = new Date(this.currentDate);
    
    switch (this.currentView) {
      case 'month':
        newDate.setMonth(newDate.getMonth() + direction);
        break;
      case 'week':
        newDate.setDate(newDate.getDate() + (direction * 7));
        break;
      case 'day':
        newDate.setDate(newDate.getDate() + direction);
        break;
    }
    
    this.setCurrentDate(newDate);
  }
  
  goToToday() {
    this.setCurrentDate(new Date());
  }
  
  setCurrentDate(date) {
    this.currentDate = new Date(date);
    this.render();
  }
  
  selectDate(date) {
    this.selectedDate = new Date(date);
    this.render();
  }
  
  setView(view) {
    if (this.currentView === view) return;
    
    // Update view toggle buttons
    document.querySelectorAll('.view-toggle').forEach(btn => {
      btn.classList.remove('active');
    });
    
    document.querySelector(`[data-view="${view}"]`).classList.add('active');
    
    this.currentView = view;
    this.render();
  }
  
  showView(view) {
    // Hide all view containers
    document.getElementById('calendar-grid').style.display = 
      ['month', 'week', 'day'].includes(view) ? 'block' : 'none';
    document.getElementById('calendar-list-view').style.display = 
      view === 'list' ? 'block' : 'none';
    document.getElementById('calendar-gantt-view').style.display = 
      view === 'gantt' ? 'block' : 'none';
  }
  
  updateDateTitle() {
    const titleElement = document.getElementById('calendar-date-title');
    
    switch (this.currentView) {
      case 'month':
        titleElement.textContent = this.currentDate.toLocaleDateString('en-US', {
          year: 'numeric',
          month: 'long'
        });
        break;
      case 'week':
        const startOfWeek = this.getStartOfWeek(this.currentDate);
        const endOfWeek = new Date(startOfWeek);
        endOfWeek.setDate(endOfWeek.getDate() + 6);
        titleElement.textContent = `${startOfWeek.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} - ${endOfWeek.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}`;
        break;
      case 'day':
        titleElement.textContent = this.formatDate(this.currentDate, 'full');
        break;
      case 'list':
        titleElement.textContent = 'Task List';
        break;
      case 'gantt':
        titleElement.textContent = 'Project Timeline';
        break;
    }
  }
  
  /**
   * Task management methods
   */
  
  selectTask(taskId) {
    this.selectedTaskId = taskId;
    
    if (store.tasks) {
      store.tasks.selectTask(taskId);
    }
    
    this.showTaskDetailPanel(taskId);
  }
  
  showTaskDetailPanel(taskId) {
    const task = store.tasks?.getTaskById(taskId);
    if (!task) return;
    
    const panel = document.getElementById('task-detail-panel');
    const content = panel.querySelector('.task-detail-content');
    
    const category = store.tasks?.categories.find(cat => cat.id === task.category_id);
    
    content.innerHTML = `
      <div class="task-detail-header">
        <h3>${task.title}</h3>
        <button class="btn-close" onclick="calendarManager.hideTaskDetailPanel()">
          <i class="fas fa-times"></i>
        </button>
      </div>
      <div class="task-detail-body">
        <div class="task-info">
          <div class="info-item">
            <label>Type:</label>
            <span>${task.task_type}</span>
          </div>
          <div class="info-item">
            <label>Status:</label>
            <span class="status-badge status-${task.status}">${task.status}</span>
          </div>
          <div class="info-item">
            <label>Priority:</label>
            <span class="priority-badge priority-${task.priority}">${task.priority}</span>
          </div>
          <div class="info-item">
            <label>Date:</label>
            <span>${this.formatTaskTime(task)}</span>
          </div>
          ${task.description ? `
            <div class="info-item">
              <label>Description:</label>
              <p>${task.description}</p>
            </div>
          ` : ''}
          ${category ? `
            <div class="info-item">
              <label>Category:</label>
              <span class="category-badge" style="background-color: ${category.color}">
                ${category.icon ? `<i class="${category.icon}"></i>` : ''} ${category.name}
              </span>
            </div>
          ` : ''}
        </div>
        <div class="task-actions">
          <button class="btn-primary" onclick="calendarManager.editTask(${task.id})">
            <i class="fas fa-edit"></i> Edit Task
          </button>
          <button class="btn-secondary" onclick="calendarManager.toggleTaskStatus(${task.id})">
            <i class="fas fa-check"></i> ${task.status === 'completed' ? 'Mark Pending' : 'Mark Complete'}
          </button>
          <button class="btn-danger" onclick="calendarManager.deleteTask(${task.id})">
            <i class="fas fa-trash"></i> Delete
          </button>
        </div>
      </div>
    `;
    
    panel.style.display = 'block';
  }
  
  hideTaskDetailPanel() {
    document.getElementById('task-detail-panel').style.display = 'none';
    this.selectedTaskId = null;
  }
  
  /**
   * Cleanup
   */
  destroy() {
    if (this.unsubscribe) {
      this.unsubscribe();
    }
    
    // Remove event listeners
    // Clean up resources
    
    console.log('Calendar manager destroyed');
  }
}

// Export for use in other modules
export default CalendarManager;

// Global instance for backward compatibility
window.CalendarManager = CalendarManager;
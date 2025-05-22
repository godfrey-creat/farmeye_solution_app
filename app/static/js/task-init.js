/**
 * Task Management System Initialization
 */
import store from './store/index.js';
import TaskManager from './modules/task-manager.js';
import CalendarManager from './modules/calendar-manager.js';
import TaskAnalytics from './modules/task-analytics.js';

// Global task management instances
let taskManager;
let calendarManager;
let taskAnalytics;

/**
 * Initialize task management system
 */
async function initializeTaskManagement() {
  try {
    console.log('Initializing FarmEye Task Management System...');
    
    // Wait for store to be initialized
    if (!store.initialized) {
      await store.initialize();
    }
    
    // Initialize task manager
    taskManager = new TaskManager({
      enableAnalytics: true,
      enableRecurrence: true,
      enableBulkActions: true
    });
    
    // Initialize calendar manager if calendar container exists
    const calendarContainer = document.getElementById('task-calendar');
    if (calendarContainer) {
      calendarManager = new CalendarManager('task-calendar', {
        view: 'month',
        showGrowthStages: true,
        showWeatherInfo: true,
        allowTaskCreation: true
      });
    }
    
    // Initialize analytics dashboard if container exists
    const analyticsContainer = document.getElementById('task-analytics');
    if (analyticsContainer) {
      taskAnalytics = new TaskAnalytics('task-analytics');
    }
    
    // Make instances globally available
    window.taskManager = taskManager;
    window.calendarManager = calendarManager;
    window.taskAnalytics = taskAnalytics;
    
    // Setup global shortcuts and integration
    setupGlobalIntegration();
    
    console.log('Task Management System initialized successfully');
    
  } catch (error) {
    console.error('Error initializing task management system:', error);
  }
}

/**
 * Setup global integration
 */
function setupGlobalIntegration() {
  // Add task management to main navigation
  addTaskNavigationItems();
  
  // Setup dashboard widgets
  setupDashboardWidgets();
  
  // Setup quick action buttons
  setupQuickActions();
}

/**
 * Add task management items to navigation
 */
function addTaskNavigationItems() {
  const sidebarNav = document.querySelector('.sidebar-nav');
  if (!sidebarNav) return;
  
  // Check if task items already exist
  if (document.getElementById('nav-tasks')) return;
  
  const taskNavHTML = `
    <li class="nav-item" id="nav-tasks">
      <a href="/dashboard/schedule" class="nav-link">
        <i class="fas fa-tasks"></i>
        <span>Tasks</span>
      </a>
    </li>
    <li class="nav-item" id="nav-calendar">
      <a href="#" class="nav-link" onclick="showTaskCalendar()">
        <i class="fas fa-calendar-alt"></i>
        <span>Calendar</span>
      </a>
    </li>
    <li class="nav-item" id="nav-analytics">
      <a href="#" class="nav-link" onclick="showTaskAnalytics()">
        <i class="fas fa-chart-bar"></i>
        <span>Analytics</span>
      </a>
    </li>
  `;
  
  sidebarNav.insertAdjacentHTML('beforeend', taskNavHTML);
}

/**
 * Setup dashboard widgets
 */
function setupDashboardWidgets() {
  // Add quick task summary to dashboard
  const dashboardContent = document.querySelector('.dashboard-content');
  if (!dashboardContent) return;
  
  // Check if widget already exists
  if (document.getElementById('task-summary-widget')) return;
  
  const widgetHTML = `
    <div class="dashboard-widget" id="task-summary-widget">
      <div class="widget-header">
        <h4>Task Summary</h4>
        <button class="btn-icon" onclick="taskManager.showTaskEditor()">
          <i class="fas fa-plus"></i>
        </button>
      </div>
      <div class="widget-content">
        <div class="task-summary-grid">
          <div class="summary-item">
            <span class="count" id="widget-pending-count">0</span>
            <span class="label">Pending</span>
          </div>
          <div class="summary-item">
            <span class="count" id="widget-today-count">0</span>
            <span class="label">Due Today</span>
          </div>
          <div class="summary-item">
            <span class="count" id="widget-completed-count">0</span>
            <span class="label">Completed</span>
          </div>
        </div>
        <div class="widget-actions">
          <button class="btn-secondary btn-sm" onclick="showTaskCalendar()">
            View Calendar
          </button>
          <button class="btn-primary btn-sm" onclick="taskManager.createTask()">
            Add Task
          </button>
        </div>
      </div>
    </div>
  `;
  
  dashboardContent.insertAdjacentHTML('afterbegin', widgetHTML);
  
  // Update widget with real data
  updateDashboardWidget();
  
  // Subscribe to updates
  store.subscribe(action => {
    if (['TASKS_LOADED', 'TASK_CREATED', 'TASK_UPDATED', 'TASK_DELETED', 'TASK_STATISTICS_LOADED'].includes(action.type)) {
      updateDashboardWidget();
    }
  });
}

/**
 * Update dashboard widget
 */
function updateDashboardWidget() {
  const statistics = store.tasks?.statistics;
  if (!statistics) return;
  
  const pendingCount = document.getElementById('widget-pending-count');
  const todayCount = document.getElementById('widget-today-count');
  const completedCount = document.getElementById('widget-completed-count');
  
  if (pendingCount) pendingCount.textContent = statistics.counts.pending || 0;
  if (todayCount) todayCount.textContent = statistics.counts.due_today || 0;
  if (completedCount) completedCount.textContent = statistics.counts.completed || 0;
}

/**
 * Setup quick action buttons
 */
function setupQuickActions() {
  // Add floating action button for quick task creation
  const fabHTML = `
    <div class="floating-action-button" id="task-fab" onclick="taskManager.createTask()">
      <i class="fas fa-plus"></i>
    </div>
  `;
  
  document.body.insertAdjacentHTML('beforeend', fabHTML);
}

/**
 * Global utility functions
 */
window.showTaskCalendar = function() {
  if (calendarManager) {
    // Show calendar in modal or navigate to calendar page
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.innerHTML = `
      <div class="modal-container" style="width: 95%; max-width: 1200px; height: 90vh;">
        <div class="modal-header">
          <h3>Task Calendar</h3>
          <button class="btn-close" onclick="this.closest('.modal-overlay').remove()">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="modal-body" style="height: calc(90vh - 120px); padding: 0;">
          <div id="modal-calendar" style="height: 100%;"></div>
        </div>
      </div>
    `;
    
    document.body.appendChild(modal);
    
    // Initialize calendar in modal
    new CalendarManager('modal-calendar', {
      view: 'month',
      showGrowthStages: true,
      showWeatherInfo: true,
      allowTaskCreation: true
    });
  }
};

window.showTaskAnalytics = function() {
  if (taskAnalytics) {
    // Show analytics in modal
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.innerHTML = `
      <div class="modal-container" style="width: 95%; max-width: 1400px; height: 90vh;">
        <div class="modal-header">
          <h3>Task Analytics</h3>
          <button class="btn-close" onclick="this.closest('.modal-overlay').remove()">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="modal-body" style="height: calc(90vh - 120px); padding: 0;">
          <div id="modal-analytics" style="height: 100%;"></div>
        </div>
      </div>
    `;
    
    document.body.appendChild(modal);
    
    // Initialize analytics in modal
    new TaskAnalytics('modal-analytics');
  }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', initializeTaskManagement);

// Export for manual initialization
export { initializeTaskManagement, taskManager, calendarManager, taskAnalytics };
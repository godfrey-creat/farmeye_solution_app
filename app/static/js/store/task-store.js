/**
 * Task Store
 * Manages tasks data and operations
 */
class TaskStore {
  constructor(rootStore) {
    this.rootStore = rootStore;
    
    // Task data
    this.tasks = [];
    this.categories = [];
    this.loading = false;
    this.error = null;
    
    // Task filter state
    this.filter = {
      startDate: new Date(),
      endDate: new Date(new Date().setDate(new Date().getDate() + 30)),
      view: 'month', // month, week, day, list, gantt
      taskType: 'all',
      status: 'all',
      farmId: null,
      fieldId: null,
      categoryId: null
    };
    
    // Selected task
    this.selectedTaskId = null;
    
    // Cache for task recommendations
    this.recommendedTasks = [];
    this.upcomingTasks = [];
    this.statistics = null;
    
    // Bind methods
    this.initialize = this.initialize.bind(this);
    this.fetchTasks = this.fetchTasks.bind(this);
    this.fetchCategories = this.fetchCategories.bind(this);
    this.createTask = this.createTask.bind(this);
    this.updateTask = this.updateTask.bind(this);
    this.deleteTask = this.deleteTask.bind(this);
    this.selectTask = this.selectTask.bind(this);
    this.setFilter = this.setFilter.bind(this);
    this.fetchTaskStatistics = this.fetchTaskStatistics.bind(this);
    this.fetchUpcomingTasks = this.fetchUpcomingTasks.bind(this);
    this.fetchRecommendedTasks = this.fetchRecommendedTasks.bind(this);
  }
  
  /**
   * Initialize task store
   */
  async initialize() {
    try {
      // Load task categories first (they're needed for task creation)
      await this.fetchCategories();
      
      // Load initial tasks with default filter
      await this.fetchTasks();
      
      // Load upcoming tasks for dashboard
      await this.fetchUpcomingTasks();
      
      // Load task statistics
      await this.fetchTaskStatistics();
      
      console.log('Task store initialized');
      return true;
    } catch (error) {
      console.error('Error initializing task store:', error);
      this.error = error.message;
      this.rootStore.notifySubscribers({ 
        type: 'TASKS_LOAD_ERROR', 
        payload: error.message 
      });
      return false;
    }
  }
  
  /**
   * Fetch tasks based on current filter
   */
  async fetchTasks() {
    try {
      this.loading = true;
      this.rootStore.notifySubscribers({ type: 'TASKS_LOADING' });
      
      // Build query parameters
      const params = new URLSearchParams();
      params.append('start_date', this.filter.startDate.toISOString());
      params.append('end_date', this.filter.endDate.toISOString());
      
      if (this.filter.farmId) {
        params.append('farm_id', this.filter.farmId);
      }
      
      if (this.filter.fieldId) {
        params.append('field_id', this.filter.fieldId);
      }
      
      if (this.filter.status && this.filter.status !== 'all') {
        params.append('status', this.filter.status);
      }
      
      if (this.filter.taskType && this.filter.taskType !== 'all') {
        params.append('task_type', this.filter.taskType);
      }
      
      if (this.filter.categoryId) {
        params.append('category_id', this.filter.categoryId);
      }
      
      // Make API request
      const response = await fetch(`/tasks/api/tasks?${params.toString()}`);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch tasks: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      if (data.status === 'success') {
        this.tasks = data.tasks;
        this.error = null;
        this.rootStore.notifySubscribers({ 
          type: 'TASKS_LOADED', 
          payload: this.tasks 
        });
      } else {
        throw new Error(data.message || 'Unknown error fetching tasks');
      }
      
      return this.tasks;
    } catch (error) {
      console.error('Error fetching tasks:', error);
      this.error = error.message;
      this.rootStore.notifySubscribers({ 
        type: 'TASKS_LOAD_ERROR', 
        payload: error.message 
      });
      return [];
    } finally {
      this.loading = false;
    }
  }
  
  /**
   * Fetch task categories
   */
  async fetchCategories() {
    try {
      const response = await fetch('/tasks/api/task-categories');
      
      if (!response.ok) {
        throw new Error(`Failed to fetch categories: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      if (data.status === 'success') {
        this.categories = data.categories;
        this.rootStore.notifySubscribers({ 
          type: 'TASK_CATEGORIES_LOADED', 
          payload: this.categories 
        });
      } else {
        throw new Error(data.message || 'Unknown error fetching task categories');
      }
      
      return this.categories;
    } catch (error) {
      console.error('Error fetching task categories:', error);
      return [];
    }
  }
  
  /**
   * Create a new task
   * @param {Object} taskData Task data
   */
  async createTask(taskData) {
    try {
      this.rootStore.notifySubscribers({ type: 'TASK_CREATING' });
      
      const response = await fetch('/tasks/api/tasks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(taskData),
      });
      
      if (!response.ok) {
        throw new Error(`Failed to create task: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      if (data.status === 'success') {
        // Add new task to list
        this.tasks.push(data.task);
        
        // Notify subscribers
        this.rootStore.notifySubscribers({ 
          type: 'TASK_CREATED', 
          payload: data.task 
        });
        
        // Refresh upcoming tasks and statistics
        this.fetchUpcomingTasks();
        this.fetchTaskStatistics();
        
        return data.task;
      } else {
        throw new Error(data.message || 'Unknown error creating task');
      }
    } catch (error) {
      console.error('Error creating task:', error);
      this.rootStore.notifySubscribers({ 
        type: 'TASK_CREATE_ERROR', 
        payload: error.message 
      });
      throw error;
    }
  }
  
  /**
   * Update an existing task
   * @param {number} taskId Task ID
   * @param {Object} taskData Updated task data
   */
  async updateTask(taskId, taskData) {
    try {
      this.rootStore.notifySubscribers({ 
        type: 'TASK_UPDATING',
        payload: { taskId } 
      });
      
      const response = await fetch(`/tasks/api/tasks/${taskId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(taskData),
      });
      
      if (!response.ok) {
        throw new Error(`Failed to update task: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      if (data.status === 'success') {
        // Update task in list
        const index = this.tasks.findIndex(task => task.id === taskId);
        if (index !== -1) {
          this.tasks[index] = data.task;
        }
        
        // Notify subscribers
        this.rootStore.notifySubscribers({ 
          type: 'TASK_UPDATED', 
          payload: data.task 
        });
        
        // Refresh related data
        this.fetchUpcomingTasks();
        this.fetchTaskStatistics();
        
        return data.task;
      } else {
        throw new Error(data.message || 'Unknown error updating task');
      }
    } catch (error) {
      console.error('Error updating task:', error);
      this.rootStore.notifySubscribers({ 
        type: 'TASK_UPDATE_ERROR', 
        payload: { taskId, error: error.message } 
      });
      throw error;
    }
  }
  
  /**
   * Delete a task
   * @param {number} taskId Task ID
   */
  async deleteTask(taskId) {
    try {
      this.rootStore.notifySubscribers({ 
        type: 'TASK_DELETING',
        payload: { taskId } 
      });
      
      const response = await fetch(`/tasks/api/tasks/${taskId}`, {
        method: 'DELETE',
      });
      
      if (!response.ok) {
        throw new Error(`Failed to delete task: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      if (data.status === 'success') {
        // Remove task from list
        this.tasks = this.tasks.filter(task => task.id !== taskId);
        
        // If this was the selected task, clear selection
        if (this.selectedTaskId === taskId) {
          this.selectedTaskId = null;
        }
        
        // Notify subscribers
        this.rootStore.notifySubscribers({ 
          type: 'TASK_DELETED', 
          payload: { taskId } 
        });
        
        // Refresh related data
        this.fetchUpcomingTasks();
        this.fetchTaskStatistics();
        
        return true;
      } else {
        throw new Error(data.message || 'Unknown error deleting task');
      }
    } catch (error) {
      console.error('Error deleting task:', error);
      this.rootStore.notifySubscribers({ 
        type: 'TASK_DELETE_ERROR', 
        payload: { taskId, error: error.message } 
      });
      throw error;
    }
  }
  
  /**
   * Select a task
   * @param {number} taskId Task ID to select
   */
  selectTask(taskId) {
    this.selectedTaskId = taskId;
    
    this.rootStore.notifySubscribers({ 
      type: 'TASK_SELECTED', 
      payload: { taskId } 
    });
    
    return this.getTaskById(taskId);
  }
  
  /**
   * Get task by ID
   * @param {number} taskId Task ID
   */
  getTaskById(taskId) {
    return this.tasks.find(task => task.id === taskId);
  }
  
  /**
   * Update task filters
   * @param {Object} filterUpdates Filter updates
   */
  setFilter(filterUpdates) {
    this.filter = { ...this.filter, ...filterUpdates };
    
    this.rootStore.notifySubscribers({ 
      type: 'TASK_FILTER_CHANGED', 
      payload: this.filter 
    });
    
    // Fetch tasks with new filter
    this.fetchTasks();
    
    return this.filter;
  }
  
  /**
   * Fetch task statistics
   */
  async fetchTaskStatistics() {
    try {
      let url = '/tasks/api/tasks/statistics';
      
      if (this.filter.farmId) {
        url += `?farm_id=${this.filter.farmId}`;
      }
      
      const response = await fetch(url);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch task statistics: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      if (data.status === 'success') {
        this.statistics = data;
        
        this.rootStore.notifySubscribers({ 
          type: 'TASK_STATISTICS_LOADED', 
          payload: data 
        });
        
        return data;
      } else {
        throw new Error(data.message || 'Unknown error fetching task statistics');
      }
    } catch (error) {
      console.error('Error fetching task statistics:', error);
      return null;
    }
  }
  
  /**
   * Fetch upcoming tasks
   * @param {number} days Number of days ahead
   */
  async fetchUpcomingTasks(days = 7) {
    try {
      const response = await fetch(`/tasks/api/tasks/upcoming?days=${days}`);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch upcoming tasks: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      if (data.status === 'success') {
        this.upcomingTasks = data.tasks;
        
        this.rootStore.notifySubscribers({ 
          type: 'UPCOMING_TASKS_LOADED', 
          payload: data.tasks 
        });
        
        return data.tasks;
      } else {
        throw new Error(data.message || 'Unknown error fetching upcoming tasks');
      }
    } catch (error) {
      console.error('Error fetching upcoming tasks:', error);
      return [];
    }
  }
  
  /**
   * Fetch recommended tasks based on growth stages
   * @param {number} farmId Farm ID
   */
  async fetchRecommendedTasks(farmId) {
    try {
      if (!farmId && this.filter.farmId) {
        farmId = this.filter.farmId;
      }
      
      if (!farmId) {
        return [];
      }
      
      const response = await fetch(`/tasks/api/tasks/recommended?farm_id=${farmId}`);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch recommended tasks: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      if (data.status === 'success') {
        this.recommendedTasks = data.recommended_tasks;
        
        this.rootStore.notifySubscribers({ 
          type: 'RECOMMENDED_TASKS_LOADED', 
          payload: data.recommended_tasks 
        });
        
        return data.recommended_tasks;
      } else {
        throw new Error(data.message || 'Unknown error fetching recommended tasks');
      }
    } catch (error) {
      console.error('Error fetching recommended tasks:', error);
      return [];
    }
  }
  
  /**
   * Get tasks for a specific date range
   * @param {Date} startDate Range start date
   * @param {Date} endDate Range end date
   */
  getTasksForDateRange(startDate, endDate) {
    return this.tasks.filter(task => {
      const taskStart = new Date(task.start_date);
      const taskEnd = task.end_date ? new Date(task.end_date) : taskStart;
      
      // Task starts or ends within the range, or spans the entire range
      return (
        (taskStart >= startDate && taskStart <= endDate) ||
        (taskEnd >= startDate && taskEnd <= endDate) ||
        (taskStart <= startDate && taskEnd >= endDate)
      );
    });
  }
  
  /**
   * Convert a task to calendar event format
   * @param {Object} task Task object
   */
  taskToCalendarEvent(task) {
    // Find category for color
    const category = this.categories.find(cat => cat.id === task.category_id) || {
      color: '#3788d8',
      name: 'Default'
    };
    
    return {
      id: task.id,
      title: task.title,
      start: task.start_date,
      end: task.end_date || task.start_date,
      allDay: task.is_all_day,
      backgroundColor: category.color,
      borderColor: category.color,
      textColor: '#ffffff',
      extendedProps: {
        taskId: task.id,
        taskType: task.task_type,
        description: task.description,
        status: task.status,
        priority: task.priority,
        farmId: task.farm_id,
        fieldId: task.field_id,
        categoryId: task.category_id,
        categoryName: category.name
      }
    };
  }
  
  /**
   * Get all tasks as calendar events
   */
  getTasksAsCalendarEvents() {
    return this.tasks.map(task => this.taskToCalendarEvent(task));
  }
}

export default TaskStore;
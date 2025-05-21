// store/task-store.js
class TaskStore {
  constructor(rootStore) {
    this.rootStore = rootStore;
    this.tasks = [];
    this.categories = [];
    this.filter = {
      startDate: new Date(),
      view: 'month', // month, week, day, list, gantt
      taskType: 'all',
      status: 'all',
      assignee: 'all'
    };
  }
  
  async initialize() {
    await this.fetchTasks();
    await this.fetchCategories();
  }
  
  async fetchTasks(params = {}) {
    try {
      const response = await fetch('/api/tasks?' + new URLSearchParams(params));
      if (!response.ok) throw new Error('Failed to fetch tasks');
      
      const data = await response.json();
      this.tasks = data.tasks;
      
      this.rootStore.notifySubscribers({ 
        type: 'TASKS_LOADED', 
        payload: this.tasks 
      });
      
      return this.tasks;
    } catch (error) {
      console.error('Error fetching tasks:', error);
      return [];
    }
  }
  
  // CRUD operations for tasks
  async createTask(taskData) {
    try {
      const response = await fetch('/api/tasks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(taskData),
      });
      
      if (!response.ok) throw new Error('Failed to create task');
      
      const data = await response.json();
      this.tasks.push(data.task);
      
      this.rootStore.notifySubscribers({ 
        type: 'TASK_CREATED', 
        payload: data.task 
      });
      
      return data.task;
    } catch (error) {
      console.error('Error creating task:', error);
      throw error;
    }
  }
  
  // Additional methods for updating and deleting tasks
  // Methods for filtering and organizing tasks by date, type, etc.
}

export default TaskStore;
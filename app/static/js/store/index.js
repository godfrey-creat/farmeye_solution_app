/**
 * Main Store Manager for FarmEye
 * Centralizes state management and coordinates between different store modules
 */
class Store {
  constructor() {
    // Initialize store modules
    this.taskStore = null;
    this.growthStore = null;
    this.farmStore = null;
    this.weatherStore = null;
    
    // Global subscribers list
    this.subscribers = [];
    
    // Store initialization status
    this.initialized = false;
    this.initializing = false;
    
    // Bind methods to preserve 'this' context
    this.initialize = this.initialize.bind(this);
    this.subscribe = this.subscribe.bind(this);
    this.notifySubscribers = this.notifySubscribers.bind(this);
  }
  
  /**
   * Initialize all store modules
   */
  async initialize() {
    if (this.initialized || this.initializing) {
      return;
    }
    
    this.initializing = true;
    
    try {
      // Import store modules dynamically
      const TaskStore = (await import('./task-store.js')).default;
      const GrowthStore = (await import('./growth-store.js')).default;
      const FarmStore = (await import('./farm-store.js')).default;
      const WeatherStore = (await import('./weather-store.js')).default;
      
      // Initialize store modules
      this.taskStore = new TaskStore(this);
      this.growthStore = new GrowthStore(this);
      this.farmStore = new FarmStore(this);
      this.weatherStore = new WeatherStore(this);
      
      // Initialize each store in the right order (dependencies first)
      await this.farmStore.initialize();
      await this.growthStore.initialize();
      await this.weatherStore.initialize();
      await this.taskStore.initialize();
      
      this.initialized = true;
      this.initializing = false;
      
      // Notify subscribers that store is ready
      this.notifySubscribers({ type: 'STORE_INITIALIZED' });
      
      console.log('Store initialization complete.');
    } catch (error) {
      console.error('Error initializing store:', error);
      this.initializing = false;
      this.notifySubscribers({ 
        type: 'STORE_INITIALIZATION_ERROR', 
        payload: error.message 
      });
    }
  }
  
  /**
   * Subscribe to store updates
   * @param {Function} callback Function to call when state changes
   * @returns {Function} Unsubscribe function
   */
  subscribe(callback) {
    this.subscribers.push(callback);
    
    // Return unsubscribe function
    return () => {
      this.subscribers = this.subscribers.filter(cb => cb !== callback);
    };
  }
  
  /**
   * Notify all subscribers of state changes
   * @param {Object} action Action object with type and optional payload
   */
  notifySubscribers(action) {
    this.subscribers.forEach(callback => {
      try {
        callback(action);
      } catch (error) {
        console.error('Error in store subscriber:', error);
      }
    });
  }
  
  /**
   * Convenience getters for each store
   */
  get tasks() {
    return this.taskStore;
  }
  
  get growth() {
    return this.growthStore;
  }
  
  get farm() {
    return this.farmStore;
  }
  
  get weather() {
    return this.weatherStore;
  }
}

// Create singleton instance
const store = new Store();

// Auto-initialize when document is ready
document.addEventListener('DOMContentLoaded', () => {
  store.initialize();
});

export default store;
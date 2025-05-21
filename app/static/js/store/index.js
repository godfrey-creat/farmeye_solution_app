// store/index.js
import UserStore from './user-store.js';
import FarmStore from './farm-store.js';
import TaskStore from './task-store.js';
import WeatherStore from './weather-store.js';
import GrowthStore from './growth-store.js';

class Store {
  constructor() {
    // Initialize all store modules
    this.userStore = new UserStore(this);
    this.farmStore = new FarmStore(this);
    this.taskStore = new TaskStore(this);
    this.weatherStore = new WeatherStore(this);
    this.growthStore = new GrowthStore(this);
    
    this.subscribers = [];
    this.initializeStores();
  }
  
  async initializeStores() {
    // Load initial data and interconnect stores
    await this.userStore.initialize();
    await this.farmStore.initialize();
    await this.taskStore.initialize();
    await this.weatherStore.initialize();
    await this.growthStore.initialize();
    
    this.notifySubscribers({ type: 'STORE_INITIALIZED' });
  }
  
  subscribe(callback) {
    this.subscribers.push(callback);
    return () => {
      this.subscribers = this.subscribers.filter(cb => cb !== callback);
    };
  }
  
  notifySubscribers(action) {
    this.subscribers.forEach(callback => callback(action));
  }
  
  // Convenience methods to access specific stores
  get user() { return this.userStore; }
  get farm() { return this.farmStore; }
  get tasks() { return this.taskStore; }
  get weather() { return this.weatherStore; }
  get growth() { return this.growthStore; }
}

// Create a singleton store instance
const store = new Store();
export default store;
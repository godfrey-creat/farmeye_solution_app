/**
 * Farm Store
 * Manages farm and field data
 */
class FarmStore {
    constructor(rootStore) {
      this.rootStore = rootStore;
      
      // Farm data
      this.farms = [];
      this.fields = [];
      this.activeFarmId = null;
      this.activeFieldId = null;
      this.loading = false;
      this.error = null;
      
      // Bind methods
      this.initialize = this.initialize.bind(this);
      this.fetchFarms = this.fetchFarms.bind(this);
      this.fetchFields = this.fetchFields.bind(this);
      this.setActiveFarm = this.setActiveFarm.bind(this);
      this.setActiveField = this.setActiveField.bind(this);
      this.getActiveFarm = this.getActiveFarm.bind(this);
      this.getActiveField = this.getActiveField.bind(this);
    }
    
    /**
     * Initialize farm store
     */
    async initialize() {
      try {
        await this.fetchFarms();
        
        // Set active farm if not already set
        if (this.farms.length > 0 && !this.activeFarmId) {
          this.setActiveFarm(this.farms[0].id);
        }
        
        console.log('Farm store initialized');
        return true;
      } catch (error) {
        console.error('Error initializing farm store:', error);
        this.error = error.message;
        return false;
      }
    }
    
    /**
     * Fetch farms for current user
     */
    async fetchFarms() {
      try {
        this.loading = true;
        
        const response = await fetch('/api/farms');
        
        if (!response.ok) {
          throw new Error(`Failed to fetch farms: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        if (data.status === 'success') {
          this.farms = data.farms;
          this.error = null;
          
          this.rootStore.notifySubscribers({ 
            type: 'FARMS_LOADED', 
            payload: this.farms 
          });
          
          // If we have farms, fetch fields for active farm
          if (this.farms.length > 0 && this.activeFarmId) {
            await this.fetchFields(this.activeFarmId);
          }
          
          return this.farms;
        } else {
          throw new Error(data.message || 'Unknown error fetching farms');
        }
      } catch (error) {
        console.error('Error fetching farms:', error);
        this.error = error.message;
        return [];
      } finally {
        this.loading = false;
      }
    }
    
    /**
     * Fetch fields for a farm
     * @param {number} farmId Farm ID
     */
    async fetchFields(farmId) {
      if (!farmId) {
        return [];
      }
      
      try {
        const response = await fetch(`/api/farms/${farmId}/fields`);
        
        if (!response.ok) {
          throw new Error(`Failed to fetch fields: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        if (data.status === 'success') {
          this.fields = data.fields;
          
          this.rootStore.notifySubscribers({ 
            type: 'FIELDS_LOADED', 
            payload: { farmId, fields: this.fields } 
          });
          
          return this.fields;
        } else {
          throw new Error(data.message || 'Unknown error fetching fields');
        }
      } catch (error) {
        console.error('Error fetching fields:', error);
        return [];
      }
    }
    
    /**
     * Set active farm
     * @param {number} farmId Farm ID
     */
    async setActiveFarm(farmId) {
      if (this.activeFarmId === farmId) {
        return;
      }
      
      const farm = this.farms.find(f => f.id === farmId);
      
      if (!farm) {
        console.error(`Farm with ID ${farmId} not found`);
        return;
      }
      
      this.activeFarmId = farmId;
      this.activeFieldId = null; // Reset active field
      
      // Fetch fields for this farm
      await this.fetchFields(farmId);
      
      // Update task store filter
      if (this.rootStore.taskStore) {
        this.rootStore.taskStore.setFilter({
          farmId: farmId,
          fieldId: null
        });
      }
      
      // Update growth stages
      if (this.rootStore.growthStore) {
        this.rootStore.growthStore.fetchGrowthStages(farmId);
      }
      
      this.rootStore.notifySubscribers({ 
        type: 'ACTIVE_FARM_CHANGED', 
        payload: { farmId, farm } 
      });
      
      return farm;
    }
    
    /**
     * Set active field
     * @param {number} fieldId Field ID
     */
    setActiveField(fieldId) {
      if (this.activeFieldId === fieldId) {
        return;
      }
      
      const field = this.fields.find(f => f.id === fieldId);
      
      if (!field) {
        console.error(`Field with ID ${fieldId} not found`);
        return;
      }
      
      this.activeFieldId = fieldId;
      
      // Update task store filter
      if (this.rootStore.taskStore) {
        this.rootStore.taskStore.setFilter({
          fieldId: fieldId
        });
      }
      
      this.rootStore.notifySubscribers({ 
        type: 'ACTIVE_FIELD_CHANGED', 
        payload: { fieldId, field } 
      });
      
      return field;
    }
    
    /**
     * Get active farm
     */
    getActiveFarm() {
      return this.farms.find(farm => farm.id === this.activeFarmId);
    }
    
    /**
     * Get active field
     */
    getActiveField() {
      return this.fields.find(field => field.id === this.activeFieldId);
    }
    
    /**
     * Get farm by ID
     * @param {number} farmId Farm ID
     */
    getFarmById(farmId) {
      return this.farms.find(farm => farm.id === farmId);
    }
    
    /**
     * Get field by ID
     * @param {number} fieldId Field ID
     */
    getFieldById(fieldId) {
      return this.fields.find(field => field.id === fieldId);
    }
    
    /**
     * Get fields for a farm
     * @param {number} farmId Farm ID
     */
    getFieldsByFarmId(farmId) {
      return this.fields.filter(field => field.farm_id === farmId);
    }
  }
  
  export default FarmStore;
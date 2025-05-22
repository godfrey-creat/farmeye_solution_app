/**
 * Growth Stage Store
 * Manages growth stage data and integration with task planning
 */
class GrowthStore {
  constructor(rootStore) {
    this.rootStore = rootStore;
    
    // Growth stage data
    this.stages = [];
    this.loading = false;
    this.error = null;
    
    // Bind methods
    this.initialize = this.initialize.bind(this);
    this.fetchGrowthStages = this.fetchGrowthStages.bind(this);
    this.getStageForDate = this.getStageForDate.bind(this);
    this.getStagesForDateRange = this.getStagesForDateRange.bind(this);
    this.getRecommendedTasksForStage = this.getRecommendedTasksForStage.bind(this);
  }
  
  /**
   * Initialize growth stage store
   */
  async initialize() {
    try {
      await this.fetchGrowthStages();
      console.log('Growth store initialized');
      return true;
    } catch (error) {
      console.error('Error initializing growth stage store:', error);
      this.error = error.message;
      return false;
    }
  }
  
  /**
   * Fetch growth stages for a farm
   * @param {number} farmId Farm ID (optional)
   */
  async fetchGrowthStages(farmId = null) {
    try {
      this.loading = true;
      
      let url = '/tasks/api/growth-stages';
      if (farmId) {
        url += `?farm_id=${farmId}`;
      }
      
      const response = await fetch(url);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch growth stages: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      if (data.status === 'success') {
        this.stages = data.growth_stages;
        this.error = null;
        
        this.rootStore.notifySubscribers({ 
          type: 'GROWTH_STAGES_LOADED', 
          payload: this.stages 
        });
        
        return this.stages;
      } else {
        throw new Error(data.message || 'Unknown error fetching growth stages');
      }
    } catch (error) {
      console.error('Error fetching growth stages:', error);
      this.error = error.message;
      return [];
    } finally {
      this.loading = false;
    }
  }
  
  /**
   * Get growth stage active on a specific date
   * @param {Date} date Date to check
   * @param {number} farmId Farm ID
   */
  getStageForDate(date, farmId) {
    if (!date || !farmId) {
      return null;
    }
    
    const dateStr = date instanceof Date ? date.toISOString() : date;
    const dateObj = new Date(dateStr);
    
    return this.stages.find(stage => {
      if (stage.farm_id !== farmId) {
        return false;
      }
      
      const stageStart = new Date(stage.start_date);
      const stageEnd = stage.end_date ? new Date(stage.end_date) : new Date('9999-12-31');
      
      return dateObj >= stageStart && dateObj <= stageEnd;
    });
  }
  
  /**
   * Get all growth stages active during a date range
   * @param {Date} startDate Range start date
   * @param {Date} endDate Range end date
   * @param {number} farmId Farm ID
   */
  getStagesForDateRange(startDate, endDate, farmId) {
    if (!startDate || !endDate || !farmId) {
      return [];
    }
    
    const start = startDate instanceof Date ? startDate : new Date(startDate);
    const end = endDate instanceof Date ? endDate : new Date(endDate);
    
    return this.stages.filter(stage => {
      if (stage.farm_id !== farmId) {
        return false;
      }
      
      const stageStart = new Date(stage.start_date);
      const stageEnd = stage.end_date ? new Date(stage.end_date) : new Date('9999-12-31');
      
      // Stage starts or ends within the range, or spans the entire range
      return (
        (stageStart >= start && stageStart <= end) ||
        (stageEnd >= start && stageEnd <= end) ||
        (stageStart <= start && stageEnd >= end)
      );
    });
  }
  
  /**
   * Get recommended tasks for a specific growth stage
   * @param {number} stageId Growth stage ID
   */
  getRecommendedTasksForStage(stageId) {
    const stage = this.stages.find(s => s.id === stageId);
    
    if (!stage || !stage.recommended_tasks || !stage.recommended_tasks.length) {
      return [];
    }
    
    return stage.recommended_tasks;
  }
  
  /**
   * Convert growth stages to calendar events for visualization
   * @param {number} farmId Farm ID
   */
  stagesToCalendarEvents(farmId) {
    if (!farmId) {
      return [];
    }
    
    return this.stages
      .filter(stage => stage.farm_id === farmId)
      .map(stage => {
        return {
          id: `growth-stage-${stage.id}`,
          title: stage.stage_name,
          start: stage.start_date,
          end: stage.end_date || undefined,
          allDay: true,
          display: 'background',
          backgroundColor: this.getStageColor(stage.stage_name),
          extendedProps: {
            type: 'growth-stage',
            stageId: stage.id,
            stageName: stage.stage_name,
            farmId: stage.farm_id,
            notes: stage.notes,
            recommendedTasks: stage.recommended_tasks || []
          }
        };
      });
  }
  
  /**
   * Get color for growth stage (for visualization)
   * @param {string} stageName Growth stage name
   */
  getStageColor(stageName) {
    // Map stage names to colors
    const stageColors = {
      'Germination': 'rgba(173, 216, 230, 0.3)', // Light blue
      'Vegetative': 'rgba(144, 238, 144, 0.3)',  // Light green
      'Flowering': 'rgba(255, 192, 203, 0.3)',   // Pink
      'Fruiting': 'rgba(255, 165, 0, 0.3)',      // Orange
      'Maturity': 'rgba(255, 215, 0, 0.3)',      // Gold
      'Harvesting': 'rgba(205, 133, 63, 0.3)',   // Peru
    };
    
    return stageColors[stageName] || 'rgba(200, 200, 200, 0.3)'; // Default gray
  }
}

export default GrowthStore;
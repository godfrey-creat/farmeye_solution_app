// store/growth-store.js
class GrowthStore {
  constructor(rootStore) {
    this.rootStore = rootStore;
    this.stages = [];
  }
  
  async initialize() {
    await this.fetchGrowthStages();
  }
  
  async fetchGrowthStages(farmId = null) {
    try {
      let url = '/api/growth-stages';
      if (farmId) {
        url += `?farm_id=${farmId}`;
      }
      
      const response = await fetch(url);
      if (!response.ok) throw new Error('Failed to fetch growth stages');
      
      const data = await response.json();
      this.stages = data.growth_stages;
      
      this.rootStore.notifySubscribers({ 
        type: 'GROWTH_STAGES_LOADED', 
        payload: this.stages 
      });
      
      return this.stages;
    } catch (error) {
      console.error('Error fetching growth stages:', error);
      return [];
    }
  }
  
  getStageForDate(date) {
    // Find growth stage active on a specific date
    const dateStr = date.toISOString().split('T')[0];
    
    return this.stages.find(stage => {
      const stageStart = stage.start_date.split('T')[0];
      const stageEnd = stage.end_date ? stage.end_date.split('T')[0] : '9999-12-31';
      
      return stageStart <= dateStr && dateStr <= stageEnd;
    });
  }
  
  getRecommendedTasksForStage(stageName) {
    // Get recommended tasks for a specific growth stage
    const stage = this.stages.find(s => s.stage_name === stageName);
    if (!stage || !stage.recommended_tasks) return [];
    
    try {
      return typeof stage.recommended_tasks === 'string' ? 
        JSON.parse(stage.recommended_tasks) : stage.recommended_tasks;
    } catch (error) {
      console.error('Error parsing recommended tasks:', error);
      return [];
    }
  }
}

export default GrowthStore;
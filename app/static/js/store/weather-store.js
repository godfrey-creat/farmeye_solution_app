/**
 * Weather Store
 * Manages weather data and integrates with task planning
 */
class WeatherStore {
    constructor(rootStore) {
      this.rootStore = rootStore;
      
      // Weather data
      this.forecast = [];
      this.currentWeather = null;
      this.loading = false;
      this.error = null;
      this.lastUpdated = null;
      
      // Bind methods
      this.initialize = this.initialize.bind(this);
      this.fetchWeatherForecast = this.fetchWeatherForecast.bind(this);
      this.fetchCurrentWeather = this.fetchCurrentWeather.bind(this);
      this.getWeatherForDate = this.getWeatherForDate.bind(this);
      this.shouldTaskReschedule = this.shouldTaskReschedule.bind(this);
    }
    
    /**
     * Initialize weather store
     */
    async initialize() {
      try {
        await this.fetchCurrentWeather();
        await this.fetchWeatherForecast();
        
        // Set up automatic refresh every 3 hours
        setInterval(() => {
          this.fetchCurrentWeather();
          this.fetchWeatherForecast();
        }, 3 * 60 * 60 * 1000);
        
        console.log('Weather store initialized');
        return true;
      } catch (error) {
        console.error('Error initializing weather store:', error);
        this.error = error.message;
        return false;
      }
    }
    
    /**
     * Fetch weather forecast
     */
    async fetchWeatherForecast() {
      try {
        this.loading = true;
        
        // Get active farm location
        const activeFarm = this.rootStore.farm && this.rootStore.farm.getActiveFarm();
        
        if (!activeFarm || !activeFarm.latitude || !activeFarm.longitude) {
          // Use default location if no farm is selected
          // This is a simplified implementation
          console.warn('No active farm with location, using default location');
        }
        
        const response = await fetch('/api/weather/forecast');
        
        if (!response.ok) {
          throw new Error(`Failed to fetch weather forecast: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        if (data.status === 'success') {
          this.forecast = data.forecast;
          this.error = null;
          this.lastUpdated = new Date();
          
          this.rootStore.notifySubscribers({ 
            type: 'WEATHER_FORECAST_LOADED', 
            payload: this.forecast 
          });
          
          return this.forecast;
        } else {
          throw new Error(data.message || 'Unknown error fetching weather forecast');
        }
      } catch (error) {
        console.error('Error fetching weather forecast:', error);
        this.error = error.message;
        return [];
      } finally {
        this.loading = false;
      }
    }
    
    /**
     * Fetch current weather
     */
    async fetchCurrentWeather() {
      try {
        const response = await fetch('/api/weather/current');
        
        if (!response.ok) {
          throw new Error(`Failed to fetch current weather: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        if (data.status === 'success') {
          this.currentWeather = data.weather;
          
          this.rootStore.notifySubscribers({ 
            type: 'CURRENT_WEATHER_LOADED', 
            payload: this.currentWeather 
          });
          
          return this.currentWeather;
        } else {
          throw new Error(data.message || 'Unknown error fetching current weather');
        }
      } catch (error) {
        console.error('Error fetching current weather:', error);
        return null;
      }
    }
    
    /**
     * Get weather forecast for a specific date
     * @param {Date} date Date to get weather for
     */
    getWeatherForDate(date) {
      if (!date || !this.forecast || !this.forecast.length) {
        return null;
      }
      
      const dateStr = date instanceof Date 
        ? date.toISOString().split('T')[0] 
        : new Date(date).toISOString().split('T')[0];
      
      return this.forecast.find(day => day.date.split('T')[0] === dateStr);
    }
    
    /**
     * Check if a task should be rescheduled based on weather
     * @param {Object} task Task object
     */
    shouldTaskReschedule(task) {
      if (!task || !task.start_date) {
        return false;
      }
      
      // Get weather for task date
      const taskWeather = this.getWeatherForDate(task.start_date);
      
      if (!taskWeather) {
        return false;
      }
      
      // Define weather conditions that would impact different task types
      const taskWeatherConstraints = {
        'Weeding': { 
          maxRainProbability: 40, 
          maxWindSpeed: 25 
        },
        'Irrigating': { 
          minRainProbability: 60  // Don't irrigate if it's likely to rain
        },
        'Land Preparation': { 
          maxRainProbability: 30, 
          maxWindSpeed: 20 
        },
        'Harvesting': { 
          maxRainProbability: 30, 
          maxWindSpeed: 15 
        },
        'Pruning': { 
          maxRainProbability: 20, 
          maxWindSpeed: 15 
        }
      };
      
      // Get constraints for this task type
      const constraints = taskWeatherConstraints[task.task_type];
      
      if (!constraints) {
        return false;
      }
      
      // Check constraints against forecast
      if (constraints.maxRainProbability && 
          taskWeather.precipitation_probability > constraints.maxRainProbability) {
        return {
          reason: 'rain',
          message: `Rain probability of ${taskWeather.precipitation_probability}% exceeds limit of ${constraints.maxRainProbability}%`
        };
      }
      
      if (constraints.minRainProbability && 
          taskWeather.precipitation_probability < constraints.minRainProbability) {
        return {
          reason: 'no_rain',
          message: `Rain probability of ${taskWeather.precipitation_probability}% is below threshold of ${constraints.minRainProbability}%`
        };
      }
      
      if (constraints.maxWindSpeed && 
          taskWeather.wind_speed > constraints.maxWindSpeed) {
        return {
          reason: 'wind',
          message: `Wind speed of ${taskWeather.wind_speed} km/h exceeds limit of ${constraints.maxWindSpeed} km/h`
        };
      }
      
      return false;
    }
    
    /**
     * Get recommendations for task scheduling based on weather
     * @param {Date} startDate Start date for recommendations
     * @param {Date} endDate End date for recommendations
     * @param {string} taskType Task type
     */
    getRecommendedDays(startDate, endDate, taskType) {
      if (!startDate || !endDate || !taskType || !this.forecast || !this.forecast.length) {
        return [];
      }
      
      const start = startDate instanceof Date ? startDate : new Date(startDate);
      const end = endDate instanceof Date ? endDate : new Date(endDate);
      
      // Get constraints for this task type
      const taskWeatherConstraints = {
        'Weeding': { 
          maxRainProbability: 40, 
          maxWindSpeed: 25 
        },
        'Irrigating': { 
          minRainProbability: 60  
        },
        'Land Preparation': { 
          maxRainProbability: 30, 
          maxWindSpeed: 20 
        },
        'Harvesting': { 
          maxRainProbability: 30, 
          maxWindSpeed: 15 
        },
        'Pruning': { 
          maxRainProbability: 20, 
          maxWindSpeed: 15 
        }
      };
      
      const constraints = taskWeatherConstraints[taskType];
      
      if (!constraints) {
        return [];
      }
      
      // Filter days that meet the constraints
      return this.forecast
        .filter(day => {
          const dayDate = new Date(day.date);
          
          // Check if day is within date range
          if (dayDate < start || dayDate > end) {
            return false;
          }
          
          // Check constraints
          if (constraints.maxRainProbability && 
              day.precipitation_probability > constraints.maxRainProbability) {
            return false;
          }
          
          if (constraints.minRainProbability && 
              day.precipitation_probability < constraints.minRainProbability) {
            return false;
          }
          
          if (constraints.maxWindSpeed && 
              day.wind_speed > constraints.maxWindSpeed) {
            return false;
          }
          
          return true;
        })
        .map(day => ({
          date: day.date,
          conditions: day.conditions,
          temperature: day.temperature,
          suitability: this.calculateSuitability(day, taskType)
        }))
        .sort((a, b) => b.suitability - a.suitability);
    }
    
    /**
     * Calculate suitability score for a day (0-100)
     * @param {Object} day Weather day object
     * @param {string} taskType Task type
     */
    calculateSuitability(day, taskType) {
      // This is a simplified algorithm - could be more sophisticated
      let score = 100;
      
      const taskWeatherImpact = {
        'Weeding': { 
          rainImpact: -2,
          windImpact: -1,
          tempOptimal: 25,
          tempImpact: 0.5
        },
        'Irrigating': { 
          rainImpact: 2,
          windImpact: -0.5,
          tempOptimal: 30,
          tempImpact: 0.3
        },
        'Land Preparation': { 
          rainImpact: -1.5,
          windImpact: -0.8,
          tempOptimal: 20,
          tempImpact: 0.2
        },
        'Harvesting': { 
          rainImpact: -2,
          windImpact: -1.2,
          tempOptimal: 22,
          tempImpact: 0.4
        },
        'Pruning': { 
          rainImpact: -2.5,
          windImpact: -1.5,
          tempOptimal: 18,
          tempImpact: 0.3
        }
      };
      
      const impact = taskWeatherImpact[taskType] || taskWeatherImpact['Weeding'];
      
      // Adjust for rain
      score += day.precipitation_probability * impact.rainImpact;
      
      // Adjust for wind
      score += day.wind_speed * impact.windImpact;
      
      // Adjust for temperature deviation from optimal
      score -= Math.abs(day.temperature - impact.tempOptimal) * impact.tempImpact;
      
      // Ensure score is between 0 and 100
      return Math.max(0, Math.min(100, Math.round(score)));
    }
  }
  
  export default WeatherStore;
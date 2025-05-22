/**
 * Task Analytics Dashboard
 * Provides comprehensive analytics and reporting for tasks
 */
import store from '../store/index.js';

class TaskAnalytics {
  constructor(containerId) {
    this.containerId = containerId;
    this.container = document.getElementById(containerId);
    
    // Analytics data
    this.analyticsData = null;
    this.chartInstances = {};
    
    // Store subscription
    this.unsubscribe = null;
    
    this.initialize();
  }
  
  initialize() {
    // Subscribe to store changes
    this.unsubscribe = store.subscribe(action => {
      if (['TASKS_LOADED', 'TASK_CREATED', 'TASK_UPDATED', 'TASK_DELETED', 'TASK_STATISTICS_LOADED'].includes(action.type)) {
        this.refreshAnalytics();
      }
    });
    
    this.createAnalyticsStructure();
    this.refreshAnalytics();
  }
  
  createAnalyticsStructure() {
    this.container.innerHTML = `
      <div class="analytics-dashboard">
        <!-- Summary Cards -->
        <div class="analytics-summary">
          <div class="summary-card">
            <div class="card-icon">
              <i class="fas fa-tasks"></i>
            </div>
            <div class="card-content">
              <h3 id="total-tasks">0</h3>
              <p>Total Tasks</p>
            </div>
          </div>
          
          <div class="summary-card">
            <div class="card-icon pending">
              <i class="fas fa-clock"></i>
            </div>
            <div class="card-content">
              <h3 id="pending-tasks">0</h3>
              <p>Pending Tasks</p>
            </div>
          </div>
          
          <div class="summary-card">
            <div class="card-icon in-progress">
              <i class="fas fa-play"></i>
            </div>
            <div class="card-content">
              <h3 id="in-progress-tasks">0</h3>
              <p>In Progress</p>
            </div>
          </div>
          
          <div class="summary-card">
            <div class="card-icon completed">
              <i class="fas fa-check"></i>
            </div>
            <div class="card-content">
              <h3 id="completed-tasks">0</h3>
              <p>Completed</p>
            </div>
          </div>
          
          <div class="summary-card">
            <div class="card-icon due-today">
              <i class="fas fa-calendar-day"></i>
            </div>
            <div class="card-content">
              <h3 id="due-today">0</h3>
              <p>Due Today</p>
            </div>
          </div>
          
          <div class="summary-card">
            <div class="card-icon overdue">
              <i class="fas fa-exclamation-triangle"></i>
            </div>
            <div class="card-content">
              <h3 id="overdue-tasks">0</h3>
              <p>Overdue</p>
            </div>
          </div>
        </div>
        
        <!-- Charts Section -->
        <div class="analytics-charts">
          <div class="chart-row">
            <div class="chart-container">
              <h4>Task Status Distribution</h4>
              <canvas id="status-chart"></canvas>
            </div>
            
            <div class="chart-container">
              <h4>Tasks by Type</h4>
              <canvas id="type-chart"></canvas>
            </div>
          </div>
          
          <div class="chart-row">
            <div class="chart-container full-width">
              <h4>Task Completion Trend (Last 30 Days)</h4>
              <canvas id="completion-trend-chart"></canvas>
            </div>
          </div>
          
          <div class="chart-row">
            <div class="chart-container">
              <h4>Tasks by Priority</h4>
              <canvas id="priority-chart"></canvas>
            </div>
            
            <div class="chart-container">
              <h4>Tasks by Farm</h4>
              <canvas id="farm-chart"></canvas>
            </div>
          </div>
        </div>
        
        <!-- Performance Metrics -->
        <div class="performance-metrics">
          <h4>Performance Metrics</h4>
          
          <div class="metrics-grid">
            <div class="metric-item">
              <label>Completion Rate</label>
              <div class="progress-bar">
                <div class="progress-fill" id="completion-rate-fill"></div>
                <span class="progress-text" id="completion-rate-text">0%</span>
              </div>
            </div>
            
            <div class="metric-item">
              <label>On-Time Completion</label>
              <div class="progress-bar">
                <div class="progress-fill" id="on-time-rate-fill"></div>
                <span class="progress-text" id="on-time-rate-text">0%</span>
              </div>
            </div>
            
            <div class="metric-item">
              <label>Average Task Duration</label>
              <div class="metric-value" id="avg-duration">0 days</div>
            </div>
            
            <div class="metric-item">
              <label>Most Active Day</label>
              <div class="metric-value" id="most-active-day">-</div>
            </div>
            
            <div class="metric-item">
              <label>Peak Task Type</label>
              <div class="metric-value" id="peak-task-type">-</div>
            </div>
            
            <div class="metric-item">
              <label>Productivity Score</label>
              <div class="metric-value" id="productivity-score">0/100</div>
            </div>
          </div>
        </div>
        
        <!-- Task List -->
        <div class="recent-tasks">
          <h4>Recent Activity</h4>
          <div class="task-activity-list" id="recent-activity">
            <!-- Recent task activity will be rendered here -->
          </div>
        </div>
      </div>
    `;
  }
  
  async refreshAnalytics() {
    try {
      // Get fresh statistics from store
      await store.tasks?.fetchTaskStatistics();
      
      // Calculate analytics
      this.calculateAnalytics();
      
      // Update summary cards
      this.updateSummaryCards();
      
      // Update charts
      this.updateCharts();
      
      // Update performance metrics
      this.updatePerformanceMetrics();
      
      // Update recent activity
      this.updateRecentActivity();
      
    } catch (error) {
      console.error('Error refreshing analytics:', error);
    }
  }
  
  calculateAnalytics() {
    const tasks = store.tasks?.tasks || [];
    const statistics = store.tasks?.statistics || { counts: {} };
    
    this.analyticsData = {
      summary: {
        total: tasks.length,
        pending: statistics.counts.pending || 0,
        inProgress: statistics.counts.in_progress || 0,
        completed: statistics.counts.completed || 0,
        dueToday: statistics.counts.due_today || 0,
        overdue: this.calculateOverdueTasks(tasks)
      },
      charts: {
        statusDistribution: this.calculateStatusDistribution(tasks),
        typeDistribution: this.calculateTypeDistribution(tasks),
        priorityDistribution: this.calculatePriorityDistribution(tasks),
        farmDistribution: this.calculateFarmDistribution(tasks),
        completionTrend: this.calculateCompletionTrend(tasks)
      },
      performance: this.calculatePerformanceMetrics(tasks)
    };
  }
  
  calculateOverdueTasks(tasks) {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    return tasks.filter(task => {
      const taskDate = new Date(task.start_date);
      return taskDate < today && task.status !== 'completed';
    }).length;
  }
  
  calculateStatusDistribution(tasks) {
    const distribution = {};
    
    tasks.forEach(task => {
      distribution[task.status] = (distribution[task.status] || 0) + 1;
    });
    
    return distribution;
  }
  
  calculateTypeDistribution(tasks) {
    const distribution = {};
    
    tasks.forEach(task => {
      distribution[task.task_type] = (distribution[task.task_type] || 0) + 1;
    });
    
    return distribution;
  }
  
  calculatePriorityDistribution(tasks) {
    const distribution = { low: 0, medium: 0, high: 0 };
    
    tasks.forEach(task => {
      distribution[task.priority] = (distribution[task.priority] || 0) + 1;
    });
    
    return distribution;
  }
  
  calculateFarmDistribution(tasks) {
    const distribution = {};
    const farms = store.farm?.farms || [];
    
    tasks.forEach(task => {
      const farm = farms.find(f => f.id === task.farm_id);
      const farmName = farm ? farm.name : 'Unknown';
      distribution[farmName] = (distribution[farmName] || 0) + 1;
    });
    
    return distribution;
  }
  
  calculateCompletionTrend(tasks) {
    const trend = {};
    const thirtyDaysAgo = new Date();
    thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
    
    // Initialize with zeros for last 30 days
    for (let i = 0; i < 30; i++) {
      const date = new Date(thirtyDaysAgo);
      date.setDate(date.getDate() + i);
      const dateStr = date.toISOString().split('T')[0];
      trend[dateStr] = 0;
    }
    
    // Count completed tasks by date
    tasks
      .filter(task => task.status === 'completed' && task.updated_at)
      .forEach(task => {
        const completedDate = new Date(task.updated_at).toISOString().split('T')[0];
        if (trend.hasOwnProperty(completedDate)) {
          trend[completedDate]++;
        }
      });
    
    return trend;
  }
  
  calculatePerformanceMetrics(tasks) {
    const completed = tasks.filter(t => t.status === 'completed');
    const total = tasks.length;
    
    // Completion rate
    const completionRate = total > 0 ? Math.round((completed.length / total) * 100) : 0;
    
    // On-time completion rate
    const onTimeCompleted = completed.filter(task => {
      const dueDate = new Date(task.end_date || task.start_date);
      const completedDate = new Date(task.updated_at);
      return completedDate <= dueDate;
    });
    const onTimeRate = completed.length > 0 ? Math.round((onTimeCompleted.length / completed.length) * 100) : 0;
    
    // Average duration
    const durations = completed
      .filter(task => task.end_date)
      .map(task => {
        const start = new Date(task.start_date);
        const end = new Date(task.end_date);
        return Math.ceil((end - start) / (1000 * 60 * 60 * 24));
      });
    const avgDuration = durations.length > 0 ? Math.round(durations.reduce((a, b) => a + b, 0) / durations.length) : 0;
    
    // Most active day
    const dayCount = {};
    tasks.forEach(task => {
      const day = new Date(task.start_date).toLocaleDateString('en-US', { weekday: 'long' });
      dayCount[day] = (dayCount[day] || 0) + 1;
    });
    const mostActiveDay = Object.keys(dayCount).reduce((a, b) => dayCount[a] > dayCount[b] ? a : b, '-');
    
    // Peak task type
    const typeCount = this.calculateTypeDistribution(tasks);
    const peakTaskType = Object.keys(typeCount).reduce((a, b) => typeCount[a] > typeCount[b] ? a : b, '-');
    
    // Productivity score (custom calculation)
    const productivityScore = Math.round((completionRate * 0.4) + (onTimeRate * 0.4) + (Math.min(avgDuration, 7) / 7 * 20));
    
    return {
      completionRate,
      onTimeRate,
      avgDuration,
      mostActiveDay,
      peakTaskType,
      productivityScore
    };
  }
  
  updateSummaryCards() {
    const { summary } = this.analyticsData;
    
    document.getElementById('total-tasks').textContent = summary.total;
    document.getElementById('pending-tasks').textContent = summary.pending;
    document.getElementById('in-progress-tasks').textContent = summary.inProgress;
    document.getElementById('completed-tasks').textContent = summary.completed;
    document.getElementById('due-today').textContent = summary.dueToday;
    document.getElementById('overdue-tasks').textContent = summary.overdue;
  }
  
  updateCharts() {
    this.updateStatusChart();
    this.updateTypeChart();
    this.updatePriorityChart();
    this.updateFarmChart();
    this.updateCompletionTrendChart();
  }
  
  updateStatusChart() {
    const canvas = document.getElementById('status-chart');
    const ctx = canvas.getContext('2d');
    
    // Destroy existing chart
    if (this.chartInstances.status) {
      this.chartInstances.status.destroy();
    }
    
    const { statusDistribution } = this.analyticsData.charts;
    
    this.chartInstances.status = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: Object.keys(statusDistribution).map(status => 
          status.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())
        ),
        datasets: [{
          data: Object.values(statusDistribution),
          backgroundColor: [
            '#ffc107', // pending
            '#17a2b8', // in_progress
            '#28a745'  // completed
          ],
          borderWidth: 2,
          borderColor: '#ffffff'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom'
          }
        }
      }
    });
  }
  
  updateTypeChart() {
    const canvas = document.getElementById('type-chart');
    const ctx = canvas.getContext('2d');
    
    if (this.chartInstances.type) {
      this.chartInstances.type.destroy();
    }
    
    const { typeDistribution } = this.analyticsData.charts;
    
    this.chartInstances.type = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: Object.keys(typeDistribution),
        datasets: [{
          label: 'Tasks',
          data: Object.values(typeDistribution),
          backgroundColor: '#3a8456',
          borderColor: '#2a6041',
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: {
              stepSize: 1
            }
          }
        }
      }
    });
  }
  
  updatePriorityChart() {
    const canvas = document.getElementById('priority-chart');
    const ctx = canvas.getContext('2d');
    
    if (this.chartInstances.priority) {
      this.chartInstances.priority.destroy();
    }
    
    const { priorityDistribution } = this.analyticsData.charts;
    
    this.chartInstances.priority = new Chart(ctx, {
      type: 'pie',
      data: {
        labels: ['Low', 'Medium', 'High'],
        datasets: [{
          data: [priorityDistribution.low, priorityDistribution.medium, priorityDistribution.high],
          backgroundColor: ['#6c757d', '#ffc107', '#dc3545'],
          borderWidth: 2,
          borderColor: '#ffffff'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom'
          }
        }
      }
    });
  }
  
  updateFarmChart() {
    const canvas = document.getElementById('farm-chart');
    const ctx = canvas.getContext('2d');
    
    if (this.chartInstances.farm) {
      this.chartInstances.farm.destroy();
    }
    
    const { farmDistribution } = this.analyticsData.charts;
    
    this.chartInstances.farm = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: Object.keys(farmDistribution),
        datasets: [{
          data: Object.values(farmDistribution),
          backgroundColor: [
            '#3a8456',
            '#49a86b',
            '#5fb380',
            '#75be95',
            '#8bc9aa'
          ],
          borderWidth: 2,
          borderColor: '#ffffff'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom'
          }
        }
      }
    });
  }
  
  updateCompletionTrendChart() {
    const canvas = document.getElementById('completion-trend-chart');
    const ctx = canvas.getContext('2d');
    
    if (this.chartInstances.trend) {
      this.chartInstances.trend.destroy();
    }
    
    const { completionTrend } = this.analyticsData.charts;
    
    this.chartInstances.trend = new Chart(ctx, {
      type: 'line',
      data: {
        labels: Object.keys(completionTrend).map(date => 
          new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
        ),
        datasets: [{
          label: 'Completed Tasks',
          data: Object.values(completionTrend),
          borderColor: '#3a8456',
          backgroundColor: 'rgba(58, 132, 86, 0.1)',
          borderWidth: 2,
          fill: true,
          tension: 0.1
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: {
              stepSize: 1
            }
          }
        }
      }
    });
  }
  
  updatePerformanceMetrics() {
    const { performance } = this.analyticsData;
    
    // Update progress bars
    this.updateProgressBar('completion-rate', performance.completionRate);
    this.updateProgressBar('on-time-rate', performance.onTimeRate);
    
    // Update metric values
    document.getElementById('avg-duration').textContent = `${performance.avgDuration} day${performance.avgDuration !== 1 ? 's' : ''}`;
    document.getElementById('most-active-day').textContent = performance.mostActiveDay;
    document.getElementById('peak-task-type').textContent = performance.peakTaskType;
    document.getElementById('productivity-score').textContent = `${performance.productivityScore}/100`;
  }
  
  updateProgressBar(id, percentage) {
    const fill = document.getElementById(`${id}-fill`);
    const text = document.getElementById(`${id}-text`);
    
    fill.style.width = `${percentage}%`;
    text.textContent = `${percentage}%`;
    
    // Update color based on percentage
    if (percentage >= 80) {
      fill.style.backgroundColor = '#28a745';
    } else if (percentage >= 60) {
      fill.style.backgroundColor = '#ffc107';
    } else {
      fill.style.backgroundColor = '#dc3545';
    }
  }
  
  updateRecentActivity() {
    const tasks = store.tasks?.tasks || [];
    const recentTasks = tasks
      .filter(task => task.updated_at)
      .sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at))
      .slice(0, 10);
    
    const container = document.getElementById('recent-activity');
    
    if (recentTasks.length === 0) {
      container.innerHTML = `
        <div class="no-activity">
          <i class="fas fa-clock"></i>
          <p>No recent task activity</p>
        </div>
      `;
      return;
    }
    
    container.innerHTML = recentTasks.map(task => {
      const timeAgo = this.getTimeAgo(new Date(task.updated_at));
      const farm = store.farm?.getFarmById(task.farm_id);
      
      return `
        <div class="activity-item">
          <div class="activity-icon status-${task.status}">
            <i class="fas fa-${this.getStatusIcon(task.status)}"></i>
          </div>
          <div class="activity-content">
            <div class="activity-title">${task.title}</div>
            <div class="activity-details">
              <span class="activity-status">${task.status.replace('_', ' ')}</span>
              <span class="activity-farm">${farm?.name || 'Unknown Farm'}</span>
              <span class="activity-time">${timeAgo}</span>
            </div>
          </div>
        </div>
      `;
    }).join('');
  }
  
  getStatusIcon(status) {
    const icons = {
      pending: 'clock',
      in_progress: 'play',
      completed: 'check'
    };
    return icons[status] || 'tasks';
  }
  
  getTimeAgo(date) {
    const now = new Date();
    const diff = Math.floor((now - date) / 1000);
    
    if (diff < 60) return 'just now';
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    if (diff < 604800) return `${Math.floor(diff / 86400)}d ago`;
    
    return date.toLocaleDateString();
  }
  
  destroy() {
    // Destroy chart instances
    Object.values(this.chartInstances).forEach(chart => {
      if (chart) chart.destroy();
    });
    
    if (this.unsubscribe) {
      this.unsubscribe();
    }
  }
}

export default TaskAnalytics;
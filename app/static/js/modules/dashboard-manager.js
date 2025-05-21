// DashboardManager class to handle all dashboard operations
import { API } from './api.js';
import { UIManager } from './ui.js';
import { ModalController } from './modal.js';

export class DashboardManager {    constructor() {
        this.api = new API();
        this.charts = new Map();
        this.refreshInterval = null;
        this.setupEventListeners();
        this.initializeCharts();
    }    setupEventListeners() {
        // Refresh button event listener
        const refreshButton = document.getElementById('refreshButton');
        if (refreshButton) {
            refreshButton.addEventListener('click', () => this.refreshData());
        }

        // Auto-refresh toggle
        const toggleSwitch = document.querySelector('.toggle-switch');
        if (toggleSwitch) {
            toggleSwitch.addEventListener('click', () => this.toggleAutoRefresh());
        }

        // Time range selector
        const timeRangeSelector = document.getElementById('timeRangeSelector');
        if (timeRangeSelector) {
            timeRangeSelector.addEventListener('change', (e) => this.handleTimeRangeChange(e));
        }

        // Chart metric buttons
        const chartButtons = document.querySelectorAll('.btn-primary, .btn-outline');
        chartButtons.forEach(button => {
            button.addEventListener('click', (e) => this.handleChartMetricChange(e));
        });
    }    initializeCharts() {
        const ctx = document.getElementById('fieldMetricsChart');
        if (ctx) {
            // Destroy existing chart if it exists
            const existingChart = this.charts.get('fieldMetrics');
            if (existingChart) {
                existingChart.destroy();
            }
            this.charts.set('fieldMetrics', this.createFieldMetricsChart(ctx));
        }
    }

    createFieldMetricsChart(ctx) {
        // Clear any existing chart instances
        if (Chart.getChart(ctx)) {
            Chart.getChart(ctx).destroy();
        }
        return new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: []
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            boxWidth: 15,
                            usePointStyle: true,
                            pointStyle: 'circle',
                            font: { size: 12 }
                        }
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        backgroundColor: 'rgba(44, 62, 80, 0.8)',
                        padding: 12,
                        bodySpacing: 6
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        grid: {
                            color: 'rgba(236, 240, 241, 0.6)'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
    }    async refreshData() {
        UIManager.toggleSkeleton(true);
        try {
            const data = await this.api.getDashboardData();
            if (data.error) {
                UIManager.showWarning(data.error);
                this.showNoFarmState();
                return;
            }
            this.updateDashboard(data);
        } catch (error) {
            UIManager.showError('Failed to refresh dashboard data');
            console.error('Dashboard refresh error:', error);
        } finally {
            UIManager.toggleSkeleton(false);
        }
    }

    showNoFarmState() {
        const container = document.querySelector('.grid-cols-1.lg\\:grid-cols-2.gap-8.mb-8');
        if (container) {
            container.innerHTML = `
                <div class="col-span-2 text-center py-12 bg-white rounded-xl shadow-card">
                    <i class="fas fa-farm text-6xl text-gray-300 mb-4"></i>
                    <h2 class="text-2xl font-semibold text-gray-700 mb-2">No Farm Registered</h2>
                    <p class="text-gray-500 mb-6">Please register a farm to view dashboard data</p>
                    <a href="/farm/register" class="btn btn-primary">
                        <i class="fas fa-plus mr-2"></i>Register Farm
                    </a>
                </div>
            `;
        }
    }

    toggleAutoRefresh() {
        const toggleSwitch = document.querySelector('.toggle-switch');
        if (!toggleSwitch) return;

        const isEnabled = toggleSwitch.classList.toggle('on');
        toggleSwitch.classList.toggle('off', !isEnabled);

        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }

        if (isEnabled) {
            this.refreshInterval = setInterval(() => this.refreshData(), 60000);
            localStorage.setItem('autoRefreshEnabled', 'true');
        } else {
            localStorage.setItem('autoRefreshEnabled', 'false');
        }
    }    updateDashboard(data) {
        if (!data) return;
        
        // Update metrics if available
        if (data.metrics) {
            this.updateMetrics(data.metrics);
        }
        
        // Update recommendations if available
        if (data.recommendations) {
            this.updateRecommendations(data.recommendations);
        }
        
        // Update alerts if available
        if (data.alerts) {
            this.updateAlerts(data.alerts);
        }
        
        // Update chart data if available
        if (data.historical_data) {
            this.updateCharts({
                labels: data.historical_data.dates,
                datasets: [{
                    label: 'Temperature (°C)',
                    data: data.historical_data.temperature,
                    borderColor: '#F1C40F',
                    backgroundColor: 'rgba(241, 196, 15, 0.1)',
                    borderWidth: 3,
                    pointRadius: 4,
                    pointBackgroundColor: '#F1C40F',
                    tension: 0.3,
                    fill: true
                }]
            });
        }
    }

    updateMetrics(metrics) {
        if (!metrics) return;

        Object.entries(metrics).forEach(([key, value]) => {
            const card = this.findCardByTitle(key);
            if (card) {
                const valueElement = card.querySelector('.font-semibold.text-lg');
                if (valueElement) {
                    valueElement.textContent = this.formatMetricValue(value, key);
                }
            }
        });
    }

    updateCharts(chartData) {
        if (!chartData) return;
        
        const chart = this.charts.get('fieldMetrics');
        if (!chart) return;

        chart.data.labels = chartData.labels;
        chart.data.datasets = chartData.datasets;
        chart.update();
    }

    handleChartMetricChange(event) {
        const button = event.currentTarget;
        const chartButtons = document.querySelectorAll('.btn-primary, .btn-outline');
        
        // Update button states
        chartButtons.forEach(btn => {
            btn.classList.remove('btn-primary');
            btn.classList.add('btn-outline');
        });
        button.classList.remove('btn-outline');
        button.classList.add('btn-primary');

        // Update chart data
        const metric = button.textContent.trim();
        this.updateChartMetric(metric);
    }    async updateChartMetric(metric) {
        try {
            UIManager.toggleSkeleton(true);
            const timeRange = document.getElementById('timeRangeSelector')?.value || 30;
            const data = await this.api.fetchMetricData(metric, timeRange);
            const chart = this.charts.get('fieldMetrics');
            if (chart && data) {
                chart.data.labels = data.labels;
                chart.data.datasets = data.datasets;
                chart.update('none'); // Update without animation for better performance
            }
        } catch (error) {
            UIManager.showError(`Failed to update ${metric} data`);
            console.error('Chart update error:', error);
        } finally {
            UIManager.toggleSkeleton(false);
        }
    }async handleTimeRangeChange(event) {
        const timeRange = parseInt(event.target.value);
        try {
            UIManager.toggleSkeleton(true);
            
            // Get the currently selected metric
            const activeMetricButton = document.querySelector('.btn-primary');
            const currentMetric = activeMetricButton?.textContent.trim() || 'Temperature';
            
            // Update both dashboard data and chart data
            const [dashboardData, metricData] = await Promise.all([
                this.api.getDashboardData(timeRange),
                this.api.fetchMetricData(currentMetric, timeRange)
            ]);
            
            // Update dashboard and chart
            this.updateDashboard(dashboardData);
            const chart = this.charts.get('fieldMetrics');
            if (chart && metricData) {
                chart.data.labels = metricData.labels;
                chart.data.datasets = metricData.datasets;
                chart.update();
            }
        } catch (error) {
            UIManager.showError('Failed to update time range');
            console.error('Time range update error:', error);
        } finally {
            UIManager.toggleSkeleton(false);
        }
    }

    findCardByTitle(title) {
        const titleElements = document.querySelectorAll('.data-card .text-lg.font-semibold');
        for (const element of titleElements) {
            if (element.textContent.trim() === title) {
                return element.closest('.data-card');
            }
        }
        return null;
    }

    formatMetricValue(value, metric) {
        switch (metric.toLowerCase()) {
            case 'temperature':
                return `${value}°C`;
            case 'humidity':
            case 'soil moisture':
                return `${value}%`;
            case 'wind speed':
                return `${value} km/h`;
            case 'soil ph':
                return value.toFixed(1);
            default:
                return value.toString();
        }
    }

    updateRecommendations(recommendations) {
        if (!recommendations) return;
        
        const container = document.querySelector('.grid-cols-1.md\\:grid-cols-2.lg\\:grid-cols-3.gap-6');
        if (!container) return;

        // Clear existing recommendations
        container.innerHTML = '';

        // Add new recommendations
        recommendations.forEach(rec => {
            const priorityColor = this.getPriorityColor(rec.priority);
            container.innerHTML += `
                <div class="bg-white rounded-xl shadow-card overflow-hidden">
                    <div class="h-4 ${priorityColor}"></div>
                    <div class="p-5">
                        <div class="flex items-center justify-between mb-3">
                            <h3 class="font-semibold">${rec.action}</h3>
                            <span class="bg-opacity-10 text-xs font-medium px-2 py-1 rounded-full ${priorityColor} text-${priorityColor.replace('bg-', '')}">${rec.priority} Priority</span>
                        </div>
                        <p class="text-medium text-sm mb-4">${rec.description}</p>
                        <div class="flex justify-between items-center">
                            <span class="text-xs text-medium">Due: ${rec.due}</span>
                            <button class="btn btn-primary text-sm">Schedule</button>
                        </div>
                    </div>
                </div>
            `;
        });
    }

    updateAlerts(alerts) {
        if (!alerts) return;
        
        const container = document.querySelector('.alerts-container');
        if (!container) return;

        // Clear existing alerts
        container.innerHTML = '';

        // Add new alerts
        alerts.forEach(alert => {
            container.innerHTML += `
                <div class="alert-card bg-white rounded-lg p-4 mb-3 shadow-sm border-l-4 border-${this.getAlertColor(alert.severity)}">
                    <div class="flex justify-between items-start">
                        <div>
                            <h4 class="font-semibold text-sm">${alert.title}</h4>
                            <p class="text-medium text-sm mt-1">${alert.message}</p>
                        </div>
                        <span class="text-xs text-medium">${this.formatAlertTime(alert.created_at)}</span>
                    </div>
                </div>
            `;
        });
    }

    getPriorityColor(priority) {
        switch(priority.toLowerCase()) {
            case 'high':
                return 'bg-primary';
            case 'medium':
                return 'bg-warning';
            case 'info':
                return 'bg-water';
            default:
                return 'bg-gray-400';
        }
    }

    getAlertColor(severity) {
        switch(severity.toLowerCase()) {
            case 'critical':
                return 'red-500';
            case 'warning':
                return 'yellow-500';
            case 'info':
                return 'blue-500';
            default:
                return 'gray-500';
        }
    }

    formatAlertTime(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diffInHours = Math.floor((now - date) / (1000 * 60 * 60));
        
        if (diffInHours < 24) {
            return diffInHours === 0 ? 'Just now' : `${diffInHours}h ago`;
        } else {
            return date.toLocaleDateString();
        }
    }
}

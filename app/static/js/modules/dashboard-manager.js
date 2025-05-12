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
    }

    setupEventListeners() {
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
            this.updateDashboard(data);
        } catch (error) {
            if (error.type === 'NO_FARM') {
                UIManager.showWarning('Please register a farm to view dashboard data');
            } else {
                UIManager.showError('Failed to refresh dashboard data');
                console.error('Dashboard refresh error:', error);
            }
        } finally {
            UIManager.toggleSkeleton(false);
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
    }

    updateDashboard(data) {
        this.updateMetrics(data.metrics);
        this.updateRecommendations(data.recommendations);
        this.updateAlerts(data.alerts);
        this.updateCharts(data.chartData);
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
    }

    async updateChartMetric(metric) {
        try {
            const data = await this.api.fetchMetricData(metric);
            const chart = this.charts.get('fieldMetrics');
            if (chart) {
                chart.data.datasets = data.datasets;
                chart.update();
            }
        } catch (error) {            UIManager.showError(`Failed to update ${metric} data`);
            console.error('Chart update error:', error);
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
}

// app/static/js/dashboard.js
import { DashboardManager } from './modules/dashboard-manager.js';

document.addEventListener('DOMContentLoaded', function() {
    // Initialize the dashboard manager
    const dashboard = new DashboardManager();

    // Initial data load with loading UI
    dashboard.refreshData();
});
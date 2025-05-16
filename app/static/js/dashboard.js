// app/static/js/dashboard.js
<<<<<<< HEAD

document.addEventListener('DOMContentLoaded', function() {
    // Set up skeleton loading
    showSkeletonLoading();

    // Initial data load
    fetchDashboardData();

    // Set up periodic refresh (every 60 seconds)
    setInterval(fetchDashboardData, 60000);

    // Refresh button event listener
    const refreshButton = document.getElementById('refreshButton');
    if (refreshButton) {
        refreshButton.addEventListener('click', function() {
            showSkeletonLoading();
            fetchDashboardData();
        });
    }

    // Profile button and user info
    fetchUserProfile();

    // Setup auto-refresh toggle
    setupAutoRefreshToggle();
});

/**
 * Show skeleton loading UI
 */
function showSkeletonLoading() {
    // Add skeleton class to all data cards
    document.querySelectorAll('.data-card').forEach(card => {
        card.classList.add('skeleton-loading');
    });

    // Add skeleton class to charts
    document.querySelectorAll('.h-80').forEach(chart => {
        chart.classList.add('skeleton-loading');
    });

    // Add skeleton class to alerts and recommendations
    document.querySelectorAll('.alert-card, .bg-white.rounded-xl.shadow-card').forEach(element => {
        element.classList.add('skeleton-loading');
    });
}

/**
 * Hide skeleton loading UI
 */
function hideSkeletonLoading() {
    document.querySelectorAll('.skeleton-loading').forEach(element => {
        element.classList.remove('skeleton-loading');
    });
}

/**
 * Show error message to user
 */
function showErrorMessage(message) {
    let errorContainer = document.getElementById('error-container');
    if (!errorContainer) {
        errorContainer = document.createElement('div');
        errorContainer.id = 'error-container';
        errorContainer.className = 'fixed top-4 right-4 bg-danger text-white p-4 rounded-lg shadow-lg z-50';
        document.body.appendChild(errorContainer);
    }

    errorContainer.textContent = message;
    errorContainer.style.display = 'block';

    setTimeout(() => {
        errorContainer.style.display = 'none';
    }, 5000);
}

/**
 * Format date and time for display
 */
function formatDateTime(dateTimeStr) {
    const date = new Date(dateTimeStr);
    return date.toLocaleString();
}

/**
 * Format time ago for alerts and notifications
 */
function formatTimeAgo(dateTimeStr) {
    const date = new Date(dateTimeStr);
    const now = new Date();
    const diffMs = now - date;
    const diffSec = Math.round(diffMs / 1000);
    const diffMin = Math.round(diffSec / 60);
    const diffHour = Math.round(diffMin / 60);
    const diffDay = Math.round(diffHour / 24);

    if (diffSec < 60) {
        return 'Just now';
    } else if (diffMin < 60) {
        return `${diffMin} minute${diffMin !== 1 ? 's' : ''} ago`;
    } else if (diffHour < 24) {
        return `${diffHour} hour${diffHour !== 1 ? 's' : ''} ago`;
    } else if (diffDay < 30) {
        return `${diffDay} day${diffDay !== 1 ? 's' : ''} ago`;
    } else {
        return date.toLocaleDateString();
    }
}

/**
 * Helper function to find a card by its title
 */
function findCardByTitle(title) {
    const titleElements = document.querySelectorAll('.data-card .text-lg.font-semibold');

    for (let i = 0; i < titleElements.length; i++) {
        if (titleElements[i].textContent.trim() === title) {
            return titleElements[i].closest('.data-card');
        }
    }
    return null;
}

/**
 * Update recommendations section
 */
function updateRecommendations(recommendations) {
    const recommendationsContainer = document.querySelector('.grid.grid-cols-1.md\\:grid-cols-2.lg\\:grid-cols-3.gap-6');
    if (!recommendationsContainer) return;

    recommendationsContainer.innerHTML = '';

    recommendations.forEach(recommendation => {
        let headerClass = 'bg-water';
        let priorityBgClass = 'bg-water bg-opacity-10 text-water';

        if (recommendation.priority === 'High') {
            headerClass = 'bg-primary';
            priorityBgClass = 'bg-primary bg-opacity-10 text-primary-dark';
        } else if (recommendation.priority === 'Medium') {
            headerClass = 'bg-warning';
            priorityBgClass = 'bg-warning bg-opacity-10 text-warning';
        }

        const recommendationHTML = `
            <div class="bg-white rounded-xl shadow-card overflow-hidden">
                <div class="h-4 ${headerClass}"></div>
                <div class="p-5">
                    <div class="flex items-center justify-between mb-3">
                        <h3 class="font-semibold">${recommendation.action}</h3>
                        <span class="${priorityBgClass} text-xs font-medium px-2 py-1 rounded-full">${recommendation.priority} Priority</span>
                    </div>
                    <p class="text-medium text-sm mb-4">${recommendation.description}</p>
                    <div class="flex justify-between items-center">
                        <span class="text-xs text-medium">Due: ${recommendation.due}</span>
                        <button class="btn btn-primary text-sm">Schedule</button>
                    </div>
                </div>
            </div>
        `;
        recommendationsContainer.insertAdjacentHTML('beforeend', recommendationHTML);
    });

    if (recommendations.length === 0) {
        recommendationsContainer.innerHTML = `
            <div class="col-span-3 text-center py-8">
                <i class="fas fa-check-circle text-primary text-4xl mb-3"></i>
                <h3 class="text-lg font-medium">No actionable recommendations</h3>
                <p class="text-medium mt-2">Your farm operations are on track.</p>
            </div>
        `;
    }
}

/**
 * Update alerts section
 */
function updateAlerts(alerts) {
    const alertsContainer = document.querySelector('.grid.grid-cols-1.md\\:grid-cols-3.gap-6');
    if (!alertsContainer) return;

    alertsContainer.innerHTML = '';

    alerts.forEach(alert => {
        let iconClass = 'fa-info-circle';
        let bgClass = 'bg-water';
        let cardClass = 'alert-card-info';

        if (alert.severity === 'High') {
            iconClass = 'fa-exclamation-triangle';
            bgClass = 'bg-danger';
            cardClass = 'alert-card-critical';
        } else if (alert.severity === 'Medium') {
            iconClass = 'fa-exclamation-circle';
            bgClass = 'bg-warning';
            cardClass = 'alert-card-warning';
        }

        const alertHTML = `
            <div class="alert-card ${cardClass} rounded p-5 flex items-start">
                <div class="${bgClass} p-3 rounded-lg text-white mr-4 flex-shrink-0">
                    <i class="fas ${iconClass} text-xl"></i>
                </div>
                <div>
                    <h4 class="font-semibold text-lg mb-1">${alert.title}</h4>
                    <p class="text-sm text-medium mb-3">${alert.message}</p>
                    <div class="flex items-center">
                        <span class="text-xs text-medium mr-3">${formatTimeAgo(alert.created_at)}</span>
                        <button class="btn btn-primary text-xs px-3 py-1">View Details</button>
                    </div>
                </div>
            </div>
        `;
        alertsContainer.insertAdjacentHTML('beforeend', alertHTML);
    });

    if (alerts.length === 0) {
        alertsContainer.innerHTML = `
            <div class="col-span-3 text-center py-8">
                <i class="fas fa-check-circle text-primary text-4xl mb-3"></i>
                <h3 class="text-lg font-medium">No active alerts</h3>
                <p class="text-medium mt-2">All systems are operating normally.</p>
            </div>
        `;
    }
}

/**
 * Fetch user profile data from the API
 */
function fetchUserProfile() {
    fetch('/api/user-profile')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            updateUserProfile(data);
        })
        .catch(error => {
            console.error('Error fetching user profile:', error);
        });
}

/**
 * Update user profile in header
 */
function updateUserProfile(userData) {
    const profileBtn = document.getElementById('userProfileBtn');
    if (!profileBtn) return;

    const avatar = profileBtn.querySelector('div');
    const nameElement = profileBtn.querySelector('span');

    if (avatar && userData.initials) {
        avatar.textContent = userData.initials;
    }

    if (nameElement && userData.full_name) {
        nameElement.textContent = userData.full_name;
    }
}

/**
 * Setup auto-refresh toggle
 */
function setupAutoRefreshToggle() {
    const toggleSwitch = document.querySelector('.toggle-switch');
    if (!toggleSwitch) return;

    const autoRefreshEnabled = localStorage.getItem('autoRefreshEnabled') !== 'false';

    toggleSwitch.classList.toggle('on', autoRefreshEnabled);
    toggleSwitch.classList.toggle('off', !autoRefreshEnabled);

    let refreshInterval = null;

    if (autoRefreshEnabled) {
        refreshInterval = setInterval(fetchDashboardData, 60000);
    }

    toggleSwitch.addEventListener('click', function() {
        this.classList.toggle('on');
        this.classList.toggle('off');

        const isEnabled = this.classList.contains('on');

        localStorage.setItem('autoRefreshEnabled', isEnabled);

        if (refreshInterval) {
            clearInterval(refreshInterval);
            refreshInterval = null;
        }

        if (isEnabled) {
            refreshInterval = setInterval(fetchDashboardData, 60000);
        }
    });
}

/**
 * Fetch dashboard data from the API
 */
function fetchDashboardData() {
    fetch('/api/dashboard-data')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            updateDashboard(data);
            hideSkeletonLoading();
        })
        .catch(error => {
            console.error('Error fetching dashboard data:', error);
            showErrorMessage('Failed to load dashboard data.');
        });
}

/**
 * Update dashboard UI with new data
 */
function updateDashboard(data) {
    updateRecommendations(data.recommendations || []);
    updateAlerts(data.alerts || []);
    // You can add more sections to update here
}
// Fetch advisory data for a specific farm
function fetchAdvisoryData(farmId) {
    fetch(`/api/advisory/${farmId}`)
        .then(response => response.json())
        .then(data => {
            updateAdvisorySection(data.advisory);
        })
        .catch(error => console.error('Error fetching advisory data:', error));
}

// Update advisory section
function updateAdvisorySection(advisoryText) {
    const advisoryContainer = document.querySelector('#advisory-section');
    if (advisoryContainer) {
        advisoryContainer.textContent = advisoryText;
    }
}
=======
import { DashboardManager } from './modules/dashboard-manager.js';

document.addEventListener('DOMContentLoaded', function() {
    // Initialize the dashboard manager
    const dashboard = new DashboardManager();

    // Initial data load with loading UI
    dashboard.refreshData();
});
>>>>>>> origin/Dynamic-Parsing

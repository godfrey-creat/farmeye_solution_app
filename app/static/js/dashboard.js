// Add this to a new file: app/static/js/dashboard.js

document.addEventListener('DOMContentLoaded', function() {
    // Set up skeleton loading
    showSkeletonLoading();

    // Initial data load
    fetchDashboardData();

    // Set up periodic refresh (every 30 seconds)
    setInterval(fetchDashboardData, 30000);

    // Refresh button event listener
    const refreshButton = document.getElementById('refreshButton');
    if (refreshButton) {
        refreshButton.addEventListener('click', function() {
            showSkeletonLoading();
            fetchDashboardData();
        });
    }
});

/**
 * Fetch dashboard data from the API
 */
// Update the fetchDashboardData function in app/static/js/dashboard.js:

/**
 * Fetch dashboard data from the API
 */
function fetchDashboardData() {
    // Show loading spinner or skeleton
    showSkeletonLoading();

    fetch('/api/dashboard-data')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok: ' + response.status);
            }
            return response.json();
        })
        .then(data => {
            console.log('Dashboard data loaded successfully');
            updateDashboard(data);
            hideSkeletonLoading();
        })
        .catch(error => {
            console.error('Error fetching dashboard data:', error);
            // Try fallback URL
            console.log('Trying fallback URL...');
            fetch('/api/debug')
                .then(response => response.json())
                .then(debugData => {
                    console.log('API Debug data:', debugData);
                    showErrorMessage('API Error: ' + error.message + '. Check console for debug info.');
                })
                .catch(debugError => {
                    console.error('Debug API also failed:', debugError);
                    showErrorMessage('Unable to load dashboard data. Please try again later.');
                })
                .finally(() => {
                    hideSkeletonLoading();
                });
        });
}
/**
 * Update all dashboard components with the fetched data
 */
function updateDashboard(data) {
    // 1. Update Farm & Field Info
    updateFarmInfo(data.farm_info);

    // 2. Update Weather Info
    updateWeatherInfo(data.weather);

    // 3. Update Soil Health
    updateSoilHealth(data.soil_health);

    // 4. Update Crop Growth
    updateCropGrowth(data.crop_growth);

    // 5. Update Charts
    updateCharts(data.historical_data);

    // 6. Update Alerts
    updateAlerts(data.alerts);

    // 7. Update Recommendations
    updateRecommendations(data.recommendations);
}

/**
 * Update farm and field information
 */
function updateFarmInfo(farmInfo) {
    // Update farm name and field
    const farmNameElement = document.querySelector('.text-3xl.font-semibold.text-dark');
    if (farmNameElement) {
        farmNameElement.textContent = `${farmInfo.field} Dashboard`;
    }

    // Update last updated time
    const lastUpdatedElement = document.querySelector('.text-medium.mt-1');
    if (lastUpdatedElement) {
        lastUpdatedElement.textContent = `Last updated: ${formatDateTime(farmInfo.last_updated)}`;
    }
}

/**
 * Update weather widget information
 */
function updateWeatherInfo(weather) {
    // Update temperature in header weather widget
    const tempElement = document.querySelector('.weather-widget .font-bold.text-lg');
    if (tempElement) {
        tempElement.textContent = `${weather.temperature}°C`;
    }

    // Update weather condition text
    const conditionElement = document.querySelector('.weather-widget .text-xs');
    if (conditionElement) {
        conditionElement.textContent = weather.condition;
    }

    // Update weather icon (if available)
    const iconElement = document.querySelector('.weather-widget i');
    if (iconElement) {
        // Map OpenWeather icon codes to Font Awesome icons
        const iconMap = {
            '01d': 'fa-sun',          // clear sky day
            '01n': 'fa-moon',         // clear sky night
            '02d': 'fa-cloud-sun',    // few clouds day
            '02n': 'fa-cloud-moon',   // few clouds night
            '03d': 'fa-cloud',        // scattered clouds
            '03n': 'fa-cloud',
            '04d': 'fa-cloud',        // broken clouds
            '04n': 'fa-cloud',
            '09d': 'fa-cloud-rain',   // shower rain
            '09n': 'fa-cloud-rain',
            '10d': 'fa-cloud-sun-rain', // rain day
            '10n': 'fa-cloud-moon-rain', // rain night
            '11d': 'fa-bolt',         // thunderstorm
            '11n': 'fa-bolt',
            '13d': 'fa-snowflake',    // snow
            '13n': 'fa-snowflake',
            '50d': 'fa-smog',         // mist
            '50n': 'fa-smog'
        };

        // Remove all existing weather icon classes
        iconElement.className = '';
        // Add base classes and the mapped weather icon
        iconElement.classList.add('fas', iconMap[weather.icon] || 'fa-sun', 'text-accent', 'text-2xl', 'mr-3');
    }
}

/**
 * Update soil health information
 */
function updateSoilHealth(soilHealth) {
    // Update field health percentage
    const healthPercentElement = document.querySelector('.health-indicator-inner');
    if (healthPercentElement) {
        healthPercentElement.textContent = `${soilHealth.overall_health}%`;
    }

    // Update health indicator color and percentage
    const healthIndicator = document.querySelector('.health-indicator');
    if (healthIndicator) {
        healthIndicator.style.setProperty('--percentage', `${soilHealth.overall_health}%`);
    }

    // Update improvement text
    const improvementElement = document.querySelector('.text-primary-light + span');
    if (improvementElement) {
        improvementElement.textContent = `${soilHealth.improvement}% improvement from last week`;
    }

    // Update soil health quality percentage
    const qualityPercentElement = document.querySelector('.progress-bar .bg-soil');
    if (qualityPercentElement) {
        qualityPercentElement.style.width = `${soilHealth.quality}%`;
    }

    // Update soil health metrics
    document.querySelectorAll('.grid.grid-cols-2.gap-4 .font-semibold').forEach((element, index) => {
        switch(index) {
            case 0: element.textContent = `${soilHealth.nitrogen} ppm`; break;
            case 1: element.textContent = `${soilHealth.phosphorus} ppm`; break;
            case 2: element.textContent = `${soilHealth.ph_level}`; break;
            case 3: element.textContent = `${soilHealth.organic_matter}%`; break;
        }
    });

    // Update moisture level
    const moistureElement = document.querySelector('.progress-bar .bg-water');
    if (moistureElement) {
        moistureElement.style.width = `${soilHealth.moisture}%`;
    }

    // Update moisture percentage text
    const moistureTextElement = document.querySelector('.flex.justify-between.mb-1 .text-sm.font-medium');
    if (moistureTextElement) {
        moistureTextElement.textContent = `${soilHealth.moisture}%`;
    }

    // Update irrigation info
    const irrigationElements = document.querySelectorAll('.grid.grid-cols-1.gap-3 .font-medium');
    if (irrigationElements.length >= 2) {
        irrigationElements[0].textContent = soilHealth.last_irrigation;
        irrigationElements[1].textContent = soilHealth.next_irrigation;
    }
}

/**
 * Update crop growth information
 */
function updateCropGrowth(cropGrowth) {
    // Update growth stage
    const stageElement = document.querySelector('.mt-6 .text-lg.font-semibold');
    if (stageElement) {
        stageElement.textContent = cropGrowth.stage;
    }

    // Update progress percentage
    const progressText = document.querySelector('.mt-6 .text-sm.text-medium');
    if (progressText) {
        progressText.textContent = `${cropGrowth.progress}% complete`;
    }

    // Update progress bar
    const progressBar = document.querySelector('.progress-bar .bg-primary');
    if (progressBar) {
        progressBar.style.width = `${cropGrowth.progress}%`;
    }

    // Update days counter
    const daysElement = document.querySelector('.flex.justify-between.mb-1 .text-sm.font-medium');
    if (daysElement) {
        daysElement.textContent = `Day ${cropGrowth.days}`;
    }

    // Update next stage and harvest info
    const growthInfoElements = document.querySelectorAll('.text-sm .font-medium');
    if (growthInfoElements.length >= 2) {
        growthInfoElements[0].textContent = cropGrowth.next_stage;
        growthInfoElements[1].textContent = cropGrowth.harvest_date;
    }
}

/**
 * Update Chart.js visualizations
 */
function updateCharts(historicalData) {
    // Get field metrics chart context
    const ctx = document.getElementById('fieldMetricsChart');
    if (!ctx) return;

    // Check if chart already exists
    let fieldMetricsChart = Chart.getChart(ctx);

    // If chart exists, update its data
    if (fieldMetricsChart) {
        fieldMetricsChart.data.labels = historicalData.dates;
        fieldMetricsChart.data.datasets[0].data = historicalData.temperature;
        fieldMetricsChart.update();
    } else {
        // Initialize new chart with data
        fieldMetricsChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: historicalData.dates,
                datasets: [
                    {
                        label: 'Temperature (°C)',
                        data: historicalData.temperature,
                        borderColor: '#F1C40F',
                        backgroundColor: 'rgba(241, 196, 15, 0.1)',
                        borderWidth: 3,
                        pointRadius: 4,
                        pointBackgroundColor: '#F1C40F',
                        tension: 0.3,
                        fill: true
                    }
                ]
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
                            font: {
                                size: 12
                            }
                        }
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        backgroundColor: 'rgba(44, 62, 80, 0.8)',
                        padding: 12,
                        bodySpacing: 6,
                        titleFont: {
                            size: 14,
                            weight: 'bold'
                        },
                        bodyFont: {
                            size: 13
                        },
                        cornerRadius: 6
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        grid: {
                            color: 'rgba(236, 240, 241, 0.6)'
                        },
                        ticks: {
                            font: {
                                size: 11
                            }
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            font: {
                                size: 11
                            },
                            maxRotation: 45,
                            minRotation: 45
                        }
                    }
                },
                elements: {
                    line: {
                        borderJoinStyle: 'round'
                    }
                }
            }
        });
    }

    // Set up chart type buttons
    setupChartTypeButtons(fieldMetricsChart, historicalData);
}

/**
 * Setup event handlers for chart type buttons
 */
function setupChartTypeButtons(chart, historicalData) {
    const chartButtons = document.querySelectorAll('.btn-primary, .btn-outline');

    chartButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Remove active class from all buttons
            chartButtons.forEach(btn => {
                btn.classList.remove('btn-primary');
                btn.classList.add('btn-outline');
            });

            // Add active class to clicked button
            this.classList.remove('btn-outline');
            this.classList.add('btn-primary');

            // Update chart data based on button text
            const metric = this.textContent.trim();

            // Update chart data based on selected metric
            switch(metric) {
                case 'Temperature':
                    chart.data.datasets = [{
                        label: 'Temperature (°C)',
                        data: historicalData.temperature,
                        borderColor: '#F1C40F',
                        backgroundColor: 'rgba(241, 196, 15, 0.1)',
                        borderWidth: 3,
                        pointRadius: 4,
                        pointBackgroundColor: '#F1C40F',
                        tension: 0.3,
                        fill: true
                    }];
                    break;
                case 'Moisture':
                    chart.data.datasets = [{
                        label: 'Soil Moisture (%)',
                        data: historicalData.moisture,
                        borderColor: '#3498DB',
                        backgroundColor: 'rgba(52, 152, 219, 0.1)',
                        borderWidth: 3,
                        pointRadius: 4,
                        pointBackgroundColor: '#3498DB',
                        tension: 0.3,
                        fill: true
                    }];
                    break;
                case 'Growth':
                    chart.data.datasets = [{
                        label: 'Growth Rate (cm/day)',
                        data: historicalData.growth,
                        borderColor: '#1D8348',
                        backgroundColor: 'rgba(29, 131, 72, 0.1)',
                        borderWidth: 3,
                        pointRadius: 4,
                        pointBackgroundColor: '#1D8348',
                        tension: 0.3,
                        fill: true
                    }];
                    break;
                case 'Soil Health':
                    chart.data.datasets = [{
                        label: 'Soil Health Index',
                        data: historicalData.soil_health,
                        borderColor: '#6E2C00',
                        backgroundColor: 'rgba(110, 44, 0, 0.1)',
                        borderWidth: 3,
                        pointRadius: 4,
                        pointBackgroundColor: '#6E2C00',
                        tension: 0.3,
                        fill: true
                    }];
                    break;
            }

            chart.update();
        });
    });
}

/**
 * Update alerts section
 */
function updateAlerts(alerts) {
    const alertsContainer = document.querySelector('.grid.grid-cols-1.md\\:grid-cols-3.gap-6');
    if (!alertsContainer) return;

    // Clear existing alerts
    alertsContainer.innerHTML = '';

    // Add new alerts
    alerts.forEach(alert => {
        // Determine icon and color based on severity
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

        // Create alert HTML
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

        // Add alert to container
        alertsContainer.insertAdjacentHTML('beforeend', alertHTML);
    });

    // If no alerts, show a message
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
 * Update recommendations section
 */
function updateRecommendations(recommendations) {
    const recommendationsContainer = document.querySelector('.grid.grid-cols-1.md\\:grid-cols-2.lg\\:grid-cols-3.gap-6');
    if (!recommendationsContainer) return;

    // Clear existing recommendations
    recommendationsContainer.innerHTML = '';

    // Add new recommendations
    recommendations.forEach(recommendation => {
        // Determine color based on priority
        let headerClass = 'bg-water';
        let priorityBgClass = 'bg-water bg-opacity-10 text-water';

        if (recommendation.priority === 'High') {
            headerClass = 'bg-primary';
            priorityBgClass = 'bg-primary bg-opacity-10 text-primary-dark';
        } else if (recommendation.priority === 'Medium') {
            headerClass = 'bg-warning';
            priorityBgClass = 'bg-warning bg-opacity-10 text-warning';
        }

        // Create recommendation HTML
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

        // Add recommendation to container
        recommendationsContainer.insertAdjacentHTML('beforeend', recommendationHTML);
    });

    // If no recommendations, show a message
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
    // Remove skeleton class from all elements
    document.querySelectorAll('.skeleton-loading').forEach(element => {
        element.classList.remove('skeleton-loading');
    });
}

/**
 * Show error message to user
 */
function showErrorMessage(message) {
    // Check if error container exists, create if not
    let errorContainer = document.getElementById('error-container');
    if (!errorContainer) {
        errorContainer = document.createElement('div');
        errorContainer.id = 'error-container';
        errorContainer.className = 'fixed top-4 right-4 bg-danger text-white p-4 rounded-lg shadow-lg z-50';
        document.body.appendChild(errorContainer);
    }

    // Set error message
    errorContainer.textContent = message;

    // Show error
    errorContainer.style.display = 'block';

    // Hide after 5 seconds
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
        // For older dates, return the formatted date
        return date.toLocaleDateString();
    }
}
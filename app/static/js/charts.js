<<<<<<< HEAD
document.addEventListener('DOMContentLoaded', function() {
    const ctx = document.getElementById('fieldMetricsChart');
    if (!ctx) return;
    
    const fieldMetricsChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['May 1', 'May 3', 'May 5', 'May 7', 'May 9', 'May 11', 'May 13', 'May 15', 'May 17', 'May 19', 'May 21', 'May 23', 'May 25', 'May 27', 'May 29'],
            datasets: [
                {
                    label: 'Temperature (°C)',
                    data: [22, 24, 26, 25, 27, 26, 24, 25, 26, 28, 29, 27, 26, 24, 23],
                    borderColor: '#F1C40F',
                    backgroundColor: 'rgba(241, 196, 15, 0.1)',
                    borderWidth: 3,
                    pointRadius: 4,
                    pointBackgroundColor: '#F1C40F',
                    tension: 0.3,
                    fill: true
                },
                {
                    label: 'Soil Moisture (%)',
                    data: [68, 65, 62, 60, 58, 75, 72, 68, 65, 62, 59, 56, 53, 70, 68],
                    borderColor: '#3498DB',
                    backgroundColor: 'rgba(52, 152, 219, 0.1)',
                    borderWidth: 3,
                    pointRadius: 4,
                    pointBackgroundColor: '#3498DB',
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
    
    // Add click handlers for the chart type buttons
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
            updateChartData(fieldMetricsChart, metric);
        });
    });
    
    function updateChartData(chart, metric) {
        // This would be replaced with actual API calls in a real application
        switch(metric) {
            case 'Temperature':
                chart.data.datasets = [{
                    label: 'Temperature (°C)',
                    data: [22, 24, 26, 25, 27, 26, 24, 25, 26, 28, 29, 27, 26, 24, 23],
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
                    data: [68, 65, 62, 60, 58, 75, 72, 68, 65, 62, 59, 56, 53, 70, 68],
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
                    data: [2.1, 2.3, 2.8, 3.0, 3.2, 3.1, 2.9, 2.7, 2.5, 2.4, 2.2, 2.0, 1.9, 1.8, 1.7],
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
                    data: [76, 75, 74, 76, 78, 80, 78, 77, 76, 75, 74, 73, 75, 78, 77],
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
    }
=======
document.addEventListener('DOMContentLoaded', function() {
    const ctx = document.getElementById('fieldMetricsChart');
    if (!ctx) return;
    
    const fieldMetricsChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['May 1', 'May 3', 'May 5', 'May 7', 'May 9', 'May 11', 'May 13', 'May 15', 'May 17', 'May 19', 'May 21', 'May 23', 'May 25', 'May 27', 'May 29'],
            datasets: [
                {
                    label: 'Temperature (°C)',
                    data: [22, 24, 26, 25, 27, 26, 24, 25, 26, 28, 29, 27, 26, 24, 23],
                    borderColor: '#F1C40F',
                    backgroundColor: 'rgba(241, 196, 15, 0.1)',
                    borderWidth: 3,
                    pointRadius: 4,
                    pointBackgroundColor: '#F1C40F',
                    tension: 0.3,
                    fill: true
                },
                {
                    label: 'Soil Moisture (%)',
                    data: [68, 65, 62, 60, 58, 75, 72, 68, 65, 62, 59, 56, 53, 70, 68],
                    borderColor: '#3498DB',
                    backgroundColor: 'rgba(52, 152, 219, 0.1)',
                    borderWidth: 3,
                    pointRadius: 4,
                    pointBackgroundColor: '#3498DB',
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
    
    // Add click handlers for the chart type buttons
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
            updateChartData(fieldMetricsChart, metric);
        });
    });
    
    function updateChartData(chart, metric) {
        // This would be replaced with actual API calls in a real application
        switch(metric) {
            case 'Temperature':
                chart.data.datasets = [{
                    label: 'Temperature (°C)',
                    data: [22, 24, 26, 25, 27, 26, 24, 25, 26, 28, 29, 27, 26, 24, 23],
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
                    data: [68, 65, 62, 60, 58, 75, 72, 68, 65, 62, 59, 56, 53, 70, 68],
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
                    data: [2.1, 2.3, 2.8, 3.0, 3.2, 3.1, 2.9, 2.7, 2.5, 2.4, 2.2, 2.0, 1.9, 1.8, 1.7],
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
                    data: [76, 75, 74, 76, 78, 80, 78, 77, 76, 75, 74, 73, 75, 78, 77],
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
    }
>>>>>>> origin/Dynamic-Parsing
});
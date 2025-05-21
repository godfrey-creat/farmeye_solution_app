// UIManager class for handling all UI operations
export class UIManager {
    constructor() {
        this.setupContainers();
    }

    setupContainers() {
        // Create error container if it doesn't exist
        if (!document.getElementById('error-container')) {
            const container = document.createElement('div');
            container.id = 'error-container';
            container.className = 'fixed top-4 right-4 bg-danger text-white p-4 rounded-lg shadow-lg z-50 hidden';
            document.body.appendChild(container);
        }

        // Create success container if it doesn't exist
        if (!document.getElementById('success-container')) {
            const container = document.createElement('div');
            container.id = 'success-container';
            container.className = 'fixed top-4 right-4 bg-green-500 text-white p-4 rounded-lg shadow-lg z-50 hidden';
            document.body.appendChild(container);
        }
    }

    showLoading() {
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

    hideLoading() {
        document.querySelectorAll('.skeleton-loading').forEach(element => {
            element.classList.remove('skeleton-loading');
        });
    }

    showError(message, duration = 5000) {
        const container = document.getElementById('error-container');
        if (!container) return;

        container.textContent = message;
        container.classList.remove('hidden');

        setTimeout(() => {
            container.classList.add('hidden');
        }, duration);
    }

    showSuccess(message, duration = 5000) {
        const container = document.getElementById('success-container');
        if (!container) return;

        container.textContent = message;
        container.classList.remove('hidden');

        setTimeout(() => {
            container.classList.add('hidden');
        }, duration);
    }

    formatDateTime(dateTimeStr) {
        const date = new Date(dateTimeStr);
        return date.toLocaleString();
    }

    formatTimeAgo(dateTimeStr) {
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
}

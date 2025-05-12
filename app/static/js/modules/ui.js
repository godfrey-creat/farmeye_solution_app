// UI Components Module
export class UIManager {
    static toastTypes = {
        INFO: 'info',
        SUCCESS: 'success',
        ERROR: 'error',
        WARNING: 'warning'
    };

    static showToast(message, type = 'info', duration = 3000) {
        const existingToast = document.querySelector('.toast');
        if (existingToast) {
            existingToast.remove();
        }

        const toast = document.createElement('div');
        toast.className = `toast toast-${type} fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 flex items-center`;
        
        // Add appropriate background color and icon based on type
        switch (type) {
            case 'success':
                toast.classList.add('bg-green-500', 'text-white');
                break;
            case 'error':
                toast.classList.add('bg-red-500', 'text-white');
                break;
            case 'warning':
                toast.classList.add('bg-yellow-500', 'text-white');
                break;
            default:
                toast.classList.add('bg-blue-500', 'text-white');
        }

        // Add progress bar
        const progressBar = document.createElement('div');
        progressBar.className = 'absolute bottom-0 left-0 h-1 bg-white bg-opacity-50';
        progressBar.style.width = '100%';
        progressBar.style.transition = `width ${duration}ms linear`;

        toast.innerHTML = `
            <div class="flex-1">${message}</div>
            <button class="ml-4 text-white hover:text-gray-200" onclick="this.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        `;
        toast.appendChild(progressBar);
        document.body.appendChild(toast);

        // Animate progress bar
        setTimeout(() => {
            progressBar.style.width = '0%';
        }, 100);

        // Remove toast after duration
        setTimeout(() => {
            toast.remove();
        }, duration);
    }

    static showLoading(message = 'Loading...') {
        return this.showToast(message, 'info');
    }

    static showSuccess(message) {
        return this.showToast(message, 'success');
    }

    static showError(message) {
        return this.showToast(message, 'error');
    }

    static showWarning(message) {
        return this.showToast(message, 'warning');
    }

    static toggleSkeleton(show = true) {
        document.querySelectorAll('.skeleton-loading').forEach(element => {
            element.classList.toggle('skeleton-active', show);
        });
    }

    static showFallbackUI(container, message = 'Unable to load data', retryCallback = null) {
        container.innerHTML = `
            <div class="text-center py-8">
                <i class="fas fa-exclamation-circle text-gray-400 text-4xl mb-4"></i>
                <h3 class="text-lg font-medium text-gray-600">${message}</h3>
                ${retryCallback ? `
                    <button class="mt-4 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark transition">
                        <i class="fas fa-sync-alt mr-2"></i>Retry
                    </button>
                ` : ''}
            </div>
        `;

        if (retryCallback) {
            container.querySelector('button')?.addEventListener('click', retryCallback);
        }
    }
}

/**
 * API Module
 * Handles all API requests to backend services
 */
export class API {
    constructor() {
        this.baseUrl = ''; // Can be updated if needed, e.g., 'https://api.yourdomain.com'
        this.defaultHeaders = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        };
    }

    /**
     * Helper method for making API requests
     * @param {string} url API endpoint
     * @param {Object} options Fetch options
     * @param {string} errorType Custom error type for specific API calls
     * @param {string} defaultErrorMessage Default message if no specific error message is available
     */
    async request(url, options = {}, errorType = 'API_ERROR', defaultErrorMessage = 'API request failed') {
        const response = await fetch(url, {
            headers: this.defaultHeaders,
            credentials: 'same-origin',
            ...options
        });

        if (!response.ok) {
            let errorData;
            try {
                errorData = await response.json();
            } catch (e) {
                // If response is not JSON, use status text
                errorData = { message: response.statusText };
            }

            throw {
                type: errorType,
                message: errorData.error || errorData.message || defaultErrorMessage
            };
        }

        return response.json();
    }

    /**
     * Generic GET request
     * @param {string} url API endpoint
     */
    async get(url) {
        return this.request(url, { method: 'GET' });
    }

    /**
     * Generic POST request
     * @param {string} url API endpoint
     * @param {Object} data Request data
     */
    async post(url, data) {
        return this.request(url, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    /**
     * Generic PUT request
     * @param {string} url API endpoint
     * @param {Object} data Request data
     */
    async put(url, data) {
        return this.request(url, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    /**
     * Generic DELETE request
     * @param {string} url API endpoint
     */
    async delete(url) {
        return this.request(url, {
            method: 'DELETE'
        });
    }

    // --- Dashboard and User Profile API Methods ---

    /**
     * Fetches dashboard data for a given time range.
     * @param {number} timeRange The time range in days (default: 30).
     */
    async getDashboardData(timeRange = 30) {
        return this.request(
            `/api/dashboard-data?range=${timeRange}`,
            {},
            'API_ERROR',
            'Failed to fetch dashboard data'
        );
    }

    /**
     * Fetches specific metric data for a given time range.
     * @param {string} metric The name of the metric to fetch.
     * @param {number} timeRange The time range in days (default: 30).
     */
    async fetchMetricData(metric, timeRange = 30) {
        return this.request(
            `/api/metric-data?metric=${metric}&range=${timeRange}`,
            {},
            'API_ERROR',
            `Failed to fetch ${metric} data`
        );
    }

    /**
     * Registers a new farm.
     * @param {Object} farmData The data for the farm to register.
     */
    async registerFarm(farmData) {
        return this.request(
            '/farm/register',
            {
                method: 'POST',
                body: JSON.stringify(farmData)
            },
            'REGISTRATION_ERROR',
            'Failed to register farm'
        );
    }

    /**
     * Fetches the user profile data.
     */
    async getUserProfile() {
        return this.request(
            '/api/user-profile',
            {},
            'PROFILE_ERROR',
            'Failed to fetch user profile'
        );
    }

    // --- Task-specific API Methods ---

    /**
     * Get tasks with filters.
     * @param {Object} filters Filter parameters.
     */
    async getTasks(filters = {}) {
        const params = new URLSearchParams();

        // Add filters to query string
        Object.entries(filters).forEach(([key, value]) => {
            if (value !== undefined && value !== null) {
                // Handle Date objects
                if (value instanceof Date) {
                    params.append(key, value.toISOString());
                } else {
                    params.append(key, value);
                }
            }
        });

        return this.get(`/tasks/api/tasks?${params.toString()}`);
    }

    /**
     * Create a new task.
     * @param {Object} taskData Task data.
     */
    async createTask(taskData) {
        return this.post('/tasks/api/tasks', taskData);
    }

    /**
     * Update an existing task.
     * @param {number} taskId Task ID.
     * @param {Object} taskData Updated task data.
     */
    async updateTask(taskId, taskData) {
        return this.put(`/tasks/api/tasks/${taskId}`, taskData);
    }

    /**
     * Delete a task.
     * @param {number} taskId Task ID.
     */
    async deleteTask(taskId) {
        return this.delete(`/tasks/api/tasks/${taskId}`);
    }

    /**
     * Get task categories.
     */
    async getTaskCategories() {
        return this.get('/tasks/api/task-categories');
    }

    /**
     * Get growth stages for a farm.
     * @param {number} farmId Farm ID.
     */
    async getGrowthStages(farmId) {
        const url = farmId ?
            `/tasks/api/growth-stages?farm_id=${farmId}` :
            '/tasks/api/growth-stages';

        return this.get(url);
    }

    /**
     * Get task statistics.
     * @param {number} farmId Farm ID (optional).
     */
    async getTaskStatistics(farmId) {
        const url = farmId ?
            `/tasks/api/tasks/statistics?farm_id=${farmId}` :
            '/tasks/api/tasks/statistics';

        return this.get(url);
    }

    /**
     * Get upcoming tasks.
     * @param {number} days Number of days ahead.
     */
    async getUpcomingTasks(days = 7) {
        return this.get(`/tasks/api/tasks/upcoming?days=${days}`);
    }

    /**
     * Get recommended tasks based on growth stages.
     * @param {number} farmId Farm ID.
     */
    async getRecommendedTasks(farmId) {
        return this.get(`/tasks/api/tasks/recommended?farm_id=${farmId}`);
    }
}

// Create singleton instance
const api = new API();
export default api;
// API Module - Handles all API calls
export class API {    async getDashboardData(timeRange = 30) {
        const response = await fetch(`/api/dashboard-data?range=${timeRange}`, {
            credentials: 'same-origin'  // Include cookies with the request
        });
        if (!response.ok) {
            throw { type: 'API_ERROR', message: 'Failed to fetch dashboard data' };
        }
        const data = await response.json();
        return data;
    }

    async fetchMetricData(metric, timeRange = 30) {
        const response = await fetch(`/api/metric-data?metric=${metric}&range=${timeRange}`, {
            credentials: 'same-origin'
        });
        if (!response.ok) {
            throw { type: 'API_ERROR', message: `Failed to fetch ${metric} data` };
        }
        return await response.json();
    }async registerFarm(farmData) {
        const response = await fetch('/farm/register', {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(farmData)
        });

        if (!response.ok) {
            const error = await response.json();
            throw { type: 'REGISTRATION_ERROR', message: error.error || 'Failed to register farm' };
        }
        return await response.json();
    }    async getUserProfile() {
        const response = await fetch('/api/user-profile', {
            credentials: 'same-origin'
        });
        if (!response.ok) {
            throw { type: 'PROFILE_ERROR', message: 'Failed to fetch user profile' };
        }
        return await response.json();
    }
}

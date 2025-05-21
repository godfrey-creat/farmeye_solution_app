import { API } from './api.js';
import { UIManager } from './ui.js';
import { modalController } from './modal.js';

class DashboardManager {
    constructor() {
        this.dashboardContainer = document.getElementById('dashboard-content');
        this.farmRegistrationModal = document.getElementById('farmRegistrationModal');
        this.init();
    }

    async init() {
        this.setupEventListeners();
        await this.loadDashboardData();
    }

    setupEventListeners() {
        // Farm registration form
        const farmForm = document.querySelector('#farmRegistrationModal form');
        if (farmForm) {
            farmForm.addEventListener('submit', this.handleFarmRegistration.bind(this));
        }

        // Modal control
        document.querySelectorAll('[data-action="open-farm-modal"]').forEach(button => {
            button.addEventListener('click', () => this.openFarmModal());
        });

        document.querySelectorAll('[data-action="close-modal"]').forEach(button => {
            button.addEventListener('click', () => this.closeFarmModal());
        });

        // Team member management
        const addTeamMemberBtn = document.querySelector('[data-action="add-team-member"]');
        if (addTeamMemberBtn) {
            addTeamMemberBtn.addEventListener('click', this.addTeamMemberField.bind(this));
        }
    }

    async loadDashboardData() {
        UIManager.toggleSkeleton(true);
        
        const result = await API.getDashboardData();
        
        UIManager.toggleSkeleton(false);

        if (result.status === 'NO_FARM') {
            this.showNoFarmState();
        } else if (result.status === 'ERROR') {
            UIManager.showError('Failed to load dashboard data');
            UIManager.showFallbackUI(this.dashboardContainer, 'Unable to load dashboard data', () => this.loadDashboardData());
        } else {
            this.renderDashboard(result.data);
        }
    }

    showNoFarmState() {
        UIManager.showWarning('Please register a farm to get started');
        this.dashboardContainer.innerHTML = `
            <div class="text-center py-12">
                <i class="fas fa-seedling text-6xl text-gray-400 mb-4"></i>
                <h2 class="text-2xl font-bold text-gray-700 mb-2">Welcome to FarmEye</h2>
                <p class="text-gray-500 mb-6">Get started by registering your farm</p>
                <button class="btn btn-primary" data-action="open-farm-modal">
                    <i class="fas fa-plus mr-2"></i>Register Farm
                </button>
            </div>
        `;

        // Reattach event listener
        document.querySelector('[data-action="open-farm-modal"]')
            ?.addEventListener('click', () => this.openFarmModal());
    }

    renderDashboard(data) {
        // Implement dashboard rendering logic
        // This would include charts, stats, and other visualizations
    }

    openFarmModal() {
        this.farmRegistrationModal?.classList.add('active');
        document.querySelector('.modal-overlay')?.classList.add('active');
    }

    closeFarmModal() {
        this.farmRegistrationModal?.classList.remove('active');
        document.querySelector('.modal-overlay')?.classList.remove('active');
    }

    async handleFarmRegistration(event) {
        event.preventDefault();
        const form = event.target;
        const formData = new FormData(form);
        
        // Basic validation
        const requiredFields = ['name', 'size_acres', 'latitude', 'longitude'];
        for (const field of requiredFields) {
            if (!formData.get(field)) {
                UIManager.showError(`${field.replace('_', ' ')} is required`);
                return;
            }
        }

        // Process team members
        const teamMembers = Array.from(document.querySelectorAll('.team-member')).map(member => ({
            email: member.querySelector('input[type="email"]').value,
            role: member.querySelector('select').value
        })).filter(member => member.email);

        const data = {
            name: formData.get('name'),
            size_acres: parseFloat(formData.get('size_acres')),
            crop_type: formData.get('crop_type'),
            latitude: parseFloat(formData.get('latitude')),
            longitude: parseFloat(formData.get('longitude')),
            region: formData.get('region'),
            soil_type: formData.get('soil_type'),
            ph_level: formData.get('ph_level') ? parseFloat(formData.get('ph_level')) : null,
            soil_notes: formData.get('soil_notes'),
            irrigation_type: formData.get('irrigation_type'),
            water_source: formData.get('water_source'),
            description: formData.get('description'),
            team_members: teamMembers
        };

        UIManager.showLoading('Registering farm...');
        const result = await API.registerFarm(data);

        if (result.status === 'SUCCESS') {
            UIManager.showSuccess('Farm registered successfully');
            this.closeFarmModal();
            await this.loadDashboardData();
        } else {
            UIManager.showError(result.message || 'Failed to register farm');
        }
    }

    addTeamMemberField() {
        const teamMembersContainer = document.getElementById('teamMembers');
        const newMember = document.createElement('div');
        newMember.className = 'team-member grid grid-cols-3 gap-4 items-center';
        newMember.innerHTML = `
            <div class="input-group mb-0">
                <input type="email" placeholder="Email address" class="w-full">
            </div>
            <div class="input-group mb-0">
                <select class="w-full">
                    <option value="viewer">Viewer</option>
                    <option value="editor">Editor</option>
                    <option value="admin">Admin</option>
                </select>
            </div>
            <button type="button" class="text-red-500 hover:text-red-700">
                <i class="fas fa-trash"></i>
            </button>
        `;

        // Add remove handler
        newMember.querySelector('button').addEventListener('click', () => {
            newMember.remove();
        });

        teamMembersContainer.appendChild(newMember);
    }
}

// Initialize dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new DashboardManager();
});

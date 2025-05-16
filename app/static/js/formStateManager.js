// Form State Manager
class FormStateManager {
    constructor() {
        this.state = {
            manager: {
                firstName: '',
                lastName: '',
                email: ''
            },
            farms: [],
            teamMembers: []
        };
        this.initialState = null;
        this.subscribers = [];
        this.isDirty = false;
    }    // Update state
    setState(newState) {
        this.state = { ...this.state, ...newState };
        this.isDirty = true;
        this.notifySubscribers();
    }

    // Subscribe to state changes
    subscribe(callback) {
        this.subscribers.push(callback);
    }

    // Notify all subscribers
    notifySubscribers() {
        this.subscribers.forEach(callback => callback(this.state));
    }

    // Save form data
    async saveFormData() {
        try {
            const response = await fetch('/farm/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('input[name="csrf_token"]').value
                },
                body: JSON.stringify(this.state)
            });

            if (!response.ok) {
                throw new Error('Failed to save form data');
            }

            const result = await response.json();
            return { success: true, data: result };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }    // Load initial data
    loadInitialData() {
        const managerSection = document.getElementById('manager-info');
        if (managerSection) {
            this.state.manager = {
                firstName: managerSection.querySelector('#first_name').value,
                lastName: managerSection.querySelector('#last_name').value,
                email: managerSection.querySelector('#email').value
            };
            // Store initial state for comparison
            this.initialState = JSON.stringify(this.state);
        }
    }

    // Check if form is valid for submission
    isValid() {
        // Check if at least one farm is added
        if (this.state.farms.length === 0) {
            return { valid: false, message: 'Please add at least one farm.' };
        }

        // Check if manager info is complete
        if (!this.state.manager.firstName || !this.state.manager.lastName || !this.state.manager.email) {
            return { valid: false, message: 'Please complete manager information.' };
        }

        return { valid: true };
    }

    // Check if any changes were made
    hasChanges() {
        return this.isDirty || JSON.stringify(this.state) !== this.initialState;
    }

    // Update manager info
    updateManagerInfo(data) {
        this.setState({
            manager: { ...this.state.manager, ...data }
        });
    }

    // Add farm
    addFarm(farm) {
        this.setState({
            farms: [...this.state.farms, farm]
        });
    }

    // Remove farm
    removeFarm(farmId) {
        this.setState({
            farms: this.state.farms.filter(farm => farm.id !== farmId)
        });
    }

    // Add team member
    addTeamMember(member) {
        this.setState({
            teamMembers: [...this.state.teamMembers, member]
        });
    }

    // Remove team member
    removeTeamMember(memberId) {
        this.setState({
            teamMembers: this.state.teamMembers.filter(member => member.id !== memberId)
        });
    }
}
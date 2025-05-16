// ModalController class for handling all modal operations
export class ModalController {
    constructor() {
        this.activeModal = null;
        this.modalContainer = this.createModalContainer();
        this.setupEventListeners();
    }

    createModalContainer() {
        const container = document.createElement('div');
        container.id = 'modalContainer';
        container.className = 'fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center hidden';
        document.body.appendChild(container);
        return container;
    }

    setupEventListeners() {
        // Close modal when clicking outside
        this.modalContainer.addEventListener('click', (e) => {
            if (e.target === this.modalContainer) {
                this.closeActiveModal();
            }
        });

        // Close modal on Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.activeModal) {
                this.closeActiveModal();
            }
        });
    }

    openModal(modalContent) {
        // If modalContent is a string, assume it's the ID of a template
        if (typeof modalContent === 'string') {
            const template = document.getElementById(modalContent);
            if (template) {
                modalContent = template.content.cloneNode(true);
            } else {
                console.error(`Modal template not found: ${modalContent}`);
                return;
            }
        }

        // Clean up any existing modal
        if (this.activeModal) {
            this.activeModal.remove();
        }

        // Setup new modal
        this.activeModal = document.createElement('div');
        this.activeModal.className = 'bg-white rounded-lg p-8 max-w-md w-full mx-4';
        this.activeModal.appendChild(modalContent);

        // Add close button if not present
        if (!this.activeModal.querySelector('.modal-close')) {
            const closeButton = document.createElement('button');
            closeButton.className = 'absolute top-4 right-4 text-gray-500 hover:text-gray-700';
            closeButton.innerHTML = '<i class="fas fa-times"></i>';
            closeButton.addEventListener('click', () => this.closeActiveModal());
            this.activeModal.appendChild(closeButton);
        }

        // Show modal
        this.modalContainer.appendChild(this.activeModal);
        this.modalContainer.classList.remove('hidden');

        // Focus first input if present
        const firstInput = this.activeModal.querySelector('input, select, textarea');
        if (firstInput) {
            firstInput.focus();
        }

        // Return reference for chaining
        return this.activeModal;
    }

    closeActiveModal() {
        if (this.activeModal) {
            this.modalContainer.classList.add('hidden');
            this.activeModal.remove();
            this.activeModal = null;
        }
    }

    showFarmRegistrationModal() {
        const modalContent = `
            <h2 class="text-2xl font-bold mb-4">Register Your Farm</h2>
            <form id="farmRegistrationForm" class="space-y-4">
                <div>
                    <label class="block text-sm font-medium text-gray-700">Farm Name</label>
                    <input type="text" name="name" required class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-50">
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700">Location (Coordinates)</label>
                    <div class="flex gap-2">
                        <input type="text" name="latitude" placeholder="Latitude" required class="mt-1 block w-1/2 rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-50">
                        <input type="text" name="longitude" placeholder="Longitude" required class="mt-1 block w-1/2 rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-50">
                    </div>
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700">Size (Acres)</label>
                    <input type="number" name="size_acres" required class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-50">
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700">Crop Type</label>
                    <input type="text" name="crop_type" required class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-50">
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700">Description</label>
                    <textarea name="description" rows="3" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-50"></textarea>
                </div>
                <div class="flex justify-end space-x-3 mt-6">
                    <button type="button" class="btn btn-outline" onclick="modalController.closeActiveModal()">Cancel</button>
                    <button type="submit" class="btn btn-primary">Register Farm</button>
                </div>
            </form>
        `;

        const modal = this.openModal(modalContent);
        const form = modal.querySelector('#farmRegistrationForm');

        // Handle form submission
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(form);
            const location = `${formData.get('latitude')},${formData.get('longitude')}`;
            
            try {
                const response = await fetch('/farm/register', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        name: formData.get('name'),
                        location: location,
                        size_acres: formData.get('size_acres'),
                        crop_type: formData.get('crop_type'),
                        description: formData.get('description')
                    })
                });

                const data = await response.json();
                if (response.ok) {
                    document.dispatchEvent(new CustomEvent('farmRegistered'));
                    this.closeActiveModal();
                } else {
                    throw new Error(data.error || 'Failed to register farm');
                }
            } catch (error) {
                console.error('Error registering farm:', error);
                const errorMessage = error.message || 'An error occurred while registering the farm';
                // Show error in the form
                let errorDiv = form.querySelector('.error-message');
                if (!errorDiv) {
                    errorDiv = document.createElement('div');
                    errorDiv.className = 'error-message text-danger text-sm mt-4';
                    form.appendChild(errorDiv);
                }
                errorDiv.textContent = errorMessage;
            }
        });
    }
}

// Modal Controller Module
export class ModalController {
    constructor() {
        this.activeModal = null;
        this.setupGlobalListeners();
    }

    setupGlobalListeners() {
        // Close modal when clicking outside
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal-overlay')) {
                this.closeActiveModal();
            }
        });

        // Handle escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.activeModal) {
                this.closeActiveModal();
            }
        });
    }

    openModal(modalId) {
        const modal = document.getElementById(modalId);
        if (!modal) return;

        // Close any active modal first
        if (this.activeModal) {
            this.closeActiveModal();
        }

        // Show modal and overlay
        modal.classList.add('active');
        const overlay = modal.closest('.modal-overlay');
        if (overlay) {
            overlay.classList.add('active');
        }

        this.activeModal = modal;

        // Prevent body scroll
        document.body.style.overflow = 'hidden';

        // Trigger open event
        const event = new CustomEvent('modal:opened', { detail: { modalId } });
        document.dispatchEvent(event);
    }

    closeActiveModal() {
        if (!this.activeModal) return;

        const modalId = this.activeModal.id;

        // Hide modal and overlay
        this.activeModal.classList.remove('active');
        const overlay = this.activeModal.closest('.modal-overlay');
        if (overlay) {
            overlay.classList.remove('active');
        }

        // Reset active modal
        this.activeModal = null;

        // Restore body scroll
        document.body.style.overflow = '';

        // Trigger close event
        const event = new CustomEvent('modal:closed', { detail: { modalId } });
        document.dispatchEvent(event);
    }

    isModalOpen() {
        return !!this.activeModal;
    }

    getActiveModal() {
        return this.activeModal;
    }
}

// Create and export a singleton instance
export const modalController = new ModalController();

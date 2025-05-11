// Mobile menu toggle
document.addEventListener('DOMContentLoaded', function() {
    const mobileMenuButton = document.getElementById('mobileMenuButton');
    const sidebar = document.querySelector('.sidebar');
    
    if (mobileMenuButton && sidebar) {
        mobileMenuButton.addEventListener('click', function() {
            sidebar.classList.toggle('open');
        });
    }

    // Toggle switch functionality
    const toggleSwitches = document.querySelectorAll('.toggle-switch');
    toggleSwitches.forEach(function(toggle) {
        toggle.addEventListener('click', function() {
            this.classList.toggle('on');
            this.classList.toggle('off');
        });
    });

    // Dropdown functionality for farm selector, field selector, etc.
    setupDropdowns();
    
    // Close dropdowns when clicking elsewhere
    document.addEventListener('click', function(e) {
        const dropdowns = document.querySelectorAll('.dropdown');
        dropdowns.forEach(dropdown => {
            if (!dropdown.parentElement.contains(e.target)) {
                dropdown.classList.add('hidden');
            }
        });
        
        // Also close notification dropdown
        const notificationDropdown = document.getElementById('notificationDropdown');
        if (notificationDropdown && !notificationDropdown.parentElement.contains(e.target)) {
            notificationDropdown.classList.add('hidden');
        }
    });
});

function setupDropdowns() {
    // Farm selector dropdown
    setupDropdown('farmSelector', 'farmDropdown');
    
    // Field selector dropdown
    setupDropdown('fieldSelector', 'fieldDropdown');
    
    // User profile dropdown (if added)
    setupDropdown('userProfileBtn', 'userProfileDropdown');
}

function setupDropdown(buttonId, dropdownId) {
    const button = document.getElementById(buttonId);
    const dropdown = document.getElementById(dropdownId);
    
    if (button && dropdown) {
        button.addEventListener('click', function(e) {
            e.stopPropagation();
            dropdown.classList.toggle('hidden');
            
            // Close other dropdowns
            document.querySelectorAll('.dropdown').forEach(d => {
                if (d.id !== dropdownId) {
                    d.classList.add('hidden');
                }
            });
        });
    }
}
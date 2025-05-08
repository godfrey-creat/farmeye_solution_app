document.addEventListener('DOMContentLoaded', function() {
    // Notification toggle functionality
    const notificationBtn = document.getElementById('notificationBtn');
    const notificationDropdown = document.getElementById('notificationDropdown');
    
    if (notificationBtn && notificationDropdown) {
        notificationBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            notificationDropdown.classList.toggle('hidden');
            
            // Close other dropdowns when opening notifications
            document.querySelectorAll('.dropdown').forEach(d => {
                d.classList.add('hidden');
            });
        });
        
        // Prevent closing when clicking inside dropdown
        // Prevent closing when clicking inside dropdown
        notificationDropdown.addEventListener('click', function(e) {
            e.stopPropagation();
        });
        
        // Setup action buttons in notifications
        document.querySelectorAll('.notification-item button').forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                const action = this.textContent.trim();
                const notificationType = this.closest('.notification-item').querySelector('h4').textContent;
                
                console.log(`Action "${action}" triggered for notification: ${notificationType}`);
                // Here you would handle different actions based on notification type
                // For example: redirecting to details page, opening scheduling modal, etc.
            });
        });
    }
    
    // Function to add a new notification programmatically
    window.addNotification = function(type, title, message, time, actionText) {
        if (!notificationDropdown) return;
        
        const notificationList = notificationDropdown.querySelector('.notification-list');
        if (!notificationList) return;
        
        // Determine icon and styles based on type
        let iconClass, bgClass, notificationClass;
        switch(type) {
            case 'critical':
                iconClass = 'fa-exclamation-triangle';
                bgClass = 'bg-danger';
                notificationClass = 'notification-critical';
                break;
            case 'warning':
                iconClass = 'fa-exclamation-circle';
                bgClass = 'bg-warning';
                notificationClass = 'notification-warning';
                break;
            default: // info
                iconClass = 'fa-info-circle';
                bgClass = 'bg-water';
                notificationClass = 'notification-info';
                break;
        }
        
        // Create notification HTML
        const notificationHTML = `
            <div class="notification-item ${notificationClass} p-4 flex items-start">
                <div class="${bgClass} p-2 rounded-lg text-white mr-3 flex-shrink-0">
                    <i class="fas ${iconClass}"></i>
                </div>
                <div class="flex-grow">
                    <h4 class="font-semibold text-sm">${title}</h4>
                    <p class="text-xs text-medium mb-2">${message}</p>
                    <div class="flex justify-between items-center">
                        <span class="text-xs text-medium">${time}</span>
                        <button class="${bgClass} text-white text-xs px-3 py-1 rounded hover:bg-opacity-90 transition">${actionText}</button>
                    </div>
                </div>
            </div>
        `;
        
        // Add to notification list
        notificationList.insertAdjacentHTML('afterbegin', notificationHTML);
        
        // Update notification count
        const countBadge = notificationBtn.querySelector('span');
        if (countBadge) {
            const currentCount = parseInt(countBadge.textContent);
            countBadge.textContent = currentCount + 1;
        }
        
        // Add event listener to the new button
        const newButton = notificationList.querySelector('.notification-item:first-child button');
        if (newButton) {
            newButton.addEventListener('click', function(e) {
                e.preventDefault();
                console.log(`Action "${actionText}" triggered for notification: ${title}`);
                // Handle action
            });
        }
    };
});
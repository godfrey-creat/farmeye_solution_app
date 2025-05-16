<<<<<<< HEAD
// Add this to your existing JavaScript code
document.addEventListener('DOMContentLoaded', function() {
    // Notification toggle functionality
    const notificationBtn = document.querySelector('#notificationBtn');
    const notificationDropdown = document.querySelector('#notificationDropdown');
    
    notificationBtn.addEventListener('click', function(e) {
      e.stopPropagation();
      notificationDropdown.classList.toggle('hidden');
      
      // Close other dropdowns when opening notifications
      document.querySelectorAll('.dropdown').forEach(d => {
        if (d !== notificationDropdown) d.classList.add('hidden');
      });
    });
    
    // Close notification dropdown when clicking elsewhere
    document.addEventListener('click', function() {
      notificationDropdown.classList.add('hidden');
    });
    
    // Prevent closing when clicking inside dropdown
    notificationDropdown.addEventListener('click', function(e) {
      e.stopPropagation();
    });
=======
// Add this to your existing JavaScript code
document.addEventListener('DOMContentLoaded', function() {
    // Notification toggle functionality
    const notificationBtn = document.querySelector('#notificationBtn');
    const notificationDropdown = document.querySelector('#notificationDropdown');
    
    notificationBtn.addEventListener('click', function(e) {
      e.stopPropagation();
      notificationDropdown.classList.toggle('hidden');
      
      // Close other dropdowns when opening notifications
      document.querySelectorAll('.dropdown').forEach(d => {
        if (d !== notificationDropdown) d.classList.add('hidden');
      });
    });
    
    // Close notification dropdown when clicking elsewhere
    document.addEventListener('click', function() {
      notificationDropdown.classList.add('hidden');
    });
    
    // Prevent closing when clicking inside dropdown
    notificationDropdown.addEventListener('click', function(e) {
      e.stopPropagation();
    });
>>>>>>> origin/Dynamic-Parsing
  });
// Add this to your main.js or create a new file profile.js

document.addEventListener('DOMContentLoaded', function() {
    // Fetch user profile data
    fetch('/api/user-profile')
        .then(response => response.json())
        .then(data => {
            // Update user profile button
            updateUserProfileButton(data);
        })
        .catch(error => {
            console.error('Error fetching user profile:', error);
        });
});

function updateUserProfileButton(userData) {
    const profileBtn = document.getElementById('userProfileBtn');
    if (!profileBtn) return;

    // Get the avatar element (first div child)
    const avatar = profileBtn.querySelector('div');
    // Get the name element (span)
    const nameElement = profileBtn.querySelector('span');

    if (avatar && userData.initials) {
        avatar.textContent = userData.initials;
    }

    if (nameElement && userData.full_name) {
        nameElement.textContent = userData.full_name;
    }
}
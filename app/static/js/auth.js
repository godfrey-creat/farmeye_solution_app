<<<<<<< HEAD
document.addEventListener('DOMContentLoaded', function() {
    // Tab switching functionality
    const loginTab = document.getElementById('loginTab');
    const registerTab = document.getElementById('registerTab');
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    const switchToLogin = document.getElementById('switchToLogin');
    
    if (loginTab && registerTab && loginForm && registerForm) {
        loginTab.addEventListener('click', () => {
            loginTab.classList.add('active');
            registerTab.classList.remove('active');
            loginForm.classList.remove('hidden');
            registerForm.classList.add('hidden');
            
            // Update URL without page reload
            history.pushState(null, null, '/login');
        });
        
        registerTab.addEventListener('click', () => {
            registerTab.classList.add('active');
            loginTab.classList.remove('active');
            registerForm.classList.remove('hidden');
            loginForm.classList.add('hidden');
            
            // Update URL without page reload
            history.pushState(null, null, '/register');
        });
        
        if (switchToLogin) {
            switchToLogin.addEventListener('click', () => {
                loginTab.classList.add('active');
                registerTab.classList.remove('active');
                loginForm.classList.remove('hidden');
                registerForm.classList.add('hidden');
                
                // Update URL without page reload
                history.pushState(null, null, '/login');
            });
        }
    }
    
    // Password strength indicator functionality
    const passwordInput = document.getElementById('registerPassword');
    const strengthIndicator = document.getElementById('passwordStrength');
    
    if (passwordInput && strengthIndicator) {
        passwordInput.addEventListener('input', updatePasswordStrength);
        
        function updatePasswordStrength() {
            const password = passwordInput.value;
            let strength = 0;
            let feedback = '';
            
            // Length check
            if (password.length >= 8) {
                strength += 1;
            }
            
            // Contains lowercase
            if (/[a-z]/.test(password)) {
                strength += 1;
            }
            
            // Contains uppercase
            if (/[A-Z]/.test(password)) {
                strength += 1;
            }
            
            // Contains number
            if (/[0-9]/.test(password)) {
                strength += 1;
            }
            
            // Contains special character
            if (/[^A-Za-z0-9]/.test(password)) {
                strength += 1;
            }
            
            // Update UI based on strength
            let strengthClass = '';
            switch(strength) {
                case 0:
                case 1:
                    feedback = 'Weak';
                    strengthClass = 'bg-danger';
                    break;
                case 2:
                case 3:
                    feedback = 'Medium';
                    strengthClass = 'bg-warning';
                    break;
                case 4:
                case 5:
                    feedback = 'Strong';
                    strengthClass = 'bg-primary';
                    break;
            }
            
            // Update the strength indicator
            strengthIndicator.textContent = feedback;
            strengthIndicator.className = 'text-xs font-medium px-2 py-1 rounded ' + strengthClass;
            
            const progressWidth = (strength / 5) * 100;
            document.getElementById('passwordStrengthBar').style.width = `${progressWidth}%`;
            document.getElementById('passwordStrengthBar').className = 'h-1 ' + strengthClass;
        }
    }
    
    // Form validation
    const loginFormElement = document.querySelector('#loginForm form');
    const registerFormElement = document.querySelector('#registerForm form');
    
    if (loginFormElement) {
        loginFormElement.addEventListener('submit', function(e) {
            const email = document.getElementById('loginEmail').value;
            const password = document.getElementById('loginPassword').value;
            let isValid = true;
            
            // Basic validation
            if (!email || !isValidEmail(email)) {
                isValid = false;
                highlightError('loginEmail', 'Please enter a valid email');
            } else {
                removeError('loginEmail');
            }
            
            if (!password) {
                isValid = false;
                highlightError('loginPassword', 'Please enter your password');
            } else {
                removeError('loginPassword');
            }
            
            // Only submit if valid
            if (!isValid) {
                e.preventDefault();
            }
        });
    }
    
    if (registerFormElement) {
        registerFormElement.addEventListener('submit', function(e) {
            let isValid = true;
            
            // Collect form values
            const firstName = document.getElementById('firstName').value;
            const lastName = document.getElementById('lastName').value;
            const username = document.getElementById('username').value;
            const email = document.getElementById('registerEmail').value;
            const password = document.getElementById('registerPassword').value;
            const confirmPassword = document.getElementById('confirmPassword').value;
            const terms = document.getElementById('terms').checked;
            
            // Basic validation
            if (!firstName) {
                isValid = false;
                highlightError('firstName', 'Please enter your first name');
            } else {
                removeError('firstName');
            }
            
            if (!lastName) {
                isValid = false;
                highlightError('lastName', 'Please enter your last name');
            } else {
                removeError('lastName');
            }
            
            if (!username) {
                isValid = false;
                highlightError('username', 'Please choose a username');
            } else {
                removeError('username');
            }
            
            if (!email || !isValidEmail(email)) {
                isValid = false;
                highlightError('registerEmail', 'Please enter a valid email');
            } else {
                removeError('registerEmail');
            }
            
            if (!password || password.length < 8) {
                isValid = false;
                highlightError('registerPassword', 'Password must be at least 8 characters');
            } else {
                removeError('registerPassword');
            }
            
            if (password !== confirmPassword) {
                isValid = false;
                highlightError('confirmPassword', 'Passwords do not match');
            } else {
                removeError('confirmPassword');
            }
            
            if (!terms) {
                isValid = false;
                highlightError('terms', 'You must agree to the Terms and Privacy Policy');
            } else {
                removeError('terms');
            }
            
            // Only submit if valid
            if (!isValid) {
                e.preventDefault();
            }
        });
    }
    
    // Helper functions
    function isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }
    
    function highlightError(inputId, message) {
        const input = document.getElementById(inputId);
        if (input) {
            input.classList.add('border-danger');
            
            // Check if error message already exists
            let errorElement = input.parentElement.nextElementSibling;
            if (!errorElement || !errorElement.classList.contains('text-red-500')) {
                errorElement = document.createElement('div');
                errorElement.classList.add('text-red-500', 'text-xs', 'mt-1');
                input.parentElement.parentElement.appendChild(errorElement);
            }
            
            errorElement.textContent = message;
        }
    }
    
    function removeError(inputId) {
        const input = document.getElementById(inputId);
        if (input) {
            input.classList.remove('border-danger');
            
            // Remove error message if it exists
            const errorElement = input.parentElement.nextElementSibling;
            if (errorElement && errorElement.classList.contains('text-red-500')) {
                errorElement.remove();
            }
        }
    }
    
    // Handle flash messages
    const flashMessages = document.querySelectorAll('.flash-message');
    if (flashMessages.length > 0) {
        flashMessages.forEach(message => {
            // Add dismiss button
            const dismissButton = document.createElement('button');
            dismissButton.innerHTML = '&times;';
            dismissButton.classList.add('ml-auto', 'text-lg', 'font-bold', 'focus:outline-none');
            message.appendChild(dismissButton);
            
            // Make flash message dismissible
            dismissButton.addEventListener('click', () => {
                message.remove();
            });
            
            // Auto-dismiss after 5 seconds
            setTimeout(() => {
                message.style.opacity = '0';
                setTimeout(() => message.remove(), 500);
            }, 5000);
        });
    }
=======
document.addEventListener('DOMContentLoaded', function() {
    // Tab switching functionality
    const loginTab = document.getElementById('loginTab');
    const registerTab = document.getElementById('registerTab');
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    const switchToLogin = document.getElementById('switchToLogin');
    
    if (loginTab && registerTab && loginForm && registerForm) {
        loginTab.addEventListener('click', () => {
            loginTab.classList.add('active');
            registerTab.classList.remove('active');
            loginForm.classList.remove('hidden');
            registerForm.classList.add('hidden');
            
            // Update URL without page reload
            history.pushState(null, null, '/login');
        });
        
        registerTab.addEventListener('click', () => {
            registerTab.classList.add('active');
            loginTab.classList.remove('active');
            registerForm.classList.remove('hidden');
            loginForm.classList.add('hidden');
            
            // Update URL without page reload
            history.pushState(null, null, '/register');
        });
        
        if (switchToLogin) {
            switchToLogin.addEventListener('click', () => {
                loginTab.classList.add('active');
                registerTab.classList.remove('active');
                loginForm.classList.remove('hidden');
                registerForm.classList.add('hidden');
                
                // Update URL without page reload
                history.pushState(null, null, '/login');
            });
        }
    }
    
    // Password strength indicator functionality
    const passwordInput = document.getElementById('registerPassword');
    const strengthIndicator = document.getElementById('passwordStrength');
    
    if (passwordInput && strengthIndicator) {
        passwordInput.addEventListener('input', updatePasswordStrength);
        
        function updatePasswordStrength() {
            const password = passwordInput.value;
            let strength = 0;
            let feedback = '';
            
            // Length check
            if (password.length >= 8) {
                strength += 1;
            }
            
            // Contains lowercase
            if (/[a-z]/.test(password)) {
                strength += 1;
            }
            
            // Contains uppercase
            if (/[A-Z]/.test(password)) {
                strength += 1;
            }
            
            // Contains number
            if (/[0-9]/.test(password)) {
                strength += 1;
            }
            
            // Contains special character
            if (/[^A-Za-z0-9]/.test(password)) {
                strength += 1;
            }
            
            // Update UI based on strength
            let strengthClass = '';
            switch(strength) {
                case 0:
                case 1:
                    feedback = 'Weak';
                    strengthClass = 'bg-danger';
                    break;
                case 2:
                case 3:
                    feedback = 'Medium';
                    strengthClass = 'bg-warning';
                    break;
                case 4:
                case 5:
                    feedback = 'Strong';
                    strengthClass = 'bg-primary';
                    break;
            }
            
            // Update the strength indicator
            strengthIndicator.textContent = feedback;
            strengthIndicator.className = 'text-xs font-medium px-2 py-1 rounded ' + strengthClass;
            
            const progressWidth = (strength / 5) * 100;
            document.getElementById('passwordStrengthBar').style.width = `${progressWidth}%`;
            document.getElementById('passwordStrengthBar').className = 'h-1 ' + strengthClass;
        }
    }
    
    // Form validation
    const loginFormElement = document.querySelector('#loginForm form');
    const registerFormElement = document.querySelector('#registerForm form');
    
    if (loginFormElement) {
        loginFormElement.addEventListener('submit', function(e) {
            const email = document.getElementById('loginEmail').value;
            const password = document.getElementById('loginPassword').value;
            let isValid = true;
            
            // Basic validation
            if (!email || !isValidEmail(email)) {
                isValid = false;
                highlightError('loginEmail', 'Please enter a valid email');
            } else {
                removeError('loginEmail');
            }
            
            if (!password) {
                isValid = false;
                highlightError('loginPassword', 'Please enter your password');
            } else {
                removeError('loginPassword');
            }
            
            // Only submit if valid
            if (!isValid) {
                e.preventDefault();
            }
        });
    }
    
    if (registerFormElement) {
        registerFormElement.addEventListener('submit', function(e) {
            let isValid = true;
            
            // Collect form values
            const firstName = document.getElementById('firstName').value;
            const lastName = document.getElementById('lastName').value;
            const username = document.getElementById('username').value;
            const email = document.getElementById('registerEmail').value;
            const password = document.getElementById('registerPassword').value;
            const confirmPassword = document.getElementById('confirmPassword').value;
            const terms = document.getElementById('terms').checked;
            
            // Basic validation
            if (!firstName) {
                isValid = false;
                highlightError('firstName', 'Please enter your first name');
            } else {
                removeError('firstName');
            }
            
            if (!lastName) {
                isValid = false;
                highlightError('lastName', 'Please enter your last name');
            } else {
                removeError('lastName');
            }
            
            if (!username) {
                isValid = false;
                highlightError('username', 'Please choose a username');
            } else {
                removeError('username');
            }
            
            if (!email || !isValidEmail(email)) {
                isValid = false;
                highlightError('registerEmail', 'Please enter a valid email');
            } else {
                removeError('registerEmail');
            }
            
            if (!password || password.length < 8) {
                isValid = false;
                highlightError('registerPassword', 'Password must be at least 8 characters');
            } else {
                removeError('registerPassword');
            }
            
            if (password !== confirmPassword) {
                isValid = false;
                highlightError('confirmPassword', 'Passwords do not match');
            } else {
                removeError('confirmPassword');
            }
            
            if (!terms) {
                isValid = false;
                highlightError('terms', 'You must agree to the Terms and Privacy Policy');
            } else {
                removeError('terms');
            }
            
            // Only submit if valid
            if (!isValid) {
                e.preventDefault();
            }
        });
    }
    
    // Helper functions
    function isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }
    
    function highlightError(inputId, message) {
        const input = document.getElementById(inputId);
        if (input) {
            input.classList.add('border-danger');
            
            // Check if error message already exists
            let errorElement = input.parentElement.nextElementSibling;
            if (!errorElement || !errorElement.classList.contains('text-red-500')) {
                errorElement = document.createElement('div');
                errorElement.classList.add('text-red-500', 'text-xs', 'mt-1');
                input.parentElement.parentElement.appendChild(errorElement);
            }
            
            errorElement.textContent = message;
        }
    }
    
    function removeError(inputId) {
        const input = document.getElementById(inputId);
        if (input) {
            input.classList.remove('border-danger');
            
            // Remove error message if it exists
            const errorElement = input.parentElement.nextElementSibling;
            if (errorElement && errorElement.classList.contains('text-red-500')) {
                errorElement.remove();
            }
        }
    }
    
    // Handle flash messages
    const flashMessages = document.querySelectorAll('.flash-message');
    if (flashMessages.length > 0) {
        flashMessages.forEach(message => {
            // Add dismiss button
            const dismissButton = document.createElement('button');
            dismissButton.innerHTML = '&times;';
            dismissButton.classList.add('ml-auto', 'text-lg', 'font-bold', 'focus:outline-none');
            message.appendChild(dismissButton);
            
            // Make flash message dismissible
            dismissButton.addEventListener('click', () => {
                message.remove();
            });
            
            // Auto-dismiss after 5 seconds
            setTimeout(() => {
                message.style.opacity = '0';
                setTimeout(() => message.remove(), 500);
            }, 5000);
        });
    }
>>>>>>> origin/Dynamic-Parsing
});
const API_BASE_URL = 'http://localhost:5000/api';

document.getElementById('signupForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const name = document.getElementById('name').value.trim();
    const email = document.getElementById('email').value.trim();
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value.trim();
    const role = document.getElementById('role').value;
    
    if (!name || !email || !username || !password || !role) {
        showMessage('signupMessage', 'Please fill in all fields', 'error');
        return;
    }
    
    // Basic email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        showMessage('signupMessage', 'Please enter a valid email address', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, email, username, password, role })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showMessage('signupMessage', `✓ Registration successful! Welcome email has been sent to ${email}. Redirecting to login...`, 'success');
            
            setTimeout(() => {
                window.location.href = 'login.html';
            }, 2000);
        } else {
            showMessage('signupMessage', data.error || 'Registration failed', 'error');
        }
    } catch (error) {
        showMessage('signupMessage', 'Network error: ' + error.message, 'error');
    }
});

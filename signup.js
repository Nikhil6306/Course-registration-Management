const API_BASE_URL = 'http://localhost:5000/api';

document.getElementById('signupForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value.trim();
    const role = document.getElementById('role').value;
    
    if (!username || !password || !role) {
        showMessage('signupMessage', 'Please fill in all fields', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password, role })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showMessage('signupMessage', 'Registration successful! Redirecting to login...', 'success');
            
            setTimeout(() => {
                window.location.href = 'login.html';
            }, 1500);
        } else {
            showMessage('signupMessage', data.error || 'Registration failed', 'error');
        }
    } catch (error) {
        showMessage('signupMessage', 'Network error: ' + error.message, 'error');
    }
});

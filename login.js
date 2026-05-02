const API_BASE_URL = 'http://localhost:5000/api';

const loginForm = document.getElementById('loginForm');
const loginBtn = document.getElementById('loginBtn');
const forgotPasswordContainer = document.getElementById('forgotPasswordContainer');

loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value.trim();
    
    if (!username || !password) {
        showMessage('loginMessage', 'Please enter both username and password', 'error');
        return;
    }

    // Set loading state
    loginBtn.classList.add('loading');
    loginBtn.disabled = true;
    forgotPasswordContainer.classList.remove('show');
    
    try {
        const response = await fetch(`${API_BASE_URL}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Save user data to localStorage
            localStorage.setItem('currentUser', JSON.stringify(data.user));
            
            showMessage('loginMessage', 'Login successful! Redirecting...', 'success');
            
            // Redirect based on role
            setTimeout(() => {
                const role = data.user.role.toLowerCase();
                let redirectPage = 'index.html';
                
                if (role === 'student') redirectPage = 'student-dashboard.html';
                else if (role === 'teacher') redirectPage = 'teacher-dashboard.html';
                else if (role === 'hod') redirectPage = 'hod-dashboard.html';
                else if (role === 'admin') redirectPage = 'index.html'; // Or admin dashboard if exists
                
                window.location.href = redirectPage;
            }, 1000);
        } else {
            showMessage('loginMessage', data.error || 'Invalid credentials', 'error');
            // Show forgot password link on failed attempt
            forgotPasswordContainer.classList.add('show');
        }
    } catch (error) {
        showMessage('loginMessage', 'Network error: ' + error.message, 'error');
    } finally {
        loginBtn.classList.remove('loading');
        loginBtn.disabled = false;
    }
});

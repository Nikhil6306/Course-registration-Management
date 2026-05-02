const API_BASE_URL = 'http://localhost:5000/api';

const loginForm = document.getElementById('loginForm');
const loginBtn = document.getElementById('loginBtn');
const forgotPasswordContainer = document.getElementById('forgotPasswordContainer');

let currentLoginAttempt = null;

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
                else if (role === 'admin') redirectPage = 'index.html';
                
                window.location.href = redirectPage;
            }, 1000);
        } else {
            // Check if wrong password requires verification
            if (data.requiresVerification) {
                showMessage('loginMessage', data.message, 'error');
                currentLoginAttempt = {
                    username: data.username,
                    email: data.email
                };
                
                // Show verification code container if available
                const verificationContainer = document.getElementById('verificationContainer');
                if (verificationContainer) {
                    verificationContainer.classList.add('show');
                    const codeInput = document.getElementById('verificationCode');
                    if (codeInput) codeInput.focus();
                }
            } else {
                showMessage('loginMessage', data.error || 'Invalid credentials', 'error');
            }
            
            // Show forgot password link
            forgotPasswordContainer.classList.add('show');
        }
    } catch (error) {
        showMessage('loginMessage', 'Network error: ' + error.message, 'error');
    } finally {
        loginBtn.classList.remove('loading');
        loginBtn.disabled = false;
    }
});

// Handle verification code submission if container exists
const verificationContainer = document.getElementById('verificationContainer');
if (verificationContainer) {
    const verifyBtn = document.getElementById('verifyCodeBtn');
    if (verifyBtn) {
        verifyBtn.addEventListener('click', verifyCode);
    }
    
    const codeInput = document.getElementById('verificationCode');
    if (codeInput) {
        codeInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') verifyCode();
        });
    }
}

async function verifyCode() {
    const code = document.getElementById('verificationCode').value.trim();
    
    if (!code) {
        showMessage('verificationMessage', 'Please enter the verification code', 'error');
        return;
    }
    
    if (!currentLoginAttempt) {
        showMessage('verificationMessage', 'Session expired. Please try logging in again.', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/verify-password-code`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                username: currentLoginAttempt.username,
                email: currentLoginAttempt.email,
                code: code
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showMessage('verificationMessage', `✓ Identity verified! Redirecting to password reset...`, 'success');
            
            setTimeout(() => {
                window.location.href = `forgot-password.html?username=${currentLoginAttempt.username}&email=${currentLoginAttempt.email}`;
            }, 1500);
        } else {
            showMessage('verificationMessage', data.error || 'Invalid verification code', 'error');
        }
    } catch (error) {
        showMessage('verificationMessage', 'Network error: ' + error.message, 'error');
    }
}

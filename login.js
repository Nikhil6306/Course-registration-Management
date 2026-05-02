const API_BASE_URL = 'http://localhost:5000/api';

const loginForm = document.getElementById('loginForm');
const loginBtn = document.getElementById('loginBtn');
const forgotPasswordContainer = document.getElementById('forgotPasswordContainer');
const otpContainer = document.getElementById('otpVerificationContainer');

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
    if (otpContainer) otpContainer.classList.remove('show');
    
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
            // Check if it's a wrong password error requiring OTP
            if (data.requiresOTP) {
                showMessage('loginMessage', data.message, 'error');
                currentLoginAttempt = { username };
                
                // Show OTP verification container
                if (otpContainer) {
                    otpContainer.classList.add('show');
                    document.getElementById('otpInput').focus();
                } else {
                    showMessage('loginMessage', 'OTP verification required but container not found', 'error');
                }
                
                // Also show forgot password link
                forgotPasswordContainer.classList.add('show');
            } else {
                showMessage('loginMessage', data.error || 'Invalid credentials', 'error');
                // Show forgot password link on failed attempt
                forgotPasswordContainer.classList.add('show');
            }
        }
    } catch (error) {
        showMessage('loginMessage', 'Network error: ' + error.message, 'error');
    } finally {
        loginBtn.classList.remove('loading');
        loginBtn.disabled = false;
    }
});

// Handle OTP verification
if (otpContainer) {
    const verifyOtpBtn = document.getElementById('verifyOtpBtn');
    if (verifyOtpBtn) {
        verifyOtpBtn.addEventListener('click', verifyLoginOTP);
    }
    
    // Allow Enter key to submit OTP
    const otpInput = document.getElementById('otpInput');
    if (otpInput) {
        otpInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') verifyLoginOTP();
        });
    }
}

async function verifyLoginOTP() {
    const otp = document.getElementById('otpInput').value.trim();
    
    if (!otp) {
        showMessage('otpMessage', 'Please enter the OTP', 'error');
        return;
    }
    
    if (!currentLoginAttempt || !currentLoginAttempt.username) {
        showMessage('otpMessage', 'Session expired. Please try logging in again.', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/verify-login-otp`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                username: currentLoginAttempt.username,
                otp: otp
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showMessage('otpMessage', 'OTP verified! You can now reset your password or try logging in again.', 'success');
            
            // Store verification status
            currentLoginAttempt.verified = true;
            currentLoginAttempt.email = data.email;
            
            // Show password reset option or redirect to forgot password
            setTimeout(() => {
                window.location.href = 'forgot-password.html?username=' + currentLoginAttempt.username;
            }, 1500);
        } else {
            showMessage('otpMessage', data.error || 'Invalid OTP', 'error');
        }
    } catch (error) {
        showMessage('otpMessage', 'Network error: ' + error.message, 'error');
    }
}

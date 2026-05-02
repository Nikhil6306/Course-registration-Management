const API_BASE_URL = 'http://localhost:5000/api';

let currentStep = 1;
let resetData = { username: '', email: '', name: '' };

// Hotkey Listener
document.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
        if (currentStep === 1) {
            requestCode();
        } else if (currentStep === 2) {
            resetPassword();
        }
    }
});

// Button Listeners
document.getElementById('sendCodeBtn').addEventListener('click', requestCode);
document.getElementById('resetPasswordBtn').addEventListener('click', resetPassword);

async function requestCode() {
    const username = document.getElementById('username').value.trim();
    const email = document.getElementById('email').value.trim();
    
    if (!username || !email) {
        showMessage('messageBox', 'Please enter both username and email', 'error');
        return;
    }

    // Basic email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        showMessage('messageBox', 'Please enter a valid email address', 'error');
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/forgot-password`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, email })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            resetData = { username, email, name: data.name };
            
            const emailStatus = data.emailSent ? 
                `✓ Verification code sent to ${email}` : 
                `⚠ Code generated. Check email and server logs.`;
            
            showMessage('messageBox', emailStatus, 'success');
            
            // Move to Step 2
            document.getElementById('step1').classList.remove('active');
            document.getElementById('step2').classList.add('active');
            currentStep = 2;
            document.getElementById('code').focus();
        } else {
            showMessage('messageBox', data.error || 'Failed to send verification code', 'error');
        }
    } catch (error) {
        showMessage('messageBox', 'Network error: ' + error.message, 'error');
    }
}

async function resetPassword() {
    const code = document.getElementById('code').value.trim();
    const newPassword = document.getElementById('newPassword').value.trim();
    
    if (!code || !newPassword) {
        showMessage('messageBox', 'Please enter the verification code and new password', 'error');
        return;
    }

    if (code.length !== 6) {
        showMessage('messageBox', 'Verification code must be 6 digits', 'error');
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/reset-password`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                username: resetData.username,
                email: resetData.email,
                code: code,
                newPassword: newPassword 
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showMessage('messageBox', `✓ Password reset successfully! A confirmation email has been sent to ${resetData.email}. Redirecting to login...`, 'success');
            
            setTimeout(() => {
                window.location.href = 'login.html';
            }, 2000);
        } else {
            showMessage('messageBox', data.error || 'Failed to reset password', 'error');
        }
    } catch (error) {
        showMessage('messageBox', 'Network error: ' + error.message, 'error');
    }
}


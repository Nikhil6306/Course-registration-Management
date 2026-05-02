const API_BASE_URL = 'http://localhost:5000/api';

let currentStep = 1;
let globalUsername = '';

// Hotkey Listener
document.addEventListener('keydown', (e) => {
    // If user presses Enter
    if (e.key === 'Enter') {
        if (currentStep === 1) {
            requestOTP();
        } else if (currentStep === 2) {
            resetPassword();
        }
    }
});

// Button Listeners
document.getElementById('sendOtpBtn').addEventListener('click', requestOTP);
document.getElementById('resetPasswordBtn').addEventListener('click', resetPassword);

async function requestOTP() {
    const username = document.getElementById('username').value.trim();
    if (!username) {
        showMessage('messageBox', 'Please enter your username', 'error');
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/forgot-password`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            globalUsername = username;
            // Show email address in message
            const emailDisplay = data.email ? `(${data.email})` : '';
            const message = data.emailSent ? 
                `✓ OTP sent successfully ${emailDisplay}` : 
                `⚠ OTP generated but email delivery pending. Check server logs.`;
            showMessage('messageBox', message, 'success');
            
            // Move to Step 2
            document.getElementById('step1').classList.remove('active');
            document.getElementById('step2').classList.add('active');
            currentStep = 2;
            document.getElementById('otp').focus();
        } else {
            showMessage('messageBox', data.error || 'Failed to generate OTP', 'error');
        }
    } catch (error) {
        showMessage('messageBox', 'Network error: ' + error.message, 'error');
    }
}

async function resetPassword() {
    const otp = document.getElementById('otp').value.trim();
    const newPassword = document.getElementById('newPassword').value.trim();
    
    if (!otp || !newPassword) {
        showMessage('messageBox', 'Please enter the OTP and a new password', 'error');
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/reset-password`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                username: globalUsername, 
                otp: otp, 
                newPassword: newPassword 
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showMessage('messageBox', 'Password reset successfully! Redirecting...', 'success');
            
            setTimeout(() => {
                window.location.href = 'login.html';
            }, 1500);
        } else {
            showMessage('messageBox', data.error || 'Failed to reset password', 'error');
        }
    } catch (error) {
        showMessage('messageBox', 'Network error: ' + error.message, 'error');
    }
}


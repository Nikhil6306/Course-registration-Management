# OTP Verification System Setup Guide

## Overview

The course registration system now includes a comprehensive OTP (One-Time Password) verification system for:

1. **Wrong Password Detection** - When a user enters an incorrect password during login
2. **Password Reset** - When a user forgets their password
3. **Account Security** - OTP is sent to registered email addresses

## System Features

### 1. Wrong Password OTP Verification

- When a user enters the wrong password, they receive an OTP via email
- OTP expires in 15 minutes
- User can verify their identity using the OTP
- After verification, user is redirected to password reset page

### 2. Password Reset OTP

- User requests password reset via forgot-password page
- OTP is sent to registered email address
- OTP is valid for 15 minutes
- Password can only be reset with valid OTP

### 3. Email Notifications

- Welcome email on account registration
- OTP email for security verification
- Password change confirmation email

## Setup Instructions

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs the required packages:

- `flask-mail` - For email sending
- `email-validator` - For email validation

### Step 2: Configure Email Settings

#### Option A: Using Gmail (Recommended)

1. Go to your Gmail account settings
2. Enable 2-Factor Authentication
3. Create an App Password:
   - Visit: https://support.google.com/accounts/answer/185833
   - Generate an App Password for "Mail"
   - Copy the 16-character password

4. Update `.env` file:

```
EMAIL_SENDER=your-email@gmail.com
EMAIL_PASSWORD=your-16-character-app-password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

#### Option B: Using Outlook/Hotmail

```
EMAIL_SENDER=your-email@outlook.com
EMAIL_PASSWORD=your-password
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
```

#### Option C: Using Yahoo Mail

```
EMAIL_SENDER=your-email@yahoo.com
EMAIL_PASSWORD=your-password
SMTP_SERVER=smtp.mail.yahoo.com
SMTP_PORT=587
```

### Step 3: Update User Records with Email

When creating users via signup or setup script, ensure email is included:

```python
user_data = {
    'username': 'john_doe',
    'password': 'password123',
    'email': 'john@example.com',  # IMPORTANT: Email is required
    'role': 'student'
}
```

### Step 4: Test the System

#### Test 1: Login with Wrong Password

1. Go to login page
2. Enter valid username but wrong password
3. Check if OTP is sent to email
4. Enter OTP to verify identity
5. Should be able to reset password

#### Test 2: Forgot Password

1. Go to forgot-password page
2. Enter username
3. Check if OTP is sent to email
4. Enter OTP and new password
5. Should be able to log in with new password

## API Endpoints

### 1. Login

```
POST /api/login
Body: { "username": "john", "password": "pass123" }

Response if wrong password:
{
    "error": "Invalid password",
    "requiresOTP": true,
    "message": "Wrong password. An OTP has been sent...",
    "username": "john"
}
```

### 2. Verify Login OTP

```
POST /api/verify-login-otp
Body: { "username": "john", "otp": "123456" }

Response:
{
    "message": "OTP verified successfully",
    "verified": true,
    "username": "john",
    "email": "john@example.com"
}
```

### 3. Request Password Reset OTP

```
POST /api/forgot-password
Body: { "username": "john" }

Response:
{
    "message": "OTP sent to john@example.com",
    "email": "john@example.com",
    "emailSent": true
}
```

### 4. Reset Password with OTP

```
POST /api/reset-password
Body: {
    "username": "john",
    "otp": "123456",
    "newPassword": "newpass456"
}

Response:
{
    "message": "Password reset successfully"
}
```

### 5. Register with Email

```
POST /api/register
Body: {
    "username": "john",
    "password": "pass123",
    "email": "john@example.com",
    "role": "student"
}

Response:
{
    "message": "Registration successful"
}
```

## Frontend Changes

### Login Page Enhancements

- New OTP verification section appears when wrong password is entered
- User can enter 6-digit OTP to verify identity
- Automatic redirect to password reset page after verification

### Forgot Password Page

- Unchanged UI but backend now sends emails
- OTP displayed in success message confirms email delivery

## Database Schema Changes

### Users Collection

New fields added for OTP management:

```javascript
{
    "username": String,
    "password": String,
    "email": String,        // NEW - Required for OTP
    "role": String,
    "wrong_password_otp": String,           // NEW - For login attempts
    "wrong_password_otp_timestamp": Date,   // NEW
    "wrong_password_attempts": Number,      // NEW
    "reset_otp": String,                    // NEW - For password reset
    "reset_otp_timestamp": Date,            // NEW
    "created_at": Date,                     // NEW
    "last_password_reset": Date,            // NEW
    "last_verification": Date               // NEW
}
```

## Fallback Mechanism

If email sending fails:

1. OTP is still printed to server console for testing
2. Users can manually check console logs during development
3. In production, ensure email credentials are correct

## Troubleshooting

### Issue: Emails not being sent

**Solutions:**

1. Check email credentials in `.env`
2. Verify SMTP_SERVER and SMTP_PORT
3. Check server console for error messages
4. For Gmail: Ensure App Password is used (not regular password)
5. Check if firewall is blocking SMTP port 587

### Issue: OTP not received

**Check:**

1. User has valid email in database
2. Check spam/junk folder
3. Check server console for error logs
4. Verify email configuration is correct

### Issue: "No OTP request found"

**This means:**

1. User hasn't triggered wrong password attempt
2. OTP has already been verified/used
3. Session has expired - user needs to try login again

## Security Notes

1. **OTP Validity**: 15 minutes
2. **Password Storage**: Passwords are stored (consider hashing in production)
3. **Email Privacy**: Emails not exposed in responses for security
4. **Rate Limiting**: Consider adding rate limiting for OTP requests (future enhancement)
5. **Account Lockout**: Consider implementing account lockout after N failed attempts (future enhancement)

## Demo Users

When setting up demo users, ensure email is included:

```python
demo_users = [
    {
        'username': 'admin',
        'password': 'password123',
        'email': 'admin@devsanskritiuni.edu.in',
        'role': 'admin'
    },
    {
        'username': 'student',
        'password': 'password123',
        'email': 'student@devsanskritiuni.edu.in',
        'role': 'student'
    },
    {
        'username': 'teacher',
        'password': 'password123',
        'email': 'teacher@devsanskritiuni.edu.in',
        'role': 'teacher'
    }
]
```

## Future Enhancements

1. Two-Factor Authentication (2FA)
2. SMS-based OTP (in addition to email)
3. Biometric authentication
4. Rate limiting and account lockout
5. OTP resend functionality with cooldown
6. Password strength requirements
7. Login history and suspicious activity alerts

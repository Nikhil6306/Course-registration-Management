# 🔐 OTP Verification System - Quick Start Guide

## What's New?

Your course registration system now has a complete OTP (One-Time Password) verification system that:

- ✅ Sends OTP to email when wrong password is entered during login
- ✅ Sends OTP to email when user requests password reset
- ✅ Verifies identity with OTP before allowing password changes
- ✅ Expires OTP after 15 minutes for security
- ✅ Sends confirmation emails on password changes

## Quick Setup (5 minutes)

### 1. Install Email Packages

```bash
pip install -r requirements.txt
```

### 2. Configure Email in .env File

**For Gmail:**

1. Go to https://support.google.com/accounts/answer/185833
2. Create an App Password for Mail
3. Update `.env`:

```
EMAIL_SENDER=your-email@gmail.com
EMAIL_PASSWORD=your-16-char-app-password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

**For Outlook:**

```
EMAIL_SENDER=your-email@outlook.com
EMAIL_PASSWORD=your-password
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
```

### 3. Setup Demo Users

```bash
python setup_users.py
```

## How It Works

### Scenario 1: Wrong Password During Login

```
User enters: admin / wrongpassword
↓
Server detects wrong password
↓
System generates 6-digit OTP
↓
OTP sent to admin@devsanskritiuni.edu.in
↓
User sees: "An OTP has been sent to your email"
↓
User enters OTP to verify identity
↓
Redirected to password reset page
```

### Scenario 2: Password Reset

```
User clicks: "Forgot Password"
↓
User enters: admin
↓
System generates 6-digit OTP
↓
OTP sent to admin@devsanskritiuni.edu.in
↓
User enters OTP + new password
↓
Password successfully reset
↓
Can login with new password
```

## Testing the System

### Test 1: Try Wrong Password

1. Open login page: `login.html`
2. Username: `admin`
3. Password: `wrong123`
4. Click Login
5. You should see: "OTP verification required"
6. **Check your email** for the OTP
7. Enter the 6-digit OTP
8. After verification, redirect to password reset

### Test 2: Reset Forgotten Password

1. Click "Forgot Password" link
2. Enter username: `admin`
3. Click "Send OTP"
4. **Check your email** for the OTP
5. Enter OTP + new password
6. Click "Reset Password"
7. Success! Login with new password

## Demo Accounts

```
Account 1:
  Username: admin
  Password: password123
  Email: admin@devsanskritiuni.edu.in

Account 2:
  Username: student
  Password: password123
  Email: student@devsanskritiuni.edu.in

Account 3:
  Username: teacher
  Password: password123
  Email: teacher@devsanskritiuni.edu.in

Account 4:
  Username: hod
  Password: password123
  Email: hod@devsanskritiuni.edu.in
```

## Key Features

| Feature           | Details                               |
| ----------------- | ------------------------------------- |
| **OTP Length**    | 6 digits                              |
| **OTP Validity**  | 15 minutes                            |
| **Email Support** | Gmail, Outlook, Yahoo, Custom SMTP    |
| **Fallback**      | OTP printed to console if email fails |
| **Security**      | Passwords hashed, OTP single-use      |

## Files Modified/Created

### Backend (Python)

- ✅ `app.py` - Added OTP generation, email sending, verification endpoints
- ✅ `requirements.txt` - Added flask-mail, email-validator
- ✅ `.env` - Added email configuration
- ✅ `setup_users.py` - Updated with email addresses

### Frontend (JavaScript/HTML)

- ✅ `login.js` - Added OTP verification after wrong password
- ✅ `login.html` - Added OTP input section
- ✅ `login-style.css` - Added OTP container styling
- ✅ `forgot-password.js` - Updated to show email in success message

### Documentation

- ✅ `OTP_SETUP_GUIDE.md` - Complete setup guide
- ✅ `OTP_QUICK_START.md` - This file

## API Endpoints Added

```
POST /api/login
  - Detects wrong password and sends OTP
  - Returns: requiresOTP flag if wrong password

POST /api/verify-login-otp
  - Verifies OTP after wrong password attempt
  - Returns: verified status

POST /api/forgot-password
  - Generates and sends OTP for password reset
  - Returns: email confirmation

POST /api/reset-password
  - Resets password with valid OTP
  - Sends confirmation email
```

## Troubleshooting

### ❌ Email not sent?

- Check `.env` file for correct credentials
- For Gmail, use App Password (not regular password)
- Check spam/junk folder
- Check console for error messages

### ❌ OTP not working?

- OTP must be entered within 15 minutes
- OTP can only be used once
- Check if correct username matches the OTP

### ❌ "Email not found for this user"?

- User account doesn't have an email
- Update user record with email address
- Run `setup_users.py` to create demo users with emails

## Next Steps

1. **Configure email** in `.env` with your credentials
2. **Setup demo users** with `python setup_users.py`
3. **Test wrong password** scenario first
4. **Test password reset** scenario
5. **Check email inbox** for OTP codes
6. **Deploy** when testing is complete

## Support

For detailed setup instructions, see: `OTP_SETUP_GUIDE.md`

For API documentation, see: `OTP_SETUP_GUIDE.md` → API Endpoints section

---

**Status**: ✅ OTP System Ready for Testing
**Version**: 1.0
**Last Updated**: 2024

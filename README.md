# 🎓 Advanced Course Registration Management System

An enterprise-grade, role-based course management platform built with **Flask**, **MongoDB**, and a premium modern frontend. Designed for educational institutions to manage academic lifecycles with security, auditability, and departmental oversight.

---

## 🌟 Key Features

### 🏛️ Multi-Role Ecosystem
- **Admin**: Full system control, user management (Create/Update/Delete), and global statistics.
- **Teacher**: Course creation, syllabus management, and real-time student enrollment tracking.
- **HOD (Head of Department)**: Departmental oversight, course lifecycle management, and academic reporting.
- **Student**: Department-specific course visibility, syllabus access, and profile management.

### 🛡️ Security & Auditing
- **Dual OTP Logging**: Audit-ready verification codes stored in a dedicated `otp-logs` database and persisted in user profiles.
- **Account Protection**: Mandatory 6-character Captcha verification for sensitive actions like account deletion.
- **Secure Credentials**: Admin-only visibility of user credentials for testing and support via hover tooltips.
- **Email Verification**: Integrated SMTP verification flow for profile security.

### 🎨 Premium UI/UX
- **Modern Design**: Built with a "Glassmorphism" aesthetic, curated HSL color palettes, and dark mode support.
- **Dynamic Interactions**: Micro-animations, hover effects, and responsive sidebar navigation.
- **Responsive Layout**: Fully compatible with Laptops, PCs, Tablets, and Mobile devices (Device-width optimized).
- **Default Branding**: Standardized professional avatars and consistent iconography using Phosphor Icons.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.x, Flask
- **Database**: MongoDB (Dual-connection architecture for Data & Security Logs)
- **Frontend**: Vanilla HTML5, CSS3 (Modern Flexbox/Grid), JavaScript (ES6+)
- **Security**: SMTP for Email OTP, 6-digit Captcha, Role-Based Access Control (RBAC)

---

## 🚀 Getting Started

### 1️⃣ Clone and Prepare
```bash
git clone https://github.com/Nikhil6306/Course-registration-Management.git
cd Course-registration-Management
```

### 2️⃣ Environment Setup
Create a `.env` file in the root directory:
```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-app-password
MONGO_URI=mongodb://localhost:27017/
```

### 3️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

### 4️⃣ Initialize Data (Optional)
```bash
python setup_users.py
python sample_data.py
```

### 5️⃣ Launch
```bash
python app.py
```

Open `http://localhost:5000` in your browser.

---

## 📂 Project Structure

```bash
├── app.py              # Flask Backend & API Routes
├── script.js           # Main Frontend Logic & UI Rendering
├── style.css           # Modern Design System & CSS Variables
├── index.html          # Admin Dashboard
├── teacher-dashboard.html
├── hod-dashboard.html
├── student-dashboard.html
├── login.html          # Professional Authentication Portal
├── notifications.js    # Custom Toast Notification System
└── images.png          # Default System Avatar
```

---

## 📌 Usage Highlights

### **Departmental Privacy**
Students are automatically restricted to courses within their own department. This is enforced at the API level by passing the `student_username` to the `/api/courses` endpoint.

### **Administrative Oversight**
Admins can hover over user cards in the "Manage Users" tab to reveal usernames and passwords, facilitating rapid testing and student support.

---

## 👨‍💻 Author
**Nikhil Shukla**  
*Building professional academic solutions.*

---

## 📄 License
This project is licensed under the MIT License.

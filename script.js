// ===== CONFIGURATION =====
const API_BASE_URL = 'http://localhost:5000/api';
let currentDeleteId = null;
let currentUser = null;

// ===== THEME TOGGLE =====
const themeToggleBtn = document.getElementById('themeToggleBtn');
const savedTheme = localStorage.getItem('theme') || 'light';

if (savedTheme === 'dark') {
    document.body.setAttribute('data-theme', 'dark');
    themeToggleBtn.textContent = '☀️';
}

themeToggleBtn.addEventListener('click', () => {
    if (document.body.getAttribute('data-theme') === 'dark') {
        document.body.removeAttribute('data-theme');
        localStorage.setItem('theme', 'light');
        themeToggleBtn.textContent = '🌙';
    } else {
        document.body.setAttribute('data-theme', 'dark');
        localStorage.setItem('theme', 'dark');
        themeToggleBtn.textContent = '☀️';
    }
});

// ===== AUTHENTICATION CHECK =====
function checkAuth() {
    const userStr = localStorage.getItem('currentUser');
    if (!userStr) {
        window.location.href = 'login.html';
        return;
    }
    
    currentUser = JSON.parse(userStr);
    
    // Setup Header UI
    document.getElementById('userNameDisplay').textContent = currentUser.username;
    document.getElementById('userRoleBadge').textContent = currentUser.role;
    
    if (currentUser.role === 'admin') {
        document.getElementById('userRoleBadge').style.backgroundColor = '#dc3545';
        document.getElementById('headerTitle').textContent = '⚙️ Admin Panel - Course Registration';
        const navUsers = document.getElementById('nav-users');
        if (navUsers) navUsers.style.display = 'block';
    } else if (currentUser.role === 'teacher') {
        document.getElementById('userRoleBadge').style.backgroundColor = '#28a745';
        document.getElementById('headerTitle').textContent = '👨‍🏫 Teacher Panel - Course Registration';
        
        // Show tabs for teachers
        document.getElementById('nav-create').style.display = 'block';
        document.getElementById('nav-update').style.display = 'block';
        
        // Default to View tab
        document.getElementById('nav-create').classList.remove('active');
        document.getElementById('create').classList.remove('active');
        document.getElementById('nav-view').classList.add('active');
        document.getElementById('view').classList.add('active');
    } else if (currentUser.role === 'student') {
        document.getElementById('userRoleBadge').style.backgroundColor = '#17a2b8';
        document.getElementById('headerTitle').textContent = '🎓 Student Portal - Course Registration';
        
        // Hide Admin/Teacher tabs
        const navCreate = document.getElementById('nav-create');
        const navUpdate = document.getElementById('nav-update');
        const navStats = document.getElementById('nav-stats');
        
        if (navCreate) navCreate.style.display = 'none';
        if (navUpdate) navUpdate.style.display = 'none';
        if (navStats) navStats.style.display = 'none';
        
        // Default to Syllabus tab for students
        const navSyllabus = document.getElementById('nav-syllabus');
        if (navSyllabus) {
            document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
            navSyllabus.classList.add('active');
            const syllabusTab = document.getElementById('syllabus');
            if (syllabusTab) syllabusTab.classList.add('active');
            loadSyllabus();
        }
    } else if (currentUser.role === 'hod') {
        document.getElementById('userRoleBadge').style.backgroundColor = '#6f42c1'; // Purple for HOD
        document.getElementById('headerTitle').textContent = '🏛️ HOD Panel - Department Oversight';
        
        // HOD has access to all tabs
        document.getElementById('nav-create').style.display = 'block';
        document.getElementById('nav-update').style.display = 'block';
        document.getElementById('nav-stats').style.display = 'block';
    }
}

// Logout
document.getElementById('logoutBtn').addEventListener('click', () => {
    localStorage.removeItem('currentUser');
    window.location.href = 'login.html';
});

// ===== TAB NAVIGATION =====
document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const tabName = btn.dataset.tab;
        
        // Update active button
        document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        
        // Update active tab
        document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
        document.getElementById(tabName).classList.add('active');
        
        // Load data when switching to view or stats tab
        if (tabName === 'view') {
            loadAllCourses();
        } else if (tabName === 'stats') {
            loadStats();
        } else if (tabName === 'users') {
            loadAllUsers();
        } else if (tabName === 'my-courses') {
            loadMyCourses();
        } else if (tabName === 'profile') {
            loadProfile();
        } else if (tabName === 'syllabus') {
            loadSyllabus();
        }
    });
});

// ===== CREATE OPERATION =====
document.getElementById('createForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const course = {
        courseCode: document.getElementById('courseCode').value.trim(),
        courseName: document.getElementById('courseName').value.trim(),
        department: document.getElementById('department').value.trim(),
        instructor: document.getElementById('instructor').value.trim(),
        credits: document.getElementById('credits').value,
        capacity: document.getElementById('capacity').value,
        description: document.getElementById('description').value.trim(),
        syllabus: document.getElementById('syllabus')?.value.trim() || '', // Added syllabus field
        schedule: document.getElementById('schedule').value.trim(),
        updatedBy: currentUser.name || currentUser.username
    };
    
    // Validation
    if (!course.courseCode || !course.courseName || !course.department || !course.instructor) {
        showMessage('createMessage', 'Please fill in all required fields', 'error');
        return;
    }
    
    try {
        console.log('Sending course data:', course);
        console.log('API URL:', `${API_BASE_URL}/courses`);
        
        const response = await fetch(`${API_BASE_URL}/courses`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(course)
        });
        
        console.log('Response status:', response.status);
        const data = await response.json();
        console.log('Response data:', data);
        
        if (response.ok) {
            showMessage('createMessage', data.message, 'success');
            document.getElementById('createForm').reset();
            // Refresh the view tab
            loadAllCourses();
        } else {
            showMessage('createMessage', data.error || 'Error creating course', 'error');
        }
    } catch (error) {
        console.error('Error details:', error);
        showMessage('createMessage', 'Network error: ' + error.message + ' | Make sure Flask server is running on http://localhost:5000', 'error');
    }
});

// ===== READ OPERATION - GET ALL COURSES =====
async function loadAllCourses() {
    try {
        const department = document.getElementById('departmentFilter').value;
        const url = department ? `${API_BASE_URL}/courses?department=${encodeURIComponent(department)}` : `${API_BASE_URL}/courses`;
        const response = await fetch(url);
        const data = await response.json();
        
        if (response.ok) {
            displayCourses(data.courses);
        } else {
            document.getElementById('coursesList').innerHTML = `<p class="error">${data.error || 'Error loading courses'}</p>`;
        }
    } catch (error) {
        document.getElementById('coursesList').innerHTML = `<p class="error">Network error: ${error.message}</p>`;
    }
}

function displayCourses(courses) {
    const coursesList = document.getElementById('coursesList');
    
    if (courses.length === 0) {
        coursesList.innerHTML = '<p style="grid-column: 1/-1; text-align: center; padding: 40px; color: #999;">No courses found. Create one to get started!</p>';
        return;
    }
    
    coursesList.innerHTML = courses.map(course => `
        <div class="course-card">
            <div class="course-code">${course.courseCode}</div>
            <div class="course-code" style="background-color: #17a2b8;">${course.department || 'General'}</div>
            <h3>${course.courseName}</h3>
            <p><strong>Instructor:</strong> ${course.instructor}</p>
            <p><strong>Description:</strong> ${course.description || 'No description'}</p>
            <p><strong>Schedule:</strong> ${course.schedule || 'Not scheduled'}</p>
            <p><strong>Updated By:</strong> <span style="color: #667eea; font-weight: bold;">${course.updatedBy || 'System Admin'}</span></p>
            
            <div class="course-meta">
                <div class="course-meta-item">
                    <strong>Credits</strong>
                    <span>${course.credits}</span>
                </div>
                <div class="course-meta-item">
                    <strong>Capacity</strong>
                    <span>${course.capacity}</span>
                </div>
                <div class="course-meta-item">
                    <strong>Enrolled</strong>
                    <span>${course.enrolledStudents || 0}</span>
                </div>
                <div class="course-meta-item">
                    <strong>Available</strong>
                    <span>${course.capacity - (course.enrolledStudents || 0)}</span>
                </div>
            </div>
            
            <div class="course-id"><strong>ID:</strong> ${course._id}</div>
            
            <div class="course-actions">
                ${(currentUser.role === 'admin' || currentUser.role === 'teacher' || currentUser.role === 'hod') ? `<button class="btn btn-info" onclick="copyToClipboard('${course._id}')">Copy ID</button>` : ''}
                ${(currentUser.role === 'admin') ? `<button class="btn btn-success" onclick="enrollStudent('${course._id}')">Enroll</button>` : ''}
                ${(currentUser.role === 'admin' || currentUser.role === 'teacher' || currentUser.role === 'hod') ? `<button class="btn btn-danger" onclick="confirmDelete('${course._id}')">Delete</button>` : ''}
            </div>
        </div>
    `).join('');
}

// ===== UPDATE OPERATION =====
document.getElementById('loadCourseBtn').addEventListener('click', async () => {
    const courseId = document.getElementById('updateCourseId').value.trim();
    
    if (!courseId) {
        showMessage('updateMessage', 'Please enter a course ID', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/courses/${courseId}`);
        const data = await response.json();
        
        if (response.ok) {
            const course = data.course;
            const fields = {
                'updateCourseName': course.courseName,
                'updateDepartment': course.department || '',
                'updateInstructor': course.instructor,
                'updateCredits': course.credits,
                'updateCapacity': course.capacity,
                'updateDescription': course.description,
                'updateSchedule': course.schedule,
                'updateSyllabus': course.syllabus || ''
            };
            
            for (const [id, value] of Object.entries(fields)) {
                const el = document.getElementById(id);
                if (el) el.value = value;
            }
            
            const updateFieldsDiv = document.getElementById('updateFields');
            if (updateFieldsDiv) updateFieldsDiv.style.display = 'block';
            showToast('Course loaded successfully', 'success');
        } else {
            showToast(data.error || 'Course not found', 'error');
            const updateFieldsDiv = document.getElementById('updateFields');
            if (updateFieldsDiv) updateFieldsDiv.style.display = 'none';
        }
    } catch (error) {
        showToast('Network error: ' + error.message, 'error');
    }
});

document.getElementById('updateForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const courseId = document.getElementById('updateCourseId').value.trim();
    const updateData = {};
    
    const fieldMapping = {
        'courseName': 'updateCourseName',
        'department': 'updateDepartment',
        'instructor': 'updateInstructor',
        'credits': 'updateCredits',
        'capacity': 'updateCapacity',
        'description': 'updateDescription',
        'schedule': 'updateSchedule',
        'syllabus': 'updateSyllabus'
    };
    
    for (const [apiKey, elementId] of Object.entries(fieldMapping)) {
        const el = document.getElementById(elementId);
        if (el) {
            const val = el.value.trim();
            if (val) {
                updateData[apiKey] = (apiKey === 'credits' || apiKey === 'capacity') ? parseInt(val) : val;
            }
        }
    }
    
    // Always track who is performing the update
    updateData.updatedBy = currentUser.name || currentUser.username;
    
    if (Object.keys(updateData).length === 0) {
        showMessage('updateMessage', 'Please enter at least one field to update', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/courses/${courseId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updateData)
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showToast(data.message, 'success');
            document.getElementById('updateForm').reset();
            document.getElementById('updateFields').style.display = 'none';
            loadAllCourses();
        } else {
            showToast(data.error || 'Error updating course', 'error');
        }
    } catch (error) {
        showToast('Network error: ' + error.message, 'error');
    }
});

// ===== DELETE OPERATION =====
function confirmDelete(courseId) {
    currentDeleteId = courseId;
    const modal = document.getElementById('deleteModal');
    modal.style.display = 'flex';
}

document.getElementById('confirmDeleteBtn').addEventListener('click', async () => {
    if (!currentDeleteId) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/courses/${currentDeleteId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showMessage('coursesList', data.message, 'success');
            loadAllCourses();
        } else {
            showMessage('coursesList', data.error || 'Error deleting course', 'error');
        }
    } catch (error) {
        showMessage('coursesList', 'Network error: ' + error.message, 'error');
    } finally {
        document.getElementById('deleteModal').style.display = 'none';
        currentDeleteId = null;
    }
});

document.getElementById('cancelDeleteBtn').addEventListener('click', () => {
    document.getElementById('deleteModal').style.display = 'none';
    currentDeleteId = null;
});

// ===== SEARCH OPERATION =====
document.getElementById('searchBtn').addEventListener('click', async () => {
    const courseCode = document.getElementById('searchCourseCode').value.trim();
    
    if (!courseCode) {
        showMessage('searchResult', 'Please enter a course code', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/courses/search/${courseCode}`);
        const data = await response.json();
        
        if (response.ok) {
            const course = data.course;
            showMessage('searchResult', 'Course found!', 'success');
            
            document.getElementById('searchCourseDetail').innerHTML = `
                <div class="course-card">
                    <div class="course-code">${course.courseCode}</div>
                    <div class="course-code" style="background-color: #17a2b8;">${course.department || 'General'}</div>
                    <h3>${course.courseName}</h3>
                    <p><strong>Instructor:</strong> ${course.instructor}</p>
                    <p><strong>Description:</strong> ${course.description || 'No description'}</p>
                    <p><strong>Schedule:</strong> ${course.schedule || 'Not scheduled'}</p>
                    
                    <div class="course-meta">
                        <div class="course-meta-item">
                            <strong>Credits</strong>
                            <span>${course.credits}</span>
                        </div>
                        <div class="course-meta-item">
                            <strong>Capacity</strong>
                            <span>${course.capacity}</span>
                        </div>
                        <div class="course-meta-item">
                            <strong>Enrolled</strong>
                            <span>${course.enrolledStudents || 0}</span>
                        </div>
                        <div class="course-meta-item">
                            <strong>Available</strong>
                            <span>${course.capacity - (course.enrolledStudents || 0)}</span>
                        </div>
                    </div>
                    
                    <div class="course-id"><strong>ID:</strong> ${course._id}</div>
                    
                    <div class="course-actions">
                        ${currentUser.role === 'admin' ? `<button class="btn btn-info" onclick="copyToClipboard('${course._id}')">Copy ID</button>` : ''}
                        ${(currentUser.role === 'student' || currentUser.role === 'admin') ? `<button class="btn btn-success" onclick="enrollStudent('${course._id}')">Enroll</button>` : ''}
                        ${currentUser.role === 'admin' ? `<button class="btn btn-danger" onclick="confirmDelete('${course._id}')">Delete</button>` : ''}
                    </div>
                </div>
            `;
        } else {
            showMessage('searchResult', data.error || 'Course not found', 'error');
            document.getElementById('searchCourseDetail').innerHTML = '';
        }
    } catch (error) {
        showMessage('searchResult', 'Network error: ' + error.message, 'error');
    }
});

// ===== STATISTICS =====
async function loadStats() {
    try {
        const response = await fetch(`${API_BASE_URL}/courses/stats`);
        const stats = await response.json();
        
        if (response.ok) {
            document.getElementById('statsContainer').innerHTML = `
                <div class="stat-card">
                    <h3>Total Courses</h3>
                    <div class="stat-value">${stats.totalCourses}</div>
                    <p>Courses in the system</p>
                </div>
                <div class="stat-card">
                    <h3>Total Capacity</h3>
                    <div class="stat-value">${stats.totalCapacity}</div>
                    <p>Combined student capacity</p>
                </div>
                <div class="stat-card">
                    <h3>Total Enrolled</h3>
                    <div class="stat-value">${stats.totalEnrolled}</div>
                    <p>Students enrolled across all courses</p>
                </div>
            `;
        } else {
            document.getElementById('statsContainer').innerHTML = '<p>Error loading statistics</p>';
        }
    } catch (error) {
        document.getElementById('statsContainer').innerHTML = `<p style="color: red;">Error: ${error.message}</p>`;
    }
}

// ===== UTILITY FUNCTIONS =====

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('Course ID copied to clipboard!', 'success');
    }).catch(err => {
        showToast('Failed to copy: ' + err, 'error');
    });
}

async function enrollStudent(courseId) {
    let studentUsername = '';
    
    if (currentUser.role === 'admin' || currentUser.role === 'teacher' || currentUser.role === 'hod') {
        studentUsername = prompt("Enter student username to enroll:");
        if (!studentUsername) return;
    } else {
        studentUsername = currentUser.username;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/courses/${courseId}/enroll`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: studentUsername })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showToast(data.message, 'success');
            loadAllCourses();
        } else {
            showToast(data.error || 'Error enrolling student', 'error');
        }
    } catch (error) {
        showToast('Network error: ' + error.message, 'error');
    }
}

// ===== PROFILE MANAGEMENT =====
async function loadProfile() {
    try {
        const response = await fetch(`${API_BASE_URL}/profile/${currentUser.username}`);
        const data = await response.json();
        
        if (response.ok) {
            const p = data.profile;
            document.getElementById('profileName').value = p.name || '';
            document.getElementById('profileEmail').value = p.email || '';
            document.getElementById('profilePhone').value = p.phone || '';
            
            const roleEl = document.getElementById('profileRole');
            if (roleEl) roleEl.value = p.role ? p.role.charAt(0).toUpperCase() + p.role.slice(1) : '';
            
            if (p.profile_image) {
                document.getElementById('profilePreview').src = p.profile_image;
                document.getElementById('headerProfileImg').src = p.profile_image;
            }
        }
    } catch (error) {
        console.error("Failed to load profile", error);
    }
}

// Profile image preview
document.getElementById('profileImage').addEventListener('change', function(e) {
    if (this.files && this.files[0]) {
        if (this.files[0].size > 5 * 1024 * 1024) {
            showMessage('profileMessage', 'Image must be smaller than 5MB', 'error');
            this.value = '';
            return;
        }
        const reader = new FileReader();
        reader.onload = function(e) {
            document.getElementById('profilePreview').src = e.target.result;
        }
        reader.readAsDataURL(this.files[0]);
    }
});

// Load Profile Data
async function loadProfile() {
    try {
        const response = await fetch(`${API_BASE_URL}/profile/${currentUser.username}`);
        const data = await response.json();
        
        if (response.ok) {
            const profile = data.profile;
            if (document.getElementById('profileName')) document.getElementById('profileName').value = profile.name || '';
            if (document.getElementById('profileEmail')) document.getElementById('profileEmail').value = profile.email || '';
            if (document.getElementById('profilePhone')) document.getElementById('profilePhone').value = profile.phone || '';
            if (document.getElementById('profileRole')) document.getElementById('profileRole').value = profile.role || '';
            
            if (profile.profile_image) {
                const profileImg = document.getElementById('profilePreview');
                const headerImg = document.getElementById('headerProfileImg');
                if (profileImg) profileImg.src = profile.profile_image;
                if (headerImg) headerImg.src = profile.profile_image;
            }
            
            // Update header display
            const userNameDisplay = document.getElementById('userNameDisplay');
            if (userNameDisplay) userNameDisplay.textContent = profile.name || profile.username;
        }
    } catch (error) {
        console.error('Error loading profile:', error);
    }
}

// Submit Profile
document.getElementById('profileForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = new FormData();
    formData.append('username', currentUser.username);
    formData.append('name', document.getElementById('profileName').value.trim());
    formData.append('email', document.getElementById('profileEmail').value.trim());
    formData.append('phone', document.getElementById('profilePhone').value.trim());
    
    const fileInput = document.getElementById('profileImage');
    if (fileInput.files[0]) {
        formData.append('profile_image', fileInput.files[0]);
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/profile`, {
            method: 'PUT',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showMessage('profileMessage', 'Profile updated successfully!', 'success');
            if (data.profile.profile_image) {
                document.getElementById('headerProfileImg').src = data.profile.profile_image;
            }
        } else {
            showMessage('profileMessage', data.error || 'Failed to update profile', 'error');
        }
    } catch (error) {
        showMessage('profileMessage', 'Network error: ' + error.message, 'error');
    }
});

// ===== EMAIL VERIFICATION =====
const verifyEmailBtn = document.getElementById('verifyEmailBtn');
if (verifyEmailBtn) {
    verifyEmailBtn.addEventListener('click', async () => {
        const email = document.getElementById('profileEmail').value.trim();
        
        if (!email) {
            showMessage('profileMessage', 'Please enter an email address', 'error');
            return;
        }
        
        if (!email.includes('@')) {
            showMessage('profileMessage', 'Please enter a valid email address', 'error');
            return;
        }
        
        try {
            verifyEmailBtn.disabled = true;
            verifyEmailBtn.textContent = 'Sending...';
            
            const response = await fetch(`${API_BASE_URL}/send-email-verification`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    username: currentUser.username,
                    email: email
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                showToast(data.message, 'success');
                const verificationGroup = document.getElementById('emailVerificationGroup');
                if (verificationGroup) verificationGroup.style.display = 'block';
                verifyEmailBtn.textContent = 'Sent ✅';
            } else {
                showToast(data.error || 'Failed to send verification email', 'error');
                verifyEmailBtn.disabled = false;
                verifyEmailBtn.textContent = 'Send Verification';
            }
        } catch (error) {
            showToast('Network error: ' + error.message, 'error');
            verifyEmailBtn.disabled = false;
            verifyEmailBtn.textContent = 'Send Verification';
        }
    });
}

const confirmEmailVerifyBtn = document.getElementById('confirmEmailVerifyBtn');
if (confirmEmailVerifyBtn) {
    confirmEmailVerifyBtn.addEventListener('click', async () => {
        const codeInput = document.getElementById('emailVerificationCode');
        const code = codeInput ? codeInput.value.trim() : '';
        
        if (!code || code.length !== 6) {
            showToast('Please enter the 6-digit code sent to your email', 'error');
            return;
        }
        
        try {
            confirmEmailVerifyBtn.disabled = true;
            confirmEmailVerifyBtn.textContent = 'Verifying...';
            
            const response = await fetch(`${API_BASE_URL}/verify-email-code`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    username: currentUser.username,
                    code: code
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                showToast(data.message, 'success');
                const verificationGroup = document.getElementById('emailVerificationGroup');
                if (verificationGroup) verificationGroup.style.display = 'none';
                
                if (verifyEmailBtn) {
                    verifyEmailBtn.textContent = 'Verified ✓';
                    verifyEmailBtn.style.backgroundColor = '#28a745';
                    verifyEmailBtn.disabled = true;
                }
            } else {
                showToast(data.error || 'Verification failed', 'error');
            }
        } catch (error) {
            showToast('Network error: ' + error.message, 'error');
        } finally {
            confirmEmailVerifyBtn.disabled = false;
            confirmEmailVerifyBtn.textContent = 'Verify Code';
        }
    });
}

// ===== REFRESH & FILTERS =====
document.getElementById('refreshBtn')?.addEventListener('click', loadAllCourses);
document.getElementById('departmentFilter')?.addEventListener('change', loadAllCourses);
document.getElementById('refreshUsersBtn')?.addEventListener('click', loadAllUsers);
document.getElementById('userSearchInput')?.addEventListener('input', filterUsers);
document.getElementById('roleFilter')?.addEventListener('change', filterUsers);

// ===== USER MANAGEMENT =====
let allUsers = [];

async function loadAllUsers() {
    try {
        const response = await fetch(`${API_BASE_URL}/users`);
        const data = await response.json();
        
        if (response.ok) {
            allUsers = data.users;
            displayUsers(allUsers);
        } else {
            showToast(data.error || 'Error loading users', 'error');
        }
    } catch (error) {
        showToast('Network error: ' + error.message, 'error');
    }
}

function displayUsers(usersToDisplay) {
    const usersList = document.getElementById('usersList');
    if (!usersList) return;

    if (usersToDisplay.length === 0) {
        usersList.innerHTML = '<p style="grid-column: 1/-1; text-align: center; padding: 40px; color: #999;">No users found.</p>';
        return;
    }

    usersList.innerHTML = usersToDisplay.map(user => `
        <div class="course-card" style="border-left: 5px solid ${getRoleColor(user.role)};">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <span class="course-code" style="background-color: ${getRoleColor(user.role)};">${user.role.toUpperCase()}</span>
                    <h3 style="margin: 10px 0 5px 0;">${user.name || user.username}</h3>
                    <p style="color: #666; font-size: 0.9em; margin-bottom: 10px;">@${user.username}</p>
                </div>
                <img src="${user.profile_image || 'https://via.placeholder.com/50'}" style="width: 50px; height: 50px; border-radius: 50%; object-fit: cover; border: 2px solid #eee;">
            </div>
            
            <div style="margin-bottom: 15px;">
                <p><strong>📧 Email:</strong> ${user.email}</p>
                <p><strong>📞 Phone:</strong> ${user.phone || 'Not provided'}</p>
                <p><strong>📅 Joined:</strong> ${user.created_at ? new Date(user.created_at).toLocaleDateString() : 'Unknown'}</p>
            </div>
            
            <div class="course-actions">
                <button class="btn btn-info" onclick="openEditUserModal('${user.username}')">Edit</button>
                <button class="btn btn-danger" onclick="confirmDeleteUser('${user.username}', '${user.name || user.username}')">Delete</button>
            </div>
        </div>
    `).join('');
}

function getRoleColor(role) {
    switch(role.toLowerCase()) {
        case 'admin': return '#dc3545';
        case 'teacher': return '#28a745';
        case 'hod': return '#6f42c1';
        case 'student': return '#17a2b8';
        default: return '#6c757d';
    }
}

function filterUsers() {
    const searchTerm = document.getElementById('userSearchInput').value.toLowerCase();
    const roleFilter = document.getElementById('roleFilter').value;

    const filtered = allUsers.filter(user => {
        const matchesSearch = (user.name && user.name.toLowerCase().includes(searchTerm)) || 
                             user.username.toLowerCase().includes(searchTerm) ||
                             user.email.toLowerCase().includes(searchTerm);
        const matchesRole = roleFilter === "" || user.role === roleFilter;
        return matchesSearch && matchesRole;
    });

    displayUsers(filtered);
}

// Add User UI Logic
document.getElementById('showAddUserBtn')?.addEventListener('click', () => {
    document.getElementById('addUserSection').style.display = 'block';
    document.getElementById('showAddUserBtn').style.display = 'none';
});

document.getElementById('cancelAddUserBtn')?.addEventListener('click', () => {
    document.getElementById('addUserSection').style.display = 'none';
    document.getElementById('showAddUserBtn').style.display = 'inline-block';
    document.getElementById('adminAddUserForm').reset();
});

document.getElementById('adminAddUserForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const userData = {
        username: document.getElementById('adminUsername').value.trim(),
        role: document.getElementById('adminRole').value,
        password: document.getElementById('adminPassword').value,
        email: document.getElementById('adminEmail').value.trim(),
        name: document.getElementById('adminFullName').value.trim()
    };

    try {
        const response = await fetch(`${API_BASE_URL}/users`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(userData)
        });
        const data = await response.json();

        if (response.ok) {
            showToast(data.message, 'success');
            document.getElementById('adminAddUserForm').reset();
            document.getElementById('addUserSection').style.display = 'none';
            document.getElementById('showAddUserBtn').style.display = 'inline-block';
            loadAllUsers();
        } else {
            showToast(data.error || 'Failed to create user', 'error');
        }
    } catch (error) {
        showToast('Network error: ' + error.message, 'error');
    }
});

// Edit User Logic
let currentEditUsername = null;

window.openEditUserModal = function(username) {
    const user = allUsers.find(u => u.username === username);
    if (!user) return;

    currentEditUsername = username;
    document.getElementById('editOldUsername').value = username;
    document.getElementById('editFullName').value = user.name || '';
    document.getElementById('editEmail').value = user.email || '';
    document.getElementById('editRole').value = user.role;
    document.getElementById('editPhone').value = user.phone || '';

    document.getElementById('editUserModal').style.display = 'flex';
}

document.getElementById('cancelEditUserBtn')?.addEventListener('click', () => {
    document.getElementById('editUserModal').style.display = 'none';
    currentEditUsername = null;
});

document.getElementById('adminEditUserForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!currentEditUsername) return;

    const updateData = {
        name: document.getElementById('editFullName').value.trim(),
        email: document.getElementById('editEmail').value.trim(),
        role: document.getElementById('editRole').value,
        phone: document.getElementById('editPhone').value.trim()
    };

    try {
        const response = await fetch(`${API_BASE_URL}/users/${currentEditUsername}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updateData)
        });
        const data = await response.json();

        if (response.ok) {
            showToast(data.message, 'success');
            document.getElementById('editUserModal').style.display = 'none';
            loadAllUsers();
        } else {
            showToast(data.error || 'Failed to update user', 'error');
        }
    } catch (error) {
        showToast('Network error: ' + error.message, 'error');
    }
});

// Delete User Logic
let userToDelete = null;

window.confirmDeleteUser = function(username, name) {
    userToDelete = username;
    document.getElementById('deleteUserNameDisplay').textContent = name || username;
    document.getElementById('userDeleteModal').style.display = 'flex';
}

document.getElementById('cancelUserDeleteBtn')?.addEventListener('click', () => {
    document.getElementById('userDeleteModal').style.display = 'none';
    userToDelete = null;
});

document.getElementById('confirmUserDeleteBtn')?.addEventListener('click', async () => {
    if (!userToDelete) return;

    try {
        const response = await fetch(`${API_BASE_URL}/users/${userToDelete}`, {
            method: 'DELETE'
        });
        const data = await response.json();

        if (response.ok) {
            showToast(data.message, 'success');
            loadAllUsers();
        } else {
            showToast(data.error || 'Failed to delete user', 'error');
        }
    } catch (error) {
        showToast('Network error: ' + error.message, 'error');
    } finally {
        document.getElementById('userDeleteModal').style.display = 'none';
        userToDelete = null;
    }
});

// ===== SYLLABUS LOGIC =====
async function loadSyllabus() {
    const list = document.getElementById('syllabusList');
    if (!list) return;

    try {
        const response = await fetch(`${API_BASE_URL}/courses`);
        const data = await response.json();
        
        if (response.ok) {
            displaySyllabus(data.courses);
        } else {
            showToast(data.error || 'Error loading syllabi', 'error');
        }
    } catch (error) {
        showToast('Network error: ' + error.message, 'error');
    }
}

function displaySyllabus(courses) {
    const list = document.getElementById('syllabusList');
    if (!list) return;

    if (courses.length === 0) {
        list.innerHTML = '<p style="grid-column: 1/-1; text-align: center; padding: 40px; color: #999;">No course syllabi available at this time.</p>';
        return;
    }

    list.innerHTML = courses.map(course => `
        <div class="course-card" style="border-top: 5px solid #667eea;">
            <div class="course-code">${course.courseCode}</div>
            <h3 style="margin: 10px 0;">${course.courseName}</h3>
            <div style="background: rgba(0,0,0,0.03); padding: 15px; border-radius: 8px; margin-top: 10px;">
                <h4 style="font-size: 0.9em; text-transform: uppercase; color: #666; margin-bottom: 8px;">📖 Syllabus (Sallibox)</h4>
                <div class="syllabus-content" style="font-size: 0.95em; line-height: 1.6; white-space: pre-wrap;">
                    ${course.syllabus || 'The syllabus for this course has not been uploaded yet. Please check back later or contact the instructor.'}
                </div>
            </div>
            <div style="margin-top: 15px; font-size: 0.85em; color: #777;">
                <strong>Instructor:</strong> ${course.instructor}<br>
                <strong>Schedule:</strong> ${course.schedule || 'TBA'}
            </div>
        </div>
    `).join('');
}

document.getElementById('refreshSyllabusBtn')?.addEventListener('click', loadSyllabus);

// ===== LOADING OVERLAY =====
function showLoader() {
    const loader = document.createElement('div');
    loader.id = 'pageLoader';
    loader.style = `
        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background: var(--bg-color); display: flex; align-items: center; justify-content: center;
        z-index: 9999; transition: opacity 0.5s ease;
    `;
    loader.innerHTML = '<div class="spinner" style="width: 50px; height: 50px; border: 5px solid #f3f3f3; border-top: 5px solid var(--primary-color); border-radius: 50%; animation: spin 1s linear infinite;"></div>';
    document.body.appendChild(loader);
}

function hideLoader() {
    const loader = document.getElementById('pageLoader');
    if (loader) {
        loader.style.opacity = '0';
        setTimeout(() => loader.remove(), 500);
    }
}

// Global initialization
window.addEventListener('DOMContentLoaded', () => {
    showLoader();
    checkAuth();
    loadProfile();
    
    // Initial data load based on active tab
    const activeTab = document.querySelector('.tab-content.active');
    if (activeTab) {
        const tabId = activeTab.id;
        if (tabId === 'view') loadAllCourses();
        else if (tabId === 'stats') loadStats();
        else if (tabId === 'users') loadAllUsers();
        else if (tabId === 'my-courses') loadMyCourses();
        else if (tabId === 'syllabus') loadSyllabus();
    }
    
    hideLoader();
});

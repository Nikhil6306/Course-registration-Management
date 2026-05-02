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
        document.getElementById('headerTitle').textContent = '🎓 Student Panel - Course Registration';
        
        // Hide Admin/Teacher tabs
        document.getElementById('nav-create').style.display = 'none';
        document.getElementById('nav-update').style.display = 'none';
        document.getElementById('nav-stats').style.display = 'none';
        
        // Default to View tab
        document.getElementById('nav-create').classList.remove('active');
        document.getElementById('create').classList.remove('active');
        document.getElementById('nav-view').classList.add('active');
        document.getElementById('view').classList.add('active');
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
        schedule: document.getElementById('schedule').value.trim()
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
                ${(currentUser.role === 'student' || currentUser.role === 'admin') ? `<button class="btn btn-success" onclick="enrollStudent('${course._id}')">Enroll</button>` : ''}
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
                'updateSchedule': course.schedule
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
        'schedule': 'updateSchedule'
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
    try {
        const response = await fetch(`${API_BASE_URL}/courses/${courseId}/enroll`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showMessage('coursesList', data.message, 'success');
            loadAllCourses();
        } else {
            showMessage('coursesList', data.error || 'Error enrolling student', 'error');
        }
    } catch (error) {
        showMessage('coursesList', 'Network error: ' + error.message, 'error');
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

// Refresh button
document.getElementById('refreshBtn').addEventListener('click', loadAllCourses);

// Department filter
document.getElementById('departmentFilter').addEventListener('change', loadAllCourses);

// Load courses on page load (if visible)
window.addEventListener('load', () => {
    checkAuth();
    loadProfile();
    if (document.getElementById('view').classList.contains('active')) {
        loadAllCourses();
    }
});

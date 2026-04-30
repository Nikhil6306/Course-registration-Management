// ===== CONFIGURATION =====
const API_BASE_URL = 'http://localhost:5000/api';
let currentDeleteId = null;

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
        instructor: document.getElementById('instructor').value.trim(),
        credits: document.getElementById('credits').value,
        capacity: document.getElementById('capacity').value,
        description: document.getElementById('description').value.trim(),
        schedule: document.getElementById('schedule').value.trim()
    };
    
    // Validation
    if (!course.courseCode || !course.courseName || !course.instructor) {
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
        const response = await fetch(`${API_BASE_URL}/courses`);
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
                <button class="btn btn-info" onclick="copyToClipboard('${course._id}')">Copy ID</button>
                <button class="btn btn-success" onclick="enrollStudent('${course._id}')">Enroll</button>
                <button class="btn btn-danger" onclick="confirmDelete('${course._id}')">Delete</button>
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
            document.getElementById('updateCourseName').value = course.courseName;
            document.getElementById('updateInstructor').value = course.instructor;
            document.getElementById('updateCredits').value = course.credits;
            document.getElementById('updateCapacity').value = course.capacity;
            document.getElementById('updateDescription').value = course.description;
            document.getElementById('updateSchedule').value = course.schedule;
            
            document.getElementById('updateFields').style.display = 'block';
            showMessage('updateMessage', 'Course loaded successfully', 'success');
        } else {
            showMessage('updateMessage', data.error || 'Course not found', 'error');
            document.getElementById('updateFields').style.display = 'none';
        }
    } catch (error) {
        showMessage('updateMessage', 'Network error: ' + error.message, 'error');
    }
});

document.getElementById('updateForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const courseId = document.getElementById('updateCourseId').value.trim();
    const updateData = {};
    
    const courseName = document.getElementById('updateCourseName').value.trim();
    const instructor = document.getElementById('updateInstructor').value.trim();
    const credits = document.getElementById('updateCredits').value;
    const capacity = document.getElementById('updateCapacity').value;
    const description = document.getElementById('updateDescription').value.trim();
    const schedule = document.getElementById('updateSchedule').value.trim();
    
    if (courseName) updateData.courseName = courseName;
    if (instructor) updateData.instructor = instructor;
    if (credits) updateData.credits = credits;
    if (capacity) updateData.capacity = capacity;
    if (description) updateData.description = description;
    if (schedule) updateData.schedule = schedule;
    
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
            showMessage('updateMessage', data.message, 'success');
            document.getElementById('updateForm').reset();
            document.getElementById('updateFields').style.display = 'none';
            loadAllCourses();
        } else {
            showMessage('updateMessage', data.error || 'Error updating course', 'error');
        }
    } catch (error) {
        showMessage('updateMessage', 'Network error: ' + error.message, 'error');
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
                        <button class="btn btn-info" onclick="copyToClipboard('${course._id}')">Copy ID</button>
                        <button class="btn btn-success" onclick="enrollStudent('${course._id}')">Enroll</button>
                        <button class="btn btn-danger" onclick="confirmDelete('${course._id}')">Delete</button>
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
function showMessage(elementId, message, type) {
    const msgElement = document.getElementById(elementId);
    msgElement.textContent = message;
    msgElement.className = `message show ${type}`;
    
    // Auto-hide message after 5 seconds
    setTimeout(() => {
        msgElement.classList.remove('show');
    }, 5000);
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        alert('Course ID copied to clipboard!');
    }).catch(err => {
        alert('Failed to copy: ' + err);
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

// Refresh button
document.getElementById('refreshBtn').addEventListener('click', loadAllCourses);

// Load courses on page load (if visible)
window.addEventListener('load', () => {
    if (document.getElementById('view').classList.contains('active')) {
        loadAllCourses();
    }
});

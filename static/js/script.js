// Web Scraping Scheduler JavaScript

// URL validation function
function isValidUrl(string) {
    try {
        new URL(string);
        return true;
    } catch (_) {
        return false;
    }
}

// Show alert function
function showAlert(message, type) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.innerHTML = message;
    
    // Try to find the best container to show the alert
    const formContainer = document.querySelector('.form-container');
    const analyticsContent = document.querySelector('.analytics-content');
    const container = formContainer || analyticsContent || document.body;
    
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);
        
        // Remove alert after 5 seconds
        setTimeout(() => {
            alertDiv.remove();
        }, 5000);
    }
}

document.addEventListener('DOMContentLoaded', function() {
    // Form validation - simplified to allow submission
    const form = document.querySelector('.scraping-form');
    if (form) {
        form.addEventListener('submit', function(e) {
            const urlInput = document.getElementById('url');
            const scheduleInput = document.getElementById('schedule');
            
            // Only prevent if completely empty
            if (!urlInput.value.trim() || !scheduleInput.value) {
                e.preventDefault();
                showAlert('Please fill in both URL and schedule', 'error');
                return;
            }
            
            // Show loading state
            const submitBtn = this.querySelector('.submit-btn');
            if (submitBtn) {
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Adding Task...';
                submitBtn.disabled = true;
            }
            
            console.log('Form submitting with:', {
                url: urlInput.value,
                schedule: scheduleInput.value
            });
        });
    }
    
    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    

    
    // Auto-format URL input
    const urlInput = document.getElementById('url');
    if (urlInput) {
        urlInput.addEventListener('blur', function() {
            let url = this.value.trim();
            if (url && !url.startsWith('http://') && !url.startsWith('https://')) {
                this.value = 'https://' + url;
            }
        });
    }
    
    // Add hover effects to feature cards
    const featureCards = document.querySelectorAll('.feature-card');
    featureCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px) scale(1.02)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
        });
    });
    
    // Add click handlers for feature cards
    document.querySelectorAll('.feature-card.clickable-card').forEach(card => {
        card.addEventListener('click', function() {
            const url = this.getAttribute('data-url');
            if (url) {
                window.location.href = url;
            }
        });
    });
    
    // Add click handlers for action buttons
    document.querySelectorAll('.action-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            if (this.classList.contains('edit-btn')) {
                // Handle edit button
                const taskId = this.getAttribute('data-task-id');
                const taskUrl = this.getAttribute('data-task-url');
                const taskSchedule = this.getAttribute('data-task-schedule');
                const taskStatus = this.getAttribute('data-task-status');
                
                openEditModal(taskId, taskUrl, taskSchedule, taskStatus);
            } else if (this.classList.contains('delete-btn')) {
                // Handle delete button
                const taskId = this.getAttribute('data-task-id');
                confirmDelete(taskId, e);
            }
        });
    });
    
    // Add responsive table functionality
    const table = document.querySelector('.tasks-table table');
    if (table) {
        // Add horizontal scroll for mobile
        const wrapper = document.createElement('div');
        wrapper.style.overflowX = 'auto';
        wrapper.style.maxWidth = '100%';
        table.parentNode.insertBefore(wrapper, table);
        wrapper.appendChild(table);
    }
});

// Utility function to format dates
function formatDate(dateString) {
    if (!dateString) return 'Never';
    const date = new Date(dateString);
    return date.toLocaleDateString();
}

// Utility function to truncate text
function truncateText(text, maxLength = 50) {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

// Toggle status function
function toggleStatus() {
    const toggleBtn = document.getElementById('statusToggle');
    const statusText = document.getElementById('statusText');
    const icon = toggleBtn.querySelector('i');
    
    // Check current status
    const isActive = toggleBtn.classList.contains('active');
    
    if (isActive) {
        // Switch to inactive
        toggleBtn.classList.remove('active');
        toggleBtn.classList.add('inactive');
        statusText.textContent = 'Inactive';
        icon.className = 'fas fa-pause-circle';
        
        showAlert('⏸️ AI Scraper is now INACTIVE - Tasks are on rest', 'success');
        localStorage.setItem('aiScraperStatus', 'inactive');
        console.log('AI Scraper Status: INACTIVE');
    } else {
        // Switch to active
        toggleBtn.classList.remove('inactive');
        toggleBtn.classList.add('active');
        statusText.textContent = 'Active';
        icon.className = 'fas fa-play-circle';
        
        showAlert('✅ AI Scraper is now ACTIVE - Tasks will run as per schedule', 'success');
        localStorage.setItem('aiScraperStatus', 'active');
        console.log('AI Scraper Status: ACTIVE');
    }
}

// Load saved status on page load
document.addEventListener('DOMContentLoaded', function() {
    const savedStatus = localStorage.getItem('aiScraperStatus') || 'active';
    const toggleBtn = document.getElementById('statusToggle');
    const statusText = document.getElementById('statusText');
    const icon = toggleBtn.querySelector('i');
    
    if (savedStatus === 'inactive') {
        toggleBtn.classList.add('inactive');
        statusText.textContent = 'Inactive';
        icon.className = 'fas fa-pause-circle';
    } else {
        toggleBtn.classList.add('active');
        statusText.textContent = 'Active';
        icon.className = 'fas fa-play-circle';
    }
});

// Modal functionality for tasks page
let currentTaskId = null;

function openEditModal(taskId, url, schedule, status) {
    console.log('Opening edit modal for task:', taskId, url, schedule, status);
    currentTaskId = taskId;
    
    // Set modal content
    document.getElementById('modalUrl').textContent = url;
    document.getElementById('editTaskId').value = taskId;
    document.getElementById('editSchedule').value = schedule;
    document.getElementById('editStatus').value = status;
    
    // Show modal
    document.getElementById('editModal').style.display = 'block';
}

function closeEditModal() {
    document.getElementById('editModal').style.display = 'none';
    currentTaskId = null;
}

function saveTaskChanges() {
    const taskId = document.getElementById('editTaskId').value;
    const schedule = document.getElementById('editSchedule').value;
    const status = document.getElementById('editStatus').value;
    
    console.log('Saving task changes:', { taskId, schedule, status });
    
    // Create form data
    const formData = new FormData();
    formData.append('schedule', schedule);
    formData.append('status', status);
    
    // Send update request
    fetch(`/edit_task/${taskId}`, {
        method: 'POST',
        body: formData
    })
    .then(response => {
        console.log('Response status:', response.status);
        return response.json();
    })
    .then(data => {
        console.log('Response data:', data);
        if (data.success) {
            showAlert('✅ Task updated successfully!', 'success');
            closeEditModal();
            // Reload the page to show updated data
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            showAlert(`❌ ${data.message}`, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('❌ Error updating task. Please try again.', 'error');
    });
}

function confirmDelete(taskId, event) {
    // Prevent default browser behavior
    if (event) {
        event.preventDefault();
        event.stopPropagation();
        event.stopImmediatePropagation();
    }
    
    currentTaskId = taskId;
    
    // Get the URL for the task to show in confirmation
    const taskRow = event ? event.target.closest('tr') : null;
    const urlCell = taskRow ? taskRow.querySelector('.url-link') : null;
    const url = urlCell ? urlCell.textContent.trim() : 'this task';
    
    document.getElementById('deleteUrl').textContent = url;
    document.getElementById('deleteModal').style.display = 'block';
    
    // Return false to prevent any default behavior
    return false;
}

function closeDeleteModal() {
    document.getElementById('deleteModal').style.display = 'none';
    currentTaskId = null;
}

function deleteTask() {
    if (!currentTaskId) return;
    
    console.log('Deleting task:', currentTaskId);
    
    // Send delete request
    fetch(`/delete_task/${currentTaskId}`, {
        method: 'POST'
    })
    .then(response => {
        console.log('Delete response status:', response.status);
        return response.json();
    })
    .then(data => {
        console.log('Delete response data:', data);
        if (data.success) {
            showAlert('✅ Task deleted successfully!', 'success');
            closeDeleteModal();
            // Reload the page to show updated data
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            showAlert(`❌ ${data.message}`, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('❌ Error deleting task. Please try again.', 'error');
    });
}

// Close modals when clicking outside
window.onclick = function(event) {
    const editModal = document.getElementById('editModal');
    const deleteModal = document.getElementById('deleteModal');
    
    if (event.target === editModal) {
        closeEditModal();
    }
    if (event.target === deleteModal) {
        closeDeleteModal();
    }
}

// Additional safety: prevent any default behavior on delete buttons
document.addEventListener('DOMContentLoaded', function() {
    const deleteButtons = document.querySelectorAll('.delete-btn');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            e.stopImmediatePropagation();
            return false;
        });
    });
}); 
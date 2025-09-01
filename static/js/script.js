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
            
            // Show loading state with enhanced messaging
            const submitBtn = this.querySelector('.submit-btn');
            if (submitBtn) {
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Fetching Sitemap...';
                submitBtn.disabled = true;
                
                // Show a loading message to the user
                showAlert('🔄 Fetching sitemap and setting up task...', 'info');
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
    
    // Add click handlers for government section
    document.querySelectorAll('.government-updates-section.clickable-card').forEach(card => {
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
                
                openEditModal(taskId, taskUrl, taskSchedule);
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

function openEditModal(taskId, url, schedule) {
    console.log('Opening edit modal for task:', taskId, url, schedule);
    currentTaskId = taskId;
    
    // Set modal content
    document.getElementById('modalUrl').textContent = url;
    document.getElementById('editTaskId').value = taskId;
    document.getElementById('editSchedule').value = schedule;
    
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
    
    console.log('Saving task changes:', { taskId, schedule });
    
    // Create form data
    const formData = new FormData();
    formData.append('schedule', schedule);
    
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
    const runAllModal = document.getElementById('runAllModal');
    
    if (event.target === editModal) {
        closeEditModal();
    }
    if (event.target === deleteModal) {
        closeDeleteModal();
    }
    if (event.target === runAllModal) {
        closeRunAllModal();
    }
}

// Run All Functions
function confirmRunAll() {
    document.getElementById('runAllModal').style.display = 'block';
}

function closeRunAllModal() {
    document.getElementById('runAllModal').style.display = 'none';
}

function runAllTasks() {
    // Show loading state for the Run All button
    const runAllBtn = document.querySelector('.run-all-btn');
    if (runAllBtn) {
        const originalText = runAllBtn.innerHTML;
        runAllBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Running Tasks...';
        runAllBtn.disabled = true;
        
        // Store original text to restore later
        runAllBtn.setAttribute('data-original-text', originalText);
    }
    
    // Show loading indicators for all active tasks
    const comparisonCells = document.querySelectorAll('td:nth-child(6)'); // Comparison Result column
    comparisonCells.forEach(cell => {
        const currentBadge = cell.querySelector('.comparison-badge');
        if (currentBadge && !currentBadge.classList.contains('error')) {
            currentBadge.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Fetching & Comparing...';
            currentBadge.className = 'comparison-badge loading';
        }
    });
    
    // Show a loading message to the user
    showAlert('🔄 Fetching sitemaps and comparing changes...', 'info');
    
    // Note: Old sitemaps will be automatically deleted after comparison to maintain clean storage

    // Send run all request
    fetch('/run_all_tasks', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => {
        console.log('Run all response status:', response.status);
        return response.json();
    })
    .then(data => {
        console.log('Run all response data:', data);
        if (data.success) {
            showAlert('✅ All active tasks started successfully!', 'success');
            closeRunAllModal();
            
            // Start polling for updates instead of immediate reload
            startPollingForUpdates();
        } else {
            showAlert('❌ Error running tasks: ' + (data.error || 'Unknown error'), 'error');
            // Reset loading indicators on error
            resetLoadingIndicators();
        }
    })
    .catch(error => {
        console.error('Error running all tasks:', error);
        showAlert('❌ Error running tasks. Please try again.', 'error');
        // Reset loading indicators on error
        resetLoadingIndicators();
    });
}

function resetLoadingIndicators() {
    const loadingCells = document.querySelectorAll('.comparison-badge.loading');
    loadingCells.forEach(cell => {
        cell.innerHTML = '<i class="fas fa-clock"></i> Not checked';
        cell.className = 'comparison-badge not-checked';
    });
    
    // Restore Run All button
    const runAllBtn = document.querySelector('.run-all-btn');
    if (runAllBtn) {
        const originalText = runAllBtn.getAttribute('data-original-text');
        if (originalText) {
            runAllBtn.innerHTML = originalText;
            runAllBtn.disabled = false;
        }
    }
}



function startPollingForUpdates() {
    let completedTasks = 0;
    const totalTasks = document.querySelectorAll('.comparison-badge.loading').length;
    let lastProgressUpdate = 0;
    
    const pollInterval = setInterval(() => {
        fetch('/api/tasks')
        .then(response => response.json())
        .then(data => {
            if (data.success && data.tasks) {
                const previousLoadingCount = document.querySelectorAll('.comparison-badge.loading').length;
                updateComparisonResults(data.tasks);
                const currentLoadingCount = document.querySelectorAll('.comparison-badge.loading').length;
                
                // Track progress
                if (currentLoadingCount < previousLoadingCount) {
                    completedTasks = totalTasks - currentLoadingCount;
                    const progressPercent = Math.round((completedTasks / totalTasks) * 100);
                    
                    // Show progress update every 2 completed tasks or when all done
                    if (completedTasks - lastProgressUpdate >= 2 || currentLoadingCount === 0) {
                        showAlert(`🔄 Progress: ${completedTasks}/${totalTasks} tasks completed (${progressPercent}%)`, 'info');
                        lastProgressUpdate = completedTasks;
                    }
                }
                
                // Check if all tasks are done (no more loading indicators)
                if (currentLoadingCount === 0) {
                    clearInterval(pollInterval);
                    showAlert('✅ All sitemap comparisons completed!', 'success');
                    
                    // Restore Run All button
                    const runAllBtn = document.querySelector('.run-all-btn');
                    if (runAllBtn) {
                        const originalText = runAllBtn.getAttribute('data-original-text');
                        if (originalText) {
                            runAllBtn.innerHTML = originalText;
                            runAllBtn.disabled = false;
                        }
                    }
                }
            }
        })
        .catch(error => {
            console.error('Error polling for updates:', error);
            clearInterval(pollInterval);
        });
    }, 2000); // Poll every 2 seconds for faster updates

    // Stop polling after 10 minutes to prevent infinite polling
    setTimeout(() => {
        clearInterval(pollInterval);
        showAlert('⚠️ Polling stopped after 10 minutes. Check task status manually.', 'warning');
    }, 600000);
}

function updateComparisonResults(tasks) {
    const rows = document.querySelectorAll('.tasks-table tbody tr');
    
    tasks.forEach((task, index) => {
        if (index < rows.length) {
            const comparisonCell = rows[index].querySelector('td:nth-child(6)');
            const badge = comparisonCell.querySelector('.comparison-badge');
            
            if (badge && badge.classList.contains('loading')) {
                const comparison_result = task[9] || "Not checked";
                
                // Update the badge based on the result
                if (comparison_result.includes("new URLs found") || comparison_result.includes("modified URLs found")) {
                    badge.innerHTML = `<i class="fas fa-plus-circle"></i> ${comparison_result}`;
                    badge.className = 'comparison-badge new-urls';
                } else if (comparison_result === "No update") {
                    badge.innerHTML = '<i class="fas fa-check-circle"></i> No update';
                    badge.className = 'comparison-badge no-update';
                } else if (comparison_result === "Error") {
                    badge.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Error';
                    badge.className = 'comparison-badge error';
                } else if (comparison_result !== "Not checked") {
                    // Still processing or other status
                    badge.innerHTML = `<i class="fas fa-clock"></i> ${comparison_result}`;
                    badge.className = 'comparison-badge not-checked';
                }
            }
        }
    });
}

// Delete All Functions
function confirmDeleteAll() {
    document.getElementById('deleteAllModal').style.display = 'block';
}

function closeDeleteAllModal() {
    document.getElementById('deleteAllModal').style.display = 'none';
}

function deleteAllTasks() {
    // Send delete all request
    fetch('/delete_all_tasks', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => {
        console.log('Delete all response status:', response.status);
        return response.json();
    })
    .then(data => {
        console.log('Delete all response data:', data);
        if (data.success) {
            showAlert('✅ All tasks deleted successfully!', 'success');
            closeDeleteAllModal();
            // Reload the page to reflect changes
            setTimeout(() => {
                window.location.reload();
            }, 1500);
        } else {
            showAlert('❌ Error deleting tasks: ' + (data.error || 'Unknown error'), 'error');
        }
    })
    .catch(error => {
        console.error('Error deleting all tasks:', error);
        showAlert('❌ Error deleting tasks. Please try again.', 'error');
    });
}

// Delete All Updates Functions
function confirmDeleteAllUpdates() {
    document.getElementById('deleteAllUpdatesModal').style.display = 'block';
}

function closeDeleteAllUpdatesModal() {
    document.getElementById('deleteAllUpdatesModal').style.display = 'none';
}

function deleteAllUpdates() {
    // Send delete all updates request
    fetch('/delete_all_updates', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => {
        console.log('Delete all updates response status:', response.status);
        return response.json();
    })
    .then(data => {
        console.log('Delete all updates response data:', data);
        if (data.success) {
            showAlert('✅ All updates deleted successfully!', 'success');
            closeDeleteAllUpdatesModal();
            // Reload the page to reflect changes
            setTimeout(() => {
                window.location.reload();
            }, 1500);
        } else {
            showAlert('❌ Error deleting updates: ' + (data.error || 'Unknown error'), 'error');
        }
    })
    .catch(error => {
        console.error('Error deleting all updates:', error);
        showAlert('❌ Error deleting updates. Please try again.', 'error');
    });
}

// Task form loading functionality
document.addEventListener('DOMContentLoaded', function() {
    // Handle task form submission with loading state
    const taskForm = document.querySelector('.task-form');
    if (taskForm) {
        taskForm.addEventListener('submit', function(e) {
            const submitBtn = this.querySelector('.submit-btn');
            if (submitBtn) {
                // Change button to loading state
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Fetching Sitemap...';
                submitBtn.disabled = true;
                submitBtn.classList.add('loading');
            }
        });
    }
    
    // Additional safety: prevent any default behavior on delete buttons
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
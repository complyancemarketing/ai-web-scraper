// Integrated Apps JavaScript - Display Only Interface

document.addEventListener('DOMContentLoaded', function() {
    // Initialize search functionality
    initializeSearch();
    // Add event listeners for integration items
    addIntegrationItemListeners();
    // Initialize sidebar navigation
    initializeSidebar();
});

function initializeSearch() {
    const searchInput = document.querySelector('.search-input');
    const integrationItems = document.querySelectorAll('.integration-item');

    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase().trim();

            integrationItems.forEach(item => {
                const appName = item.querySelector('h3').textContent.toLowerCase();
                const description = item.querySelector('p').textContent.toLowerCase();

                if (appName.includes(searchTerm) || description.includes(searchTerm)) {
                    item.style.display = 'flex';
                    item.style.animation = 'fadeInUp 0.3s ease';
                } else {
                    item.style.display = 'none';
                }
            });
        });
    }
}

function addIntegrationItemListeners() {
    const integrationItems = document.querySelectorAll('.integration-item');

    integrationItems.forEach(item => {
        item.addEventListener('click', function() {
            const appName = this.querySelector('h3').textContent;
            const appType = this.getAttribute('data-app');
            
            // Show app details modal or notification
            showAppDetails(appName, appType);
        });

        // Add hover effects
        item.addEventListener('mouseenter', function() {
            this.style.background = '#f8f9fa';
        });

        item.addEventListener('mouseleave', function() {
            this.style.background = 'transparent';
        });
    });
}

function showAppDetails(appName, appType) {
    // Create a modal or notification to show app details
    const details = getAppDetails(appName, appType);
    
    showAlert(`${appName} is connected and ready to use!`, 'success');
    
    // You can expand this to show more detailed information
    console.log(`App: ${appName}, Type: ${appType}, Status: Connected`);
}

function getAppDetails(appName, appType) {
    const appDetails = {
        'webhook': {
            description: 'Send data to external services via HTTP requests',
            features: ['Real-time data transmission', 'Custom endpoints', 'Secure authentication'],
            status: 'Connected'
        },
        'n8n': {
            description: 'Workflow automation and data processing',
            features: ['Visual workflow builder', 'Node-based automation', 'Multi-service integration'],
            status: 'Connected'
        },
        'google-drive': {
            description: 'Store and manage files in the cloud',
            features: ['File storage', 'Document management', 'Collaborative editing'],
            status: 'Connected'
        },
        'google-sheets': {
            description: 'Export data to spreadsheets for analysis',
            features: ['Data export', 'Real-time updates', 'Formula support'],
            status: 'Connected'
        },
        'airtable': {
            description: 'Organize data in flexible databases',
            features: ['Database management', 'Custom fields', 'API integration'],
            status: 'Connected'
        },
        'teams': {
            description: 'Send notifications and updates to teams',
            features: ['Team notifications', 'Channel integration', 'Message formatting'],
            status: 'Connected'
        }
    };

    return appDetails[appType] || { description: 'App details not available', status: 'Connected' };
}

function initializeSidebar() {
    // Sidebar hover effects
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('mouseenter', function() {
            if (!this.classList.contains('active')) {
                this.style.background = 'rgba(255, 255, 255, 0.1)';
                this.style.color = 'white';
            }
        });

        item.addEventListener('mouseleave', function() {
            if (!this.classList.contains('active')) {
                this.style.background = 'transparent';
                this.style.color = '#8a8a8a';
            }
        });
    });

    // Logout button functionality
    const logoutBtn = document.querySelector('.logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function() {
            showAlert('Logout functionality would be implemented here', 'info');
        });
    }
}

function showAlert(message, type = 'info') {
    // Remove any existing alerts
    const existingAlerts = document.querySelectorAll('.alert');
    existingAlerts.forEach(alert => alert.remove());

    // Create alert element
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 12px 20px;
        border-radius: 6px;
        color: white;
        font-size: 14px;
        font-weight: 500;
        z-index: 1000;
        animation: slideIn 0.3s ease;
        max-width: 300px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    `;

    // Set background color based on type
    switch(type) {
        case 'success':
            alert.style.background = '#28a745';
            break;
        case 'error':
            alert.style.background = '#dc3545';
            break;
        case 'warning':
            alert.style.background = '#ffc107';
            alert.style.color = '#333';
            break;
        default:
            alert.style.background = '#667eea';
    }

    alert.textContent = message;
    document.body.appendChild(alert);

    // Auto remove after 3 seconds
    setTimeout(() => {
        alert.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => {
            if (alert.parentNode) {
                alert.remove();
            }
        }, 300);
    }, 3000);
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }

    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    .integration-item {
        transition: all 0.3s ease;
    }

    .search-input:focus {
        transform: scale(1.02);
    }
`;
document.head.appendChild(style); 
// Settings Modal JavaScript

// Global variables
let currentTab = 'general';

// Model settings
let availableModels = [];
let currentModel = '';

// Clean up any UI artifacts by removing any elements with text exactly "API Key" that aren't labels
function cleanupApiKeyArtifacts() {
    const allElements = document.querySelectorAll('#tools-tab *');
    allElements.forEach(element => {
        if (element.textContent.trim() === "API Key" && element.tagName !== 'LABEL') {
            console.log("Found unexpected API Key element:", element);
            element.style.display = 'none';
        }
    });
}

// Initialize the settings modal
document.addEventListener('DOMContentLoaded', function() {
    // Add event listeners for tabs
    document.querySelectorAll('.modal-tab-btn').forEach(button => {
        button.addEventListener('click', function() {
            switchTab(this.getAttribute('data-tab'));
        });
    });

    // Add event listeners for tool toggles
    document.querySelectorAll('.tool-toggle').forEach(toggle => {
        toggle.addEventListener('change', function() {
            const toolItem = this.closest('.tool-item');
            const toolBody = toolItem.querySelector('.tool-body');
            
            if (toolBody) {
                toolBody.style.display = this.checked ? 'block' : 'none';
            }
        });

        // Initialize tool bodies based on toggle state
        const toolItem = toggle.closest('.tool-item');
        const toolBody = toolItem.querySelector('.tool-body');
        if (toolBody) {
            toolBody.style.display = toggle.checked ? 'block' : 'none';
        }
    });

    // Add click handlers for tool headers
    document.querySelectorAll('.tool-header').forEach(header => {
        header.addEventListener('click', function(e) {
            // Only toggle if clicking on the header itself (not the switch)
            if (!e.target.closest('.switch') && e.target.type !== 'checkbox') {
                const toggle = this.querySelector('input[type="checkbox"]');
                if (toggle) {
                    toggle.checked = !toggle.checked;
                    toggle.dispatchEvent(new Event('change'));
                }
            }
        });
    });

    // Handle wheel events for better scrolling
    document.querySelectorAll('.modal-tab-content').forEach(content => {
        content.addEventListener('wheel', function(e) {
            // Make sure this tab is active
            if (!this.classList.contains('active')) return;
            
            // Determine if we're at the edge of scrolling
            const atTop = this.scrollTop === 0;
            const atBottom = this.scrollTop + this.offsetHeight >= this.scrollHeight - 1;
            
            // Only prevent default when we're not at the edge in the scroll direction
            if (!(atTop && e.deltaY < 0) && !(atBottom && e.deltaY > 0)) {
                e.stopPropagation();
            }
        });
    });
    
    // Attach event handler to refresh button
    const refreshButton = document.getElementById('refresh-tool-status');
    if (refreshButton) {
        refreshButton.addEventListener('click', loadToolStatus);
    }
    
    // Attach event handler to clear cache button
    const clearCacheButton = document.getElementById('clear-tool-caches');
    if (clearCacheButton) {
        clearCacheButton.addEventListener('click', clearToolCaches);
    }
    
    // Attach direct event listener to settings button
    const settingsBtn = document.getElementById('settings-btn');
    if (settingsBtn) {
        settingsBtn.addEventListener('click', function() {
            console.log('Settings button clicked from main DOM listener');
            openSettingsModal();
        });
    }
});

// Open settings modal function - made more robust to ensure it works
window.openSettingsModal = function() {
    console.log('openSettingsModal called');
    const modal = document.getElementById('settings-modal');
    const backdrop = document.getElementById('settings-backdrop');
    
    if (modal && backdrop) {
        modal.classList.add('show');
        backdrop.classList.add('show');
        document.body.classList.add('modal-open');
        
        // Load stored settings
        loadSettings();
        
        // Load tool status information
        loadToolStatus();
        
        // Load model options
        loadModelOptions();
        
        // Set default tab
        switchTab('general');
        
        // Clean up any UI artifacts
        cleanupApiKeyArtifacts();
    } else {
        console.error('Modal or backdrop elements not found:', { modal, backdrop });
    }
}

// Add CSS to make modal visible when .show class is applied
document.addEventListener('DOMContentLoaded', function() {
    const styleEl = document.createElement('style');
    styleEl.textContent = `
        .modal.show, .modal-backdrop.show {
            display: block !important;
        }
        .modal.show {
            display: flex !important;
        }
    `;
    document.head.appendChild(styleEl);
});

// Close settings modal
window.closeSettingsModal = function() {
    const modal = document.getElementById('settings-modal');
    const backdrop = document.getElementById('settings-backdrop');
    
    if (modal && backdrop) {
        modal.classList.remove('show');
        backdrop.classList.remove('show');
        document.body.classList.remove('modal-open');
    }
}

// Save settings from the modal
window.saveSettingsModal = async function() {
    // Handle model selection
    await saveModelSelection();
    
    const username = document.getElementById('settings-username').value || 'User';
    const avatar = document.getElementById('settings-avatar').value || 'U';
    const systemPrompt = document.getElementById('settings-system-prompt').value || 'You are a helpful AI assistant.';
    
    // Get extract answer only setting
    const extractAnswerOnlyCheckbox = document.getElementById('extract-answer-only');
    const extractAnswerOnly = extractAnswerOnlyCheckbox ? extractAnswerOnlyCheckbox.checked : false;
    
    // Store in localStorage
    localStorage.setItem('ds_username', username);
    localStorage.setItem('ds_avatar', avatar);
    localStorage.setItem('ds_system_prompt', systemPrompt);
    localStorage.setItem('ds_extract_answer_only', extractAnswerOnly);
    
    // Save extract_answer_only setting to config
    try {
        await fetch('/api/set-config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                key: 'extract_answer_only',
                value: extractAnswerOnly
            })
        });
    } catch (error) {
        console.error('Error saving extract_answer_only setting:', error);
    }
    
    // Also save API keys to server
    await saveApiKeys();
    
    // Close modal
    closeSettingsModal();
    
    // Optional: Show a toast/notification
    showToast('Settings saved successfully');
    
    // Update UI with new settings
    updateUIWithSettings();
}

// Update UI with new settings
function updateUIWithSettings() {
    // Update user avatars
    document.querySelectorAll('.user .avatar-letter').forEach(el => {
        el.textContent = localStorage.getItem('ds_avatar') || 'U';
    });
    
    // Update hidden form fields if they exist
    const usernameHidden = document.getElementById('user_name_hidden');
    const avatarHidden = document.getElementById('user_avatar_hidden');
    const promptHidden = document.getElementById('system_prompt_hidden');
    
    if (usernameHidden) usernameHidden.value = localStorage.getItem('ds_username') || 'User';
    if (avatarHidden) avatarHidden.value = localStorage.getItem('ds_avatar') || 'U';
    if (promptHidden) promptHidden.value = localStorage.getItem('ds_system_prompt') || 'You are a helpful AI assistant.';
}

// Load stored settings
function loadSettings() {
    // Get stored values with defaults
    const username = localStorage.getItem('ds_username') || '';
    const avatar = localStorage.getItem('ds_avatar') || '';
    const systemPrompt = localStorage.getItem('ds_system_prompt') || 'You are a helpful AI assistant.';
    const extractAnswerOnly = localStorage.getItem('ds_extract_answer_only') === 'true';
    
    // Update form fields
    document.getElementById('settings-username').value = username;
    document.getElementById('settings-avatar').value = avatar;
    document.getElementById('settings-system-prompt').value = systemPrompt;
    
    // Update extract answer only checkbox if it exists
    const extractAnswerOnlyCheckbox = document.getElementById('extract-answer-only');
    if (extractAnswerOnlyCheckbox) {
        extractAnswerOnlyCheckbox.checked = extractAnswerOnly;
    }
    
    // Load API key status
    fetch('/api/key-status')
        .then(response => response.json())
        .then(data => {
            // Store API key status globally
            window.apiKeyStatus = data;
            
            // Update web search
            if (data.SEARCH_API_KEY) {
                document.getElementById('websearch-api-key').placeholder = '••••••••••••••••••••••••••';
                document.getElementById('tool-websearch-toggle').checked = true;
            }
            
            // Update weather
            if (data.OPENWEATHERMAP_API_KEY) {
                document.getElementById('weather-api-key').placeholder = '••••••••••••••••••••••••••';
                document.getElementById('tool-weather-toggle').checked = true;
            }
            
            // Update email
            if (data.EMAIL_USERNAME) {
                document.getElementById('email-username').value = data.EMAIL_USERNAME;
                document.getElementById('email-smtp-server').value = data.EMAIL_SMTP_SERVER;
                document.getElementById('email-password').placeholder = '••••••••••••••••••••••••••';
                document.getElementById('tool-email-toggle').checked = data.EMAIL_PASSWORD;
            }
        })
        .catch(error => console.error('Error loading API key status:', error));
        
    // Load config settings
    fetch('/api/config')
        .then(response => response.json())
        .then(data => {
            if (data.success && data.config) {
                const config = data.config;
                
                // Update extract answer only checkbox if it exists
                const extractAnswerOnlyCheckbox = document.getElementById('extract-answer-only');
                if (extractAnswerOnlyCheckbox && config.hasOwnProperty('extract_answer_only')) {
                    extractAnswerOnlyCheckbox.checked = config.extract_answer_only;
                    // Also update localStorage to keep things in sync
                    localStorage.setItem('ds_extract_answer_only', config.extract_answer_only);
                }
            }
        })
        .catch(error => console.error('Error loading config settings:', error));
}

// Save API keys
async function saveApiKeys() {
    // Gather input values
    const apiKeys = {};
    
    // Web search API key
    const websearchKey = document.getElementById('websearch-api-key').value;
    if (websearchKey) {
        apiKeys.SEARCH_API_KEY = websearchKey;
    }
    
    // Weather API key
    const weatherKey = document.getElementById('weather-api-key').value;
    if (weatherKey) {
        apiKeys.OPENWEATHERMAP_API_KEY = weatherKey;
    }
    
    // Email settings
    const emailSmtp = document.getElementById('email-smtp-server').value;
    const emailUsername = document.getElementById('email-username').value;
    const emailPassword = document.getElementById('email-password').value;
    
    if (emailSmtp) {
        apiKeys.EMAIL_SMTP_SERVER = emailSmtp;
    }
    if (emailUsername) {
        apiKeys.EMAIL_USERNAME = emailUsername;
    }
    if (emailPassword) {
        apiKeys.EMAIL_PASSWORD = emailPassword;
    }
    
    // Send to server
    if (Object.keys(apiKeys).length > 0) {
        try {
            const response = await fetch('/save_api_keys', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(apiKeys)
            });
            
            const data = await response.json();
            
            if (data.success) {
                console.log('API keys saved successfully');
                // Refresh tool status after saving keys
                setTimeout(loadToolStatus, 500);
                return true;
            } else {
                console.error('Failed to save API keys:', data.error);
                return false;
            }
        } catch (error) {
            console.error('Error saving API keys:', error);
            return false;
        }
    }
}

// Show a toast notification
function showToast(message, type = 'success') {
    const toastContainer = document.getElementById('toast-container');
    if (!toastContainer) return;
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    
    toastContainer.appendChild(toast);
    
    // Animate in
    setTimeout(() => toast.classList.add('show'), 10);
    
    // Remove after timeout
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Toast convenience wrappers for consistent usage across app
function showSuccessToast(message){
    return showToast(message, 'success');
}

function showErrorToast(message){
    return showToast(message, 'error');
}

function showWarnToast(message){
    return showToast(message, 'warn');
}

// Function to load tool status information
function loadToolStatus() {
    const statusContainer = document.getElementById('tool-status-container');
    const statusSummary = document.getElementById('active-tools-count');
    
    if (!statusContainer || !statusSummary) return;
    
    // Show loading state
    statusContainer.innerHTML = `
        <div class="tool-status-loading">
            <div class="tool-status-spinner"></div>
            <span>Loading tool information...</span>
        </div>
    `;
    statusSummary.textContent = 'Checking tools status...';
    
    // Fetch tool status from API
    fetch('/api/tool-status')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update summary with styled pills
                const { ready, error, not_configured } = data.summary;
                statusSummary.innerHTML = `
                    <span>
                        <span class="status-pill ready">${ready} ready</span>
                        <span class="status-pill error">${error} error</span>
                        <span class="status-pill not-configured">${not_configured} not configured</span>
                    </span>
                `;
                
                // Add cache stats summary
                const cacheInfo = document.createElement('div');
                cacheInfo.className = 'cache-summary';
                
                const hitRatioClass = data.cache_stats.hit_ratio > 0.8 ? 'hit-ratio-high' : 
                                      data.cache_stats.hit_ratio > 0.5 ? 'hit-ratio-medium' : 
                                      'hit-ratio-low';
                
                cacheInfo.innerHTML = `
                    <span>Total cache entries: <b>${data.cache_stats.total_entries}</b></span>
                    <span>Cache hit ratio: <b class="${hitRatioClass}">${(data.cache_stats.hit_ratio * 100).toFixed(1)}%</b></span>
                `;
                
                // Clear button for specific tools
                const clearAllBtn = document.createElement('button');
                clearAllBtn.className = 'secondary-button clear-all-caches-btn';
                clearAllBtn.innerHTML = `
                    <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"></path><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path></svg>
                    Clear All Caches
                `;
                clearAllBtn.addEventListener('click', () => clearToolCaches());
                
                // Generate HTML for each tool
                let statusHtml = '<div class="tool-status-list">';
                
                data.tools.forEach(tool => {
                    // Get status badge class
                    let statusBadgeClass = 'status-unknown';
                    let statusText = 'Unknown';
                    
                    if (tool.status === 'ready') {
                        statusBadgeClass = 'status-ready';
                        statusText = 'Ready';
                    } else if (tool.status === 'error') {
                        statusBadgeClass = 'status-error';
                        statusText = 'Error';
                    } else if (tool.status === 'not_configured') {
                        statusBadgeClass = 'status-not-configured';
                        statusText = 'Not Configured';
                    }
                    
                    // Get API badge if applicable
                    let apiBadge = '';
                    if (tool.has_api_key) {
                        if (tool.api_key_valid || tool.has_valid_credentials) {
                            apiBadge = `<span class="tool-status-api-badge api-valid">API Valid</span>`;
                        } else {
                            apiBadge = `<span class="tool-status-api-badge api-invalid">API Invalid</span>`;
                        }
                    }
                    
                    // Get cache badge
                    let cacheBadge = '';
                    if (tool.cache_enabled && tool.cache_size > 0) {
                        cacheBadge = `<span class="tool-status-cache-badge">${tool.cache_size} items</span>`;
                    }
                    
                    // Calculate cache hit ratio
                    let hitRatio = 0;
                    if (tool.cache_stats && (tool.cache_stats.hits + tool.cache_stats.misses > 0)) {
                        hitRatio = tool.cache_stats.hits / (tool.cache_stats.hits + tool.cache_stats.misses);
                    }
                    
                    const hitRatioClass = hitRatio > 0.8 ? 'hit-ratio-high' : 
                                         hitRatio > 0.5 ? 'hit-ratio-medium' : 
                                         'hit-ratio-low';
                    
                    // Create cache clear button for this specific tool
                    const clearBtn = tool.cache_size > 0 ? 
                        `<button class="tool-cache-clear-btn" data-tool="${tool.name}" title="Clear cache">
                            <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"></path><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path></svg>
                        </button>` : '';
                    
                    // Create status item
                    statusHtml += `
                        <div class="tool-status-item">
                            <div class="tool-status-item-header">
                                <div class="tool-status-item-name-container">
                                    <span class="tool-status-item-name">${tool.name}</span>
                                    <span class="tool-status-badge ${statusBadgeClass}">${statusText}</span>
                                    ${apiBadge}
                                    ${cacheBadge}
                                </div>
                                <div class="tool-status-actions">
                                    ${clearBtn}
                                </div>
                            </div>
                            <div class="tool-status-details">
                                <div class="cache-config">
                                    <span>Cache: <b>${tool.cache_enabled ? 'Enabled' : 'Disabled'}</b></span>
                                    <span>TTL: <b>${tool.cache_ttl}s</b></span>
                                </div>
                                ${tool.cache_stats ? `
                                <div class="cache-stats">
                                    <div class="cache-stat-item">
                                        <span class="cache-stat-label">Hits</span>
                                        <span class="cache-stat-value">${tool.cache_stats.hits}</span>
                                    </div>
                                    <div class="cache-stat-item">
                                        <span class="cache-stat-label">Misses</span>
                                        <span class="cache-stat-value">${tool.cache_stats.misses}</span>
                                    </div>
                                    <div class="cache-stat-item">
                                        <span class="cache-stat-label">Hit ratio</span>
                                        <span class="cache-stat-value ${hitRatioClass}">${(hitRatio * 100).toFixed(1)}%</span>
                                    </div>
                                </div>
                                ` : ''}
                                ${tool.last_used ? `
                                <div class="tool-status-detail">
                                    Last used: <b>${tool.last_used_relative || tool.last_used}</b>
                                </div>
                                ` : ''}
                            </div>
                        </div>
                    `;
                });
                
                statusHtml += '</div>';
                
                // Create a container for the summary
                const summaryContainer = document.createElement('div');
                summaryContainer.className = 'tool-status-summary';
                summaryContainer.appendChild(cacheInfo);
                summaryContainer.appendChild(clearAllBtn);
                
                // Update container with summary and tools list
                statusContainer.innerHTML = '';
                statusContainer.appendChild(summaryContainer);
                statusContainer.insertAdjacentHTML('beforeend', statusHtml);
                
                // Add event listeners to individual clear buttons
                document.querySelectorAll('.tool-cache-clear-btn').forEach(btn => {
                    btn.addEventListener('click', (event) => {
                        event.preventDefault();
                        const toolName = btn.getAttribute('data-tool');
                        if (toolName) {
                            clearToolCaches(toolName);
                        }
                    });
                });
            } else {
                statusContainer.innerHTML = `<p>Error: ${data.error || 'Failed to load tool status'}</p>`;
                statusSummary.textContent = 'Error loading tools';
            }
        })
        .catch(error => {
            console.error('Error fetching tool status:', error);
            statusContainer.innerHTML = `<p>Error: ${error.message || 'Failed to load tool status'}</p>`;
            statusSummary.textContent = 'Error loading tools';
        });
}

// Function to clear all tool caches
function clearToolCaches(toolName = null) {
    // Get the button reference - either the main button or the specific tool button
    let button;
    if (toolName) {
        button = document.querySelector(`.tool-cache-clear-btn[data-tool="${toolName}"]`);
    } else {
        button = document.getElementById('clear-tool-caches') || 
                 document.querySelector('.clear-all-caches-btn');
    }
    
    if (!button) return;
    
    // Store original button content
    const originalHtml = button.innerHTML;
    const originalWidth = button.offsetWidth;
    const originalHeight = button.offsetHeight;
    
    // Keep button size consistent to avoid UI jumping
    button.style.width = `${originalWidth}px`;
    button.style.height = `${originalHeight}px`;
    
    // Show loading indicator
    button.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="spinner"><circle cx="12" cy="12" r="10"></circle><path d="M16 12a4 4 0 1 1-8 0 4 4 0 0 1 8 0z"></path></svg> Clearing...';
    button.disabled = true;
    
    // Build the API endpoint with optional tool name
    const url = toolName ? 
        `/api/clear-caches?tool_name=${encodeURIComponent(toolName)}` : 
        '/api/clear-caches';
    
    // Call the API to clear caches
    fetch(url, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            // Show success message
            button.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg> Cleared!';
            
            // Reset button after 2 seconds
            setTimeout(() => {
                button.innerHTML = originalHtml;
                button.disabled = false;
                button.style.width = '';
                button.style.height = '';
            }, 2000);
            
            console.log('Tool caches cleared:', result.tools_affected || toolName);
            
            // Refresh tool status
            setTimeout(loadToolStatus, 500);
            
            // Show a toast notification
            showToast(toolName ? 
                `Cache cleared for ${toolName}` : 
                'All tool caches cleared');
        } else {
            // Show error
            console.error('Failed to clear caches:', result.error);
            button.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg> Error!';
            
            // Reset button after 2 seconds
            setTimeout(() => {
                button.innerHTML = originalHtml;
                button.disabled = false;
                button.style.width = '';
                button.style.height = '';
            }, 2000);
            
            // Show error toast
            showToast('Failed to clear cache: ' + result.error, 'error');
        }
    })
    .catch(error => {
        console.error('Error clearing caches:', error);
        // Reset button
        button.innerHTML = originalHtml;
        button.disabled = false;
        button.style.width = '';
        button.style.height = '';
        
        // Show error toast
        showToast('Network error when clearing cache', 'error');
    });
}

// Switch between tabs
function switchTab(tabName) {
    // Update currentTab
    currentTab = tabName;
    
    // Update tab buttons
    document.querySelectorAll('.modal-tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('data-tab') === tabName);
    });
    
    // Update tab content
    document.querySelectorAll('.modal-tab-content').forEach(content => {
        content.classList.toggle('active', content.id === `${tabName}-tab`);
    });
    
    // Focus the active tab content
    setTimeout(() => {
        const activeTab = document.querySelector('.modal-tab-content.active');
        if (activeTab) {
            activeTab.focus();
            
            // Small scroll to ensure scrollbar is active
            activeTab.scrollTop = 1;
            setTimeout(() => activeTab.scrollTop = 0, 50);
        }
    }, 50);
}

// Clean up unwanted elements that might interfere with layout
function cleanUpElements() {
    // Just call the more specific function for backward compatibility
    cleanupApiKeyArtifacts();
}

// Function to load model options from API
async function loadModelOptions() {
    try {
        const response = await fetch('/api/models');
        const data = await response.json();
        
        if (data.success) {
            availableModels = data.models;
            currentModel = data.current_model;
            
            // Clear and render model options
            const container = document.getElementById('model-selection-container');
            container.innerHTML = '';
            
            availableModels.forEach(model => {
                const isSelected = model === currentModel;
                const modelElement = document.createElement('div');
                modelElement.className = `model-option ${isSelected ? 'selected' : ''}`;
                modelElement.dataset.model = model;
                
                let modelDescription = '';
                let modelIcon = '<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>';
                
                if (model === 'deepseek-chat') {
                    modelDescription = 'General purpose chat model with strong knowledge across domains.';
                } else if (model === 'deepseek-coder') {
                    modelDescription = 'Specialized for code generation and technical tasks.';
                    modelIcon = '<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M8 3H7a2 2 0 0 0-2 2v5a2 2 0 0 1-2 2 2 2 0 0 1 2 2v5c0 1.1.9 2 2 2h1"></path><path d="M16 3h1a2 2 0 0 1 2 2v5a2 2 0 0 0 2 2 2 2 0 0 0-2 2v5a2 2 0 0 1-2 2h-1"></path></svg>';
                } else if (model.includes('67b')) {
                    modelDescription = 'Large model with enhanced capabilities for complex tasks.';
                    modelIcon = '<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 3a3 3 0 0 0-3 3v12a3 3 0 0 0 3 3 3 3 0 0 0 3-3 3 3 0 0 0-3-3H6a3 3 0 0 0-3 3 3 3 0 0 0 3 3 3 3 0 0 0 3-3V6a3 3 0 0 0-3-3 3 3 0 0 0-3 3 3 3 0 0 0 3 3h12a3 3 0 0 0 3-3 3 3 0 0 0-3-3z"></path></svg>';
                } else if (model.includes('7b')) {
                    modelDescription = 'Smaller, faster model for general use cases.';
                    modelIcon = '<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="2"></circle><path d="M16.24 7.76a6 6 0 0 1 0 8.49m-8.48-.01a6 6 0 0 1 0-8.49m11.31-2.82a10 10 0 0 1 0 14.14m-14.14 0a10 10 0 0 1 0-14.14"></path></svg>';
                } else if (model === 'deepseek-reasoner') {
                    modelDescription = 'Specialized for complex reasoning and problem-solving tasks.';
                    modelIcon = '<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9.86 4.02A1.73 1.73 0 0 0 8.7 2a1.745 1.745 0 0 0-1.72 2.02M14.14 4.02a1.73 1.73 0 0 1 1.16-2.02 1.745 1.745 0 0 1 1.72 2.02M12 9.33V12m-3.7-3.4a3.03 3.03 0 0 0-1.86 4c.24.46.6.85 1.05 1.14l2.4 1.67a1.49 1.49 0 0 0 2.11-.47c.26-.4.27-.92.04-1.33a1.49 1.49 0 0 0-.55-.5l-1.6-1.1M15.7 8.6a3.02 3.02 0 0 1 1.86 4c-.24.46-.6.85-1.05 1.14l-2.4 1.67a1.49 1.49 0 0 1-2.11-.47c-.26-.4-.27-.92-.04-1.33a1.49 1.49 0 0 1 .55-.5l1.6-1.1M22 12a10 10 0 0 1-10 10A10 10 0 0 1 2 12 10 10 0 0 1 12 2a10 10 0 0 1 10 10Z"></path></svg>';
                }
                
                modelElement.innerHTML = `
                    <div class="model-option-icon">
                        ${modelIcon}
                    </div>
                    <div class="model-option-info">
                        <div class="model-option-name">${model}</div>
                        <div class="model-option-description">${modelDescription}</div>
                    </div>
                    ${isSelected ? '<div class="model-option-badge">Current</div>' : ''}
                `;
                
                // Add click event to select this model
                modelElement.addEventListener('click', () => {
                    // Update selection UI
                    document.querySelectorAll('.model-option').forEach(el => {
                        el.classList.remove('selected');
                        el.querySelector('.model-option-badge')?.remove();
                    });
                    
                    modelElement.classList.add('selected');
                    
                    // Add the "Current" badge if it doesn't exist
                    if (!modelElement.querySelector('.model-option-badge')) {
                        const badge = document.createElement('div');
                        badge.className = 'model-option-badge';
                        badge.textContent = 'Current';
                        modelElement.appendChild(badge);
                    }
                    
                    // Update selected model
                    currentModel = model;
                });
                
                container.appendChild(modelElement);
            });
            
            return true;
        } else {
            showErrorToast('Failed to load models: ' + (data.error || 'Unknown error'));
            return false;
        }
    } catch (error) {
        showErrorToast('Error loading models: ' + error.message);
        return false;
    }
}

// Function to save model selection
async function saveModelSelection() {
    if (!currentModel) return true;
    
    try {
        const response = await fetch('/api/set-model', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                model: currentModel
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showSuccessToast(`Model set to ${currentModel}`);
            return true;
        } else {
            showErrorToast('Failed to set model: ' + (data.error || 'Unknown error'));
            return false;
        }
    } catch (error) {
        showErrorToast('Error saving model: ' + error.message);
        return false;
    }
}

// Add model refresh button handler
document.getElementById('refresh-models')?.addEventListener('click', loadModelOptions);

// Update the openSettingsModal function to load model options
function openSettingsModal() {
    // Load existing code...
    
    // Load model options
    loadModelOptions();
    
    document.getElementById('settings-modal').classList.add('modal-open');
    document.getElementById('settings-backdrop').classList.add('modal-open');
    
    // Set focus to the first tab content
    document.querySelector('.modal-tab-content.active').focus();
}

// Update saveSettingsModal to include model selection
async function saveSettingsModal() {
    // Handle model selection
    await saveModelSelection();
    
    // Rest of the existing save logic...
    
    closeSettingsModal();
} 
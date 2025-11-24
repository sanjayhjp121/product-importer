// API Base URL
const API_BASE = '/api';

// Global state
let currentPage = 1;
let currentFilters = {};
let currentProductId = null;
let currentWebhookId = null;
let eventSource = null;

// Tab switching
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const tab = btn.dataset.tab;
        switchTab(tab);
    });
});

function switchTab(tab) {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    
    document.querySelector(`[data-tab="${tab}"]`).classList.add('active');
    document.getElementById(`${tab}-tab`).classList.add('active');
    
    if (tab === 'products') {
        loadProducts();
    } else if (tab === 'webhooks') {
        loadWebhooks();
    }
}

// File Upload
const uploadArea = document.getElementById('upload-area');
const fileInput = document.getElementById('file-input');

uploadArea.addEventListener('click', () => fileInput.click());
uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.style.background = '#e9ecef';
});
uploadArea.addEventListener('dragleave', () => {
    uploadArea.style.background = '#f8f9fa';
});
uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.style.background = '#f8f9fa';
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFileUpload(files[0]);
    }
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFileUpload(e.target.files[0]);
    }
});

async function handleFileUpload(file) {
    if (!file.name.endsWith('.csv')) {
        showToast('Please upload a CSV file', 'error');
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    const progressContainer = document.getElementById('upload-progress');
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');
    const progressStatus = document.getElementById('progress-status');
    const progressErrors = document.getElementById('progress-errors');
    const resultMessage = document.getElementById('upload-result');

    progressContainer.style.display = 'block';
    resultMessage.style.display = 'none';
    progressErrors.style.display = 'none';

    try {
        const response = await fetch(`${API_BASE}/upload`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error('Upload failed');
        }

        const data = await response.json();
        const taskId = data.task_id;

        // Connect to SSE for progress updates
        connectProgressStream(taskId);
    } catch (error) {
        showToast('Upload failed: ' + error.message, 'error');
        progressContainer.style.display = 'none';
    }
}

function connectProgressStream(taskId) {
    // Close existing connection
    if (eventSource) {
        eventSource.close();
    }

    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');
    const progressStatus = document.getElementById('progress-status');
    const progressErrors = document.getElementById('progress-errors');
    const resultMessage = document.getElementById('upload-result');
    const progressContainer = document.getElementById('upload-progress');

    eventSource = new EventSource(`${API_BASE}/stream/${taskId}`);

    eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        const percentage = data.percentage || 0;

        progressFill.style.width = `${percentage}%`;
        progressText.textContent = `${Math.round(percentage)}%`;
        progressStatus.textContent = data.message || data.status || 'Processing...';

        if (data.errors && data.errors.length > 0) {
            progressErrors.style.display = 'block';
            progressErrors.innerHTML = `<strong>Errors:</strong><ul>${data.errors.map(e => `<li>${e}</li>`).join('')}</ul>`;
        }

        if (data.status === 'completed') {
            eventSource.close();
            resultMessage.style.display = 'block';
            resultMessage.className = 'result-message success';
            resultMessage.textContent = `Import completed! ${data.message || ''}`;
            showToast('Import completed successfully', 'success');
            if (document.getElementById('products-tab').classList.contains('active')) {
                loadProducts();
            }
        } else if (data.status === 'error') {
            eventSource.close();
            resultMessage.style.display = 'block';
            resultMessage.className = 'result-message error';
            resultMessage.textContent = `Import failed: ${data.message || 'Unknown error'}`;
            showToast('Import failed', 'error');
        }
    };

    eventSource.onerror = () => {
        // Fallback to polling if SSE fails
        eventSource.close();
        pollProgress(taskId);
    };
}

function pollProgress(taskId) {
    const interval = setInterval(async () => {
        try {
            const response = await fetch(`${API_BASE}/progress/${taskId}`);
            if (!response.ok) return;
            
            const data = await response.json();
            const percentage = data.percentage || 0;

            const progressFill = document.getElementById('progress-fill');
            const progressText = document.getElementById('progress-text');
            const progressStatus = document.getElementById('progress-status');
            const progressErrors = document.getElementById('progress-errors');
            const resultMessage = document.getElementById('upload-result');

            progressFill.style.width = `${percentage}%`;
            progressText.textContent = `${Math.round(percentage)}%`;
            progressStatus.textContent = data.message || data.status || 'Processing...';

            if (data.errors && data.errors.length > 0) {
                progressErrors.style.display = 'block';
                progressErrors.innerHTML = `<strong>Errors:</strong><ul>${data.errors.map(e => `<li>${e}</li>`).join('')}</ul>`;
            }

            if (data.status === 'completed' || data.status === 'error') {
                clearInterval(interval);
                if (data.status === 'completed') {
                    resultMessage.style.display = 'block';
                    resultMessage.className = 'result-message success';
                    resultMessage.textContent = `Import completed! ${data.message || ''}`;
                    showToast('Import completed successfully', 'success');
                    if (document.getElementById('products-tab').classList.contains('active')) {
                        loadProducts();
                    }
                } else {
                    resultMessage.style.display = 'block';
                    resultMessage.className = 'result-message error';
                    resultMessage.textContent = `Import failed: ${data.message || 'Unknown error'}`;
                    showToast('Import failed', 'error');
                }
            }
        } catch (error) {
            clearInterval(interval);
        }
    }, 2000);
}

// Products Management
async function loadProducts() {
    const tbody = document.getElementById('products-tbody');
    tbody.innerHTML = '<tr><td colspan="6" class="loading">Loading products...</td></tr>';

    const params = new URLSearchParams({
        page: currentPage,
        per_page: 50,
        ...currentFilters
    });

    try {
        const response = await fetch(`${API_BASE}/products?${params}`);
        const data = await response.json();

        if (data.items.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="loading">No products found</td></tr>';
        } else {
            tbody.innerHTML = data.items.map(product => `
                <tr>
                    <td>${product.id}</td>
                    <td>${escapeHtml(product.sku)}</td>
                    <td>${escapeHtml(product.name)}</td>
                    <td>${escapeHtml(product.description || '')}</td>
                    <td>${product.active ? 'Yes' : 'No'}</td>
                    <td>
                        <button class="action-btn edit" onclick="editProduct(${product.id})">Edit</button>
                        <button class="action-btn delete" onclick="deleteProduct(${product.id})">Delete</button>
                    </td>
                </tr>
            `).join('');
        }

        updatePagination(data);
    } catch (error) {
        tbody.innerHTML = '<tr><td colspan="6" class="loading">Error loading products</td></tr>';
        showToast('Error loading products', 'error');
    }
}

function updatePagination(data) {
    const prevBtn = document.getElementById('prev-page-btn');
    const nextBtn = document.getElementById('next-page-btn');
    const pageInfo = document.getElementById('page-info');

    prevBtn.disabled = data.page === 1;
    nextBtn.disabled = data.page >= data.pages;
    pageInfo.textContent = `Page ${data.page} of ${data.pages} (${data.total} total)`;
}

document.getElementById('prev-page-btn').addEventListener('click', () => {
    if (currentPage > 1) {
        currentPage--;
        loadProducts();
    }
});

document.getElementById('next-page-btn').addEventListener('click', () => {
    currentPage++;
    loadProducts();
});

document.getElementById('apply-filters-btn').addEventListener('click', () => {
    currentPage = 1;
    currentFilters = {
        sku: document.getElementById('filter-sku').value || undefined,
        name: document.getElementById('filter-name').value || undefined,
        description: document.getElementById('filter-description').value || undefined,
        active: document.getElementById('filter-active').value || undefined
    };
    loadProducts();
});

document.getElementById('clear-filters-btn').addEventListener('click', () => {
    document.getElementById('filter-sku').value = '';
    document.getElementById('filter-name').value = '';
    document.getElementById('filter-description').value = '';
    document.getElementById('filter-active').value = '';
    currentFilters = {};
    currentPage = 1;
    loadProducts();
});

// Product Modal
const productModal = document.getElementById('product-modal');
const productForm = document.getElementById('product-form');
const addProductBtn = document.getElementById('add-product-btn');
const cancelProductBtn = document.getElementById('cancel-product-btn');

addProductBtn.addEventListener('click', () => {
    currentProductId = null;
    document.getElementById('modal-title').textContent = 'Add Product';
    productForm.reset();
    document.getElementById('product-active').checked = true;
    productModal.style.display = 'block';
});

cancelProductBtn.addEventListener('click', () => {
    productModal.style.display = 'none';
});

productForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const productData = {
        sku: document.getElementById('product-sku').value,
        name: document.getElementById('product-name').value,
        description: document.getElementById('product-description').value || null,
        active: document.getElementById('product-active').checked
    };

    try {
        const url = currentProductId 
            ? `${API_BASE}/products/${currentProductId}`
            : `${API_BASE}/products`;
        const method = currentProductId ? 'PUT' : 'POST';

        const response = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(productData)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to save product');
        }

        productModal.style.display = 'none';
        showToast(`Product ${currentProductId ? 'updated' : 'created'} successfully`, 'success');
        loadProducts();
    } catch (error) {
        showToast(error.message, 'error');
    }
});

async function editProduct(id) {
    try {
        const response = await fetch(`${API_BASE}/products/${id}`);
        const product = await response.json();

        currentProductId = product.id;
        document.getElementById('modal-title').textContent = 'Edit Product';
        document.getElementById('product-sku').value = product.sku;
        document.getElementById('product-sku').disabled = true; // SKU cannot be changed
        document.getElementById('product-name').value = product.name;
        document.getElementById('product-description').value = product.description || '';
        document.getElementById('product-active').checked = product.active;
        productModal.style.display = 'block';
    } catch (error) {
        showToast('Error loading product', 'error');
    }
}

async function deleteProduct(id) {
    if (!confirm('Are you sure you want to delete this product?')) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/products/${id}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            throw new Error('Failed to delete product');
        }

        showToast('Product deleted successfully', 'success');
        loadProducts();
    } catch (error) {
        showToast('Error deleting product', 'error');
    }
}

// Bulk Delete
document.getElementById('bulk-delete-btn').addEventListener('click', async () => {
    if (!confirm('Are you sure you want to delete ALL products? This cannot be undone.')) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/products/bulk/all`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            throw new Error('Failed to delete products');
        }

        const data = await response.json();
        showToast(`Deleted ${data.count} products`, 'success');
        loadProducts();
    } catch (error) {
        showToast('Error deleting products', 'error');
    }
});

// Webhooks Management
async function loadWebhooks() {
    const tbody = document.getElementById('webhooks-tbody');
    tbody.innerHTML = '<tr><td colspan="5" class="loading">Loading webhooks...</td></tr>';

    try {
        const response = await fetch(`${API_BASE}/webhooks`);
        const webhooks = await response.json();

        if (webhooks.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="loading">No webhooks found</td></tr>';
        } else {
            tbody.innerHTML = webhooks.map(webhook => `
                <tr>
                    <td>${webhook.id}</td>
                    <td>${escapeHtml(webhook.url)}</td>
                    <td>${escapeHtml(webhook.event_type)}</td>
                    <td><span class="status-badge ${webhook.enabled ? 'enabled' : 'disabled'}">${webhook.enabled ? 'Enabled' : 'Disabled'}</span></td>
                    <td>
                        <button class="action-btn test" onclick="testWebhook(${webhook.id})">Test</button>
                        <button class="action-btn edit" onclick="editWebhook(${webhook.id})">Edit</button>
                        <button class="action-btn delete" onclick="deleteWebhook(${webhook.id})">Delete</button>
                    </td>
                </tr>
            `).join('');
        }
    } catch (error) {
        tbody.innerHTML = '<tr><td colspan="5" class="loading">Error loading webhooks</td></tr>';
        showToast('Error loading webhooks', 'error');
    }
}

// Webhook Modal
const webhookModal = document.getElementById('webhook-modal');
const webhookForm = document.getElementById('webhook-form');
const addWebhookBtn = document.getElementById('add-webhook-btn');
const cancelWebhookBtn = document.getElementById('cancel-webhook-btn');

addWebhookBtn.addEventListener('click', () => {
    currentWebhookId = null;
    document.getElementById('webhook-modal-title').textContent = 'Add Webhook';
    webhookForm.reset();
    document.getElementById('webhook-enabled').checked = true;
    webhookModal.style.display = 'block';
});

cancelWebhookBtn.addEventListener('click', () => {
    webhookModal.style.display = 'none';
});

webhookForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const webhookData = {
        url: document.getElementById('webhook-url').value,
        event_type: document.getElementById('webhook-event-type').value,
        enabled: document.getElementById('webhook-enabled').checked
    };

    try {
        const url = currentWebhookId 
            ? `${API_BASE}/webhooks/${currentWebhookId}`
            : `${API_BASE}/webhooks`;
        const method = currentWebhookId ? 'PUT' : 'POST';

        const response = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(webhookData)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to save webhook');
        }

        webhookModal.style.display = 'none';
        showToast(`Webhook ${currentWebhookId ? 'updated' : 'created'} successfully`, 'success');
        loadWebhooks();
    } catch (error) {
        showToast(error.message, 'error');
    }
});

async function editWebhook(id) {
    try {
        const response = await fetch(`${API_BASE}/webhooks/${id}`);
        const webhook = await response.json();

        currentWebhookId = webhook.id;
        document.getElementById('webhook-modal-title').textContent = 'Edit Webhook';
        document.getElementById('webhook-url').value = webhook.url;
        document.getElementById('webhook-event-type').value = webhook.event_type;
        document.getElementById('webhook-enabled').checked = webhook.enabled;
        webhookModal.style.display = 'block';
    } catch (error) {
        showToast('Error loading webhook', 'error');
    }
}

async function deleteWebhook(id) {
    if (!confirm('Are you sure you want to delete this webhook?')) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/webhooks/${id}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            throw new Error('Failed to delete webhook');
        }

        showToast('Webhook deleted successfully', 'success');
        loadWebhooks();
    } catch (error) {
        showToast('Error deleting webhook', 'error');
    }
}

async function testWebhook(id) {
    try {
        showToast('Testing webhook...', 'success');
        const response = await fetch(`${API_BASE}/webhooks/${id}/test`, {
            method: 'POST'
        });

        const result = await response.json();
        
        if (result.success) {
            showToast(`Webhook test successful! Status: ${result.status_code}, Time: ${Math.round(result.response_time_ms)}ms`, 'success');
        } else {
            showToast(`Webhook test failed: ${result.error || 'Unknown error'}`, 'error');
        }
    } catch (error) {
        showToast('Error testing webhook', 'error');
    }
}

// Modal close handlers
document.querySelectorAll('.close').forEach(closeBtn => {
    closeBtn.addEventListener('click', (e) => {
        e.target.closest('.modal').style.display = 'none';
    });
});

window.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal')) {
        e.target.style.display = 'none';
    }
});

// Utility functions
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type} show`;
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// Load initial data
if (document.getElementById('products-tab').classList.contains('active')) {
    loadProducts();
}


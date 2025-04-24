// static/js/upload.js

document.addEventListener('DOMContentLoaded', () => {
    const uploadBox = document.querySelector('.upload-box');
    const fileInput = document.getElementById('fileInput');
    const browseButton = document.getElementById('browseButton');
    const uploadStatus = document.getElementById('uploadStatus');
    const progressFill = document.getElementById('uploadProgress');
    const statusMessage = document.getElementById('statusMessage');

    // Handle browse button click
    browseButton.addEventListener('click', () => {
        fileInput.click();
    });

    // Handle drag and drop events
    uploadBox.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadBox.classList.add('active');
    });

    uploadBox.addEventListener('dragleave', () => {
        uploadBox.classList.remove('active');
    });

    uploadBox.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadBox.classList.remove('active');
        
        if (e.dataTransfer.files.length) {
            fileInput.files = e.dataTransfer.files;
            handleFileUpload(e.dataTransfer.files[0]);
        }
    });

    // Handle file input change
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length) {
            handleFileUpload(e.target.files[0]);
        }
    });

    // Function to handle file upload
    function handleFileUpload(file) {
        // Validate file type
        if (!file.name.toLowerCase().endsWith('.csv')) {
            alert('Please upload a CSV file');
            return;
        }

        // Show upload status
        uploadStatus.style.display = 'block';
        progressFill.style.width = '0%';
        statusMessage.textContent = 'Uploading file...';

        // Create FormData
        const formData = new FormData();
        formData.append('file', file);

        // Simulate upload progress
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += 5;
            if (progress > 90) {
                clearInterval(progressInterval);
            }
            progressFill.style.width = `${progress}%`;
        }, 200);

        // Send file to server
        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            clearInterval(progressInterval);
            
            if (data.success) {
                progressFill.style.width = '100%';
                statusMessage.textContent = 'Upload complete! Processing data...';
                
                // Show success message with data summary
                setTimeout(() => {
                    statusMessage.innerHTML = `
                        <div class="upload-success">
                            <i class="fas fa-check-circle"></i>
                            File processed successfully!
                        </div>
                        <div class="upload-summary">
                            <p><strong>Records:</strong> ${data.summary.record_count || 'N/A'}</p>
                            <p><strong>Date Range:</strong> ${data.summary.date_range || 'N/A'}</p>
                        </div>
                        <button id="viewDashboardBtn" class="btn primary">View Dashboard</button>
                    `;
                    
                    // Add event listener to dashboard button
                    document.getElementById('viewDashboardBtn').addEventListener('click', () => {
                        window.location.href = '/dashboard';
                    });
                }, 1000);
            } else {
                showUploadError(data.error || 'An error occurred during upload');
            }
        })
        .catch(error => {
            clearInterval(progressInterval);
            showUploadError('Network error. Please try again.');
            console.error('Upload error:', error);
        });
    }

    function showUploadError(message) {
        progressFill.style.width = '100%';
        progressFill.style.backgroundColor = 'var(--accent-color)';
        statusMessage.innerHTML = `
            <div class="upload-error">
                <i class="fas fa-exclamation-circle"></i>
                ${message}
            </div>
            <button id="retryBtn" class="btn secondary">Try Again</button>
        `;
        
        document.getElementById('retryBtn').addEventListener('click', () => {
            uploadStatus.style.display = 'none';
            progressFill.style.backgroundColor = 'var(--secondary-color)';
        });
    }

    // Enhanced cursor trail with velocity tracking
    let lastX = 0;
    let lastY = 0;
    let lastTime = Date.now();
    
    function updateCursorTrail(e) {
        const now = Date.now();
        const deltaTime = now - lastTime;
        const distance = Math.sqrt(Math.pow(e.clientX - lastX, 2) + Math.pow(e.clientY - lastY, 2));
        const velocity = distance / deltaTime;
    
        // Create trail particle
        const trail = document.createElement('div');
        trail.className = 'cursor-trail';
        
        // Dynamic properties based on velocity
        const size = 6 + (velocity * 0.3);
        const opacity = 0.8 - (velocity * 0.002);
        
        trail.style.width = `${Math.min(size, 12)}px`;
        trail.style.height = `${Math.min(size, 12)}px`;
        trail.style.opacity = `${Math.max(opacity, 0.3)}`;
        
        trail.style.left = e.clientX + 'px';
        trail.style.top = e.clientY + 'px';
        
        document.body.appendChild(trail);
        
        // Remove trail after animation
        setTimeout(() => trail.remove(), 1000);
        
        // Update tracking variables
        lastX = e.clientX;
        lastY = e.clientY;
        lastTime = now;
    }
    
    // Reset particles on window resize
    window.addEventListener('resize', () => {
        document.querySelectorAll('.cursor-trail').forEach(t => t.remove());
    });

    // Add mousemove listener
    window.addEventListener('mousemove', updateCursorTrail);
});
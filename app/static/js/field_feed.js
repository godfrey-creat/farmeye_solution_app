/**
 * Field Video Feed with YOLO Detection
 * 
 * This script handles the video feed display and YOLO object detection
 * functionality for the field view component.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Check if feed elements exist
    const videoContainer = document.getElementById('videoContainer');
    if (!videoContainer) return;

    // Main elements
    const videoFeed = document.getElementById('videoFeed');
    const videoOverlay = document.getElementById('videoOverlay');
    const detectionCanvas = document.getElementById('detectionCanvas');
    const yoloToggle = document.getElementById('yoloToggle');
    const yoloStatus = document.getElementById('yoloStatus');
    const detectionStats = document.getElementById('detectionStats');
    const maizeCount = document.getElementById('maizeCount');
    const weedCount = document.getElementById('weedCount');
    const expandButton = document.getElementById('expandButton');
    const expandedView = document.getElementById('expandedView');
    const collapseButton = document.getElementById('collapseButton');
    const cameraSelect = document.getElementById('cameraSelect');
    const cameraLabel = document.getElementById('cameraLabel');
    const prevCameraBtn = document.getElementById('prevCameraBtn');
    const nextCameraBtn = document.getElementById('nextCameraBtn');
    
    // Camera data - map camera names to sectors
    const cameras = [
        { name: 'Camera 1', sector: 'Sector 3' },
        { name: 'Camera 2', sector: 'Sector 3' },
        { name: 'Camera 3', sector: 'Sector 4' },
        { name: 'Camera 4', sector: 'Sector 2' }
    ];
    
    // Animation frame reference and state
    let animationFrame = null;
    let isYoloActive = false;
    let lastDetectionTime = 0;
    
    // Initialize the video
    function initVideo() {
        // Try to play the video
        videoFeed.play().then(() => {
            // Hide the play overlay if successful
            videoOverlay.style.display = 'none';
        }).catch(error => {
            console.error('Video autoplay failed:', error);
            // Keep the play overlay visible if autoplay fails
        });
        
        // Set up canvas dimensions
        updateCanvasDimensions();
    }
    
    function updateCanvasDimensions() {
        if (!videoFeed || !detectionCanvas) return;
        
        const width = videoFeed.videoWidth || 640;
        const height = videoFeed.videoHeight || 360;
        
        detectionCanvas.width = width;
        detectionCanvas.height = height;
    }
    
    // Manual play button click handler
    if (videoOverlay) {
        videoOverlay.addEventListener('click', function() {
            videoFeed.play().then(() => {
                videoOverlay.style.display = 'none';
            }).catch(error => {
                console.error('Manual play failed:', error);
                alert('Unable to play video. Please try again or check browser permissions.');
            });
        });
    }
    
    // Wait for video to load
    if (videoFeed) {
        videoFeed.addEventListener('loadeddata', initVideo);
        videoFeed.addEventListener('loadedmetadata', updateCanvasDimensions);
    }
    
    // YOLO toggle handler
    if (yoloToggle) {
        yoloToggle.addEventListener('click', function() {
            isYoloActive = !isYoloActive;
            
            if (isYoloActive) {
                yoloToggle.classList.add('active');
                yoloStatus.textContent = 'YOLO Active';
                detectionCanvas.classList.add('active');
                detectionStats.style.display = 'block';
                startDetection();
            } else {
                yoloToggle.classList.remove('active');
                yoloStatus.textContent = 'YOLO Off';
                detectionCanvas.classList.remove('active');
                detectionStats.style.display = 'none';
                stopDetection();
            }
        });
    }
    
    // Expand/collapse handlers
    if (expandButton) {
        expandButton.addEventListener('click', function() {
            if (expandedView) {
                expandedView.style.display = 'flex';
                
                // Start playing all videos in expanded view
                const videos = expandedView.querySelectorAll('video');
                videos.forEach(video => {
                    video.play().catch(error => {
                        console.error('Expanded view video play failed:', error);
                    });
                });
            }
        });
    }
    
    if (collapseButton) {
        collapseButton.addEventListener('click', function() {
            if (expandedView) {
                expandedView.style.display = 'none';
                
                // Pause all videos in expanded view to save resources
                const videos = expandedView.querySelectorAll('video');
                videos.forEach(video => {
                    video.pause();
                });
            }
        });
    }
    
    // Camera selection
    if (cameraSelect) {
        cameraSelect.addEventListener('change', function() {
            const selectedCamera = cameras.find(camera => camera.name === this.value) || cameras[1];
            updateCameraLabel(selectedCamera);
            
            // Update active camera in expanded view
            if (expandedView) {
                const cameraItems = expandedView.querySelectorAll('.camera-item');
                cameraItems.forEach(item => {
                    const cameraName = item.getAttribute('data-camera');
                    const indicator = item.querySelector('.active-indicator');
                    
                    if (indicator) {
                        if (cameraName === selectedCamera.name) {
                            indicator.style.display = 'flex';
                        } else {
                            indicator.style.display = 'none';
                        }
                    }
                });
            }
        });
    }
    
    // Previous/Next camera buttons
    if (prevCameraBtn && cameraSelect) {
        prevCameraBtn.addEventListener('click', function() {
            const currentIndex = cameras.findIndex(camera => camera.name === cameraSelect.value);
            const prevIndex = (currentIndex - 1 + cameras.length) % cameras.length;
            cameraSelect.value = cameras[prevIndex].name;
            
            // Trigger change event
            const event = new Event('change');
            cameraSelect.dispatchEvent(event);
        });
    }
    
    if (nextCameraBtn && cameraSelect) {
        nextCameraBtn.addEventListener('click', function() {
            const currentIndex = cameras.findIndex(camera => camera.name === cameraSelect.value);
            const nextIndex = (currentIndex + 1) % cameras.length;
            cameraSelect.value = cameras[nextIndex].name;
            
            // Trigger change event
            const event = new Event('change');
            cameraSelect.dispatchEvent(event);
        });
    }
    
    // Update camera label function
    function updateCameraLabel(camera) {
        if (cameraLabel) {
            cameraLabel.textContent = `${camera.sector} - ${camera.name}`;
        }
    }
    
    // YOLO Detection functions
    function startDetection() {
        if (animationFrame) {
            cancelAnimationFrame(animationFrame);
        }
        
        // Start detection loop
        detectFrame();
    }
    
    function stopDetection() {
        if (animationFrame) {
            cancelAnimationFrame(animationFrame);
            animationFrame = null;
        }
        
        // Clear canvas
        if (detectionCanvas) {
            const ctx = detectionCanvas.getContext('2d');
            ctx.clearRect(0, 0, detectionCanvas.width, detectionCanvas.height);
        }
    }
    
    function detectFrame() {
        if (!videoFeed || !detectionCanvas) return;
        
        if (videoFeed.readyState === videoFeed.HAVE_ENOUGH_DATA) {
            const now = Date.now();
            const timeSinceLastDetection = now - lastDetectionTime;
            
            // Only perform detection every 100ms to avoid excessive processing
            if (timeSinceLastDetection > 100) {
                lastDetectionTime = now;
                
                // Get canvas context
                const ctx = detectionCanvas.getContext('2d');
                
                // Draw video frame to canvas
                ctx.drawImage(videoFeed, 0, 0, detectionCanvas.width, detectionCanvas.height);
                
                // Process frame (simulate YOLO detection for now)
                processFrameForDetection(detectionCanvas)
                    .then(detections => {
                        // Update stats
                        updateDetectionStats(detections);
                        
                        // Draw detections on canvas
                        drawDetections(ctx, detections);
                    })
                    .catch(error => {
                        console.error('Detection error:', error);
                    });
            }
        }
        
        // Continue detection loop
        animationFrame = requestAnimationFrame(detectFrame);
    }
    
    // Process frame for detection (can be replaced with actual API call)
    async function processFrameForDetection(canvas) {
        // In a real implementation, this could send the canvas data to a backend API
        // For now, we'll simulate detection with random data
        
        // For mock implementation
        return await mockDetection(canvas);
        
        // For real implementation (commented out)
        /*
        try {
            // Convert canvas to blob
            const blob = await new Promise(resolve => {
                canvas.toBlob(resolve, 'image/jpeg', 0.8);
            });
            
            // Create form data
            const formData = new FormData();
            formData.append('image', blob, 'frame.jpg');
            
            // Send to detection API
            const response = await fetch('/api/detect', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error('Detection API error');
            }
            
            const result = await response.json();
            return result.detections;
        } catch (error) {
            console.error('Error calling detection API:', error);
            return [];
        }
        */
    }
    
    // Update detection stats display
    function updateDetectionStats(detections) {
        if (!maizeCount || !weedCount) return;
        
        const maizeDetections = detections.filter(d => d.class === 'maize');
        const weedDetections = detections.filter(d => d.class === 'weed');
        
        maizeCount.textContent = `${maizeDetections.length} Maize`;
        weedCount.textContent = `${weedDetections.length} Weeds`;
    }
    
    // Mock YOLO detection (simulates actual model)
    async function mockDetection(canvas) {
        // Simulate processing time
        await new Promise(resolve => setTimeout(resolve, 30));
        
        const width = canvas.width;
        const height = canvas.height;
        
        // Generate random detections
        const detections = [];
        
        // Add some maize detections
        const maizeCount = 3 + Math.floor(Math.random() * 3);
        for (let i = 0; i < maizeCount; i++) {
            const x = Math.floor(Math.random() * (width - 100));
            const y = Math.floor(Math.random() * (height - 150));
            const w = 80 + Math.floor(Math.random() * 40);
            const h = 120 + Math.floor(Math.random() * 60);
            
            detections.push({
                class: 'maize',
                confidence: 0.75 + Math.random() * 0.2,
                bbox: [x, y, w, h]
            });
        }
        
        // Add some weed detections
        const weedCount = 4 + Math.floor(Math.random() * 4);
        for (let i = 0; i < weedCount; i++) {
            const x = Math.floor(Math.random() * (width - 60));
            const y = Math.floor(Math.random() * (height - 40));
            const w = 30 + Math.floor(Math.random() * 40);
            const h = 20 + Math.floor(Math.random() * 30);
            
            detections.push({
                class: 'weed',
                confidence: 0.65 + Math.random() * 0.3,
                bbox: [x, y, w, h]
            });
        }
        
        return detections;
    }
    
    // Draw detection boxes on canvas
    function drawDetections(ctx, detections) {
        // Clear the canvas first (optional if we redraw the video frame each time)
        ctx.clearRect(0, 0, detectionCanvas.width, detectionCanvas.height);
        
        // Redraw the video frame
        ctx.drawImage(videoFeed, 0, 0, detectionCanvas.width, detectionCanvas.height);
        
        // Draw each detection
        detections.forEach(detection => {
            const [x, y, width, height] = detection.bbox;
            
            // Choose color based on class
            let color;
            switch (detection.class) {
                case 'maize':
                    color = '#4CAF50'; // Green for maize
                    break;
                case 'weed':
                    color = '#F44336'; // Red for weeds
                    break;
                default:
                    color = '#FFC107'; // Yellow for unknown
            }
            
            // Draw bounding box
            ctx.strokeStyle = color;
            ctx.lineWidth = 3;
            ctx.strokeRect(x, y, width, height);
            
            // Draw label background
            ctx.fillStyle = color;
            const confidence = Math.round(detection.confidence * 100);
            const text = `${detection.class} ${confidence}%`;
            const textWidth = ctx.measureText(text).width + 10;
            ctx.fillRect(x, y - 25, textWidth, 25);
            
            // Draw label text
            ctx.fillStyle = '#FFFFFF';
            ctx.font = 'bold 14px Arial';
            ctx.fillText(text, x + 5, y - 7);
        });
    }
    
    // Initialize with default camera
    if (cameraSelect) {
        const defaultCamera = cameras.find(camera => camera.name === cameraSelect.value) || cameras[1];
        updateCameraLabel(defaultCamera);
    }
});
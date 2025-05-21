/**
 * Field Video Feed with YOLO Detection and Multiple Camera Views
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
    const cameraLabel = document.getElementById('cameraLabel');
    const cameraSelect = document.getElementById('cameraSelect');
    const prevCameraBtn = document.getElementById('prevCameraBtn');
    const nextCameraBtn = document.getElementById('nextCameraBtn');
    const snapshotBtn = document.getElementById('snapshotBtn');
    
    // Camera data with video sources
    const cameras = [
        {
            name: 'Camera 1',
            label: 'Vegetative Stage',
            sources: [
                {
                    src: 'https://www.shutterstock.com/shutterstock/videos/3703540751/preview/stock-footage-vegetative-stage-of-maize-maize-farming.webm',
                    type: 'video/webm'
                }
            ]
        },
        {
            name: 'Camera 2',
            label: 'Field View',
            sources: [
                {
                    src: 'https://www.shutterstock.com/shutterstock/videos/3719558213/preview/stock-footage-zea-mays-maize-corn-field-farming-natural.webm',
                    type: 'video/webm'
                }
            ]
        },
        {
            name: 'Camera 3',
            label: 'Top Down View',
            sources: [
                {
                    src: 'https://www.shutterstock.com/shutterstock/videos/3774732253/preview/stock-footage-top-down-view-neatly-planted-maize-crops-fertile.webm',
                    type: 'video/webm'
                }
            ]
        },
        {
            name: 'Camera 4',
            label: 'Aerial View',
            sources: [
                {
                    src: 'https://www.shutterstock.com/shutterstock/videos/3750960769/preview/stock-footage-aerial-view-rows-maize-corn-field-landscape.webm',
                    type: 'video/webm'
                }
            ]
        }
    ];
    
    // Fallback source to use if Shutterstock videos fail
    const fallbackSource = {
        src: '/static/Constants/corn.mp4',
        type: 'video/mp4'
    };
    
    // Animation frame reference and state
    let animationFrame = null;
    let isYoloActive = false;
    let lastDetectionTime = 0;
    let lastDetections = [];
    let processingImage = false;
    let currentCameraIndex = 1; // Start with Camera 2
    
    // Initialize the video element with a camera source
    function loadCamera(cameraIndex) {
        if (cameraIndex < 0 || cameraIndex >= cameras.length) {
            console.error('Invalid camera index:', cameraIndex);
            return;
        }
        
        currentCameraIndex = cameraIndex;
        const camera = cameras[cameraIndex];
        
        // Update camera label
        if (cameraLabel) {
            cameraLabel.textContent = `${camera.label} - ${camera.name}`;
        }
        
        // Update camera selector
        if (cameraSelect) {
            cameraSelect.value = camera.name;
        }
        
        // Update active indicators in expanded view
        if (expandedView) {
            const cameraItems = expandedView.querySelectorAll('.camera-item');
            cameraItems.forEach((item, index) => {
                const indicator = item.querySelector('.active-indicator');
                if (indicator) {
                    indicator.style.display = (index === cameraIndex) ? 'flex' : 'none';
                }
            });
        }
        
        // Load video sources
        if (videoFeed) {
            // Remove existing sources
            while (videoFeed.firstChild) {
                videoFeed.removeChild(videoFeed.firstChild);
            }
            
            // Add new sources
            camera.sources.forEach(source => {
                const sourceElement = document.createElement('source');
                sourceElement.src = source.src;
                sourceElement.type = source.type;
                videoFeed.appendChild(sourceElement);
            });
            
            // Add fallback source
            const fallbackElement = document.createElement('source');
            fallbackElement.src = fallbackSource.src;
            fallbackElement.type = fallbackSource.type;
            videoFeed.appendChild(fallbackElement);
            
            // Add text for browsers that don't support video
            const textNode = document.createTextNode('Your browser does not support the video tag.');
            videoFeed.appendChild(textNode);
            
            // Load the video
            videoFeed.load();
            playVideo();
        }
    }
    
    // Play video function
    function playVideo() {
        videoFeed.play().then(() => {
            // Hide the play overlay if successful
            if (videoOverlay) {
                videoOverlay.style.display = 'none';
            }
        }).catch(error => {
            console.error('Video autoplay failed:', error);
            // Keep the play overlay visible if autoplay fails
        });
    }
    
    // Initialize the video
    function initVideo() {
        // Set up canvas dimensions
        updateCanvasDimensions();
        
        // Load the initial camera
        loadCamera(currentCameraIndex);
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
            playVideo();
        });
    }
    
    // Wait for video to load
    if (videoFeed) {
        videoFeed.addEventListener('loadeddata', function() {
            updateCanvasDimensions();
            playVideo();
        });
        videoFeed.addEventListener('loadedmetadata', updateCanvasDimensions);
        
        // Handle video errors
        videoFeed.addEventListener('error', function(e) {
            console.error('Video error:', e);
            alert('There was an error loading the video. The videos are preview files from Shutterstock and may have restricted access. The local fallback video should load instead.');
        });
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
                const expandedVideos = expandedView.querySelectorAll('video');
                expandedVideos.forEach(video => {
                    video.load(); // Make sure sources are loaded
                    video.play().catch(error => {
                        console.error('Expanded view video play failed:', error);
                    });
                });
                
                // Update active camera in expanded view
                const cameraItems = expandedView.querySelectorAll('.camera-item');
                cameraItems.forEach((item, index) => {
                    const indicator = item.querySelector('.active-indicator');
                    if (indicator) {
                        indicator.style.display = (index === currentCameraIndex) ? 'flex' : 'none';
                    }
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
            const selectedCameraName = this.value;
            const cameraIndex = cameras.findIndex(camera => camera.name === selectedCameraName);
            
            if (cameraIndex >= 0) {
                loadCamera(cameraIndex);
            }
        });
    }
    
    // Previous/Next camera buttons
    if (prevCameraBtn) {
        prevCameraBtn.addEventListener('click', function() {
            const prevIndex = (currentCameraIndex - 1 + cameras.length) % cameras.length;
            loadCamera(prevIndex);
        });
    }
    
    if (nextCameraBtn) {
        nextCameraBtn.addEventListener('click', function() {
            const nextIndex = (currentCameraIndex + 1) % cameras.length;
            loadCamera(nextIndex);
        });
    }
    
    // Take snapshot button
    if (snapshotBtn) {
        snapshotBtn.addEventListener('click', function() {
            if (!videoFeed || videoFeed.paused || videoFeed.ended) {
                console.warn('Cannot take snapshot: video not playing');
                return;
            }
            
            const canvas = document.createElement('canvas');
            canvas.width = videoFeed.videoWidth;
            canvas.height = videoFeed.videoHeight;
            
            const ctx = canvas.getContext('2d');
            ctx.drawImage(videoFeed, 0, 0, canvas.width, canvas.height);
            
            // If YOLO is active, also draw detections
            if (isYoloActive && lastDetections.length > 0) {
                drawDetections(ctx, lastDetections);
            }
            
            // Convert to image and download
            try {
                const image = canvas.toDataURL('image/png');
                const link = document.createElement('a');
                
                link.href = image;
                link.download = `farm-snapshot-${new Date().toISOString().slice(0,19).replace(/:/g, '-')}.png`;
                link.click();
            } catch (error) {
                console.error('Error creating snapshot:', error);
                alert('Could not create snapshot. This might be due to CORS restrictions with the video source.');
            }
        });
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
            
            // Only perform detection every 500ms to avoid excessive processing and API calls
            if (timeSinceLastDetection > 500 && !processingImage) {
                lastDetectionTime = now;
                processingImage = true;
                
                // Get canvas context
                const ctx = detectionCanvas.getContext('2d');
                
                // Draw video frame to canvas
                ctx.drawImage(videoFeed, 0, 0, detectionCanvas.width, detectionCanvas.height);
                
                // Process frame with YOLO API
                processFrameForDetection(detectionCanvas)
                    .then(detections => {
                        if (detections && detections.length > 0) {
                            lastDetections = detections;
                            // Update stats
                            updateDetectionStats(detections);
                            
                            // Draw detections on canvas
                            drawDetections(ctx, detections);
                        }
                        processingImage = false;
                    })
                    .catch(error => {
                        console.error('Detection error:', error);
                        processingImage = false;
                        
                        // If API fails, still try to display last known detections
                        if (lastDetections.length > 0) {
                            const ctx = detectionCanvas.getContext('2d');
                            ctx.drawImage(videoFeed, 0, 0, detectionCanvas.width, detectionCanvas.height);
                            drawDetections(ctx, lastDetections);
                        }
                    });
            } else {
                // Just redraw last detections without calling API
                if (lastDetections.length > 0) {
                    const ctx = detectionCanvas.getContext('2d');
                    ctx.drawImage(videoFeed, 0, 0, detectionCanvas.width, detectionCanvas.height);
                    drawDetections(ctx, lastDetections);
                }
            }
        }
        
        // Continue detection loop
        animationFrame = requestAnimationFrame(detectFrame);
    }
    
    // Process frame for detection using real YOLO API
    async function processFrameForDetection(canvas) {
        try {
            // Convert canvas to blob
            const blob = await new Promise(resolve => {
                canvas.toBlob(resolve, 'image/jpeg', 0.8);
            });
            
            // Create form data
            const formData = new FormData();
            formData.append('image', blob, 'frame.jpg');
            
            // Send to detection API
            const response = await fetch('/feed/detect', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(`Detection API error: ${errorData.error || response.statusText}`);
            }
            
            const result = await response.json();
            
            if (!result.success) {
                throw new Error(result.error || 'Unknown API error');
            }
            
            return result.detections;
        } catch (error) {
            console.error('Error calling detection API:', error);
            // Return empty array on error
            return [];
        }
    }
    
    // Update detection stats display
    function updateDetectionStats(detections) {
        if (!maizeCount || !weedCount) return;
        
        const maizeDetections = detections.filter(d => d.class === 'maize');
        const weedDetections = detections.filter(d => d.class === 'weed');
        
        maizeCount.textContent = `${maizeDetections.length} Maize`;
        weedCount.textContent = `${weedDetections.length} Weeds`;
    }
    
    // Draw detection boxes on canvas
    function drawDetections(ctx, detections) {
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
    
    // Initialize video when DOM is ready
    initVideo();
});
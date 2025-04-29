/**
 * Utility functions for the Steganography application
 */

// Method information for display
const stegoMethods = {
    "DCT": {
        title: "Discrete Cosine Transform",
        description: "Hides data in frequency coefficients after DCT transform. Similar to JPEG compression, provides good balance between robustness and capacity.",
        strengthName: "Quantization Factor",
        defaultStrength: 10.0,
        minStrength: 1.0,
        maxStrength: 50.0,
        icon: "wave-square"
    },
    "Wavelet": {
        title: "Wavelet Transform",
        description: "Embeds data in wavelet coefficients, offering good localization in both spatial and frequency domains. More robust against certain types of image processing.",
        strengthName: "Threshold",
        defaultStrength: 30.0,
        minStrength: 5.0,
        maxStrength: 100.0,
        icon: "waveform"
    },
    "DFT": {
        title: "Discrete Fourier Transform",
        description: "Embeds data in the magnitude of frequency components. Offers good resistance to geometric transformations like rotation and scaling.",
        strengthName: "Strength",
        defaultStrength: 10.0,
        minStrength: 1.0,
        maxStrength: 50.0,
        icon: "wave"
    },
    "SVD": {
        title: "Singular Value Decomposition",
        description: "Modifies singular values of image blocks. Highly resistant to common image processing operations and compression.",
        strengthName: "Strength",
        defaultStrength: 10.0,
        minStrength: 1.0,
        maxStrength: 50.0,
        icon: "matrix"
    },
    "LBP": {
        title: "Local Binary Pattern",
        description: "Uses texture patterns for embedding data. This method leverages the texture descriptors and can be resilient to certain types of noise.",
        strengthName: "Strength",
        defaultStrength: 10.0,
        minStrength: 1.0,
        maxStrength: 30.0,
        icon: "pattern"
    }
};

/**
 * Get information about a steganography method
 * @param {string} methodName - The name of the method (DCT, Wavelet, etc.)
 * @returns {Object} Method information object
 */
function getStegoMethodInfo(methodName) {
    return stegoMethods[methodName] || null;
}

/**
 * Update UI elements based on selected steganography method
 * @param {string} methodName - The name of the method (DCT, Wavelet, etc.)
 * @param {Object} options - Optional parameters
 */
function updateStegoMethodUI(methodName, options = {}) {
    const methodInfo = getStegoMethodInfo(methodName);
    if (!methodInfo) return;
    
    // Update method description if element exists
    const descriptionEl = document.getElementById('method-info');
    if (descriptionEl) {
        descriptionEl.innerHTML = `<p><strong>${methodInfo.title}:</strong> ${methodInfo.description}</p>`;
    }
    
    // Update strength label if element exists
    const strengthLabelEl = document.getElementById('strength-label');
    if (strengthLabelEl) {
        strengthLabelEl.textContent = methodInfo.strengthName + ':';
    }
    
    // Update strength slider if element exists
    const strengthSliderEl = document.getElementById('strength');
    if (strengthSliderEl) {
        strengthSliderEl.min = methodInfo.minStrength;
        strengthSliderEl.max = methodInfo.maxStrength;
        strengthSliderEl.value = options.strength || methodInfo.defaultStrength;
    }
}

/**
 * Calculate estimated message capacity for an image
 * @param {HTMLImageElement} imageElement - The image element
 * @param {string} methodName - The steganography method
 * @returns {number} Estimated bit capacity
 */
function estimateMessageCapacity(imageElement, methodName) {
    if (!imageElement || !imageElement.width || !imageElement.height) return 0;
    
    const width = imageElement.width;
    const height = imageElement.height;
    
    // Different methods have different capacities
    switch (methodName) {
        case 'DCT':
            // For DCT, we use 8x8 blocks and store 1 bit per block
            return Math.floor(width / 8) * Math.floor(height / 8);
            
        case 'Wavelet':
            // For Wavelet, we use level-1 decomposition detail coefficients
            // Which gives us width/2 * height/2 coefficients
            return Math.floor(width / 2) * Math.floor(height / 2);
            
        case 'DFT':
            // For DFT, we can use selected frequency components
            // Typically mid-frequency regions, roughly width*height/16
            return Math.floor((width * height) / 16);
            
        case 'SVD':
            // For SVD, we use 8x8 blocks and store 1 bit per block
            return Math.floor(width / 8) * Math.floor(height / 8);
            
        case 'LBP':
            // For LBP, we use a subset of pixels
            return Math.floor((width * height) / 8);
            
        default:
            // Default conservative estimate
            return Math.floor((width * height) / 10);
    }
}

/**
 * Convert bits to character capacity
 * @param {number} bits - Number of available bits
 * @returns {number} - Estimated character capacity
 */
function bitsToCharCapacity(bits) {
    // Assuming UTF-8 encoding, average 8-16 bits per character
    return Math.floor(bits / 12); // Conservative estimate
}

/**
 * Preview an image and update capacity information
 * @param {File} file - Image file to preview
 * @param {string} previewElementId - ID of the image preview element
 * @param {string} methodName - Steganography method
 * @param {string} capacityElementId - ID of the capacity display element
 */
function previewImageAndCapacity(file, previewElementId, methodName, capacityElementId) {
    const preview = document.getElementById(previewElementId);
    const capacityEl = document.getElementById(capacityElementId);
    
    if (!preview || !file) return;
    
    const reader = new FileReader();
    
    reader.onload = function(e) {
        preview.src = e.target.result;
        preview.style.display = 'block';
        
        // If we need to calculate capacity, do it after the image loads
        if (capacityEl && methodName) {
            preview.onload = function() {
                const bitCapacity = estimateMessageCapacity(preview, methodName);
                const charCapacity = bitsToCharCapacity(bitCapacity);
                capacityEl.textContent = `Estimated Capacity: ~${charCapacity} characters`;
            };
        }
    };
    
    reader.readAsDataURL(file);
}

/**
 * Transform Domain Steganography - Frontend JavaScript
 * Provides interactive features for the web interface
 */

// Update strength label when slider changes
function updateStrengthLabel(value) {
    document.getElementById('strength-value').textContent = value;
}

// Preview image before upload
function previewImage(inputId, previewId) {
    const input = document.getElementById(inputId);
    const preview = document.getElementById(previewId);
    
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        
        reader.onload = function(e) {
            preview.src = e.target.result;
            preview.style.display = 'block';
        };
        
        reader.readAsDataURL(input.files[0]);
    }
}

// Character counter for message input
function countChars(textareaId, counterId) {
    const textarea = document.getElementById(textareaId);
    const counter = document.getElementById(counterId);
    const text = textarea.value;
    const charCount = text.length;
    let binaryLength;
    
    try {
        // Estimate binary length (accounting for Unicode)
        binaryLength = new TextEncoder().encode(text).length * 8;
    } catch (e) {
        // Fallback if TextEncoder is not supported
        binaryLength = charCount * 8;
    }
    
    counter.textContent = `${charCount} characters (approximately ${binaryLength} bits)`;
    
    // Visual indicator for message size
    if (charCount > 0) {
        counter.style.display = 'block';
    } else {
        counter.style.display = 'none';
    }
}

// Method selector UI update
function selectMethod(method, element) {
    // Update radio selection
    document.querySelector(`input[value="${method}"]`).checked = true;
    
    // Update UI
    document.querySelectorAll('.method-card').forEach(card => {
        card.classList.remove('selected', 'bg-blue-50', 'bg-green-50');
    });
    
    // Add appropriate class based on page
    const isEncode = window.location.pathname.includes('encode');
    element.classList.add('selected');
    element.classList.add(isEncode ? 'bg-blue-50' : 'bg-green-50');
    
    // Update method info text
    updateMethodInfo(method);
}

// Update method information display
function updateMethodInfo(method) {
    const methodInfo = document.getElementById('method-info');
    if (!methodInfo) return;
    
    switch(method) {
        case 'DCT':
            methodInfo.innerHTML = '<p><strong>DCT (Discrete Cosine Transform):</strong> Hides data in frequency coefficients. Similar to JPEG compression, provides good balance between robustness and capacity.</p>';
            break;
        case 'Wavelet':
            methodInfo.innerHTML = '<p><strong>Wavelet Transform:</strong> Embeds data in wavelet coefficients, offering good localization in spatial and frequency domains. More robust against certain types of processing.</p>';
            break;
        case 'DFT':
            methodInfo.innerHTML = '<p><strong>DFT (Discrete Fourier Transform):</strong> Embeds data in the magnitude of frequency components. Offers resistance to geometric transformations like rotation and scaling.</p>';
            break;
        case 'SVD':
            methodInfo.innerHTML = '<p><strong>SVD (Singular Value Decomposition):</strong> Modifies singular values of image blocks. Highly resistant to common image processing operations and compression.</p>';
            break;
        case 'LBP':
            methodInfo.innerHTML = '<p><strong>LBP (Local Binary Pattern):</strong> Uses texture patterns for embedding data. Leverages texture descriptors and can be resilient to certain types of noise.</p>';
            break;
    }
}

// Initialize interactive image comparison slider
function initComparisonSlider() {
    const slider = document.querySelector('.image-comparison-slider');
    if (!slider) return;
    
    const handle = slider.querySelector('.slider-handle');
    const container = slider.closest('.slider-container');
    let isDragging = false;
    
    // Mouse events
    handle.addEventListener('mousedown', startDragging);
    document.addEventListener('mousemove', moveSlider);
    document.addEventListener('mouseup', stopDragging);
    
    // Touch events for mobile
    handle.addEventListener('touchstart', startDragging);
    document.addEventListener('touchmove', moveSlider);
    document.addEventListener('touchend', stopDragging);
    
    function startDragging(e) {
        isDragging = true;
        e.preventDefault();
    }
    
    function moveSlider(e) {
        if (!isDragging) return;
        
        let clientX;
        if (e.type === 'touchmove') {
            clientX = e.touches[0].clientX;
        } else {
            clientX = e.clientX;
        }
        
        const containerRect = container.getBoundingClientRect();
        let position = (clientX - containerRect.left) / containerRect.width;
        
        // Limit position between 0 and 1
        position = Math.max(0, Math.min(1, position));
        
        slider.style.width = `${position * 100}%`;
    }
    
    function stopDragging() {
        isDragging = false;
    }
}

// Initialize when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize comparison sliders if present
    initComparisonSlider();
    
    // Set up character counters
    const messageTextarea = document.getElementById('secret_message');
    if (messageTextarea) {
        const counterElement = document.createElement('div');
        counterElement.id = 'char-counter';
        counterElement.className = 'text-xs text-gray-500 mt-1';
        counterElement.style.display = 'none';
        messageTextarea.parentNode.insertBefore(counterElement, messageTextarea.nextSibling);
        
        messageTextarea.addEventListener('input', () => countChars('secret_message', 'char-counter'));
    }
});

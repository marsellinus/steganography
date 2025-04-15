/**
 * Utility functions for the Steganography application
 */

// Method information for display
const methodInfo = {
    DCT: {
        title: "DCT (Discrete Cosine Transform)",
        description: "Hides data in frequency coefficients. This method is similar to JPEG compression and provides good balance between robustness and capacity.",
        strengths: "Good resistance to compression and filtering",
        weaknesses: "May be sensitive to cropping and rotation",
        recommendedUses: "Text hiding in photographic images"
    },
    Wavelet: {
        title: "Wavelet Transform",
        description: "Embeds data in wavelet coefficients, offering good localization in both spatial and frequency domains. More robust against certain types of image processing.",
        strengths: "Good localization in both space and frequency domains",
        weaknesses: "More complex implementation",
        recommendedUses: "Robust hiding in natural images"
    },
    DFT: {
        title: "DFT (Discrete Fourier Transform)",
        description: "Embeds data in the magnitude of frequency components. Offers good resistance to geometric transformations like rotation and scaling.",
        strengths: "Resistant to geometric transformations",
        weaknesses: "May affect image quality more visibly",
        recommendedUses: "Applications where geometric transforms might occur"
    },
    SVD: {
        title: "SVD (Singular Value Decomposition)",
        description: "Modifies singular values of image blocks. Highly resistant to common image processing operations and compression.",
        strengths: "Very resistant to compression and filtering",
        weaknesses: "Lower capacity compared to other methods",
        recommendedUses: "High-security applications where robustness is critical"
    },
    LBP: {
        title: "LBP (Local Binary Pattern)",
        description: "Uses texture patterns for embedding data. This method leverages the texture descriptors and can be resilient to certain types of noise.",
        strengths: "Good for textured regions",
        weaknesses: "Less effective in smooth regions",
        recommendedUses: "Images with significant texture content"
    }
};

/**
 * Update the method information display
 * @param {string} method - The selected method (DCT, Wavelet, DFT, SVD, or LBP)
 * @param {string} elementId - The ID of the element to update
 */
function updateMethodInfo(method, elementId) {
    const infoElement = document.getElementById(elementId);
    if (!infoElement || !methodInfo[method]) return;
    
    const info = methodInfo[method];
    infoElement.innerHTML = `
        <p><strong>${info.title}:</strong> ${info.description}</p>
        <div class="mt-2 text-xs">
            <p><strong>Strengths:</strong> ${info.strengths}</p>
            <p><strong>Weaknesses:</strong> ${info.weaknesses}</p>
            <p><strong>Recommended Uses:</strong> ${info.recommendedUses}</p>
        </div>
    `;
}

/**
 * Copy text to clipboard
 * @param {string} text - The text to copy
 * @returns {Promise} - Resolves when copying is complete
 */
function copyToClipboard(text) {
    return navigator.clipboard.writeText(text)
        .then(() => {
            return true;
        })
        .catch(err => {
            console.error('Could not copy text: ', err);
            return false;
        });
}

/**
 * Convert text to binary representation
 * @param {string} text - The text to convert
 * @returns {string} - Space-separated binary representation
 */
function textToBinary(text) {
    return text.split('').map(char => {
        return char.charCodeAt(0).toString(2).padStart(8, '0');
    }).join(' ');
}

/**
 * Preview an image before upload
 * @param {HTMLInputElement} input - The file input element
 * @param {string} previewId - The ID of the image element for preview
 */
function previewImage(input, previewId) {
    const preview = document.getElementById(previewId);
    if (!preview) return;
    
    const file = input.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            preview.src = e.target.result;
            preview.style.display = 'block';
        };
        reader.readAsDataURL(file);
    } else {
        preview.src = '';
        preview.style.display = 'none';
    }
}

document.addEventListener("DOMContentLoaded", function () {
    const filterDropdown = document.getElementById("filter");
    const sortDropdown = document.getElementById("sort");
    if (filterDropdown && sortDropdown) {
        filterDropdown.addEventListener("change", function () {
            document.getElementById("filterForm").submit();
        });

        sortDropdown.addEventListener("change", function () {
            document.getElementById("filterForm").submit();
        });
    }

    const selectAllCheckbox = document.getElementById("select-all");
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener("change", function () {
            const checkboxes = document.querySelectorAll("input[name='selectedIds']");
            checkboxes.forEach(checkbox => {
                checkbox.checked = selectAllCheckbox.checked;
            });
        });
    }

    // Clear search button functionality
    const clearSearchBtn = document.querySelector('.ClearSearchBtn');
    if (clearSearchBtn) {
        clearSearchBtn.addEventListener('click', function(e) {
            e.preventDefault();
            const searchInput = document.getElementById('search');
            searchInput.value = '';
            document.getElementById('filterForm').submit();
        });
    }
});


async function analyzeImage(imageId, imageUrl) {
    // Fetch the image from the server
    const response = await fetch(imageUrl);
    const imageBlob = await response.blob();

    // Create a FormData object and append the image
    const formData = new FormData();
    formData.append('file', imageBlob, 'image.jpg');

    // Send the image to the analysis endpoint
    const predictionResponse = await fetch(`/analyzeImage/${imageId}/`, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),  // Include the CSRF token
        },
    });

    // Parse the prediction result
    const prediction = await predictionResponse.json();

    // Display the prediction result
    if (prediction.result) {
        document.getElementById(`prediction-${imageId}`).innerText = `Prediction: ${prediction.result}`;
    } else if (prediction.error) {
        document.getElementById(`prediction-${imageId}`).innerText = `Error: ${prediction.error}`;
    }
}

// Helper function to get the CSRF token from cookies
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.startsWith(name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
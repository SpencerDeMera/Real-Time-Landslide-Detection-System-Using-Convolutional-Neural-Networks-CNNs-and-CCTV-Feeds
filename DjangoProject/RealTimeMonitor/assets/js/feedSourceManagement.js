document.addEventListener("DOMContentLoaded", function () {
    // Initialize all as collapsed
    document.querySelectorAll('.route-content').forEach(content => {
        content.style.display = 'none';
    });

    // Toggle dropdowns
    document.querySelectorAll('.collapsible-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const content = this.closest('.route-header').nextElementSibling;
            const arrow = this.querySelector('.arrow');

            if (content.style.display === 'block') {
                content.style.display = 'none';
                arrow.textContent = '▼';
            } else {
                content.style.display = 'block';
                arrow.textContent = '▲';
            }
        });
    });

    document.getElementById('analyzeSelectedBtn').addEventListener('click', async function() {
        const btn = this;
        const selectedIds = Array.from(
            document.querySelectorAll('input[name="selectedIds"]:checked')
        ).map(el => el.value);

        if (!selectedIds.length) {
            alert('Please select at least one image');
            return;
        }

        const hours = document.getElementById("analysisDuration").value;

        try {
            // Disable button during processing
            btn.disabled = true;
            btn.textContent = 'Analyzing...';

            // Send request to server
            const response = await fetch('/bulkAnalyzeImages/', {
                method: 'POST',
                body: JSON.stringify({ selectedIds, hours }),
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken'),
                }
            });

            if (!response.ok) {
                throw new Error(await response.text());
            }

            // Redirect when done
            window.location.href = '/analyze/';

        }
        catch (error) {
            console.error('Error:', error);
            alert('Analysis failed: ' + error.message);
        }
        finally {
            btn.disabled = false;
            btn.textContent = 'Analyze Selected';
        }
    });

    // Select all for specific route
    document.querySelectorAll('.select-all-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const routeSlug = this.dataset.route;
            document.querySelectorAll(`.${routeSlug}-checkbox`).forEach(checkbox => {
                checkbox.checked = true;
            });
        });
    });

    // Deselect all for specific route
    document.querySelectorAll('.deselect-all-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const routeSlug = this.dataset.route;
            document.querySelectorAll(`.${routeSlug}-checkbox`).forEach(checkbox => {
                checkbox.checked = false;
            });
        });
    });
});

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
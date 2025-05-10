document.addEventListener("DOMContentLoaded", function () {
    const storedErrors = JSON.parse(localStorage.getItem('analysisErrors'));
    if (storedErrors && storedErrors.length > 0) {

        const errContainer = document.getElementById('AnalysisErrorsContainer');
        if (errContainer && storedErrors.length > 0) {
            let errHTML = `<ul>`;
            storedErrors.forEach(err => {
                errHTML += `<li>${err}</li>`;
            });
            errHTML += `</ul>`;

            errContainer.innerHTML = errHTML;

            errContainer.style.display = 'block';
        }

        localStorage.removeItem('analysisErrors'); // Clear after showing
    }

    fetch('/api/getGroupedFeedSources/')
        .then(response => response.json())
        .then(data => {
            const container = document.getElementById('FeedSourceRouteGroups');
            const grouped = data.groupedFeedSources;

            if (grouped) {
                for (const route in grouped) {
                    const routeSlug = route ? route.toLowerCase().replace(/\s+/g, '-') : 'unknown-route';

                    let html = `
                        <div class="route-group">
                            <div class="route-header">
                                <button type="button" class="collapsible-btn">
                                    ${route || "Unknown Route"}
                                    <span class="arrow">▼</span>
                                </button>
                                <div class="route-controls">
                                    <button type="button" class="select-all-btn" data-route="${routeSlug}">
                                        Select All
                                    </button>
                                    <button type="button" class="deselect-all-btn" data-route="${routeSlug}">
                                        Deselect All
                                    </button>
                                </div>
                            </div>
                            <div class="route-content" style="display: none;">
                                <table>
                                    <thead>
                                        <tr>
                                            <th>Select</th>
                                            <th>Source Name</th>
                                            <th>County</th>
                                            <th>Nearby Place</th>
                                            <th>Last Poll Date</th>
                                            <th>Status</th>
                                        </tr>
                                    </thead>
                                    <tbody>`;

                    grouped[route].forEach(fs => {
                        const isPolling = fs.isPolling === true || fs.isPolling === "true"; // normalize
                        const statusClass = fs.isPolling ? 'active-status' : 'inactive-status';
                        const statusText = fs.isPolling ? 'Active' : 'Inactive';
                        const date = new Date(fs.lastPollDate);
                        const formattedDate = date.toISOString().slice(0, 19).replace('T', ' ');

                        html += `
                            <tr>
                                <td>
                                    <input type="checkbox" name="selectedIds" value="${fs.id}" class="route-checkbox ${routeSlug}-checkbox">
                                </td>
                                <td>${fs.streamSourceName}</td>
                                <td>${fs.county}</td>
                                <td>${fs.nearbyPlace}</td>
                                <td>${formattedDate}</td>
                                <td><span class="${statusClass}">${statusText}</span></td>
                            </tr>`;
                    });

                    html += `
                                    </tbody>
                                </table>
                            </div>
                        </div>`;

                    container.insertAdjacentHTML('beforeend', html);
                }
            }
            else {
                let html = `
                    <div class="weather-alert-container" style="display:flex; justify-content:center; align-items:center;">
                        <div class="weather-alert-title" style="text-align:center;">
                            <p>No Feed Sources Downloaded. See Home Page to Scrape Sources.</p>
                        </div>
                    </div>
                `;

                container.insertAdjacentHTML('beforeend', html);
            }

            document.querySelectorAll('.collapsible-btn').forEach(btn => {
                btn.addEventListener('click', function () {
                    const content = this.closest('.route-header').nextElementSibling;
                    const arrow = this.querySelector('.arrow');

                    const isVisible = content.style.display === 'block';
                    content.style.display = isVisible ? 'none' : 'block';
                    arrow.textContent = isVisible ? '▼' : '▲';
                });
            });

            document.querySelectorAll('.select-all-btn').forEach(btn => {
                btn.addEventListener('click', function () {
                    const routeSlug = this.dataset.route;
                    document.querySelectorAll(`.${routeSlug}-checkbox`).forEach(checkbox => {
                        checkbox.checked = true;
                    });
                });
            });

            document.querySelectorAll('.deselect-all-btn').forEach(btn => {
                btn.addEventListener('click', function () {
                    const routeSlug = this.dataset.route;
                    document.querySelectorAll(`.${routeSlug}-checkbox`).forEach(checkbox => {
                        checkbox.checked = false;
                    });
                });
            });

            if (document.getElementById('Inventory-Infinite-LoadingContainer')) {
                document.getElementById('Inventory-Infinite-LoadingContainer').style.display = "none";
            }
        })
        .catch(error => {
            console.error('Error loading feed sources:', error);
        });

    document.getElementById('analyzeSelectedBtn').addEventListener('click', async function () {
        const btn = this;
        const selectedIds = Array.from(document.querySelectorAll('input[name="selectedIds"]:checked')).map(el => el.value);

        if (!selectedIds.length) {
            alert('Please select at least one image');
            return;
        }

        const hours = document.getElementById("analysisDuration").value;

        try {
            btn.disabled = true;
            btn.textContent = 'Analyzing...';

            const response = await fetch('/bulkAnalyzeImages/', {
                method: 'POST',
                body: JSON.stringify({ selectedIds, hours }),
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken'),
                }
            });

            const data = await response.json();  // Parse JSON response

            if (!response.ok || !data.success) {
                localStorage.setItem('analysisErrors', JSON.stringify(data.errors || [data.error]));
            }

            window.location.href = '/analyze/';
        } catch (error) {
            console.error('Error:', error);
            alert('Analysis failed: ' + error.message);
        } finally {
            btn.disabled = false;
            btn.textContent = 'Analyze Selected';
        }
    });
});

// Helper function to get CSRF token
function getCookie(name) {
    const cookies = document.cookie.split(';').map(c => c.trim());
    for (const cookie of cookies) {
        if (cookie.startsWith(name + '=')) {
            return decodeURIComponent(cookie.slice(name.length + 1));
        }
    }
    return null;
}

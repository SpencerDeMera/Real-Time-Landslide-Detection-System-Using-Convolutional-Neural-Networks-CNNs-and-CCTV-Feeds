document.addEventListener('DOMContentLoaded', function () {
    fetch('https://api.weather.gov/alerts/active?area=CA')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            const alerts = data.features;

            let infoContainer = document.getElementById('WeatherInfoCards');

            if (alerts.length === 0) {
                infoContainer.innerHTML += `
                    <div class="weather-alert-container" style="display:flex; justify-content:center; align-items:center;">
                        <div class="weather-alert-title" style="text-align:center;">
                            <p>No NOAA/NWS alerts issued for California at this time</p>
                        </div>
                    </div>
                `;
            }
            else {
                alerts.forEach(alert => {
                    let headline = alert.properties.headline;
                    let NWSZones = alert.properties.geocode.UGC;
                    let mainMessage = alert.properties.description;
                    let event = alert.properties.event;

                    fetch('/api/checkIfZoneIsValidForCounty/', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': getCookie('csrftoken'), // Include if using CSRF protection
                        },
                        body: JSON.stringify({
                            zoneCodes: NWSZones
                        })
                    })
                        .then(response => {
                            if (!response.ok) {
                                throw new Error('Network response was not ok');
                            }
                            return response.json(); // Only read the response once here
                        })
                        .then(zoneData => {
                            let isValid = zoneData.isValid;

                            if (isValid) {
                                infoContainer.innerHTML += `
                                    <div class="weather-alert-container">
                                        <div class="weather-alert-title">
                                            <div class="weatherIcon" id="alert_icon">
                                                <i class="fa-solid fa-triangle-exclamation"></i>
                                            </div>
                                            <p>WEATHER ALERT: ${event}</p>
                                        </div>
                                        <div class="weather-alert-headline">
                                            <p>${headline}</p>
                                        </div>
                                        <div class="wetaher-info-message">
                                            <p>${mainMessage}</p>
                                        </div>
                                    </div>
                                `;
                            }
                        })
                        .catch(error => {
                            console.error('Error loading feed sources:', error);
                        });
                });

                if (infoContainer.innerHTML === '') {
                    infoContainer.innerHTML += `
                        <div class="weather-alert-container" style="display:flex; justify-content:center; align-items:center;">
                            <div class="weather-alert-title" style="text-align:center;">
                                <p>No NOAA/NWS alerts issued for coverage areas at this time</p>
                            </div>
                        </div>
                    `;
                }
            }

            if (document.getElementById('Weather-Infinite-LoadingContainer')) {
                document.getElementById('Weather-Infinite-LoadingContainer').style.display = "none";
            }
        })
        .catch(error => {
            console.error('Failed to fetch alerts:', error);
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

document.addEventListener('DOMContentLoaded', function() {
   fetch('/api/getPositivePredictedMediaFiles')
       .then(response => response.json())
       .then(data => {
            const container = document.getElementById('MediaFilesWAnomalies');
            let html = '';

            if (data.mediaFiles.length === 0) {
                html = `
                    <div class="weather-alert-container" style="display:flex; justify-content:center; align-items:center;">
                        <div class="weather-alert-title" style="text-align:center;">
                            <p>No current road anomalies</p>
                        </div>
                    </div>
                `;
            }
            else {
                html = `
                    <div class="media-group">
                    <div class="media-content">
                    <table>
                    <thead>
                    <tr>
                    <th>Image</th>
                    <th>Location Name</th>
                    <th>Prediction</th>
                    <th>Uploaded Date</th>
                    <th>Manual Upload</th>
                    </tr>
                    </thead>
                    <tbody>`;

                data.mediaFiles.forEach(file => {
                    const formattedDate = new Date(file.uploadedDate)
                        .toISOString()
                        .slice(0, 19)
                        .replace('T', ' ');

                    const imageUrl = file.mediaFile; // assumes it's already a full URL or handled by MEDIA_URL

                    html += `
                        <tr>
                            <td><img class="ImageFile" src="/media/${imageUrl}" alt="Media" width="100"></td>
                            <td>${file.locationName || 'N/A'}</td>
                            <td>${file.predictionString || '1'}</td>
                            <td>${formattedDate}</td>
                            <td>${file.isManualUpload ? 'Yes' : 'No'}</td>
                        </tr>`;
                });

                html += `
                    </tbody>
                    </table>
                    </div>
                    </div>`;
            }

            if (document.getElementById('Anomalies-Infinite-LoadingContainer')) {
                document.getElementById('Anomalies-Infinite-LoadingContainer').style.display = "none";
            }

            container.insertAdjacentHTML('beforeend', html);
        })
        .catch(error => {
            console.error('Error loading feed sources:', error);
        });

   fetch('/api/getPollingFeedSources/')
        .then(response => response.json())
        .then(data => {
            const container = document.getElementById('FeedSourcesPolling');
            let html = '';

            if (data.feedSources.length === 0) {
                html = `
                    <div class="weather-alert-container" style="display:flex; justify-content:center; align-items:center;">
                        <div class="weather-alert-title" style="text-align:center;">
                            <p>No camera feeds currently polling</p>
                        </div>
                    </div>
                `;
            }
            else {
                html = `
                    <div class="route-group">
                    <div class="route-content">
                    <table>
                    <thead>
                    <tr>
                    <th>Camera Name</th>
                    <th>County</th>
                    <th>Nearby Place</th>
                    <th>Last Poll Date</th>
                    <th>Status</th>
                    </tr>
                    </thead>
                    <tbody>`;

                data.feedSources.forEach(fs => {
                    const statusClass = fs.isPolling ? 'active-status' : 'inactive-status';
                    const statusText = fs.isPolling ? 'Active' : 'Inactive';
                    const date = new Date(fs.lastPollDate);
                    const formattedDate = date.toISOString().slice(0, 19).replace('T', ' ');

                    html += `
                        <tr>
                            <td>${fs.streamSourceName}</td>
                            <td>${fs.county}</td>
                            <td>${fs.nearbyPlace}</td>
                            <td>${formattedDate}</td>
                            <td><span class="${statusClass}">${statusText}</span></td>
                        </tr>
                    `;
                });

                html += `
                    </tbody>
                    </table>
                    </div>
                    </div>`;
            }

            if (document.getElementById('Polling-Infinite-LoadingContainer')) {
                document.getElementById('Polling-Infinite-LoadingContainer').style.display = "none";
            }

            container.insertAdjacentHTML('beforeend', html);
        })
        .catch(error => {
            console.error('Error loading feed sources:', error);
        });
});
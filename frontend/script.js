document.addEventListener('DOMContentLoaded', () => {
    const clinicsListDiv = document.getElementById('clinics-list');
    // NOTE: 'web' is the service name in docker-compose.yml,
    // Docker's internal DNS allows resolving it to the web container's IP.
    // Port 8000 is the port Gunicorn is listening on inside the 'web' container.
    const API_URL = 'http://localhost:8008/api/clinics/';

    // Function to fetch clinics from the API
    async function fetchClinics() {
        try {
            const response = await fetch(API_URL);
            if (!response.ok) {
                // Handle non-2xx status codes
                const errorText = await response.text();
                throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
            }
            const data = await response.json();
            displayClinics(data.results); // Assuming DRF pagination returns results in 'results'
        } catch (error) {
            console.error('Error fetching clinics:', error);
            clinicsListDiv.innerHTML = '<p class="text-red-500">Failed to load clinics. Please try again later.</p>';
        }
    }

    // Function to display clinics in the HTML
    function displayClinics(clinics) {
        clinicsListDiv.innerHTML = ''; // Clear loading message

        if (clinics.length === 0) {
            clinicsListDiv.innerHTML = '<p class="text-gray-600">No clinics found.</p>';
            return;
        }

        clinics.forEach(clinic => {
            const clinicCard = `
                <div class="bg-white p-6 rounded-lg shadow-md">
                    <h2 class="text-xl font-semibold mb-2">${clinic.name}</h2>
                    <p class="text-gray-700 mb-1"><strong>Location:</strong> ${clinic.location}</p>
                    <p class="text-gray-700 mb-1"><strong>Address:</strong> ${clinic.address}</p>
                    <p class="text-gray-700"><strong>Phone:</strong> ${clinic.phone}</p>
                    ${clinic.is_active ? '<span class="mt-3 inline-block bg-green-200 text-green-800 text-xs px-2 rounded-full uppercase font-semibold tracking-wide">Active</span>' : '<span class="mt-3 inline-block bg-red-200 text-red-800 text-xs px-2 rounded-full uppercase font-semibold tracking-wide">Inactive</span>'}
                </div>
            `;
            clinicsListDiv.innerHTML += clinicCard;
        });
    }

    // Fetch clinics when the page loads
    fetchClinics();
});

document.addEventListener('DOMContentLoaded', () => {
    const loginSection = document.getElementById('login-section');
    const contentSection = document.getElementById('content-section');
    const loginForm = document.getElementById('login-form');
    const loginMessageDiv = document.getElementById('login-message');

    const clinicsListDiv = document.getElementById('clinics-list');
    const doctorsListDiv = document.getElementById('doctors-list');
    const servicesListDiv = document.getElementById('services-list');

    // Base API URL - Use localhost and the HOST port mapped to the web service
    // Assuming your web service is mapped to port 8008 on your host
    const API_BASE_URL = 'http://localhost:8008/api/';
    // Django Login URL - Use localhost and the HOST port
    const LOGIN_URL = 'http://localhost:8008/login/'; // Ensure this URL is correct for your login view
    // URL for fetching CSRF token - Use localhost and the HOST port
    const CSRF_URL = 'http://localhost:8008/csrf/'; // URL for the new CSRF view

    // Function to get the CSRF token from the cookie
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                // Does this cookie string begin with the name we want?
                if (cookie.startsWith(name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Fetch CSRF token on page load
    async function fetchCsrfToken() {
        try {
            await fetch(CSRF_URL, { credentials: 'include' });
            console.log('CSRF token fetched and cookie set.');
        } catch (error) {
            console.error('Error fetching CSRF token:', error);
            loginMessageDiv.textContent = 'Could not fetch security token. Login may not work.';
            loginMessageDiv.className = 'mb-4 text-center text-sm text-orange-600';
        }
    }

    // --- Handle Login ---
    loginForm.addEventListener('submit', async (event) => {
        event.preventDefault(); // Prevent default form submission

        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        const csrftoken = getCookie('csrftoken'); // Get the CSRF token from the cookie

        loginMessageDiv.textContent = 'Logging in...';
        loginMessageDiv.className = 'mb-4 text-center text-sm text-gray-600'; // Reset class

        // Ensure we have a CSRF token before attempting login
        if (!csrftoken) {
             loginMessageDiv.textContent = 'CSRF token not available. Please refresh the page.';
             loginMessageDiv.className = 'mb-4 text-center text-sm text-red-600';
             console.error('CSRF token is missing.');
             return; // Stop the login process
        }


        try {
            const response = await fetch(LOGIN_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken, // Include the CSRF token in the headers
                },
                body: JSON.stringify({ username, password }),
                credentials: 'include',
            });

            // Check if the response is successful (status code 2xx)
            if (response.ok) {
                // Assuming successful login sets a session cookie or returns a token
                // In a real app, you'd handle the cookie or token here and store it
                // for subsequent authenticated requests.
                loginMessageDiv.textContent = 'Login successful!';
                loginMessageDiv.className = 'mb-4 text-center text-sm text-green-600';

                // Hide login, show content
                loginSection.classList.add('hidden');
                contentSection.classList.remove('hidden');

                // Fetch and display data after successful login
                // These might still fail if they require authentication
                // and the session cookie isn't automatically sent/handled correctly
                fetchClinics(); // Might be public
                fetchDoctors(); // Might be public
                fetchServices(); // Might be public

            } else {
                // Handle login errors (e.g., invalid credentials, CSRF failure response)
                // Note: A 403 Forbidden due to CSRF might return an HTML page,
                // so response.json() might fail.
                let errorMessage = 'Login failed.';
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.detail || errorData.error || errorMessage;
                } catch (e) {
                    // If JSON parsing fails, check status and use a generic message
                    if (response.status === 403) {
                         errorMessage = 'Login failed: CSRF verification failed. Ensure cookies are enabled and try again.';
                    } else {
                         errorMessage = `Login failed with status: ${response.status}`;
                    }
                }

                loginMessageDiv.textContent = errorMessage;
                loginMessageDiv.className = 'mb-4 text-center text-sm text-red-600';
            }
        } catch (error) {
            console.error('Error during login fetch:', error);
            loginMessageDiv.textContent = 'An error occurred during login.';
            loginMessageDiv.className = 'mb-4 text-center text-sm text-red-600';
        }
    });


    // --- Fetch and Display Clinics ---
    async function fetchClinics() {
        clinicsListDiv.innerHTML = '<p class="text-gray-500">Loading clinics...</p>'; // Reset loading state
        try {
            // NOTE: For protected endpoints, you would need to include authentication credentials
            // (e.g., session cookie or Authorization: Token <token>) in the headers.
            const response = await fetch(`${API_BASE_URL}clinics/`);
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
            }
            const data = await response.json();
            displayClinics(data.results); // Assuming DRF pagination
        } catch (error) {
            console.error('Error fetching clinics:', error);
            clinicsListDiv.innerHTML = '<p class="text-red-500">Failed to load clinics.</p>';
        }
    }

    function displayClinics(clinics) {
        clinicsListDiv.innerHTML = ''; // Clear loading message
         if (clinics.length === 0) {
            clinicsListDiv.innerHTML = '<p class="text-gray-600">No clinics found.</p>';
            return;
        }

        clinics.forEach(clinic => {
            const clinicCard = `
                <div class="bg-white p-6 rounded-lg shadow-md">
                    <h3 class="text-xl font-semibold mb-2">${clinic.name}</h3>
                    <p class="text-gray-700 mb-1"><strong>Location:</strong> ${clinic.location}</p>
                    <p class="text-gray-700 mb-1"><strong>Address:</strong> ${clinic.address}</p>
                    <p class="text-gray-700"><strong>Phone:</strong> ${clinic.phone}</p>
                    ${clinic.is_active ? '<span class="mt-3 inline-block bg-green-200 text-green-800 text-xs px-2 rounded-full uppercase font-semibold tracking-wide">Active</span>' : '<span class="mt-3 inline-block bg-red-200 text-red-800 text-xs px-2 rounded-full uppercase font-semibold tracking-wide">Inactive</span>'}
                </div>
            `;
            clinicsListDiv.innerHTML += clinicCard;
        });
    }

    // --- Fetch and Display Doctors ---
    async function fetchDoctors() {
         doctorsListDiv.innerHTML = '<p class="text-gray-500">Loading doctors...</p>'; // Reset loading state
        try {
             // NOTE: For protected endpoints, you would need to include authentication credentials
            // (e.g., session cookie or Authorization: Token <token>) in the headers.
            const response = await fetch(`${API_BASE_URL}doctors/`);
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
            }
            const data = await response.json();
            displayDoctors(data.results); // Assuming DRF pagination
        } catch (error) {
            console.error('Error fetching doctors:', error);
            doctorsListDiv.innerHTML = '<p class="text-red-500">Failed to load doctors.</p>';
        }
    }

    function displayDoctors(doctors) {
         doctorsListDiv.innerHTML = ''; // Clear loading message
         if (doctors.length === 0) {
            doctorsListDiv.innerHTML = '<p class="text-gray-600">No doctors found.</p>';
            return;
        }

        doctors.forEach(doctor => {
            const doctorCard = `
                <div class="bg-white p-6 rounded-lg shadow-md">
                    <h3 class="text-xl font-semibold mb-2">${doctor.user.first_name} ${doctor.user.last_name}</h3>
                    <p class="text-gray-700"><strong>Specialization:</strong> ${doctor.specialization}</p>
                    <p class="text-gray-700"><strong>Contact:</strong> ${doctor.user.email || 'N/A'}</p>
                    </div>
            `;
            doctorsListDiv.innerHTML += doctorCard;
        });
    }

    // --- Fetch and Display Services ---
    async function fetchServices() {
        servicesListDiv.innerHTML = '<p class="text-gray-500">Loading services...</p>'; // Reset loading state
        try {
            // NOTE: For protected endpoints, you would need to include authentication credentials
            // (e.g., session cookie or Authorization: Token <token>) in the headers.
            const response = await fetch(`${API_BASE_URL}services/`);
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
            }
            const data = await response.json();
            displayServices(data.results); // Assuming DRF pagination
        } catch (error) {
            console.error('Error fetching services:', error);
            servicesListDiv.innerHTML = '<p class="text-red-500">Failed to load services.</p>';
        }
    }

    function displayServices(services) {
        servicesListDiv.innerHTML = ''; // Clear loading message
        if (services.length === 0) {
            servicesListDiv.innerHTML = '<p class="text-gray-600">No services found.</p>';
            return;
        }

        services.forEach(service => {
            const serviceCard = `
                <div class="bg-white p-6 rounded-lg shadow-md">
                    <h3 class="text-xl font-semibold mb-2">${service.name}</h3>
                    <p class="text-gray-700 mb-1"><strong>Type:</strong> ${service.type}</p>
                    <p class="text-gray-700"><strong>Duration:</strong> ${service.duration_minutes} minutes</p>
                    </div>
            `;
            servicesListDiv.innerHTML += serviceCard;
        }
    );
    }

    // --- Initial Setup ---
    // Fetch CSRF token first
    fetchCsrfToken();

    // Initially, only display the login section
    loginSection.classList.remove('hidden');
    contentSection.classList.add('hidden');

    // Data fetching is now triggered after successful login


});

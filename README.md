# Island Dental Booking System

A web-based booking and management system for **Island Dental**, a chain of dental clinics in the Maldives.

## Project Overview

The **Island Dental Booking System** provides a comprehensive solution for managing dental clinic operations, from appointment scheduling and doctor rostering to service pricing and reporting. The system emphasizes **role-based access control** to ensure data security and appropriate functionality for different user types.

## Key Features

- Appointment booking and management  
- Doctor roster management  
- Service and pricing management  
- Room allocation with special rules for surgery rooms  
- Comprehensive reporting (utilization, revenue, doctor performance, service demand)  
- Role-based access control (Customer, Doctor, Administrative Officer, Manager, System Admin)

## System Architecture

The system is built using the **Django** framework with a **RESTful API** backend and customizable admin interfaces.

- **Backend:** Django, Django REST Framework  
- **Database:** SQLite (development) → PostgreSQL (recommended for production)  
- **Frontend:** Uses Django's template engine for rendering HTML

## User Roles and Access

The system implements robust **role-based access control** with five distinct user roles:

| **Role**                | **Access URL**                         | **Credentials**            | **Responsibilities**                                                                                                                                                                                                      |
|-------------------------|----------------------------------------|----------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Customer                | `http://127.0.0.1:8000/customer/`       | `customer/customer123`     | Book dental appointments, view personal appointment history, cancel confirmed appointments, browse available clinics, doctors, and services.                                                                               |
| Doctor                  | `http://127.0.0.1:8000/doctor/`         | `doctor1/doctor1123`       | View their assigned appointments, see their roster and work schedule, update appointment status (completed, no-show), view patient information for scheduled appointments.                                                 |
| Administrative Officer  | `http://127.0.0.1:8000/officer/`        | `officer/officer123`       | Manage all appointments in the system, create, modify, and cancel appointments; manage doctor rosters and schedules; view and manage clinics, rooms, and services.                                                         |
| Manager                 | `http://127.0.0.1:8000/manager/`        | `manager/manager123`       | Complete system access and management, generate reports (revenue, appointment utilization), manage users, clinics, rooms, doctors, and services; set pricing for services based on shift.                                  |
| System Admin            | `http://127.0.0.1:8000/admin/`          | `admin/admin123`           | Full Django admin access, technical administration of the system, manage user accounts and permissions, configure system settings.                                                                                         |

## Database Model (Schema)

*(Insert an image or diagram of your database schema here.)*

Key models include:
- `CustomUser`  
- `Clinic`  
- `Room`  
- `Doctor`  
- `Service`  
- `Price`  
- `Roster`  
- `Appointment`  
- `Report`

Relationships:  
- **Appointments** are linked to **Customers**, **Doctors**, **Clinics**, and **Services**  
- **Doctor rotations** are managed through the **Roster** model  
- **Prices** are tied to **Services** and **Shifts**

## API Endpoints

The system exposes a RESTful API for data access and manipulation. Common endpoints include:

- `GET /api/clinics/`  
  → List clinics  
- `POST /api/clinics/`  
  → Create a new clinic (requires Manager/Admin)  
- `GET /api/clinics/{id}/`  
  → Retrieve a specific clinic  
- `PUT /api/clinics/{id}/`  
  → Update a clinic (requires Manager/Admin)  
- `DELETE /api/clinics/{id}/`  
  → Delete a clinic (requires Manager/Admin)  
- `GET /api/rooms/`  
  → List rooms  
- `GET /api/doctors/`  
  → List doctors  
- `GET /api/services/`  
  → List services  
- `GET /api/prices/`  
  → List service prices  
- `GET /api/rosters/`  
  → List doctor rosters  
- `GET /api/appointments/`  
  → List appointments  
- `GET /api/reports/`  
  → List or generate reports  
- `GET /api/doctors/{id}/availability/?date=YYYY-MM-DD`  
  → Check doctor availability for a given date

### Example API Call (Checking Doctor Availability)

```http
GET /api/doctors/1/availability/?date=2025-03-22
```

### Example Response:

```json
{
    "doctor": "Dr. John Doe (General Dentistry)",
    "date": "2025-03-22",
    "available_shifts": [
        "MORNING"
    ]
}
```

## Business Rules

### 1. Scheduling
- No service available on Fridays.
- Surgery rooms are not available during evening shifts (after 17:00).
- Each clinic has a maximum capacity of 10 patients per shift.

### 2. Pricing
- Service prices vary based on the shift (Morning, Afternoon, Evening).

### 3. Clinic Structure
- Each clinic has 3 rooms (1 surgery room, 2 normal rooms).

### 4. Doctor Rotation
- Each clinic has a rotation of 12 dentists assigned to it.
- Doctors rotate across the 3 clinics every 5 days in groups.

---

## Installation and Setup

### 1. Clone the repository:

```bash
git clone https://github.com/Rayyan011/DentalPrototype
cd DentalPrototype
```

### 2. Create a virtual environment and activate it:

```bash
python -m venv venv
# On Linux/macOS:
source venv/bin/activate 
# On Windows:
venv\Scripts\activate
```

### 3. Install dependencies:

```bash
pip install -r requirements.txt
```

### 4. Apply migrations:

```bash
python manage.py migrate
```

### 5. Create a superuser:

```bash
python manage.py createsuperuser
```

### 6. Run the development server:

```bash
python manage.py runserver
# Or if port 8000 is in use:
python manage.py runserver 8080
```

### 7. Access the application at:

- http://127.0.0.1:8000/
- or http://127.0.0.1:8080/

---

## Setup Commands

Several management commands are provided for initial setup and data population:

```bash
# Set up the complete system with users, permissions, and test data
python manage.py setup_system

# Set up the clinic locations, rooms, and doctor rotations
python manage.py setup_clinic_rotation --days 30
```

---

## Doctor Rotation Implementation

The `setup_clinic_rotation` management command configures the doctor rotation.

### 1. Distribution:
- 36 doctors are grouped and distributed into 3 clinics, each with 12 doctors.

### 2. Shift Assignment:
- All 12 doctors are assigned to the clinic.
- 4 doctors are randomly chosen for each shift (MORNING, AFTERNOON, EVENING).

### 3. Rotation Cycle:
- Every 5 days, doctors rotate to a different clinic.

---

## Agile Development

### Plan:
- Each feature or task was planned based on user stories and requirements.

### Implementation:
- Each task was implemented in a separate branch, following feature-driven development.

### Testing:
- Automated tests were written using `pytest` to ensure reliable functionality.

### Retrospectives:
- Conducted at the end of each sprint to evaluate progress and adjust the plan.

---

## Key Technologies

- Django / Django REST Framework
- SQLite (for development)
- pytest (for automated testing)
- python-dotenv (for environment variable management)

---

**Island Dental Booking System © 2025**  
Documentation maintained by Rayyan011 and contributors.

## Docker setup 

**1. Install Node.js dependencies and build frontend styles (on your host machine):**
Before building or running the Docker containers, you need to generate the project's CSS assets using Tailwind. Ensure you have Node.js and npm installed on your host system. From the project root (`DentalPrototype/`):
```bash
- npm install
- npm run tailwind:build

- git clone -b dev https://github.com/Rayyan011/DentalPrototype.git
- docker-compose up -d --build
- docker-compose run --rm backend python manage.py migrate
- docker-compose run --rm backend python manage.py createsuperuser
- docker-compose run --rm backend python manage.py setup_system
- docker-compose run --rm backend python manage.py setup_clinic_rotation --days 30
- The landing page is http://127.0.0.1:8080/

## Manage Docker Containers through portainer
- https://docs.portainer.io/start/install-ce/server/docker/wsl

- It would be easer to attach to docker Containers using a GUI do commands as well as get logs to help you in the development process


# Island Dental Booking System

A web-based booking and management system for Island Dental, a chain of dental clinics in the Maldives.

## Project Overview

The Island Dental Booking System provides a comprehensive solution for managing dental clinic operations, from appointment scheduling and doctor rostering to service pricing and reporting. The system emphasizes role-based access control to ensure data security and appropriate functionality for different users.

## Key Features

*   Appointment booking and management
*   Doctor roster management
*   Service and pricing management
*   Room allocation with special rules for surgery rooms
*   Comprehensive reporting (utilization, revenue, doctor performance, service demand)
*   Role-based access control (Customer, Doctor, Administrative Officer, Manager, System Admin)

## System Architecture

The system is built using the Django framework with a RESTful API backend and customizable admin interfaces. Key components:

*   **Backend:** Django, Django REST Framework
*   **Database:** SQLite (development); PostgreSQL (recommended for production)
*   **Frontend:** Uses Django's template engine for rendering HTML.

## User Roles and Access

The system implements robust role-based access control with five distinct user roles:

| Role                  | Access URL                 | Credentials | Responsibilities                                                                                                                                                                                                                          |
| --------------------- | -------------------------- | ----------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Customer              | http://127.0.0.1:8000/customer/       | customer/customer123       | Book dental appointments, view personal appointment history, cancel confirmed appointments, browse available clinics, doctors, and services.                                                                       |
| Doctor                | http://127.0.0.1:8000/doctor/         | doctor1/doctor1123       | View their assigned appointments, see their roster and work schedule, update appointment status (completed, no-show), view patient information for scheduled appointments.                                         |
| Administrative Officer| http://127.0.0.1:8000/officer/        | officer/officer123       | Manage all appointments in the system, create, modify, and cancel appointments, manage doctor rosters and schedules, view and manage clinics, rooms, and services.                                                     |
| Manager               | http://127.0.0.1:8000/manager/        | manager/manager123       | Complete system access and management, generate reports (revenue, appointment utilization), manage users, clinics, rooms, doctors, and services, set pricing for services based on shift.                            |
| System Admin          | http://127.0.0.1:8000/admin/          | admin/admin123         | Full Django admin access, technical administration of the system, manage user accounts and permissions, configure system settings.                                                                                |

## Database Model (Schema)

[INSERT IMAGE OF MODEL/DATABASE DIAGRAM HERE]

The database schema includes the following key models: `CustomUser`, `Clinic`, `Room`, `Doctor`, `Service`, `Price`, `Roster`, `Appointment`, and `Report`. Key relationships include: Appointments are linked to Customers, Doctors, Clinics, and Services; Doctor rotations are managed through the Roster model; Prices are tied to Services and Shifts.

## API Endpoints

The system provides the following API endpoints for data access and manipulation:

*   `GET /api/clinics/` - List clinics
*   `POST /api/clinics/` - Create a new clinic (requires Manager/Admin)
*   `GET /api/clinics/{id}/` - Retrieve a specific clinic
*   `PUT /api/clinics/{id}/` - Update a clinic (requires Manager/Admin)
*   `DELETE /api/clinics/{id}/` - Delete a clinic (requires Manager/Admin)
*   `GET /api/rooms/` - List rooms
*   `GET /api/doctors/` - List doctors
*   `GET /api/services/` - List services
*   `GET /api/prices/` - List service prices
*   `GET /api/rosters/` - List doctor rosters
*   `GET /api/appointments/` - List appointments
*   `GET /api/reports/` - List and generate reports
*   `GET /api/doctors/{id}/availability/?date=YYYY-MM-DD` - Check doctor availability for a given date

Example API Call (Checking Doctor Availability):


GET /api/doctors/1/availability/?date=2025-03-22

Returns:

```json
{
    "doctor": "Dr. John Doe (General Dentistry)",
    "date": "2025-03-22",
    "available_shifts": [
        "MORNING"
    ]
}
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
IGNORE_WHEN_COPYING_END
Business Rules

The system enforces the following business rules:

Scheduling:

No service available on Fridays.

Surgery rooms are not available during evening shifts (after 17:00).

Each clinic has a maximum capacity of 10 patients per shift.

Pricing: Service prices vary based on the shift (Morning, Afternoon, Evening).

Clinic Structure: Each clinic has 3 rooms (1 surgery room, 2 normal rooms).

Doctor Rotation: Each clinic has a rotation of 12 dentists assigned to it. Doctors rotate across the 3 clinics every 5 days in groups.

Installation and Setup

Clone the repository:

git clone https://github.com/[YOUR_GITHUB_USERNAME]/island-dental.git
cd island-dental
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Bash
IGNORE_WHEN_COPYING_END

Create a virtual environment and activate it:

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Bash
IGNORE_WHEN_COPYING_END

Install dependencies:

pip install -r requirements.txt
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Bash
IGNORE_WHEN_COPYING_END

Apply migrations:

python manage.py migrate
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Bash
IGNORE_WHEN_COPYING_END

Create a superuser:

python manage.py createsuperuser
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Bash
IGNORE_WHEN_COPYING_END

Run the development server:

python manage.py runserver
# Or if port 8000 is in use:
python manage.py runserver 8080
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Bash
IGNORE_WHEN_COPYING_END

Access the application at http://127.0.0.1:8000/ or http://127.0.0.1:8080/

Setup Commands

The system provides several management commands for initial setup and data population:

# Set up the complete system with users, permissions, and test data
python manage.py setup_system

# Set up the clinic locations, rooms, and doctor rotations
python manage.py setup_clinic_rotation --days 30

Doctor Rotation Implementation

The system uses the setup_clinic_rotation management command to configure the doctor rotation. The implementation consists of the following steps:

Distribution: 36 doctors are grouped and distributed into 3 clinics, each assigned with 12 doctors

Shift Assignment: All 12 doctor are assigned to the clinic, 4 doctor are randomly chosen during each shift (MORNING, AFTERNOON, EVENING)

Every 5 days, doctors shift to a different clinic.

Agile Development

The development was iterative, each of the task was planned, implemented, tested and analyzed at the end to get a general overview:

Plan:

How was planned

Implementation

What was implemented each task

Testing

How the tasks are tested.

Retrospectives

Key Technologies

Django/Django REST Framework

SQLite (development database)

pytest

python-dotenv



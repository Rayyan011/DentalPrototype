# Island Dental Booking System

A web-based booking and management system for Island Dental, a chain of dental clinics in the Maldives.

## Features

- Appointment booking and management
- Doctor roster management
- Service and pricing management
- Room allocation with special rules for surgery rooms
- Comprehensive reporting (utilization, revenue, doctor performance, service demand)
- Role-based access control (Customer, Doctor, Administrative Officer, Manager, System Admin)

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/island-dental.git
cd island-dental
```

2. Create a virtual environment and activate it:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Apply migrations:

```bash
python manage.py migrate
```

5. Create a superuser:

```bash
python manage.py createsuperuser
```

6. Run the development server:

```bash
python manage.py runserver
```

7. Access the application at http://127.0.0.1:8000/

## API Endpoints

The system provides the following API endpoints:

- `/api/clinics/` - List and manage clinics
- `/api/rooms/` - List and manage rooms
- `/api/doctors/` - List and manage doctors
- `/api/services/` - List and manage services
- `/api/prices/` - List and manage service prices
- `/api/rosters/` - List and manage doctor rosters
- `/api/appointments/` - List and manage appointments
- `/api/reports/` - List and generate reports

## Business Rules

- No service is available on Fridays
- Surgery rooms are not available during evening shifts (after 17:00)
- Service prices vary based on the shift (Morning, Afternoon, Evening)
- Each clinic has 3 rooms (1 surgery room, 2 normal rooms)
- Doctors rotate across the 3 clinics

## Agile Development Reflection

The Island Dental Booking System was developed using an agile approach, focusing on iterative development and continuous improvement. The project was broken down into smaller, manageable user stories, with each iteration delivering a working piece of functionality.

### Sprint 1: Core Models and Authentication
We started with the foundational models and authentication system, establishing the database schema and user roles. This included creating the CustomUser, Clinic, Room, Doctor, and Service models, as well as implementing role-based permissions.

### Sprint 2: Booking System
The second sprint focused on the appointment booking system, including room availability checks, price calculations, and validation rules (e.g., no bookings on Fridays, surgery room restrictions). We also implemented the booking receipt generation feature.

### Sprint 3: Roster Management
This sprint was dedicated to the doctor roster management system, allowing administrative staff to schedule doctors across different clinics, dates, and shifts. We ensured that doctors couldn't be double-booked and that roster assignments respected business rules.

### Sprint 4: Reporting
The final sprint concentrated on the reporting features, implementing the four required report types: appointment utilization, revenue, doctor performance, and service demand. We created both stored reports and ad-hoc report generation endpoints.

Throughout the development process, we continuously tested and refined the system, ensuring that each component worked correctly both individually and as part of the integrated whole. User feedback was incorporated after each sprint, leading to improvements in the user experience and functionality.

## Individual Contribution Reflection

As the lead developer on this project, my contributions spanned across all aspects of the system, from initial design to final implementation. I was responsible for:

1. **System Architecture**: Designing the overall structure of the application, including the database schema, API endpoints, and authentication system.

2. **Core Backend Development**: Implementing the Django models, serializers, viewsets, and business logic that form the backbone of the system.

3. **Security Implementation**: Ensuring that the system enforces appropriate access controls, with each user only able to access the data and functionality relevant to their role.

4. **Testing**: Writing comprehensive tests to verify that the system functions correctly and handles edge cases appropriately.

During development, I considered several emerging technologies:

- **Django Channels**: For real-time updates of appointment status and availability, though this was decided against for the initial release to reduce complexity.
- **GraphQL**: As an alternative to REST for more flexible queries, but REST was chosen for better compatibility with the existing ecosystem.
- **Docker**: For containerization, which would simplify deployment but was deferred to a future release.

The most significant learning experience was balancing flexibility with performance, especially in the reporting system where complex database queries needed to be optimized while still providing comprehensive data analysis capabilities.

In future iterations, I would recommend exploring integration with payment gateways for online payments, implementing notifications via SMS or email, and developing a more sophisticated mobile interface for customers. 
# SmartCampus — Campus Complaint & Grievance Management System

A full-stack web application for submitting, tracking, and managing campus complaints through a centralized ticket-based workflow.

## Overview

SmartCampus helps students report campus issues and enables administrators to manage complaints, assign them to the appropriate departments, and track their resolution status.

The system is designed to improve transparency, simplify grievance management, and provide students with visibility into the progress of their complaints.

## Features

- **User authentication:** Student registration and login.
- **Complaint submission:** Submit complaints with a title, description, and category.
- **Automatic ticket generation:** Generate a unique ticket ID for each complaint.
- **Department assignment:** Associate complaint categories with the appropriate departments.
- **Image attachments:** Upload and view supporting images.
- **Complaint tracking:** View complaint details and current status.
- **Status management:** Administrators can update complaint statuses.
- **Role-based access:** Restrict administrative actions and limit students to their own complaints.
- **Persistent storage:** Store complaint records in MySQL.
- **REST API:** Use FastAPI endpoints to connect the React frontend with the backend.

### Complaint Categories

| Category | Responsible department |
|---|---|
| Infrastructure | Maintenance Department |
| Wi-Fi | IT Department |
| Cleanliness | Housekeeping Department |
| Transport | Transport Department |

*Department mappings should match the configuration in the application.*

### Complaint Statuses

- `Submitted`
- `In Progress`
- `Resolved`
- `Rejected`

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React |
| Frontend development server | Vite |
| Backend | Python, FastAPI |
| Database | MySQL |
| ORM | SQLAlchemy |
| API documentation | FastAPI / Swagger UI |
| Authentication | Bearer-token-based authentication |
| Image storage | Backend uploads directory |

## System Architecture

```text
              STUDENT / ADMIN
                     |
                     v
             React Frontend
              (Vite Server)
                     |
                HTTP / JSON
                     |
                     v
              FastAPI Backend
              /      |      \
             /       |       \
       Authentication API   Image
          & Access    Logic  Uploads
             |
             v
        SQLAlchemy ORM
             |
             v
           MySQL
       smartcampus_db
```

The frontend sends requests to the FastAPI backend. The backend authenticates users, enforces access permissions, processes complaint operations, and uses SQLAlchemy to interact with MySQL. Uploaded images are stored separately from the complaint records, with their paths saved in the database.

## Application Workflow

1. A student registers or logs in.
2. The student submits a complaint with its category and description.
3. The backend generates a ticket ID and assigns the relevant department.
4. The student can attach a supporting image.
5. The student views their complaints and tracks their status.
6. An administrator reviews complaints and updates their status.
7. The updated status is available to the student.

## Project Structure

```text
SmartCampus/
├── backend/
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   ├── .env
│   ├── .venv/
│   └── uploads/
├── frontend/
│   ├── src/
│   │   └── App.jsx
│   ├── package.json
│   └── ...
├── .gitignore
└── README.md
```

The structure above shows the main files and directories. Additional files may be present in the local project.

## Prerequisites

Install the following before running the application:

- Python 3.12 or another version supported by the backend dependencies
- Node.js and npm
- MySQL Server
- Git (optional, for cloning the repository)

## Setup and Installation

### 1. Clone the repository

Replace the placeholder URL with your actual GitHub repository URL.

```powershell
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd SmartCampus
```

Alternatively, open your existing project folder directly in VS Code.

### 2. Configure the MySQL database

Start MySQL Server and create the database if it does not already exist:

```sql
CREATE DATABASE smartcampus_db;
```

Configure the database connection in the backend environment file using the connection settings expected by your application.

For the current local setup:

- Database: `smartcampus_db`
- Host: `localhost`
- Port: `3307`

Use your own MySQL username and password. Do not commit database credentials to GitHub.

**Important:** If you already have complaint records, preserve the existing database. Do not drop or recreate it just to set up the application.

### 3. Configure backend environment variables

Create `backend/.env` and provide the variables required by your backend configuration.

Example template — replace the placeholder names and values with the exact variables expected by your code:

```env
DATABASE_URL=<YOUR_MYSQL_CONNECTION_STRING>
SECRET_KEY=<YOUR_RANDOM_SECRET_KEY>
```

Your project may use a different database URL format or additional settings. Check the backend configuration before using this template.

Generate a strong, unique secret key for local or production use. Never publish real credentials or secrets.

### 4. Set up the backend

Open a PowerShell terminal:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install the dependencies listed in your backend dependency file.

If your project has `requirements.txt`:

```powershell
python -m pip install -r requirements.txt
```

Ensure the required database driver and `python-multipart` are installed if they are not already included in the dependency file.

Start the FastAPI development server:

```powershell
python -m uvicorn main:app --reload --port 8000
```

Backend URL:

`http://127.0.0.1:8000`

Interactive API documentation:

`http://127.0.0.1:8000/docs`

Keep this terminal running while using the application.

### 5. Set up the frontend

Open a **second** PowerShell terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open the Vite URL shown in the terminal. The current local development URL is:

`http://localhost:5173`

Keep both frontend and backend terminals running.

### 6. Verify the application

- Open the frontend in your browser.
- Register or log in using the application's supported authentication flow.
- Submit a test complaint.
- Confirm that a ticket ID is generated.
- Upload and view an image.
- Log in as an administrator and test status updates.
- Log back in as the student and verify the updated status.
- Refresh or sign back in and confirm that the complaint remains available.

Use test data during demonstrations and avoid modifying genuine complaint records.

## API Overview

The backend exposes REST API endpoints for the application's main operations.

| Operation | Endpoint | Purpose |
|---|---|---|
| Register | `POST /api/register` | Create a user account |
| Login | `POST /api/login` | Authenticate a user |
| Current user | `GET /api/me` | Retrieve authenticated user information |
| Submit complaint | `POST /api/complaints` | Create a complaint |
| List complaints | `GET /api/complaints` | Retrieve complaints according to access permissions |
| Complaint details | `GET /api/complaints/{complaint_id}` | Retrieve a specific complaint |
| Update status | `PATCH /api/complaints/{complaint_id}/status` | Update complaint status with administrator authorization |
| Submit feedback | `PUT /api/complaints/{complaint_id}/feedback` | Submit complaint feedback |
| Upload image | `POST /api/complaints/{complaint_id}/image` | Attach an image to a complaint |
| Admin analytics | `GET /api/admin/analytics` | Retrieve administrative analytics |

Open `/docs` on the running backend to confirm the exact available routes, request formats, and response schemas.

## Security Considerations

- **Environment variables:** Keep database credentials and secret keys out of source control.
- **Authentication:** Require valid authentication for protected operations.
- **Authorization:** Enforce permissions on the backend, not just by hiding frontend controls.
- **Complaint privacy:** Ensure students cannot access other students' complaints.
- **Administrative access:** Restrict status changes and administrative endpoints to authorized administrators.
- **Image validation:** Validate uploaded file types, size, and content; do not trust file extensions alone.
- **File storage:** Keep uploaded files and sensitive configuration out of public repositories.
- **Production deployment:** Disable development reload, use HTTPS, configure production-grade secrets, and review CORS and file-serving permissions before deployment.

The local development server is intended for development and demonstration, not direct public production use.

## Testing

The following core workflows have been manually tested during development:

- Student registration and login
- Complaint creation and automatic ticket ID generation
- Image upload and image viewing
- Administrator status updates
- Student access restrictions and authorization checks
- Complaint persistence across refreshes and sign-in sessions
- Complete complaint status lifecycle

Manual testing is not a substitute for a complete automated test suite. Additional automated API, security, and database integration tests can be added later.

## Future Enhancements

Potential future improvements include:

- Student feedback and ratings after resolution
- Average resolution-time analytics
- Complaint trend dashboards and reports
- Notifications for status changes
- Automated tests and production deployment

These are proposed enhancements and should not be considered implemented unless added and tested.

## Learning Outcomes

This project demonstrates practical experience with:

- Full-stack application development
- React-based user interfaces
- REST API development with FastAPI
- Relational database integration using MySQL and SQLAlchemy
- Authentication and role-based authorization
- File uploads and backend validation
- CRUD operations and complaint lifecycle management
- Local development, debugging, and manual testing

## License

Choose a license before publishing this repository publicly. If you have not selected one, no license has yet been specified.

---

**SmartCampus** — Making campus grievance management more organized, transparent, and accessible.

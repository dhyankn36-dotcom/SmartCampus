# SmartCampus — Campus Complaint Management System

![SmartCampus CI](https://github.com/dhyankn36-dotcom/SmartCampus/actions/workflows/ci.yml/badge.svg)

A full-stack campus grievance platform that helps students report issues, track complaint progress, and submit feedback while administrators manage resolution workflows.

SmartCampus is built with **React, FastAPI, and MySQL**, with JWT authentication, role-based access, complaint status history, administrative audit logs, and optional Cloudinary image storage.

[![React](https://img.shields.io/badge/Frontend-React-61DAFB?logo=react&logoColor=20232A)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![MySQL](https://img.shields.io/badge/Database-MySQL-4479A1?logo=mysql&logoColor=white)](https://www.mysql.com/)
[![Python](https://img.shields.io/badge/Language-Python-3776AB?logo=python&logoColor=white)](https://www.python.org/)

---

## Overview

Campus issues are often difficult to report and follow up on when updates are scattered across informal channels. SmartCampus provides a centralized workflow: students submit complaints and receive ticket IDs, while administrators review submissions, update statuses, and maintain a record of actions.

## Core Features

### Student experience
- Register and log in using JWT-based authentication
- Submit complaints with a title, description, category, and optional image
- Receive a unique complaint ticket ID
- View, search, filter, and paginate complaint records
- Track status changes through a chronological history
- Submit feedback and a rating after a complaint is resolved

### Administrator experience
- View and manage complaints across the platform
- Search, filter, and update complaint statuses
- Review feedback and dashboard analytics
- Access administrative audit logs
- Search and manage user accounts
- Change user roles with administrative safeguards

### Platform capabilities
- Role-based access control
- Password hashing
- Request ID tracking and structured JSON logging
- API rate limiting and input validation
- Image type and size validation
- Cloudinary image storage when configured, with local storage fallback
- API health-check endpoint

## Technology Stack

| Layer | Technologies |
|---|---|
| Frontend | React 19, Vite, JavaScript, CSS |
| Backend | Python, FastAPI |
| Database | MySQL |
| ORM | SQLAlchemy |
| Authentication | JWT (PyJWT), HTTP Bearer |
| Password security | pwdlib |
| Image storage | Cloudinary or local uploads |
| Testing | Pytest, FastAPI TestClient |
| API documentation | OpenAPI, Swagger UI |

## Architecture

The React client communicates with the FastAPI REST API. The API validates requests, applies authentication and role checks, and uses SQLAlchemy to persist application data in MySQL. Complaint images are stored with Cloudinary when its credentials are configured; otherwise, the backend uses its local uploads directory.

```text
                 STUDENT / ADMIN
                       |
                       v
                 REACT FRONTEND
                       |
                 HTTP / REST API
                       |
                       v
                  FASTAPI APP
          _____________|_____________
         |        |        |         |
         v        v        v         v
      AUTH    COMPLAINTS  ADMIN   FEEDBACK
         |        |        |         |
         |        +--------+---------+
         |                 |
         v                 v
               SQLALCHEMY ORM
                       |
                       v
                 MYSQL DATABASE

        COMPLAINT IMAGE UPLOADS
                 |
        +--------+---------+
        |                  |
        v                  v
    CLOUDINARY         LOCAL STORAGE
   (if configured)    (fallback)
```

## Complaint Workflow

```text
Student registers / logs in
          |
          v
   Submit a complaint
          |
          v
  Generate unique ticket
          |
          v
   Assign department
          |
          v
 Administrator reviews
          |
          v
 Update complaint status
          |
          v
    Mark as resolved
          |
          v
 Student submits feedback
```

### Categories and department routing

| Complaint category | Assigned department |
|---|---|
| Infrastructure | Maintenance Department |
| Wi-Fi | IT Department |
| Cleanliness | Housekeeping Department |
| Transport | Transport Department |

### Complaint statuses

- `Submitted`
- `In Progress`
- `Resolved`
- `Rejected`

## Repository Structure

```text
SmartCampus/
├── backend/
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── requirements.txt
│   └── tests/
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── .env.example
├── README.md
└── .gitignore
```

## Run Locally

### Prerequisites

- Python 3.12 or newer
- Node.js and npm
- MySQL Server
- Git

### 1. Clone the repository

```bash
git clone https://github.com/dhyankn36-dotcom/SmartCampus.git
cd SmartCampus
```

### 2. Create the MySQL database

Start MySQL and create the application database:

```sql
CREATE DATABASE smartcampus_db;
```

The backend reads the database connection from environment variables. Its default MySQL host is `localhost` and default port is `3307`; change `DB_PORT` if your MySQL server uses a different port.

### 3. Configure and install the backend

From the repository root:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Create `backend/.env` and set the required values:

```env
DB_USER=your_mysql_username
DB_PASSWORD=your_mysql_password
DB_HOST=localhost
DB_PORT=3307
DB_NAME=smartcampus_db
JWT_SECRET=replace_with_a_long_random_secret
```

Optional Cloudinary configuration:

```env
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```

Keep real credentials in your local environment file. **Never commit `.env` files, API secrets, or production credentials.**

### 4. Start the backend

Run from the `backend/` directory:

```powershell
python -m uvicorn main:app --reload --port 8000
```

The API is available at:

- API base: `http://127.0.0.1:8000`
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
- Health check: `http://127.0.0.1:8000/api/health`

### 5. Install and start the frontend

Open a second terminal from the repository root:

```powershell
cd frontend
npm install
```

The frontend supports an API base URL through `VITE_API_URL`. Create a local `.env` file in `frontend/` if the API is not running at the default local address:

```env
VITE_API_URL=http://127.0.0.1:8000
```

Start the development server:

```powershell
npm run dev
```

Open the local URL printed by Vite (typically `http://localhost:5173`).

## API Documentation

FastAPI generates interactive API documentation automatically when the backend is running:

- Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- ReDoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

Protected endpoints use the access token returned by the login endpoint. In Swagger UI, select **Authorize** and provide the token as described in the API documentation.

## Testing

Backend tests are located in `backend/tests/`. Run them from the backend directory with the virtual environment activated:

```powershell
python -m pytest -v
```

The test suite covers key application areas such as authentication, complaint operations, authorization, status history, feedback, and administrative functionality.

## Security Notes

- Use a strong, unique `JWT_SECRET` outside development.
- Keep database passwords and Cloudinary credentials out of source control.
- Use HTTPS and appropriately secured environment variables when deploying.
- Review uploaded files and access permissions before exposing the application publicly.

## Future Enhancements

- Email or in-app notifications for complaint status updates
- Expanded reporting and analytics
- Further accessibility and mobile experience improvements

## Author

**Dhyan K N**

Artificial Intelligence and Machine Learning

[GitHub Profile](https://github.com/dhyankn36-dotcom) · [SmartCampus Repository](https://github.com/dhyankn36-dotcom/SmartCampus)

---

*SmartCampus — making campus issue reporting and resolution more transparent.*

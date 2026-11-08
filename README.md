# SmartCampus — Campus Complaint Management System

A full-stack web application designed to improve campus issue reporting, complaint tracking, transparency, and accountability.

SmartCampus allows students to submit campus complaints, track their progress, upload supporting images, and provide feedback after resolution. Administrators can manage complaints, assign departments, update statuses, and monitor system activity.

## Features

### Student Features
- User registration and login
- JWT-based authentication
- Submit campus complaints
- Upload complaint images
- Automatically generated complaint ticket IDs
- Track complaint status
- View complaint status history
- Search, filter, and paginate complaints
- Submit feedback and ratings after resolution

### Administrator Features
- View and manage complaints
- Update complaint statuses
- Search and filter complaints
- View dashboard analytics
- Monitor feedback and ratings
- View audit logs
- Search and manage user accounts
- Change user roles with administrative safeguards

### Additional Features
- Role-based access control
- Password hashing
- Request ID tracking
- Structured application logging
- API rate limiting
- Input validation
- Image type and size validation
- Cloudinary image storage with local-storage fallback
- Health-check endpoint

## Technology Stack

| Layer | Technologies |
|---|---|
| Frontend | React, Vite, JavaScript, CSS |
| Backend | Python, FastAPI |
| Database | MySQL |
| ORM | SQLAlchemy |
| Authentication | JWT |
| Password Security | Password hashing |
| Image Storage | Cloudinary |
| Testing | Pytest, FastAPI TestClient |
| Version Control | Git, GitHub |

## Application Architecture

```text
             STUDENT / ADMIN
                    |
                    v
             REACT FRONTEND
                    |
                    v
              FASTAPI BACKEND
                    |
          +---------+---------+
          |         |         |
          v         v         v
       AUTH     COMPLAINTS   ADMIN
          |         |         |
          +---------+---------+
                    |
                    v
              MYSQL DATABASE
                    |
                    v
             CLOUDINARY
           (Complaint Images)
```

## Project Structure

```text
SmartCampus/
|
|-- backend/
|   |-- main.py
|   |-- database.py
|   |-- models.py
|   |-- requirements.txt
|   |-- tests/
|   |-- .env.example
|
|-- frontend/
|   |-- src/
|   |-- public/
|   |-- package.json
|   |-- .env.example
|
|-- README.md
|-- .gitignore
```

## Local Installation and Setup

### Prerequisites

- Python 3.12+
- Node.js and npm
- MySQL Server
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/dhyankn36-dotcom/SmartCampus.git
cd SmartCampus
```

### 2. Configure the MySQL Database

Create a database:

```sql
CREATE DATABASE smartcampus_db;
```

Make sure your MySQL server is running.

### 3. Set Up the Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create your `.env` file using `.env.example` and configure your database credentials and JWT secret.

If using Cloudinary, configure its cloud name, API key, and API secret in the backend environment.

Never commit your actual `.env` file or credentials.

### 4. Start the Backend

```bash
python -m uvicorn main:app --reload --port 8000
```

Backend:

`http://127.0.0.1:8000`

Interactive API documentation:

`http://127.0.0.1:8000/docs`

Health check:

`http://127.0.0.1:8000/api/health`

### 5. Set Up the Frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the local Vite URL displayed in your terminal, usually:

`http://localhost:5173`

Ensure the frontend API configuration points to the running backend at `http://127.0.0.1:8000`.

## Complaint Management Workflow

```text
Student Login
     |
     v
Submit Complaint
     |
     v
Generate Ticket ID
     |
     v
Department Assignment
     |
     v
Admin Reviews Complaint
     |
     v
Status Update
     |
     v
Resolution
     |
     v
Student Feedback
```

### Complaint Categories

| Category | Assigned Department |
|---|---|
| Infrastructure | Maintenance Department |
| Wi-Fi | IT Department |
| Cleanliness | Housekeeping Department |
| Transport | Transport Department |

### Complaint Statuses

- Submitted
- In Progress
- Resolved
- Rejected

## Testing

The backend includes automated tests covering authentication, complaint management, authorization, status history, feedback, administrative operations, and other API functionality.

Latest recorded test result:

**77 tests passed**

Run the backend tests using:

```bash
python -m pytest -v
```

## Future Enhancements

- Email notifications for complaint updates
- More advanced dashboard analytics
- Improved mobile responsiveness
- Additional reporting and visualization features

## Author

**Dhyan K N**

Artificial Intelligence and Machine Learning

GitHub: [dhyankn36-dotcom](https://github.com/dhyankn36-dotcom)

Repository: [SmartCampus](https://github.com/dhyankn36-dotcom/SmartCampus)

---

*SmartCampus is a full-stack project focused on improving campus issue reporting, transparency, and accountability.*
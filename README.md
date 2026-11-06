# SmartCampus — Campus Complaint Management System

A full-stack web application that helps students report campus issues, track complaint progress, and submit feedback while enabling administrators to manage complaints and monitor service quality.

## Features

### Student
- Secure registration and login
- Submit complaints with title, description, category, and location
- Upload supporting images
- Generate unique complaint ticket IDs
- View submitted complaints and their current status
- Track status changes through an activity timeline
- Submit feedback and ratings after a complaint is resolved

### Administrator
- View and manage student complaints
- Update complaint statuses
- Access student feedback
- View average ratings and feedback analytics
- Monitor the distribution of ratings

## Technology Stack

| Layer | Technologies |
|---|---|
| Frontend | React, Vite, CSS |
| Backend | Python, FastAPI |
| Database | MySQL |
| ORM | SQLAlchemy |
| Authentication | JWT |
| API Documentation | Swagger UI |

## Complaint Workflow

1. Student registers or logs in.
2. Student submits a complaint.
3. The system generates a ticket ID.
4. Administrator reviews and updates the complaint.
5. Student tracks status changes.
6. Once resolved, the student can submit feedback.
7. Administrators can review feedback and analytics.

## Complaint Categories

- Infrastructure — Maintenance Department
- Wi-Fi — IT Department
- Cleanliness — Housekeeping Department
- Transport — Transport Department

## Project Structure

```text
SmartCampus/
│
├── backend/
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   └── .env
│
└── frontend/
    ├── src/
    │   ├── App.jsx
    │   └── App.css
    ├── package.json
    └── ...
```

## Run Locally

### 1. Clone the repository

```bash
git clone https://github.com/dhyankn36-dotcom/SmartCampus.git
cd SmartCampus
```

### 2. Configure the backend

Navigate to the backend folder:

```bash
cd backend
```

Create and activate a virtual environment:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install fastapi "uvicorn[standard]" sqlalchemy pymysql python-dotenv PyJWT "pwdlib[argon2]" email-validator python-multipart
```

Create a `.env` file in the backend folder and configure your own database credentials and JWT secret:

```env
DB_USER=your_mysql_username
DB_PASSWORD=your_mysql_password
DB_HOST=localhost
DB_PORT=3307
DB_NAME=smartcampus_db
JWT_SECRET=your_secure_secret
```

Start the backend:

```bash
python -m uvicorn main:app --reload --port 8000
```

### 3. Run the frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the local URL displayed by Vite in your browser.

## API Documentation

When the backend is running, interactive API documentation is available at:

`http://localhost:8000/docs`

## Security

- Password hashing
- JWT-based authentication
- Role-based access control
- Complaint ownership checks
- Image type and file-size validation
- Feedback submission restrictions

## Future Improvements

- Cloud deployment
- Email notifications for complaint updates
- Advanced dashboard analytics
- Automated testing
- Improved mobile experience

## Author

**Dhyan K N**

Artificial Intelligence and Machine Learning

GitHub: [dhyankn36-dotcom](https://github.com/dhyankn36-dotcom)

---

*SmartCampus is a full-stack project focused on improving campus issue reporting, transparency, and accountability.*

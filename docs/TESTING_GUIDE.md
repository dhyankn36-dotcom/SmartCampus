# SmartCampus Testing Guide

This guide describes the repository's documented backend test workflow.

## Backend tests

1. Configure the backend environment using the instructions in the root README.
2. Change into the `backend/` directory.
3. Activate the project's Python virtual environment.
4. Install dependencies from `requirements.txt`.
5. Run:

```powershell
python -m pytest -v
```

The backend test suite is located in `backend/tests/`. The project README identifies coverage for authentication, complaint operations, authorization, status history, feedback, and administrative functionality.

## Manual integration checks

Use a development database and test accounts rather than real student records.

- Register and sign in; verify that protected pages require authentication.
- Submit a complaint and confirm that a ticket ID is returned.
- Verify that a user can access only their own complaint records.
- Update a complaint status as an authorized administrator and inspect its status history.
- Submit feedback for a resolved complaint.
- If image storage is configured, test valid and rejected uploads with non-sensitive sample images.
- Confirm that administrative actions are recorded in the audit log.

## Reporting failures

Include the command, relevant traceback, and expected versus actual behavior. Remove passwords, JWTs, database URLs, personal details, and uploaded user content from logs before sharing them.

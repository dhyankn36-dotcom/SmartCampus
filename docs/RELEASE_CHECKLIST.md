# SmartCampus Release Checklist

Use this checklist before deploying a new version of the campus complaint platform.

## Configuration

- [ ] Configure a unique production `JWT_SECRET` outside source control.
- [ ] Verify database credentials and connection settings.
- [ ] Configure HTTPS and secure cookie behavior for the deployment.
- [ ] Configure image storage credentials if Cloudinary is enabled.
- [ ] Confirm frontend API configuration points to the intended backend.

## Student workflows

- [ ] Register and sign in with a test account.
- [ ] Submit one sample complaint for each supported category.
- [ ] Confirm ticket IDs and department routing.
- [ ] Verify search, filters, pagination, and complaint ownership.
- [ ] Check status history after an administrator changes a complaint.
- [ ] Submit feedback for a resolved test complaint.

## Administrative workflows

- [ ] Verify that non-admin accounts cannot access administrative actions.
- [ ] Review complaint status updates and audit log entries.
- [ ] Check account-management safeguards and role changes.
- [ ] Confirm administrative views do not expose password data.

## Quality and data safety

- [ ] Run `python -m pytest -v` from `backend/`.
- [ ] Review the frontend build and available automated checks.
- [ ] Test valid and invalid image uploads with sample files.
- [ ] Back up the database and test restoring it in a separate environment.
- [ ] Remove personal information from screenshots, logs, and release notes.

## Publish

- [ ] Review API changes and update the README/API documentation.
- [ ] Record migration or configuration steps.
- [ ] Review the final diff and CI status.
- [ ] Publish release notes with known limitations.

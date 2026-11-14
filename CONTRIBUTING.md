# Contributing to SmartCampus

Thanks for helping improve SmartCampus. Contributions should keep the student complaint workflow reliable, secure, and understandable.

## Getting started

1. Fork the repository and clone your fork.
2. Create a focused branch from `main`, such as `feature/complaint-search` or `fix/status-validation`.
3. Follow the prerequisites and setup instructions in [README.md](README.md).
4. Keep changes scoped to the frontend, backend, or documentation area they affect.

## Development guidelines

- Keep API behavior consistent with the frontend's expectations.
- Validate request data on the backend; do not rely only on client-side validation.
- Preserve authentication and role-based authorization checks on protected operations.
- Keep complaint status history and administrative audit records consistent with status changes.
- Validate uploaded image type and size, and avoid trusting client-provided filenames.
- Never commit database passwords, JWT secrets, Cloudinary credentials, uploaded user files, or local environment files.
- Update API documentation and examples when endpoints or response formats change.

## Run backend tests

From the backend directory, activate your virtual environment, install the requirements, and run:

```bash
python -m pytest -v
```

For frontend changes, install dependencies from `frontend/` and run the available project scripts:

```bash
npm install
npm run
```

Run the relevant checks before opening a pull request and report any checks you could not run.

## Pull requests

Describe the user problem, implementation, and any API or database impact. Include test results and screenshots for UI changes when helpful. Call out configuration or migration steps explicitly. Keep unrelated changes out of the pull request.

## Reporting issues

Include reproducible steps, expected and actual results, and sanitized logs. Do not include real student information, credentials, or private complaint attachments.

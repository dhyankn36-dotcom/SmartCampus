# Complaint Lifecycle

This document describes the expected end-to-end complaint workflow in SmartCampus. The API and UI are the source of truth for the exact fields and permissions implemented in a given release.

## Lifecycle

1. **Submission:** An authenticated student submits a complaint with a title, description, category, and optional image.
2. **Ticket creation:** The system creates a unique ticket identifier and stores the complaint.
3. **Department routing:** The category determines the department that should review the issue.
4. **Review:** An authorized administrator reviews the complaint and its details.
5. **Progress update:** The administrator updates the complaint status as work progresses.
6. **Resolution or rejection:** The administrator records the outcome.
7. **Feedback:** The student can provide feedback after resolution.

## Category routing

| Category | Responsible department |
|---|---|
| Infrastructure | Maintenance Department |
| Wi-Fi | IT Department |
| Cleanliness | Housekeeping Department |
| Transport | Transport Department |

## Status meanings

| Status | Meaning |
|---|---|
| `Submitted` | The complaint has been received |
| `In Progress` | The complaint is being reviewed or worked on |
| `Resolved` | The reported issue has been addressed |
| `Rejected` | The complaint was reviewed but will not be actioned |

A status change should be made only by an account with the appropriate administrative permission. The interface should make the current status clear and preserve the status history where that feature is enabled.

## Role boundaries

- **Student:** Create complaints, view their own complaint records, follow progress, and submit eligible feedback.
- **Administrator:** Review complaints, update workflow status, and use administrative management features.
- **Unauthenticated visitor:** Must authenticate before accessing protected complaint data.

## Suggested verification checklist

- A student can submit a complaint and receives a ticket identifier.
- A student cannot access another student's private complaint by changing an identifier.
- A regular student cannot use administrator-only status or account-management actions.
- Category routing selects the expected department.
- Status updates are reflected in the complaint view.
- Feedback is accepted only when the complaint meets the application's eligibility rules.
- Invalid or missing input produces a useful validation response.

## Security and privacy

Do not include passwords, access tokens, database credentials, or sensitive personal details in issue reports or screenshots. Validate uploaded files on the server and keep secrets in environment variables rather than committed files.

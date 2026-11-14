# Security Policy

## Supported versions

Security fixes are accepted for the latest version on the default branch.

## Reporting a vulnerability

Do not publish JWTs, database credentials, personal student information, or exploit details in a public issue. Use the repository's private vulnerability reporting option in GitHub's Security tab. Include the affected endpoint, impact, and safe reproduction steps using test accounts.

## Application-specific precautions

- Keep `JWT_SECRET`, database passwords, and Cloudinary credentials outside source control.
- Use test accounts and synthetic complaint records during development.
- Treat complaint descriptions, uploaded images, account details, and feedback as potentially sensitive.
- Verify authentication, role checks, and record ownership when modifying API routes.
- Avoid sharing production logs or screenshots without removing personal data.

## Deployment checklist

Use HTTPS, secure cookie settings, strong unique secrets, restricted administrative access, and appropriately protected database and upload storage. Allow reasonable time to investigate reports before public disclosure.

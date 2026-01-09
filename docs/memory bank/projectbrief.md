# Project Brief

> Foundation document for Company ProjectOps - the source of truth for project scope and requirements.

---

## Project Overview

**Name:** Company ProjectOps  
**Type:** Enterprise Project & Task Management Platform  
**Version:** 1.20.4  
**Repository:** https://github.com/mkschulze/company-projectops

---

## Core Purpose

Company ProjectOps is a centralized web application for managing projects, tasks, and deadlines across teams and organizations. Originally developed as a Tax Compliance Calendar (TaxOps), it evolved into a full-featured Project Management platform with multi-tenant support for enterprise clients.

---

## Key Requirements

### Functional Requirements

1. **Multi-Tenant Architecture**
   - Complete client/data separation
   - Per-tenant roles and permissions
   - Tenant-specific branding (logo)
   - Compliance export for audits

2. **Project Management**
   - Multiple methodologies: Scrum, Kanban, Waterfall, Custom
   - Iterations/Sprints with burndown charts
   - Kanban boards with drag-and-drop
   - Issue tracking with configurable workflows

3. **Task Management**
   - Task lifecycle with status workflow
   - Multi-reviewer approval process
   - Evidence uploads (files + links)
   - Comments and audit logging

4. **Calendar & Deadlines**
   - Month and year calendar views
   - iCal subscription for Outlook/Google/Apple
   - Due date reminders via email
   - Recurring tasks from presets

5. **Team Collaboration**
   - Team creation and member management
   - Task assignment to teams or individuals
   - Real-time notifications (WebSocket)
   - Email notifications with preferences

### Non-Functional Requirements

1. **Security**
   - Role-based access control (RBAC)
   - Entity-level permissions
   - Audit trail for compliance
   - Secure file uploads

2. **Internationalization**
   - German (default) and English
   - Methodology-specific terminology

3. **Enterprise-Ready**
   - SQLite (dev) / PostgreSQL (prod)
   - Scalable architecture
   - API key support for integrations

---

## Target Users

| Role | Description |
|------|-------------|
| **Super-Admin** | Manages all tenants, global settings |
| **Tenant Admin** | Manages tenant members, projects, settings |
| **Manager** | Assigns tasks, views reports, manages teams |
| **Reviewer** | Reviews and approves/rejects work |
| **Member/Preparer** | Works on assigned tasks, uploads evidence |
| **Viewer** | Read-only access to status and reports |

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Flask 3.x, SQLAlchemy, Flask-Login |
| Frontend | Bootstrap 5.3, Jinja2, Chart.js |
| Real-time | Flask-SocketIO, eventlet |
| Database | SQLite (dev), PostgreSQL (prod) |
| Export | openpyxl (Excel), WeasyPrint (PDF) |
| Calendar | icalendar, python-dateutil |

---

## Project Structure

```
company-projectops/
├── app.py              # Main application (~3900 lines)
├── models.py           # SQLAlchemy models (~1200 lines)
├── services.py         # Business logic
├── admin/              # Admin blueprints (tenants)
├── middleware/         # Request middleware (tenant context)
├── modules/            # Feature modules (projects, tasks)
├── scripts/            # Automation (release, demo data)
├── templates/          # Jinja2 templates
├── docs/               # Memory Bank documentation
└── migrations/         # Alembic database migrations
```

---

## Success Criteria

1. ✅ Multi-tenant client separation with full data isolation
2. ✅ Flexible project methodologies (Scrum, Kanban, Waterfall, Custom)
3. ✅ Multi-reviewer approval workflow
4. ✅ Calendar integration with iCal subscriptions
5. ✅ Complete audit trail for compliance
6. ✅ German and English language support
7. ✅ Company branding and design system
8. 🔜 OIDC/Entra ID SSO integration
9. 🔜 MS Teams notifications

---

## Constraints

- **Branding:** Must follow Company 2024 Design System
- **Languages:** German as default, English as secondary
- **Privacy:** Data must be isolated per tenant
- **Compliance:** Full audit logging for regulatory requirements

---

## Release Process

Automated via `scripts/release.py`:
1. Update version in all files
2. Update CHANGELOG.md
3. Update Memory Bank docs
4. Create git commit and tag
5. Push to GitHub

---

*Last updated: 2026-01-03*

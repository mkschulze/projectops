# Product Context

> Company ProjectOps — Tax Compliance Calendar & Deadline Tracking

## Purpose

The **Company ProjectOps** is a web application designed to centralize tax compliance deadline management for enterprises. It provides a single platform to:

- **Plan** annual tax compliance calendars with all relevant deadlines
- **Assign** tasks to responsible owners and **multiple reviewers**
- **Track** progress against due dates with visual status indicators
- **Review** submitted work through a structured **multi-reviewer approval process**
- **Evidence** compliance with document uploads and audit trails

### Core Promise

> One place to plan, assign, track, review, and evidence tax compliance deadlines across entities and tax types.

---

## Target Users

### Primary Personas

| Role | Responsibilities | Key Needs |
|------|------------------|-----------|
| **Tax Manager (Owner)** | Accountable for compliance calendar completeness and reporting | Dashboard overview, KPIs, assignment tools, status reports |
| **Contributor (Preparer)** | Prepares tasks, uploads evidence, submits for review | Task list, clear due dates, easy upload, status updates |
| **Reviewer (Four-Eyes)** | Reviews submissions, requests changes, completes tasks | Review queue, comparison tools, approval workflow |
| **Admin** | Configures entities, templates, tax types, users, permissions | CRUD interfaces, import tools, user management |
| **Read-Only/Audit** | Views status and evidence, cannot modify | Read-only access, export capability |

### User Roles (RBAC)

```
admin       Full access to all features and settings
manager     Can assign tasks, view all entities, run reports
reviewer    Can review and complete tasks (four-eyes)
preparer    Can work on assigned tasks, upload evidence
readonly    View-only access to task status and evidence
```

### Permission Scopes

Access can be scoped by:
- **Entity** — Which legal entities the user can see/manage
- **Jurisdiction** — Country or regional filtering
- **Tax Type** — Specific tax categories (KSt, USt, GewSt, etc.)

---

## Problems Solved

### Current Pain Points (Without the App)

| Problem | Impact | Solution |
|---------|--------|----------|
| **Scattered Excel files** | Deadlines missed, no single source of truth | Centralized database with web access |
| **No visibility** | Managers don't know status until it's too late | Real-time dashboard with KPIs |
| **Missing evidence** | Cannot prove compliance during audits | Attached documents with immutable log |
| **Unclear ownership** | Tasks fall through the cracks | Explicit owner/reviewer assignment |
| **Manual tracking** | Time-consuming status updates | Automatic due-soon/overdue detection |
| **No audit trail** | Cannot explain what happened and when | Complete activity logging |
| **Email chaos** | Evidence buried in inboxes | Centralized evidence storage |

### Value Proposition

1. **Reduce compliance risk** — Never miss a tax deadline again
2. **Save time** — Automated status tracking and reminders
3. **Prove compliance** — Immutable audit trail for regulators
4. **Improve visibility** — Dashboard shows real-time status
5. **Enable collaboration** — Clear handoffs between preparer/reviewer

---

## Key Features

### Data Management (CRUD)

#### Entities (Gesellschaften)

| Field | Description |
|-------|-------------|
| Name | Legal entity name |
| Country | Jurisdiction (DE, AT, CH, etc.) |
| Group | Optional parent entity grouping |
| Active | Soft delete flag |

#### Tax Types (Steuerarten)

| Field | Description |
|-------|-------------|
| Code | Short identifier (KSt, USt, GewSt) |
| Name | Full name (Körperschaftsteuer) |

#### Task Templates

| Field | Description |
|-------|-------------|
| Tax Type | Associated tax category |
| Keyword | Short task identifier |
| Description | Detailed task description |
| Default Recurrence | monthly, quarterly, annual |
| Default Due Rule | Day of month, end of month, etc. |

#### Tasks (Calendar Items)

| Field | Description |
|-------|-------------|
| Template | Source template |
| Entity | Associated legal entity |
| Year | Fiscal year |
| Due Date | Deadline |
| Status | Draft, Submitted, In Review, Completed |
| Owner | Responsible user |
| Reviewer | Four-eyes reviewer |
| Submitted At | Timestamp of submission |
| Completed At | Timestamp of completion |

#### Evidence

| Field | Description |
|-------|-------------|
| Task | Parent task |
| Type | File or Link |
| Path/URL | File location or external URL |
| Uploaded By | User who added |
| Uploaded At | Timestamp |

#### References

- **Anträge** — Law-based applications library
- **Kommentare** — Structured notes mapped to law references

---

### User Experience

#### Dashboard

- **KPI Cards**: #Overdue, #Due Soon, Completion Rate, Awaiting Review
- **Filters**: Year/Period, Entity, Tax Type, Owner
- **My Tasks Panel**: User's assigned tasks with quick actions
- **Recent Activity**: Latest changes across the organization

#### Calendar View

- **Month/Week Toggle**: Switch between views
- **Color-Coded Events**: Status indicated by Company colors
- **Click-to-Open**: Task drawer with quick actions
- **Entity Filter**: Show tasks for specific entities

#### Task List

- **Sortable Columns**: Due date, status, owner, entity
- **Filters**: Status, tax type, entity, date range
- **Batch Operations**: Reassign, change due date, export
- **Row Details**: Entity, tax type, keyword, due date, status badge, owner, reviewer

#### Task Detail

- **Header**: Status badge, due date, entity, tax type
- **Tabs**:
  - Overview: Description, checklist, recurrence info
  - Evidence: Upload files, add links
  - Comments: Discussion thread
  - Audit Log: Read-only activity history

#### Admin Interfaces

- **User Management**: Create, edit, deactivate users
- **Entity Management**: Add/edit legal entities
- **Tax Type Catalog**: Manage tax categories
- **Template Management**: View/edit task templates
- **Excel Import**: Upload and process YEAR/Anträge/Kommentare

---

## Status Workflow

### Task Lifecycle

```
┌─────────┐     ┌───────────┐     ┌───────────┐     ┌──────────┐     ┌───────────┐
│  Draft  │────▶│ Submitted │────▶│ In Review │────▶│ Approved │────▶│ Completed │
└─────────┘     └───────────┘     └─────┬─────┘     └──────────┘     └───────────┘
                      ▲                 │
                      │                 │
                      └─────────────────┘
                       (Rework Required)
```

### Multi-Reviewer Approval (NEW)

When multiple reviewers are assigned to a task:

1. **All Must Approve:** Task only transitions to "Approved" when every assigned reviewer has approved
2. **Any Can Reject:** If any single reviewer rejects, the entire task is rejected
3. **Progress Tracking:** Visual progress bar shows `X/Y` reviewers approved
4. **Individual Actions:** Each reviewer has their own approve/reject buttons
5. **Audit Trail:** Each approval/rejection is logged with timestamp and optional note

```
┌─────────────────────────────────────────────────────────────┐
│                        In Review                             │
│                                                              │
│  Reviewer 1: ✅ Approved (28.12.2025 14:30)                 │
│  Reviewer 2: ⏳ Pending                                      │
│  Reviewer 3: ⏳ Pending                                      │
│                                                              │
│  Progress: [████░░░░░░] 1/3 approved                        │
│                                                              │
│  → When all 3 approve → Auto-transition to "Approved"       │
│  → If any rejects → Immediate transition to "Rejected"      │
└─────────────────────────────────────────────────────────────┘
```

### Automatic Overlays

| Overlay | Condition | Color |
|---------|-----------|-------|
| **Due Soon** | Due date within 7 days | Orange |
| **Overdue** | Past due date, not completed | Red |

---

## Reporting

### MVP Reports

| Report | Description |
|--------|-------------|
| **Task Export** | Filtered task list to Excel |
| **Status Summary** | Count by status and entity |

### Phase 2 Reports

| Report | Description |
|--------|-------------|
| **Compliance Heatmap** | Entity × Month grid with status colors |
| **Overdue Aging** | Tasks grouped by days overdue (0-7, 8-30, 31+) |
| **On-Time Rate** | Completion rate by tax type |
| **Workload Report** | Tasks due in next 30/60/90 days by owner |

---

## Import/Export

### Excel Import

**Source Sheets:**
- **YEAR**: Task catalog with tax types, keywords, due dates
- **Anträge**: Law-based applications library
- **Kommentare**: Reference notes

**Import Process:**
1. Upload workbook
2. Validate expected headers
3. Normalize task rows
4. Create/update templates
5. Generate tasks for selected year + entities
6. Display import report

### Excel Export

- Filtered task list download
- Includes: Entity, Tax Type, Keyword, Due Date, Status, Owner, Reviewer
- Format: XLSX with Company branding

---

## Localization

### Supported Languages

| Code | Language | Status |
|------|----------|--------|
| `de` | German | Default |
| `en` | English | Available |

### Key UI Terms

| German | English |
|--------|---------|
| Aufgaben | Tasks |
| Fällig | Due |
| Überfällig | Overdue |
| Eingereicht | Submitted |
| In Prüfung | In Review |
| Abgeschlossen | Completed |
| Gesellschaft | Entity |
| Steuerart | Tax Type |

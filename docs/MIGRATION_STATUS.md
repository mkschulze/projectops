# Route Migration Status

## Overview
Routes are being migrated from `app.py` to Flask Blueprints in the `routes/` package.

- **Total routes in app.py**: 0 (cleaned up ✅)
- **Routes in blueprints**: 98 (all routes now in blueprints)
- **Legacy code removed**: ~3,960 lines (95% reduction in app.py)
- **app.py size**: 237 lines (down from 4,196 lines)

## Completed Migrations

### auth_bp (routes/auth.py) - 5 routes
- ✅ `/login` GET/POST
- ✅ `/logout` GET
- ✅ `/select-tenant` GET
- ✅ `/switch-tenant/<int:tenant_id>` POST
- ✅ `/api/switch-tenant/<int:tenant_id>` POST

### main_bp (routes/main.py) - 15 routes
- ✅ `/` GET
- ✅ `/dashboard` GET
- ✅ `/calendar` GET
- ✅ `/calendar/year` GET
- ✅ `/calendar/week` GET
- ✅ `/calendar/ical/<token>.ics` GET
- ✅ `/calendar/subscription` GET
- ✅ `/calendar/regenerate-token` POST
- ✅ `/set-language/<lang>` GET
- ✅ `/notifications` GET
- ✅ `/notifications/mark-read/<id>` POST
- ✅ `/notifications/mark-all-read` POST
- ✅ `/profile` GET
- ✅ `/profile/notifications` GET
- ✅ `/profile/notifications` POST

### tasks_bp (routes/tasks.py) - 20 routes
- ✅ `/tasks` GET (list)
- ✅ `/tasks/<id>` GET (detail)
- ✅ `/tasks/new` GET/POST (create)
- ✅ `/tasks/<id>/edit` GET/POST
- ✅ `/tasks/<id>/status` POST
- ✅ `/tasks/<id>/reviewer-action` POST
- ✅ `/tasks/<id>/archive` POST
- ✅ `/tasks/<id>/restore` POST
- ✅ `/tasks/<id>/delete` POST
- ✅ `/tasks/archive` GET (archive list)
- ✅ `/tasks/<id>/evidence/upload` POST
- ✅ `/tasks/<id>/evidence/link` POST
- ✅ `/tasks/<id>/evidence/<eid>/download` GET
- ✅ `/tasks/<id>/evidence/<eid>/preview` GET
- ✅ `/tasks/<id>/evidence/<eid>/delete` POST
- ✅ `/tasks/<id>/comments` POST
- ✅ `/tasks/<id>/comments/<cid>/delete` POST
- ✅ `/tasks/export/excel` GET
- ✅ `/tasks/export/summary` GET
- ✅ `/tasks/<id>/export/pdf` GET

### admin_bp (routes/admin.py) - 24 routes
- ✅ `/admin` GET (dashboard)
- ✅ `/admin/modules` GET
- ✅ `/admin/modules/<id>/toggle` POST
- ✅ `/admin/users` GET
- ✅ `/admin/users/new` GET/POST
- ✅ `/admin/users/<id>` GET/POST
- ✅ `/admin/users/<id>/modules` GET
- ✅ `/admin/users/<id>/modules` POST
- ✅ `/admin/users/<id>/entities` GET
- ✅ `/admin/users/<id>/entities` POST
- ✅ `/admin/entities` GET
- ✅ `/admin/entities/new` GET/POST
- ✅ `/admin/entities/<id>` GET/POST
- ✅ `/admin/entities/<id>/delete` POST
- ✅ `/admin/entities/<id>/users` GET
- ✅ `/admin/entities/<id>/users` POST
- ✅ `/admin/teams` GET
- ✅ `/admin/teams/new` GET/POST
- ✅ `/admin/teams/<id>` GET/POST
- ✅ `/admin/teams/<id>/delete` POST
- ✅ `/admin/categories` GET
- ✅ `/admin/categories/new` GET/POST
- ✅ `/admin/categories/<id>` GET/POST
- ✅ `/admin/tax-types` GET (redirect)

### api_bp (routes/api.py) - 20 routes
- ✅ `/api/tasks/bulk-archive` POST
- ✅ `/api/tasks/bulk-restore` POST
- ✅ `/api/tasks/bulk-status` POST
- ✅ `/api/tasks/bulk-assign-owner` POST
- ✅ `/api/tasks/bulk-delete` POST
- ✅ `/api/tasks/archive/bulk-delete` POST
- ✅ `/api/tasks/<id>/approval-status` GET
- ✅ `/api/tasks/<id>/workflow-timeline` GET
- ✅ `/api/dashboard/status-chart` GET
- ✅ `/api/dashboard/monthly-chart` GET
- ✅ `/api/dashboard/team-chart` GET
- ✅ `/api/dashboard/project-velocity/<id>` GET
- ✅ `/api/dashboard/trends` GET
- ✅ `/api/dashboard/project-distribution` GET
- ✅ `/api/notifications` GET
- ✅ `/api/notifications/unread-count` GET
- ✅ `/api/notifications/<id>/read` POST
- ✅ `/api/notifications/mark-all-read` POST
- ✅ `/api/presets` GET
- ✅ `/api/presets/<id>` GET

### presets_bp (routes/presets.py) - 13 routes
- ✅ `/admin/presets` GET
- ✅ `/admin/presets/new` GET/POST
- ✅ `/admin/presets/<id>` GET/POST
- ✅ `/admin/presets/<id>/delete` POST
- ✅ `/admin/presets/export` GET
- ✅ `/admin/presets/template` GET
- ✅ `/admin/presets/seed` POST
- ✅ `/api/presets/<id>` PATCH
- ✅ `/api/presets/bulk-toggle-active` POST
- ✅ `/api/presets/bulk-delete` POST
- ✅ `/api/preset-fields` POST
- ✅ `/api/preset-fields/<id>` GET
- ✅ `/api/preset-fields/<id>` PUT/DELETE

---

## Migration History

### Phase 4a (v1.19.0)
- Created blueprint structure
- Migrated core routes (auth, main, tasks, admin, api)
- 67 routes migrated

### Phase 4b (v1.20.0)
- Migrated User-Entity Permission routes (6 routes) to admin_bp
- Migrated Dashboard API routes (4 routes) to api_bp
- Migrated Notification API routes (4 routes) to api_bp
- Created presets_bp for preset management (13 routes)
- Added export routes to tasks_bp (3 routes)
- Total: 97 routes now in blueprints

### Notes
- Routes in app.py are superseded by blueprint routes (blueprints take precedence)
- The duplicate definitions in app.py are harmless but could be cleaned up
- Full removal requires careful testing to ensure all routes work correctly

---

## Code Coverage (v1.20.3)

**Overall: 65%** (6,775 statements, 2,380 missed)  
**Tests: 814 passed**, 12 skipped, 97 xfailed

### By Module

| Module | Coverage | Status |
|--------|----------|--------|
| config.py | 100% | ✅ |
| extensions.py | 100% | ✅ |
| translations.py | 100% | ✅ |
| routes/__init__.py | 100% | ✅ |
| modules/core/__init__.py | 100% | ✅ |
| middleware/tenant.py | 98% | ✅ |
| modules/__init__.py | 88% | |
| models.py | 74% | |
| modules/projects/models.py | 69% | |
| routes/main.py | 68% | |
| services.py | 65% | ✅ (up from 52%) |
| admin/tenants.py | 63% | ✅ (up from 17%) |
| routes/auth.py | 57% | |
| routes/api.py | 43% | |
| modules/projects/routes.py | 42% | (up from 19%) |
| routes/tasks.py | 28% | |
| routes/admin.py | 24% | |
| routes/presets.py | 20% | |
| app.py | 17% | Legacy |

### Coverage Goals
- **Current**: 65% overall coverage ✅
- **Next target**: 75% overall coverage
- **Priority areas**: routes/tasks.py, routes/admin.py, routes/presets.py
- **High coverage maintained**: Core modules (config, extensions, translations)

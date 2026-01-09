# ZAP DOM XSS Scan Notes

This document provides context for ZAP support regarding DOM XSS areas in the ProjectOps application.

## Overview

The ZAP scan appears to stall when applying DomXssScanRule tests. This document identifies the primary DOM manipulation areas in the codebase that may be relevant for investigation.

## Key DOM XSS Areas

### 1. Notification System (`templates/base.html`)

**Location:** Lines ~571-582 in `templates/base.html`

The `createNotificationItem()` function uses `innerHTML` to render notification content:

```javascript
function createNotificationItem(data) {
    const item = document.createElement('div');
    item.className = 'notification-item p-3 border-bottom';
    item.innerHTML = `
        <div class="d-flex justify-content-between">
            <strong>${data.title}</strong>
            <small class="text-muted">${data.time}</small>
        </div>
        <p class="mb-0 text-muted small">${data.message}</p>
    `;
    return item;
}
```

**Risk Assessment:** Medium - Data comes from server via Socket.IO. Server-side sanitization applies.

**Socket.IO Handler:** Lines ~511-515
```javascript
socket.on('notification', function(data) {
    prependNotification(data);
    // ...
});
```

### 2. Markdown Rendering (`templates/base.html`)

**Location:** Line ~1012 in `templates/base.html`

The application uses `marked.js` to parse markdown without DOMPurify sanitization:

```javascript
marked.setOptions({ breaks: true, gfm: true, headerIds: false, mangle: false });
targetEl.innerHTML = marked.parse(markdown);
```

**Risk Assessment:** Medium - If user-controlled markdown contains malicious HTML/JS, it could execute.

**Used in:** Issue/Task descriptions in project management module.

### 3. Search Results

**Location:** Lines ~976-1010 in `templates/base.html`

The `createResultItem()` and `createSearchResultItem()` functions use `innerHTML` but include an `escapeHtml()` helper for user content.

**Risk Assessment:** Low - Proper escaping implemented.

### 4. URL Fragment/Hash Handling

**Location:** Line ~1039 in `templates/base.html`

```javascript
window.location.hash
```

**Risk Assessment:** Low - Review for DOM-based open redirect potential.

## Recommended Test Focus

For ZAP scanning, focus on these URL patterns:

| Path Pattern | Reason |
|--------------|--------|
| `/notifications` | Real-time notification rendering |
| `/projects/*/issues/*` | Markdown description rendering |
| `/projects/*/board` | Drag-and-drop with DOM updates |
| `/dashboard` | Chart.js and KPI card rendering |
| `/tasks/*` | Task detail with evidence/comments |
| `/admin/presets/*` | Preset form with dynamic fields |

## Socket.IO Endpoints

The application uses Socket.IO for real-time features:
- WebSocket endpoint: `/socket.io/`
- Events: `notification`, `task_update`, `connect`, `disconnect`

## CSP Configuration

The application uses nonce-based Content Security Policy. All inline scripts include `nonce="{{ csp_nonce }}"`.

## Mitigation Recommendations

1. **Add DOMPurify for markdown rendering** - The marked.js output should be sanitized before DOM insertion
2. **Server-side notification sanitization** - Ensure notification title/message are HTML-escaped server-side
3. **Consider using textContent instead of innerHTML** where appropriate

## Files for Reference

- [templates/base.html](../templates/base.html) - Main template with JS
- [services.py](../services.py) - Notification creation logic
- [routes/api.py](../routes/api.py) - API endpoints returning JSON data

---

*Document created for ZAP support review - January 2026*

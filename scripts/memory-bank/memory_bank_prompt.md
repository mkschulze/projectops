# Memory Bank Update Prompt Template

You are updating the Memory Bank documentation for Deloitte ProjectOps after a new release.

## Release Information

**New Version:** {version}
**Release Title:** {title}
**Date:** {date}
**Previous Version:** {previous_version}

## Changes Since Last Release

### Git Commits
```
{git_commits}
```

### Changed Files
```
{changed_files}
```

### Git Diff Summary
```
{git_diff_summary}
```

## Current Memory Bank Files

### docs/activeContext.md
```markdown
{active_context}
```

### docs/progress.md
```markdown
{progress}
```

### docs/productContext.md
```markdown
{product_context}
```

### docs/techContext.md
```markdown
{tech_context}
```

### docs/systemPatterns.md
```markdown
{system_patterns}
```

## Instructions

Please update each Memory Bank file with the new release information:

### 1. activeContext.md
- Update **Date** to {date}
- Update **Version** to {version}
- Update **Last Action** with the main feature from this release
- Update **Status** to reflect completed work
- Add a new section under "What Was Accomplished" with the release changes
- Move previous accomplishments to "Previously Completed"

### 2. progress.md
- Update **Last Updated** date
- Update **Version** to {version}
- Add new release section at the top of "Recent Releases"
- Include all Added/Changed/Fixed items from the release

### 3. productContext.md
- Update if there are new features, user roles, or functionality changes
- Add new features to the appropriate tables

### 4. techContext.md
- Update if there are new dependencies, routes, or technical changes
- Update project structure if new files/folders were added

### 5. systemPatterns.md
- Update if there are new patterns, conventions, or architectural changes

## Output Format

Provide the complete updated content for each file that needs changes:

```activeContext.md
[Full updated content]
```

```progress.md
[Full updated content]
```

(Only include files that need updates)

#!/usr/bin/env python3
"""
Release Script for Deloitte ProjectOps

IMPORTANT: Before running this script, you MUST first run:
    python scripts/check_memory_bank.py --for-release X.Y.Z

This ensures you've read and updated all Memory Bank files BEFORE the
release process begins.

Release workflow:
1. Validates Memory Bank files are already updated
2. Creates commit with release message
3. Creates and pushes git tag
4. Pushes to remote

Usage:
    # First, read and update Memory Bank files:
    python scripts/check_memory_bank.py --for-release 1.17.0
    
    # Then verify and release:
    python scripts/release.py --version 1.17.0 --title "Feature XYZ"
    
    # Or just verify (no release):
    python scripts/check_memory_bank.py --verify 1.17.0
"""

import argparse
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent.absolute()

# Files that contain version information
VERSION_FILES = {
    'VERSION': {
        'pattern': r'^[\d.]+$',
        'replacement': '{version}'
    },
    'config.py': {
        'pattern': r"APP_VERSION = '[^']+'",
        'replacement': "APP_VERSION = '{version}'"
    },
    'README.md': {
        'pattern': r'Version-[\d.]+-blue',
        'replacement': 'Version-{version}-blue'
    },
    'docs/progress.md': {
        'pattern': r'\*\*Version:\*\* [\d.]+',
        'replacement': '**Version:** {version}'
    },
    'docs/activeContext.md': {
        'pattern': r'\*\*Version:\*\* [\d.]+',
        'replacement': '**Version:** {version}'
    }
}

# Memory Bank files that MUST be reviewed before each release
MEMORY_BANK_FILES = [
    ('docs/activeContext.md', 'Session info, last action, version, current state'),
    ('docs/progress.md', 'Release history, version changelog, milestones'),
    ('docs/projectbrief.md', 'Version number in Project Overview section'),
    ('docs/techContext.md', 'Test counts, dependencies, project structure'),
    ('docs/systemPatterns.md', 'Coverage stats, architecture patterns'),
    ('docs/productContext.md', 'Product scope, features (if changed)'),
    ('docs/technicalConcept.md', 'Technical design, architecture (if changed)'),
]

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """Print a styled header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}  {text}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")


def print_step(step: int, text: str):
    """Print a step indicator."""
    print(f"{Colors.CYAN}[Step {step}]{Colors.ENDC} {text}")


def print_success(text: str):
    """Print success message."""
    print(f"{Colors.GREEN}✓ {text}{Colors.ENDC}")


def print_warning(text: str):
    """Print warning message."""
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")


def print_error(text: str):
    """Print error message."""
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")


def verify_memory_bank_checked(new_version: str, release_title: str, dry_run: bool = False) -> bool:
    """
    Verify all Memory Bank files have been updated to the target version.
    
    This function ONLY VERIFIES - it does not display files.
    To read files, run: python scripts/check_memory_bank.py --for-release X.Y.Z
    """
    print(f"\n{Colors.HEADER}{'─'*70}{Colors.ENDC}")
    print(f"{Colors.HEADER}  Verifying Memory Bank Updates for v{new_version}{Colors.ENDC}")
    print(f"{Colors.HEADER}{'─'*70}{Colors.ENDC}\n")
    
    if dry_run:
        print(f"{Colors.WARNING}DRY RUN: Skipping verification{Colors.ENDC}\n")
        return True
    
    errors = []
    
    # Check version in key files
    version_checks = [
        ('docs/activeContext.md', r'\*\*Version:\*\*\s*([\d.]+)'),
        ('docs/progress.md', r'\*\*Version:\*\*\s*([\d.]+)'),
        ('docs/projectbrief.md', r'\*\*Version:\*\*\s*([\d.]+)'),
        ('VERSION', None),  # Special handling
        ('config.py', r"APP_VERSION\s*=\s*['\"]([^'\"]+)['\"]"),
    ]
    
    for filepath, pattern in version_checks:
        full_path = PROJECT_ROOT / filepath
        if not full_path.exists():
            errors.append(f"{filepath}: File not found")
            print(f"  {Colors.FAIL}✗ {filepath} - File not found{Colors.ENDC}")
            continue
        
        content = full_path.read_text()
        
        if pattern is None:  # VERSION file
            found_version = content.strip()
        else:
            match = re.search(pattern, content)
            found_version = match.group(1) if match else None
        
        if found_version == new_version:
            print(f"  {Colors.GREEN}✓ {filepath} - v{new_version}{Colors.ENDC}")
        else:
            errors.append(f"{filepath}: Found '{found_version}', expected '{new_version}'")
            print(f"  {Colors.FAIL}✗ {filepath} - Found '{found_version}', expected '{new_version}'{Colors.ENDC}")
    
    # Check systemPatterns.md coverage version
    patterns_path = PROJECT_ROOT / 'docs/systemPatterns.md'
    if patterns_path.exists():
        content = patterns_path.read_text()
        match = re.search(r'Current Coverage \(v([\d.]+)\)', content)
        if match:
            if match.group(1) == new_version:
                print(f"  {Colors.GREEN}✓ docs/systemPatterns.md - Coverage v{new_version}{Colors.ENDC}")
            else:
                errors.append(f"docs/systemPatterns.md: Coverage version is '{match.group(1)}'")
                print(f"  {Colors.FAIL}✗ docs/systemPatterns.md - Coverage shows v{match.group(1)}{Colors.ENDC}")
    
    # Check CHANGELOG has entry
    changelog_path = PROJECT_ROOT / 'CHANGELOG.md'
    if changelog_path.exists():
        content = changelog_path.read_text()
        if f'## [{new_version}]' in content:
            print(f"  {Colors.GREEN}✓ CHANGELOG.md - Entry for [{new_version}] found{Colors.ENDC}")
        else:
            errors.append(f"CHANGELOG.md: No entry for [{new_version}]")
            print(f"  {Colors.FAIL}✗ CHANGELOG.md - No entry for [{new_version}]{Colors.ENDC}")
    
    # Check README badge
    readme_path = PROJECT_ROOT / 'README.md'
    if readme_path.exists():
        content = readme_path.read_text()
        if f'version-{new_version}-blue' in content:
            print(f"  {Colors.GREEN}✓ README.md - Version badge updated{Colors.ENDC}")
        else:
            errors.append(f"README.md: Version badge not updated")
            print(f"  {Colors.FAIL}✗ README.md - Version badge not updated{Colors.ENDC}")
    
    print()
    
    if errors:
        print(f"{Colors.FAIL}{Colors.BOLD}{'='*70}{Colors.ENDC}")
        print(f"{Colors.FAIL}{Colors.BOLD}  ❌ VERIFICATION FAILED - Updates incomplete{Colors.ENDC}")
        print(f"{Colors.FAIL}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")
        
        print(f"{Colors.WARNING}The following files need updates:{Colors.ENDC}")
        for error in errors:
            print(f"  {Colors.FAIL}• {error}{Colors.ENDC}")
        
        print(f"\n{Colors.CYAN}First, read the Memory Bank files:{Colors.ENDC}")
        print(f"  python scripts/check_memory_bank.py --for-release {new_version}")
        print(f"\n{Colors.CYAN}Then verify your updates:{Colors.ENDC}")
        print(f"  python scripts/check_memory_bank.py --verify {new_version}")
        print()
        return False
    
    print(f"{Colors.GREEN}{Colors.BOLD}{'='*70}{Colors.ENDC}")
    print(f"{Colors.GREEN}{Colors.BOLD}  ✅ ALL MEMORY BANK FILES VERIFIED{Colors.ENDC}")
    print(f"{Colors.GREEN}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")
    
    return True


def run_command(cmd: str, check: bool = True, capture: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command."""
    result = subprocess.run(
        cmd,
        shell=True,
        cwd=PROJECT_ROOT,
        capture_output=capture,
        text=True
    )
    if check and result.returncode != 0:
        print_error(f"Command failed: {cmd}")
        if result.stderr:
            print(result.stderr)
        sys.exit(1)
    return result


def get_current_version() -> str:
    """Get current version from VERSION file."""
    version_file = PROJECT_ROOT / 'VERSION'
    if version_file.exists():
        return version_file.read_text().strip()
    return '0.0.0'


def parse_version(version: str) -> tuple:
    """Parse version string to tuple."""
    parts = version.split('.')
    return tuple(int(p) for p in parts)


def bump_version(current: str, bump_type: str) -> str:
    """Bump version based on type (major, minor, patch)."""
    major, minor, patch = parse_version(current)
    
    if bump_type == 'major':
        return f"{major + 1}.0.0"
    elif bump_type == 'minor':
        return f"{major}.{minor + 1}.0"
    elif bump_type == 'patch':
        return f"{major}.{minor}.{patch + 1}"
    else:
        raise ValueError(f"Invalid bump type: {bump_type}")


def check_clean_working_dir() -> bool:
    """Check if working directory is clean."""
    result = run_command("git status --porcelain", check=False)
    return len(result.stdout.strip()) == 0


def check_on_main_branch() -> bool:
    """Check if on main branch."""
    result = run_command("git branch --show-current")
    return result.stdout.strip() == 'main'


def update_version_in_file(filepath: str, pattern: str, replacement: str, version: str, dry_run: bool = False) -> bool:
    """Update version in a single file."""
    full_path = PROJECT_ROOT / filepath
    
    if not full_path.exists():
        print_warning(f"File not found: {filepath}")
        return False
    
    content = full_path.read_text()
    new_content = re.sub(pattern, replacement.format(version=version), content, flags=re.MULTILINE)
    
    if content == new_content:
        print_warning(f"No changes in: {filepath}")
        return False
    
    if not dry_run:
        full_path.write_text(new_content)
    
    print_success(f"Updated: {filepath}")
    return True


def update_changelog(version: str, title: str, dry_run: bool = False) -> bool:
    """Add new version section to CHANGELOG.md."""
    changelog_path = PROJECT_ROOT / 'CHANGELOG.md'
    
    if not changelog_path.exists():
        print_error("CHANGELOG.md not found!")
        return False
    
    content = changelog_path.read_text()
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Check if version already exists
    if f"## [{version}]" in content:
        print_warning(f"Version {version} already exists in CHANGELOG.md")
        return False
    
    # Find the position after the header (after first ---)
    header_end = content.find('---', content.find('---') + 3)
    if header_end == -1:
        header_end = 0
    else:
        header_end += 3
    
    # Create new version section
    new_section = f"""

## [{version}] - {today}

### {title}

#### Added
- TODO: Add new features

#### Changed
- TODO: Add changes

#### Fixed
- TODO: Add fixes

"""
    
    new_content = content[:header_end] + new_section + content[header_end:]
    
    if not dry_run:
        changelog_path.write_text(new_content)
    
    print_success(f"Added {version} section to CHANGELOG.md")
    print_warning("Remember to update CHANGELOG.md with actual changes!")
    return True


def get_git_changes_since_tag(previous_version: str) -> dict:
    """Get all changes since the previous version tag."""
    tag = f"v{previous_version}"
    
    # Get commits since last tag
    commits_result = run_command(f"git log {tag}..HEAD --oneline 2>/dev/null || git log --oneline -20", check=False)
    commits = commits_result.stdout.strip() if commits_result.returncode == 0 else "No previous tag found"
    
    # Get changed files since last tag
    files_result = run_command(f"git diff --name-status {tag}..HEAD 2>/dev/null || git diff --name-status HEAD~10..HEAD", check=False)
    changed_files = files_result.stdout.strip() if files_result.returncode == 0 else ""
    
    # Get diff summary (stats)
    diff_result = run_command(f"git diff --stat {tag}..HEAD 2>/dev/null || git diff --stat HEAD~10..HEAD", check=False)
    diff_summary = diff_result.stdout.strip() if diff_result.returncode == 0 else ""
    
    return {
        'commits': commits,
        'changed_files': changed_files,
        'diff_summary': diff_summary
    }


def read_memory_bank_docs() -> dict:
    """Read all Memory Bank documentation files."""
    docs = {}
    doc_files = [
        'activeContext.md',
        'progress.md', 
        'productContext.md',
        'techContext.md',
        'systemPatterns.md',
        'technicalConcept.md'
    ]
    
    for doc_file in doc_files:
        doc_path = PROJECT_ROOT / 'docs' / doc_file
        if doc_path.exists():
            docs[doc_file] = doc_path.read_text()
        else:
            docs[doc_file] = f"# {doc_file}\n\nFile not found."
    
    return docs


def generate_memory_bank_prompt(version: str, title: str, previous_version: str) -> str:
    """Generate a prompt for AI to update Memory Bank docs."""
    
    # Read the prompt template
    template_path = PROJECT_ROOT / 'scripts' / 'memory_bank_prompt.md'
    if not template_path.exists():
        print_error("memory_bank_prompt.md template not found!")
        return ""
    
    template = template_path.read_text()
    
    # Get git changes
    changes = get_git_changes_since_tag(previous_version)
    
    # Read current docs
    docs = read_memory_bank_docs()
    
    # Format the prompt
    prompt = template.format(
        version=version,
        title=title,
        date=datetime.now().strftime('%Y-%m-%d'),
        previous_version=previous_version,
        git_commits=changes['commits'],
        changed_files=changes['changed_files'],
        git_diff_summary=changes['diff_summary'],
        active_context=docs.get('activeContext.md', ''),
        progress=docs.get('progress.md', ''),
        product_context=docs.get('productContext.md', ''),
        tech_context=docs.get('techContext.md', ''),
        system_patterns=docs.get('systemPatterns.md', '')
    )
    
    return prompt


def update_memory_bank(version: str, title: str, previous_version: str, dry_run: bool = False) -> bool:
    """Update Memory Bank docs - generates prompt or calls AI API."""
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Generate the prompt
    prompt = generate_memory_bank_prompt(version, title, previous_version)
    
    if not prompt:
        return False
    
    # Save the prompt to a file for manual use or AI API call
    prompt_output_path = PROJECT_ROOT / 'scripts' / 'memory_bank_update_prompt.txt'
    
    if not dry_run:
        prompt_output_path.write_text(prompt)
    
    print_success(f"Generated Memory Bank update prompt")
    print(f"           Saved to: {Colors.CYAN}scripts/memory_bank_update_prompt.txt{Colors.ENDC}")
    
    # Update basic fields that can be done automatically
    docs_to_update = {
        'docs/activeContext.md': [
            (r'\*\*Date:\*\* \d{4}-\d{2}-\d{2}', f'**Date:** {today}'),
            (r'\*\*Version:\*\* [\d.]+', f'**Version:** {version}'),
        ],
        'docs/progress.md': [
            (r'\*\*Last Updated:\*\* \d{4}-\d{2}-\d{2}', f'**Last Updated:** {today}'),
            (r'\*\*Version:\*\* [\d.]+', f'**Version:** {version}'),
        ]
    }
    
    for filepath, patterns in docs_to_update.items():
        full_path = PROJECT_ROOT / filepath
        if full_path.exists():
            content = full_path.read_text()
            for pattern, replacement in patterns:
                content = re.sub(pattern, replacement, content)
            if not dry_run:
                full_path.write_text(content)
    
    print_success(f"Updated dates and versions in Memory Bank docs")
    
    # Check if we should try to call an AI API
    api_key = os.environ.get('ANTHROPIC_API_KEY') or os.environ.get('OPENAI_API_KEY')
    
    if api_key:
        print_warning("AI API key found - automatic update available")
        print(f"           Run: {Colors.CYAN}python scripts/update_memory_bank.py{Colors.ENDC}")
    else:
        print_warning("No AI API key found - manual update required")
        print(f"           1. Copy prompt from: scripts/memory_bank_update_prompt.txt")
        print(f"           2. Paste into Claude/ChatGPT")
        print(f"           3. Apply the generated updates to docs/")
    
    return True


def update_memory_bank_date(dry_run: bool = False):
    """Update date in Memory Bank docs. (Legacy - use update_memory_bank instead)"""
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Update activeContext.md date
    active_context = PROJECT_ROOT / 'docs/activeContext.md'
    if active_context.exists():
        content = active_context.read_text()
        # Update the date pattern
        new_content = re.sub(
            r'\*\*Date:\*\* \d{4}-\d{2}-\d{2}',
            f'**Date:** {today}',
            content
        )
        if content != new_content and not dry_run:
            active_context.write_text(new_content)
            print_success("Updated date in docs/activeContext.md")


def create_commit(version: str, title: str, dry_run: bool = False) -> bool:
    """Create release commit."""
    message = f"release: v{version} - {title}"
    
    if dry_run:
        print_success(f"Would create commit: {message}")
        return True
    
    run_command("git add -A")
    result = run_command(f'git commit -m "{message}"', check=False)
    
    if result.returncode == 0:
        print_success(f"Created commit: {message}")
        return True
    else:
        print_warning("No changes to commit")
        return False


def create_tag(version: str, title: str, dry_run: bool = False) -> bool:
    """Create git tag."""
    tag_name = f"v{version}"
    tag_message = f"v{version} - {title}"
    
    if dry_run:
        print_success(f"Would create tag: {tag_name}")
        return True
    
    # Check if tag already exists
    result = run_command(f"git tag -l {tag_name}", check=False)
    if result.stdout.strip():
        print_warning(f"Tag {tag_name} already exists")
        return False
    
    run_command(f'git tag -a {tag_name} -m "{tag_message}"')
    print_success(f"Created tag: {tag_name}")
    return True


def push_to_remote(version: str, dry_run: bool = False) -> bool:
    """Push commits and tags to remote."""
    if dry_run:
        print_success("Would push to origin (main + tags)")
        return True
    
    run_command("git push origin main")
    run_command(f"git push origin v{version}")
    print_success("Pushed to origin (main + tags)")
    return True


def interactive_mode() -> tuple:
    """Interactive mode to get version and title."""
    current = get_current_version()
    print(f"\nCurrent version: {Colors.BOLD}{current}{Colors.ENDC}")
    
    print("\nVersion bump options:")
    print(f"  1. Patch  ({bump_version(current, 'patch')})")
    print(f"  2. Minor  ({bump_version(current, 'minor')})")
    print(f"  3. Major  ({bump_version(current, 'major')})")
    print("  4. Custom version")
    
    choice = input("\nSelect option [1-4]: ").strip()
    
    if choice == '1':
        version = bump_version(current, 'patch')
    elif choice == '2':
        version = bump_version(current, 'minor')
    elif choice == '3':
        version = bump_version(current, 'major')
    elif choice == '4':
        version = input("Enter version (e.g., 1.13.0): ").strip()
    else:
        print_error("Invalid choice")
        sys.exit(1)
    
    title = input(f"\nRelease title (e.g., 'Feature XYZ'): ").strip()
    if not title:
        print_error("Title is required")
        sys.exit(1)
    
    return version, title


def main():
    parser = argparse.ArgumentParser(
        description='Release script for Deloitte ProjectOps',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('--version', '-v', help='New version number (e.g., 1.13.0)')
    parser.add_argument('--title', '-t', help='Release title')
    parser.add_argument('--dry-run', '-d', action='store_true', help='Preview changes without applying')
    parser.add_argument('--no-push', action='store_true', help='Skip pushing to remote')
    parser.add_argument('--skip-changelog', action='store_true', help='Skip CHANGELOG.md update')
    
    args = parser.parse_args()
    
    print_header("Deloitte ProjectOps Release Script")
    
    # Change to project root
    os.chdir(PROJECT_ROOT)
    
    if args.dry_run:
        print_warning("DRY RUN MODE - No changes will be made\n")
    
    # Step 1: Pre-flight checks
    print_step(1, "Running pre-flight checks...")
    
    if not check_on_main_branch():
        print_error("Not on main branch! Switch to main first.")
        sys.exit(1)
    print_success("On main branch")
    
    if not check_clean_working_dir():
        print_warning("Working directory has uncommitted changes")
        response = input("Continue anyway? [y/N]: ").strip().lower()
        if response != 'y':
            sys.exit(1)
    else:
        print_success("Working directory is clean")
    
    # Step 2: Get version info
    print_step(2, "Determining version...")
    
    current_version = get_current_version()
    print(f"Current version: {current_version}")
    
    if args.version:
        new_version = args.version
        title = args.title or input("Release title: ").strip()
    else:
        new_version, title = interactive_mode()
    
    print(f"\n{Colors.BOLD}New version: {new_version}{Colors.ENDC}")
    print(f"{Colors.BOLD}Title: {title}{Colors.ENDC}\n")
    
    if not args.dry_run:
        confirm = input("Proceed with release? [y/N]: ").strip().lower()
        if confirm != 'y':
            print("Release cancelled")
            sys.exit(0)
    
    # Step 3: Automated Memory Bank Update
    print_step(3, "Automated Memory Bank Update...")
    
    if not verify_memory_bank_checked(new_version, title, args.dry_run):
        print(f"\n{Colors.FAIL}{'='*70}{Colors.ENDC}")
        print(f"{Colors.FAIL}  RELEASE BLOCKED - Memory Bank update failed{Colors.ENDC}")
        print(f"{Colors.FAIL}{'='*70}{Colors.ENDC}\n")
        sys.exit(1)
    
    # Step 4: Update remaining version files (that weren't updated in step 3)
    print_step(4, "Updating version in files...")
    
    for filepath, config in VERSION_FILES.items():
        update_version_in_file(
            filepath,
            config['pattern'],
            config['replacement'],
            new_version,
            args.dry_run
        )
    
    # Step 5: Update CHANGELOG
    if not args.skip_changelog:
        print_step(5, "Updating CHANGELOG.md...")
        update_changelog(new_version, title, args.dry_run)
    
    # Step 6: Update Memory Bank docs (full update with AI prompt generation)
    print_step(6, "Updating Memory Bank docs...")
    update_memory_bank(new_version, title, current_version, args.dry_run)
    
    # Step 7: Create commit
    print_step(7, "Creating release commit...")
    create_commit(new_version, title, args.dry_run)
    
    # Step 8: Create tag
    print_step(8, "Creating git tag...")
    create_tag(new_version, title, args.dry_run)
    
    # Step 9: Push to remote
    if not args.no_push:
        print_step(9, "Pushing to remote...")
        push_to_remote(new_version, args.dry_run)
    else:
        print_step(9, "Skipping push (--no-push)")
    
    # Done!
    print_header("Release Complete! 🚀")
    print(f"""
{Colors.GREEN}Summary:{Colors.ENDC}
  Version:  {new_version}
  Title:    {title}
  Tag:      v{new_version}
  
{Colors.CYAN}Memory Bank files verified and updated.{Colors.ENDC}

{Colors.CYAN}Next steps:{Colors.ENDC}
  1. Create GitHub Release at:
     https://github.com/mkschulze/deloitte-projectops/releases/new?tag=v{new_version}
  2. Update GitHub 'About' description if needed
""")


if __name__ == '__main__':
    main()

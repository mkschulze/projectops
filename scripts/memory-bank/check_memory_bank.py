#!/usr/bin/env python3
"""
Memory Bank Review Script for Deloitte ProjectOps

This script displays all Memory Bank files and waits for confirmation
that they have been read and understood. Run this BEFORE release.py.

The workflow is:
  1. Display content of each Memory Bank file
  2. Wait for confirmation that files were read
  3. (Optional) Show what needs to be updated for a release

Usage:
    python scripts/check_memory_bank.py
    python scripts/check_memory_bank.py --for-release 1.17.0
"""

import argparse
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent.absolute()

# Memory Bank files to review
MEMORY_BANK_FILES = [
    ('docs/activeContext.md', 'Session info, version, current state'),
    ('docs/progress.md', 'Release history, milestones'),
    ('docs/projectbrief.md', 'Project overview, version'),
    ('docs/systemPatterns.md', 'Coverage stats, patterns'),
    ('docs/techContext.md', 'Tech stack, test counts'),
    ('docs/productContext.md', 'Product scope, features'),
    ('docs/technicalConcept.md', 'Architecture, roadmap'),
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
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}  {text}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")


def get_current_version() -> str:
    """Read current version from VERSION file."""
    version_file = PROJECT_ROOT / 'VERSION'
    if version_file.exists():
        return version_file.read_text().strip()
    return "unknown"


def display_memory_bank_files(target_version: str = None):
    """Display all Memory Bank files with full content."""
    
    current_version = get_current_version()
    
    print_header("📖 MEMORY BANK REVIEW")
    
    print(f"{Colors.CYAN}Current version: {current_version}{Colors.ENDC}")
    if target_version:
        print(f"{Colors.CYAN}Target version:  {target_version}{Colors.ENDC}")
    print()
    
    version_status = {}
    
    for filepath, description in MEMORY_BANK_FILES:
        full_path = PROJECT_ROOT / filepath
        
        print(f"\n{Colors.BOLD}{'═'*70}{Colors.ENDC}")
        print(f"{Colors.BOLD}📄 {filepath}{Colors.ENDC}")
        print(f"{Colors.CYAN}   Purpose: {description}{Colors.ENDC}")
        print(f"{'═'*70}\n")
        
        if not full_path.exists():
            print(f"{Colors.FAIL}   ❌ FILE NOT FOUND{Colors.ENDC}\n")
            version_status[filepath] = ('missing', None)
            continue
        
        content = full_path.read_text()
        lines = content.split('\n')
        
        # Display the COMPLETE file content
        for i, line in enumerate(lines, 1):
            # Highlight version patterns
            if '**Version:**' in line or 'Version:' in line:
                print(f"{Colors.WARNING}   {i:3}: {line}{Colors.ENDC}")
            elif 'Current Coverage' in line:
                print(f"{Colors.WARNING}   {i:3}: {line}{Colors.ENDC}")
            elif '## Session Information' in line or '## Recent Releases' in line:
                print(f"{Colors.CYAN}   {i:3}: {line}{Colors.ENDC}")
            elif line.startswith('###') or line.startswith('## '):
                print(f"{Colors.BOLD}   {i:3}: {line}{Colors.ENDC}")
            else:
                print(f"   {i:3}: {line}")
        
        print(f"\n   {Colors.CYAN}[END OF FILE - {len(lines)} lines total]{Colors.ENDC}")
        
        # Extract and display current version in file
        version_match = re.search(r'\*\*Version:\*\*\s*([\d.]+)', content)
        if version_match:
            file_version = version_match.group(1)
            version_status[filepath] = ('found', file_version)
            
            if target_version:
                if file_version == target_version:
                    print(f"\n   {Colors.GREEN}✓ Version: {file_version} (ready for {target_version}){Colors.ENDC}")
                else:
                    print(f"\n   {Colors.WARNING}⚠ Version: {file_version} → needs update to {target_version}{Colors.ENDC}")
            else:
                print(f"\n   {Colors.CYAN}Version in file: {file_version}{Colors.ENDC}")
        else:
            version_status[filepath] = ('no-version', None)
    
    return version_status


def show_update_instructions(target_version: str):
    """Show what needs to be updated for a release."""
    
    print(f"\n\n{Colors.HEADER}{'─'*70}{Colors.ENDC}")
    print(f"{Colors.HEADER}  📝 Updates Required for v{target_version}{Colors.ENDC}")
    print(f"{Colors.HEADER}{'─'*70}{Colors.ENDC}\n")
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    print(f"""{Colors.CYAN}To prepare for release v{target_version}, update these files:{Colors.ENDC}

  1. {Colors.BOLD}docs/activeContext.md{Colors.ENDC}
     - Update **Version:** to {target_version}
     - Update **Last Action:** to describe this release
     - Add accomplishments to "What Was Accomplished" section

  2. {Colors.BOLD}docs/progress.md{Colors.ENDC}
     - Update **Version:** to {target_version}
     - Add new release section under "## Recent Releases"

  3. {Colors.BOLD}docs/projectbrief.md{Colors.ENDC}
     - Update **Version:** to {target_version}

  4. {Colors.BOLD}docs/systemPatterns.md{Colors.ENDC}
     - Update "Current Coverage (vX.Y.Z)" to v{target_version}
     - Update test counts if changed

  5. {Colors.BOLD}docs/techContext.md{Colors.ENDC}
     - Update test file list if new tests added
     - Update any dependency changes

  6. {Colors.BOLD}docs/technicalConcept.md{Colors.ENDC}
     - Update feature roadmap status if features completed

  7. {Colors.BOLD}CHANGELOG.md{Colors.ENDC}
     - Add [{target_version}] - {today} section with actual changes

  8. {Colors.BOLD}VERSION, config.py, README.md{Colors.ENDC}
     - Update version to {target_version}
""")


def verify_versions(target_version: str) -> bool:
    """Verify all files have been updated to target version."""
    
    print(f"\n{Colors.HEADER}{'─'*70}{Colors.ENDC}")
    print(f"{Colors.HEADER}  🔍 Verifying Updates for v{target_version}{Colors.ENDC}")
    print(f"{Colors.HEADER}{'─'*70}{Colors.ENDC}\n")
    
    files_to_check = [
        ('docs/activeContext.md', r'\*\*Version:\*\*\s*([\d.]+)'),
        ('docs/progress.md', r'\*\*Version:\*\*\s*([\d.]+)'),
        ('docs/projectbrief.md', r'\*\*Version:\*\*\s*([\d.]+)'),
        ('VERSION', r'^([\d.]+)$'),
        ('config.py', r"APP_VERSION = '([\d.]+)'"),
        ('docs/systemPatterns.md', r'Current Coverage \(v([\d.]+)\)'),
        ('CHANGELOG.md', rf'\[{re.escape(target_version)}\]'),
        ('README.md', rf'version-{re.escape(target_version)}-blue'),
    ]
    
    all_ok = True
    failed = []
    
    for filepath, pattern in files_to_check:
        full_path = PROJECT_ROOT / filepath
        
        if not full_path.exists():
            print(f"  {Colors.FAIL}✗ {filepath} - FILE NOT FOUND{Colors.ENDC}")
            all_ok = False
            failed.append((filepath, 'File not found'))
            continue
        
        content = full_path.read_text()
        match = re.search(pattern, content, re.MULTILINE)
        
        if filepath == 'CHANGELOG.md':
            if match:
                print(f"  {Colors.GREEN}✓ {filepath} - Has [{target_version}] entry{Colors.ENDC}")
            else:
                print(f"  {Colors.FAIL}✗ {filepath} - No entry for [{target_version}]{Colors.ENDC}")
                all_ok = False
                failed.append((filepath, f'No entry for [{target_version}]'))
        elif filepath == 'README.md':
            if match:
                print(f"  {Colors.GREEN}✓ {filepath} - Version badge updated{Colors.ENDC}")
            else:
                print(f"  {Colors.FAIL}✗ {filepath} - Version badge not updated{Colors.ENDC}")
                all_ok = False
                failed.append((filepath, 'Version badge not updated'))
        else:
            if match:
                found_version = match.group(1)
                if found_version == target_version:
                    print(f"  {Colors.GREEN}✓ {filepath} - Version {found_version}{Colors.ENDC}")
                else:
                    print(f"  {Colors.FAIL}✗ {filepath} - Found '{found_version}', expected '{target_version}'{Colors.ENDC}")
                    all_ok = False
                    failed.append((filepath, f"Found '{found_version}', expected '{target_version}'"))
            else:
                print(f"  {Colors.FAIL}✗ {filepath} - Version pattern not found{Colors.ENDC}")
                all_ok = False
                failed.append((filepath, 'Version pattern not found'))
    
    if all_ok:
        print(f"\n{Colors.GREEN}{Colors.BOLD}{'='*70}{Colors.ENDC}")
        print(f"{Colors.GREEN}{Colors.BOLD}  ✅ ALL FILES VERIFIED - Ready for release{Colors.ENDC}")
        print(f"{Colors.GREEN}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")
    else:
        print(f"\n{Colors.FAIL}{Colors.BOLD}{'='*70}{Colors.ENDC}")
        print(f"{Colors.FAIL}{Colors.BOLD}  ❌ VERIFICATION FAILED - Updates incomplete{Colors.ENDC}")
        print(f"{Colors.FAIL}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")
        print(f"{Colors.WARNING}The following files still need updates:{Colors.ENDC}")
        for filepath, reason in failed:
            print(f"  • {filepath}: {reason}")
        print()
    
    return all_ok


def main():
    parser = argparse.ArgumentParser(
        description='Review Memory Bank files before release'
    )
    parser.add_argument(
        '--for-release',
        type=str,
        help='Target version for release (shows update instructions)'
    )
    parser.add_argument(
        '--verify',
        type=str,
        help='Verify all files are updated to this version'
    )
    parser.add_argument(
        '--brief',
        action='store_true',
        help='Only show version status, not full file content'
    )
    
    args = parser.parse_args()
    
    if args.verify:
        # Just verify versions match
        success = verify_versions(args.verify)
        sys.exit(0 if success else 1)
    
    if args.brief:
        # Brief mode - just show current versions
        print_header("📖 MEMORY BANK VERSION CHECK")
        current_version = get_current_version()
        print(f"{Colors.CYAN}Current version (VERSION file): {current_version}{Colors.ENDC}\n")
        
        for filepath, description in MEMORY_BANK_FILES:
            full_path = PROJECT_ROOT / filepath
            if full_path.exists():
                content = full_path.read_text()
                version_match = re.search(r'\*\*Version:\*\*\s*([\d.]+)', content)
                if version_match:
                    file_version = version_match.group(1)
                    if file_version == current_version:
                        print(f"  {Colors.GREEN}✓ {filepath}: {file_version}{Colors.ENDC}")
                    else:
                        print(f"  {Colors.WARNING}⚠ {filepath}: {file_version} (differs from {current_version}){Colors.ENDC}")
                else:
                    print(f"  {Colors.CYAN}○ {filepath}: (no version field){Colors.ENDC}")
            else:
                print(f"  {Colors.FAIL}✗ {filepath}: FILE NOT FOUND{Colors.ENDC}")
        print()
        sys.exit(0)
    
    # Full review mode
    display_memory_bank_files(args.for_release)
    
    if args.for_release:
        show_update_instructions(args.for_release)
    
    print(f"\n{Colors.BOLD}Memory Bank review complete.{Colors.ENDC}")
    print(f"{Colors.CYAN}After making updates, run: python scripts/check_memory_bank.py --verify {args.for_release or '<version>'}{Colors.ENDC}\n")


if __name__ == '__main__':
    main()

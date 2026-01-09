#!/usr/bin/env python3
"""
Memory Bank Update Script for Deloitte ProjectOps

This script uses an AI API (Claude or OpenAI) to automatically update
the Memory Bank documentation based on git changes.

Prerequisites:
    - Set ANTHROPIC_API_KEY or OPENAI_API_KEY environment variable
    - Run release.py first to generate the prompt

Usage:
    python scripts/update_memory_bank.py [--apply] [--provider anthropic|openai]
    
Examples:
    python scripts/update_memory_bank.py              # Preview mode
    python scripts/update_memory_bank.py --apply      # Apply changes
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.absolute()

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    ENDC = '\033[0m'


def print_success(text: str):
    print(f"{Colors.GREEN}✓ {text}{Colors.ENDC}")


def print_warning(text: str):
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")


def print_error(text: str):
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")


def call_anthropic_api(prompt: str) -> str:
    """Call Anthropic Claude API."""
    try:
        import anthropic
    except ImportError:
        print_error("anthropic package not installed. Run: pip install anthropic")
        sys.exit(1)
    
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print_error("ANTHROPIC_API_KEY not set")
        sys.exit(1)
    
    client = anthropic.Anthropic(api_key=api_key)
    
    print(f"{Colors.CYAN}Calling Claude API...{Colors.ENDC}")
    
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=8000,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    return message.content[0].text


def call_openai_api(prompt: str) -> str:
    """Call OpenAI API."""
    try:
        import openai
    except ImportError:
        print_error("openai package not installed. Run: pip install openai")
        sys.exit(1)
    
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        print_error("OPENAI_API_KEY not set")
        sys.exit(1)
    
    client = openai.OpenAI(api_key=api_key)
    
    print(f"{Colors.CYAN}Calling OpenAI API...{Colors.ENDC}")
    
    response = client.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=[
            {"role": "user", "content": prompt}
        ],
        max_tokens=8000
    )
    
    return response.choices[0].message.content


def parse_ai_response(response: str) -> dict:
    """Parse AI response to extract file updates."""
    updates = {}
    
    # Find all code blocks with filenames
    pattern = r'```(\w+\.md)\n(.*?)```'
    matches = re.findall(pattern, response, re.DOTALL)
    
    for filename, content in matches:
        updates[filename] = content.strip()
    
    return updates


def apply_updates(updates: dict, apply: bool = False) -> None:
    """Apply or preview updates to Memory Bank docs."""
    
    if not updates:
        print_warning("No updates found in AI response")
        return
    
    for filename, content in updates.items():
        filepath = PROJECT_ROOT / 'docs' / filename
        
        if not filepath.exists():
            print_warning(f"File not found: docs/{filename}")
            continue
        
        if apply:
            filepath.write_text(content)
            print_success(f"Updated: docs/{filename}")
        else:
            print(f"\n{Colors.BOLD}Would update: docs/{filename}{Colors.ENDC}")
            print(f"{Colors.CYAN}Preview (first 500 chars):{Colors.ENDC}")
            print(content[:500] + "..." if len(content) > 500 else content)
            print()


def main():
    parser = argparse.ArgumentParser(
        description='Update Memory Bank docs using AI',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--apply', '-a', action='store_true', 
                        help='Apply changes (default is preview)')
    parser.add_argument('--provider', '-p', choices=['anthropic', 'openai'],
                        default='anthropic', help='AI provider to use')
    parser.add_argument('--prompt-file', default='scripts/memory_bank_update_prompt.txt',
                        help='Path to prompt file')
    
    args = parser.parse_args()
    
    # Read the generated prompt
    prompt_path = PROJECT_ROOT / args.prompt_file
    
    if not prompt_path.exists():
        print_error(f"Prompt file not found: {args.prompt_file}")
        print_warning("Run release.py first to generate the prompt")
        sys.exit(1)
    
    prompt = prompt_path.read_text()
    print_success(f"Loaded prompt from: {args.prompt_file}")
    
    # Call the AI API
    if args.provider == 'anthropic':
        response = call_anthropic_api(prompt)
    else:
        response = call_openai_api(prompt)
    
    print_success("Received AI response")
    
    # Parse and apply updates
    updates = parse_ai_response(response)
    
    if not args.apply:
        print_warning("PREVIEW MODE - No changes will be made")
        print_warning("Run with --apply to apply changes")
    
    apply_updates(updates, args.apply)
    
    if args.apply:
        print_success("Memory Bank docs updated!")
        print_warning("Review the changes and commit if correct")
    else:
        print(f"\n{Colors.CYAN}To apply changes, run:{Colors.ENDC}")
        print(f"  python scripts/update_memory_bank.py --apply")


if __name__ == '__main__':
    main()

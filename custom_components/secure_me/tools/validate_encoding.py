#!/usr/bin/env python3
"""
Secure Me - UTF-8 Encoding Validator
Prevents garbled Unicode characters in JavaScript files
"""

import sys
import re

def validate_file(filepath):
    """Check for garbled UTF-8 sequences."""
    
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    
    # Patterns that indicate corrupted UTF-8
    bad_patterns = [
        (r'Ã[ƒÂ°Å…¸¢â€š™œÂ¡¨¯¼‹"]+', 'Corrupted UTF-8 sequence'),
        (r'‚[€¬Â]+', 'Corrupted smart quotes'),
        (r'Æ[\'"]', 'Corrupted Latin characters'),
    ]
    
    issues = []
    for pattern, description in bad_patterns:
        matches = re.finditer(pattern, content)
        for match in matches:
            line_num = content[:match.start()].count('\n') + 1
            issues.append(f"Line {line_num}: {description} - '{match.group()}'")
    
    if issues:
        print(f"❌ VALIDATION FAILED: {filepath}")
        print(f"\nFound {len(issues)} encoding issues:\n")
        for issue in issues[:10]:  # Show first 10
            print(f"  {issue}")
        if len(issues) > 10:
            print(f"\n  ... and {len(issues) - 10} more")
        return False
    else:
        print(f"✅ VALIDATION PASSED: {filepath}")
        print("   No garbled UTF-8 characters found")
        return True

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 validate_encoding.py <filepath>")
        sys.exit(1)
    
    filepath = sys.argv[1]
    if not validate_file(filepath):
        sys.exit(1)

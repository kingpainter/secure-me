#!/usr/bin/env python3
"""
Secure Me - UTF-8 Encoding Cleanup Script
Automatically fixes garbled Unicode in JavaScript files
"""

import sys
import re

def clean_file(filepath):
    """Remove all garbled UTF-8 sequences."""
    
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    
    original_size = len(content)
    
    # Remove garbled UTF-8 sequences
    replacements = {
        # Module icons - remove completely
        r'<span style="font-size:24px">[^<]*[ÃÆ‚€¬]+[^<]*</span>': '<span style="font-size:24px"></span>',
        r'<span style="font-size:28px;">[^<]*[ÃÆ‚€¬]+[^<]*</span>': '<span style="font-size:28px"></span>',
        
        # Checkmarks
        r'[ÃÆ‚€¬Å""]+(?=</span>)': '✓',
        
        # Close buttons
        r'(data-action="(?:close|remove)-[^"]*"[^>]*>)[ÃÆ‚€¬×]+': r'\1×',
        
        # Clean console.log
        r'console\.log\([\'"][^\'\"]*[ÃÆ‚€¬]+DEBUG:', 'console.log(\'DEBUG:',
        
        # Generic cleanup
        r'Ã[ƒÂ°Å…¸¢â€šâ€™â€œÂ¡Â¨Â¯Â¼Ã‹Å"]+': '',
        r'‚[€¬Â]+': '',
        r'Æ\'[^a-zA-Z\s]': '',
    }
    
    fixed_count = 0
    for pattern, replacement in replacements.items():
        new_content, count = re.subn(pattern, replacement, content)
        if count > 0:
            fixed_count += count
            content = new_content
            print(f"  ✓ Fixed {count} instances: {pattern[:40]}...")
    
    if fixed_count == 0:
        print(f"✅ File is already clean: {filepath}")
        return True
    
    # Backup original
    backup = filepath + '.backup'
    with open(backup, 'w', encoding='utf-8') as f:
        with open(filepath, 'r', encoding='utf-8') as orig:
            f.write(orig.read())
    print(f"\n  💾 Backup saved: {backup}")
    
    # Write cleaned version
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"\n✅ CLEANED: {filepath}")
    print(f"   Fixed {fixed_count} garbled sequences")
    print(f"   Size: {original_size} → {len(content)} bytes")
    return True

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 clean_encoding.py <filepath>")
        sys.exit(1)
    
    filepath = sys.argv[1]
    clean_file(filepath)

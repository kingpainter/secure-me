#!/usr/bin/env python3
# VERSION = "0.9.0"
"""Clean corrupted UTF-8 encoding in files."""
import sys
import re

def clean_file(filepath):
    """Remove corrupted UTF-8 sequences from file."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        
        # Replace common corrupted sequences
        replacements = {
            # Corrupted bullets/dots
            r'[ÃƒÆâ€™€¬Â¢]+': '****',
            # Other corrupted UTF-8
            r'Ã[ƒÆ‚€¬]+': '',
            r'â€[™˜]+': '',
        }
        
        for pattern, replacement in replacements.items():
            content = re.sub(pattern, replacement, content)
        
        # Write cleaned content
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✓ Cleaned: {filepath}")
        return True
        
    except Exception as e:
        print(f"✗ Error cleaning {filepath}: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 clean_encoding.py <filepath>")
        sys.exit(1)
    
    filepath = sys.argv[1]
    success = clean_file(filepath)
    sys.exit(0 if success else 1)

#!/usr/bin/env python3
"""
Secure Me - Version Consistency Validator
Run before every commit to ensure all files have the same version.

Usage:
    python3 validate_version.py           # Auto-detect version from manifest.json
    python3 validate_version.py 1.1.0     # Validate against specific version
    python3 validate_version.py --fix     # Auto-fix all version mismatches
"""
import sys
import re
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent  # tools/../ = custom_components/secure_me/


def get_manifest_version() -> str:
    """Read the canonical version from manifest.json."""
    manifest = ROOT / "manifest.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    return data["version"]


def check_file(path: Path, version: str, patterns: list[tuple]) -> list[str]:
    errors = []
    if not path.exists():
        return [f"FILE NOT FOUND: {path}"]

    content = path.read_text(encoding="utf-8")
    for pattern, description in patterns:
        matches = re.findall(pattern, content)
        for match in matches:
            if match != version:
                errors.append(
                    f"  {path.name}: {description} is '{match}' (expected '{version}')"
                )
    return errors


def fix_file(path: Path, version: str, replacements: list[tuple]) -> bool:
    if not path.exists():
        return False

    content = original = path.read_text(encoding="utf-8")
    for pattern, replacement in replacements:
        flags = re.MULTILINE if pattern.startswith("^") else 0
        content = re.sub(pattern, replacement.replace("VERSION", version), content, flags=flags)

    if content != original:
        path.write_text(content, encoding="utf-8")
        return True
    return False


# === File definitions ===
FILES = [
    {
        "path": ROOT / "manifest.json",
        "check": [(r'"version":\s*"([\d.]+)"', "manifest version")],
        "fix": [(r'"version":\s*"[\d.]+"', '"version": "VERSION"')],
    },
    {
        "path": ROOT / "const.py",
        "check": [
            (r'^# VERSION = "([\d.]+)"', "version comment"),
            (r'^VERSION = "([\d.]+)"', "VERSION constant"),
        ],
        "fix": [
            (r'^# VERSION = "[\d.]+"', '# VERSION = "VERSION"'),
            (r'^VERSION = "[\d.]+"', 'VERSION = "VERSION"'),
        ],
    },
    {
        "path": ROOT / "panel.py",
        "check": [
            (r'^# VERSION = "([\d.]+)"', "version comment"),
            (r'^VERSION = "([\d.]+)"', "VERSION constant"),
        ],
        "fix": [
            (r'^# VERSION = "[\d.]+"', '# VERSION = "VERSION"'),
            (r'^VERSION = "[\d.]+"', 'VERSION = "VERSION"'),
        ],
    },
    {
        "path": ROOT / "frontend" / "secure-me-panel.js",
        "check": [
            (r'const VERSION = "([\d.]+)"', "JS VERSION constant"),
        ],
        "fix": [
            (r'const VERSION = "[\d.]+"', 'const VERSION = "VERSION"'),
        ],
    },
]

# All .py files get version comment check
PY_COMMENT_FILES = [
    f for f in list(ROOT.glob("*.py")) + list((ROOT / "modules").glob("*.py"))
    if f.name not in ("const.py", "panel.py", "validate_version.py")
]
for py_file in PY_COMMENT_FILES:
    FILES.append({
        "path": py_file,
        "check": [(r'^# VERSION = "([\d.]+)"', "version comment")],
        "fix": [(r'^# VERSION = "[\d.]+"', '# VERSION = "VERSION"')],
    })


def main():
    args = sys.argv[1:]
    fix_mode = "--fix" in args
    args = [a for a in args if a != "--fix"]

    try:
        version = args[0] if args else get_manifest_version()
    except Exception as e:
        print(f"ERROR: Could not read manifest.json: {e}")
        sys.exit(1)

    print(f"Secure Me - Version Consistency Check")
    print(f"Target version: {version}")
    print(f"Mode: {'AUTO-FIX' if fix_mode else 'CHECK'}")
    print("-" * 50)

    all_errors = []

    for file_def in FILES:
        path = file_def["path"]

        if fix_mode:
            changed = fix_file(path, version, file_def["fix"])
            if changed:
                print(f"  FIXED  {path.name}")
        else:
            errors = []
            if not path.exists():
                errors.append(f"  FILE NOT FOUND: {path}")
            else:
                content = path.read_text(encoding="utf-8")
                for pattern, description in file_def["check"]:
                    flags = re.MULTILINE if pattern.startswith("^") else 0
                    matches = re.findall(pattern, content, flags)
                    for match in matches:
                        if match != version:
                            errors.append(
                                f"  {path.name}: {description} = '{match}' (expected '{version}')"
                            )
            all_errors.extend(errors)

    if fix_mode:
        print("\nAll files fixed! Run without --fix to verify.")
        sys.exit(0)

    if all_errors:
        print(f"\nFAIL - {len(all_errors)} version mismatch(es) found:\n")
        for err in all_errors:
            print(err)
        print(f"\nFix with:  python3 validate_version.py --fix")
        sys.exit(1)
    else:
        print(f"\nPASS - All files consistent at version {version}")
        sys.exit(0)


if __name__ == "__main__":
    main()

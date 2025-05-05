#!/usr/bin/env python3
"""
This script patches app code to use our mock modules for testing.

Usage:
    python patch_imports.py [directory] [pattern]

    directory: The directory to search for files (default: app)
    pattern: Optional filename pattern to filter files
"""
import sys
import os
import re
import argparse
import logging
from pathlib import Path
from typing import List, Dict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Define imports that should be mocked
MOCK_IMPORTS = {
    "keycloak": "from tests.mocks.mock_keycloak import keycloak # Mocked for testing",
}


def backup_file(file_path: str) -> bool:
    """Create a backup of the file if it doesn't already exist."""
    backup_path = f"{file_path}.bak"
    if not os.path.exists(backup_path):
        try:
            with open(file_path, "r") as src, open(backup_path, "w") as dst:
                dst.write(src.read())
            logger.debug(f"Created backup: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to create backup for {file_path}: {e}")
            return False
    return True


def patch_file(file_path: str) -> bool:
    """Patches a file to use our mock modules."""
    if not os.path.exists(file_path):
        logger.warning(f"File {file_path} doesn't exist")
        return False

    try:
        with open(file_path, "r") as f:
            content = f.read()

        # Create backup of the original file
        if not backup_file(file_path):
            return False

        # Flag to track if any changes were made
        modified = False

        # Process the content for each mock import
        for module, replacement in MOCK_IMPORTS.items():
            # Check if the file imports this module
            module_import_patterns = [
                rf"from\s+{module}(\.\w+)?\s+import\s+.*",
                rf"import\s+{module}(\.\w+)?\s+.*"
            ]

            for pattern in module_import_patterns:
                if re.search(pattern, content):
                    # Replace the import statement
                    new_content = re.sub(pattern, replacement, content)
                    if new_content != content:
                        content = new_content
                        modified = True

        # Only write the file if changes were made
        if modified:
            with open(file_path, "w") as f:
                f.write(content)
            logger.info(f"Patched {file_path}")
            return True
        else:
            logger.debug(f"No changes needed for {file_path}")
            return False

    except Exception as e:
        logger.error(f"Error patching {file_path}: {e}")
        return False


def find_and_patch_files(directory: str, pattern: str = "") -> Dict[str, int]:
    """Find and patch files matching the pattern in the directory."""
    result = {"patched": 0, "skipped": 0, "failed": 0}

    # Convert to Path object for easier handling
    dir_path = Path(directory)
    if not dir_path.exists() or not dir_path.is_dir():
        logger.error(f"Directory {directory} doesn't exist or is not a directory")
        return result

    # Find all Python files
    for file_path in dir_path.glob("**/*.py"):
        file_str = str(file_path)

        # Skip if pattern is provided and doesn't match
        if pattern and pattern not in file_str:
            result["skipped"] += 1
            continue

        # Skip backup files
        if file_str.endswith(".bak"):
            result["skipped"] += 1
            continue

        # Skip files in the tests/mocks directory
        if "tests/mocks" in file_str:
            result["skipped"] += 1
            continue

        # Patch the file
        if patch_file(file_str):
            result["patched"] += 1
        else:
            result["failed"] += 1

    return result


def restore_backups(directory: str) -> int:
    """Restore backed up files."""
    restored = 0
    dir_path = Path(directory)

    for backup_path in dir_path.glob("**/*.py.bak"):
        original_path = str(backup_path)[:-4]  # Remove .bak extension
        try:
            with open(backup_path, "r") as src, open(original_path, "w") as dst:
                dst.write(src.read())
            logger.info(f"Restored {original_path}")
            restored += 1
        except Exception as e:
            logger.error(f"Failed to restore {original_path}: {e}")

    return restored


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Patch Python files to use mock modules for testing")
    parser.add_argument("directory", nargs="?", default="app", help="Directory to search for files")
    parser.add_argument("pattern", nargs="?", default="", help="Optional filename pattern to filter files")
    parser.add_argument("--restore", action="store_true", help="Restore files from backups")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    # Set log level
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    if args.restore:
        restored = restore_backups(args.directory)
        logger.info(f"Restored {restored} files")
    else:
        result = find_and_patch_files(args.directory, args.pattern)
        logger.info(f"Patched {result['patched']} files, skipped {result['skipped']}, failed {result['failed']}")
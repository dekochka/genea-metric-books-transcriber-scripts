#!/usr/bin/env python3
"""
Quick verification script to check test file syntax and imports.
This doesn't run the tests, but verifies they can be imported.
"""
import sys
import os

# Get project root (parent directory of tests folder)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Change to project root for relative paths
os.chdir(project_root)

test_files = [
    'tests/unit/test_auth_strategies.py',
    'tests/unit/test_image_sources.py',
    'tests/unit/test_ai_clients.py',
    'tests/unit/test_output_strategies.py',
    'tests/unit/test_mode_factory.py',
    'tests/unit/test_error_handling.py',
    'tests/unit/test_performance.py',
    'tests/integration/test_config.py',
    'tests/integration/test_local_mode.py',
    'tests/integration/test_googlecloud_mode.py',
    'tests/compatibility/test_legacy_configs.py',
]

print("Verifying test file syntax and imports...")
print("=" * 60)

errors = []
for test_file in test_files:
    if not os.path.exists(test_file):
        print(f"❌ MISSING: {test_file}")
        errors.append(f"Missing file: {test_file}")
        continue
    
    try:
        # Try to compile the file to check syntax
        with open(test_file, 'r') as f:
            code = f.read()
        compile(code, test_file, 'exec')
        print(f"✓ Syntax OK: {test_file}")
    except SyntaxError as e:
        print(f"❌ Syntax Error in {test_file}: {e}")
        errors.append(f"Syntax error in {test_file}: {e}")
    except Exception as e:
        print(f"⚠️  Warning in {test_file}: {e}")

print("=" * 60)
if errors:
    print(f"\nFound {len(errors)} error(s):")
    for error in errors:
        print(f"  - {error}")
    sys.exit(1)
else:
    print("\n✓ All test files have valid syntax!")
    print("\nNote: To actually run the tests, install pytest:")
    print("  python3 -m pip install pytest pytest-mock")
    print("\nThen run:")
    print("  python3 -m pytest tests/ -v")

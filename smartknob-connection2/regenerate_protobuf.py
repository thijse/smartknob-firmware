#!/usr/bin/env python3
"""
Convenience script to regenerate protobuf files from the project root.

This script can be run from anywhere in the smartknob-connection2 project
to regenerate the protobuf files when the .proto definitions change.

Usage:
    python regenerate_protobuf.py
"""

import sys
from pathlib import Path

def main():
    """Run the protobuf generator."""
    script_path = Path(__file__).absolute().parent
    generator_script = script_path / "protobuf" / "generate_protobuf.py"
    
    if not generator_script.exists():
        print(f"ERROR: Generator script not found: {generator_script}", file=sys.stderr)
        return False
    
    print("SmartKnob Protobuf Regeneration")
    print("=" * 40)
    print(f"Running generator: {generator_script}")
    print()
    
    # Import and run the generator
    sys.path.insert(0, str(generator_script.parent))
    try:
        import generate_protobuf
        return generate_protobuf.main() is None  # main() returns None on success
    except SystemExit as e:
        return e.code == 0
    except Exception as e:
        print(f"ERROR: Failed to run generator: {e}", file=sys.stderr)
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)

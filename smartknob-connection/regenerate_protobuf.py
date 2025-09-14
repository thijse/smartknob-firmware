#!/usr/bin/env python3
"""
Convenience script to regenerate protobuf files from the project root.

This script can be run from anywhere in the smartknob-connection2 project
to regenerate the protobuf files when the .proto definitions change.

FIRST TIME SETUP:
    1. Initialize nanopb submodule (REQUIRED for C++ generation):
       git submodule update --init --recursive
    
    2. Install Python dependencies:
       pip install grpcio-tools

Usage:
    python regenerate_protobuf.py [args...]
    
All arguments are passed through to generate_protobuf.py.
Examples:
    python regenerate_protobuf.py --all      # Generate both Python and C++
    python regenerate_protobuf.py --python   # Python only
    python regenerate_protobuf.py --cpp      # C++ only
"""

import sys
from pathlib import Path

def main():
    """Run the protobuf generator with forwarded arguments."""
    script_path = Path(__file__).absolute().parent
    generator_script = script_path / "protobuf" / "generate_protobuf.py"
    
    if not generator_script.exists():
        print(f"ERROR: Generator script not found: {generator_script}", file=sys.stderr)
        return False
    
    print("SmartKnob Protobuf Regeneration")
    print("=" * 40)
    print(f"Running generator: {generator_script}")
    print(f"Arguments: {' '.join(sys.argv[1:]) if len(sys.argv) > 1 else '(default)'}")
    print()
    
    # Import and run the generator with forwarded arguments
    sys.path.insert(0, str(generator_script.parent))
    try:
        # Forward command line arguments to the generator
        sys.argv[0] = str(generator_script)  # Update script name for argparse
        import generate_protobuf  # noqa: F401 - runtime import from protobuf/
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

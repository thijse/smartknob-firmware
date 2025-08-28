#!/usr/bin/env python3
"""
Unified SmartKnob Protobuf Generator

Generates both Python and C++ (nanopb) protobuf files from the same .proto sources.
This ensures consistency between Python client and C++ firmware.
"""

import subprocess
import sys
import shutil
from pathlib import Path
import importlib.util

# Paths
REPO_ROOT = Path(__file__).parent.absolute()
PROTO_DIR = REPO_ROOT / "proto"
PYTHON_OUTPUT = REPO_ROOT / "smartknob-connection2" / "smartknob" / "proto_gen"
CPP_OUTPUT = REPO_ROOT / "firmware" / "src" / "proto" / "proto_gen"
NANOPB_DIR = REPO_ROOT / "proto" / "thirdparty" / "nanopb"

def check_dependencies():
    """Check if required tools are available."""
    print("🔍 Checking dependencies...")
    
    # Check protoc
    try:
        result = subprocess.run(["protoc", "--version"], capture_output=True, text=True)
        print(f"✅ protoc: {result.stdout.strip()}")
    except FileNotFoundError:
        print("❌ protoc not found! Install Protocol Buffers compiler.")
        return False
    
    # Check grpcio-tools for Python
    try:
        spec = importlib.util.find_spec("grpc_tools.protoc")
        if spec is not None:
            print("✅ grpcio-tools: Available")
        else:
            raise ImportError()
    except ImportError:
        print("❌ grpcio-tools not found! Run: pip install grpcio-tools")
        return False
    
    # Check nanopb
    nanopb_generator = NANOPB_DIR / "generator"
    if nanopb_generator.exists() and (nanopb_generator / "nanopb_generator.py").exists():
        print(f"✅ nanopb: Found at {nanopb_generator}")
    else:
        print(f"❌ nanopb not found! Expected at {nanopb_generator}")
        print("   Make sure git submodules are initialized: git submodule update --init")
        return False
    
    return True

def generate_python_protobuf():
    """Generate Python protobuf files."""
    print("\n🐍 Generating Python protobuf files...")
    
    # Ensure output directory exists
    PYTHON_OUTPUT.mkdir(parents=True, exist_ok=True)
    
    # Backup existing files if they exist
    backup_dir = PYTHON_OUTPUT.parent / "proto_gen_backup"
    if any(PYTHON_OUTPUT.glob("*.py")):
        print(f"📁 Backing up existing files to: {backup_dir}")
        if backup_dir.exists():
            shutil.rmtree(backup_dir)
        shutil.copytree(PYTHON_OUTPUT, backup_dir)
    
    # Create __init__.py
    (PYTHON_OUTPUT / "__init__.py").touch()
    
    # Generate Python files using grpcio-tools
    cmd = [
        sys.executable, "-m", "grpc_tools.protoc",
        f"--python_out={PYTHON_OUTPUT}",
        f"--proto_path={PROTO_DIR}",
        f"--proto_path={NANOPB_DIR / 'generator' / 'proto'}",  # For nanopb.proto
        "settings.proto",
        "smartknob.proto"
    ]
    
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=REPO_ROOT)
    
    if result.returncode == 0:
        print("✅ Python protobuf generation successful!")
        
        # List generated files
        for file in PYTHON_OUTPUT.glob("*_pb2.py"):
            print(f"   📄 {file.name}")
    else:
        print("❌ Python protobuf generation failed!")
        return False
    
    return True

def generate_nanopb_protobuf():
    """Generate C++ nanopb protobuf files."""
    print("\n⚙️ Generating C++ (nanopb) protobuf files...")
    
    # Ensure output directory exists
    CPP_OUTPUT.mkdir(parents=True, exist_ok=True)
    
    # Backup existing files if they exist
    backup_files = []
    for ext in ["*.pb.h", "*.pb.c"]:
        backup_files.extend(CPP_OUTPUT.glob(ext))
    
    if backup_files:
        print(f"📁 Backing up {len(backup_files)} existing C++ files...")
        for file in backup_files:
            backup_file = file.with_suffix(file.suffix + ".backup")
            shutil.copy2(file, backup_file)
    
    # Use nanopb generator directly with Python
    nanopb_generator = NANOPB_DIR / "generator" / "nanopb_generator.py"
    
    # Generate for each proto file
    proto_files = ["settings.proto", "smartknob.proto"]
    
    for proto_file in proto_files:
        proto_path = PROTO_DIR / proto_file
        if not proto_path.exists():
            print(f"❌ Proto file not found: {proto_path}")
            return False
        
        print(f"   Generating {proto_file}...")
        
        cmd = [
            sys.executable, str(nanopb_generator),
            f"--output-dir={CPP_OUTPUT}",
            f"--proto-path={PROTO_DIR}",
            f"--proto-path={NANOPB_DIR / 'generator' / 'proto'}",  # For nanopb.proto
            str(proto_path)
        ]
        
        result = subprocess.run(cmd, cwd=REPO_ROOT)
        
        if result.returncode != 0:
            print(f"❌ Failed to generate {proto_file}")
            return False
    
    print("✅ C++ (nanopb) protobuf generation successful!")
    
    # List generated files
    for ext in ["*.pb.h", "*.pb.c"]:
        for file in CPP_OUTPUT.glob(ext):
            print(f"   📄 {file.name}")
    
    return True

def verify_generation():
    """Verify that both Python and C++ files were generated correctly."""
    print("\n🔍 Verifying generated files...")
    
    # Check Python files
    python_files = list(PYTHON_OUTPUT.glob("*_pb2.py"))
    expected_python = ["settings_pb2.py", "smartknob_pb2.py"]
    
    missing_python = [f for f in expected_python if not (PYTHON_OUTPUT / f).exists()]
    if not missing_python:
        print(f"✅ Python: {len(python_files)} files generated")
    else:
        print(f"❌ Python: Missing files: {missing_python}")
        return False
    
    # Check C++ files
    expected_cpp = ["settings.pb.h", "settings.pb.c", "smartknob.pb.h", "smartknob.pb.c"]
    missing_cpp = [f for f in expected_cpp if not (CPP_OUTPUT / f).exists()]
    
    if not missing_cpp:
        print(f"✅ C++: {len(expected_cpp)} files generated")
    else:
        print(f"❌ C++: Missing files: {missing_cpp}")
        return False
    
    # Quick check for our new component messages in C++ header
    smartknob_h = CPP_OUTPUT / "smartknob.pb.h"
    if smartknob_h.exists():
        content = smartknob_h.read_text()
        if "PB_AppComponent" in content and "PB_ToggleConfig" in content and "PB_ComponentType" in content:
            print("✅ New component messages found in C++ header")
        else:
            print("⚠️  New component messages NOT found in C++ header (may need firmware rebuild)")
    
    # Check Python component messages
    smartknob_py = PYTHON_OUTPUT / "smartknob_pb2.py"
    if smartknob_py.exists():
        content = smartknob_py.read_text()
        if "AppComponent" in content and "ToggleConfig" in content and "ComponentType" in content:
            print("✅ New component messages found in Python module")
        else:
            print("⚠️  New component messages NOT found in Python module")
    
    return True

def update_python_imports():
    """Fix import statements in generated Python files."""
    print("\n🔧 Fixing Python import statements...")
    
    files_to_fix = [
        ("settings_pb2.py", "nanopb_pb2"),
        ("smartknob_pb2.py", "settings_pb2")
    ]
    
    for filename, import_to_fix in files_to_fix:
        file_path = PYTHON_OUTPUT / filename
        if file_path.exists():
            content = file_path.read_text()
            
            # Fix relative imports
            if f"import {import_to_fix}" in content:
                content = content.replace(
                    f"import {import_to_fix}",
                    f"from . import {import_to_fix}"
                )
                file_path.write_text(content)
                print(f"   ✅ Fixed imports in {filename}")
    
    # Update __init__.py
    init_file = PYTHON_OUTPUT / "__init__.py"
    init_content = '''"""SmartKnob Protocol Buffer Generated Files"""

from .settings_pb2 import *
from .smartknob_pb2 import *

__all__ = ['settings_pb2', 'smartknob_pb2']
'''
    init_file.write_text(init_content)
    print("   ✅ Updated __init__.py")

def main():
    """Main generation workflow."""
    print("🚀 SmartKnob Unified Protobuf Generator")
    print("=" * 50)
    print(f"Repository root: {REPO_ROOT}")
    print(f"Proto directory: {PROTO_DIR}")
    print(f"Python output: {PYTHON_OUTPUT}")
    print(f"C++ output: {CPP_OUTPUT}")
    print()
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Dependency check failed. Please install missing components.")
        return 1
    
    # Generate Python files
    if not generate_python_protobuf():
        print("\n❌ Python generation failed.")
        return 1
    
    # Generate C++ files
    if not generate_nanopb_protobuf():
        print("\n❌ C++ generation failed.")
        return 1
    
    # Fix Python imports
    update_python_imports()
    
    # Verify everything worked
    if not verify_generation():
        print("\n❌ Verification failed.")
        return 1
    
    print("\n🎉 All protobuf files generated successfully!")
    print()
    print("📂 Generated files:")
    print(f"   Python: {PYTHON_OUTPUT}")
    print(f"   C++:    {CPP_OUTPUT}")
    print()
    print("🔄 Next steps:")
    print("1. Test Python: cd smartknob-connection2 && python test_component_messages.py")
    print("2. Build firmware: cd firmware && platformio run")
    print("3. Verify new component messages are available in both Python and C++")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

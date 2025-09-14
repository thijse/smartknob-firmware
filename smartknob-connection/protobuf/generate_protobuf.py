#!/usr/bin/env python3
"""
SmartKnob Protobuf Generation Script (Python + C++)

Generates Python and C++ protobuf files from shared .proto definitions,
enabling communication between Python clients and C++ firmware.

Features:
    - Python protobuf generation using grpcio-tools
    - C++ nanopb generation for embedded firmware
    - Unified generation with --all flag
    - Automatic import fixing and backup management
    - Support for AppComponent system (remote app configuration)

Usage:
    python generate_protobuf.py [--python] [--cpp] [--all]

Arguments:
    --python    Generate Python files only (default)
    --cpp       Generate C++ nanopb files only  
    --all       Generate both Python and C++ files

Generated Files:
    Python:  smartknob/proto_gen/*.py     (for smartknob-connection2 client)
    C++:     ../../firmware/src/proto/proto_gen/*.pb.h/.pb.c  (for firmware)

Setup Requirements:
    1. Install Python dependencies:
       pip install grpcio-tools>=1.50.0
    
    2. Initialize git submodules (REQUIRED for C++ generation):
       git submodule update --init --recursive
       
    3. Verify nanopb submodule exists:
       ls ../../proto/thirdparty/nanopb/generator/nanopb_generator.py
       
Common Issues:
    - "nanopb_generator.py not found" → Run git submodule update --init --recursive
    - "grpcio-tools not found" → Activate virtual environment or pip install grpcio-tools
"""

import sys
import shutil
import filecmp
import argparse
import subprocess
from pathlib import Path

def cleanup_old_backups(backup_base_path, keep_count=3):
    """Remove old backup directories, keeping only the latest N."""
    if not backup_base_path.parent.exists():
        return
        
    backup_pattern = f"{backup_base_path.name}*"
    backups = sorted(
        backup_base_path.parent.glob(backup_pattern), 
        key=lambda p: p.stat().st_mtime if p.exists() else 0,
        reverse=True
    )
    
    for old_backup in backups[keep_count:]:
        if old_backup.is_dir():
            shutil.rmtree(old_backup)
            print(f"🗑️ Removed old backup: {old_backup.name}")

def check_grpcio_tools():
    """Check if grpcio-tools is available for Python-only protoc."""
    try:
        import grpc_tools.protoc  # noqa: F401
        print("✅ Found grpcio-tools (Python protoc)")
        return True
    except ImportError:
        print("❌ grpcio-tools not found!")
        print("Install with: pip install grpcio-tools>=1.50.0")
        return False

def generate_protobuf():
    """Generate Python protobuf files from .proto definitions using Python-only approach."""
    script_path = Path(__file__).absolute().parent
    repo_root = script_path.parent.parent  # Go up two levels to reach the repo root
    
    # Paths
    proto_path = repo_root / "proto"
    output_path = script_path.parent / "smartknob" / "proto_gen"  # Output to smartknob-connection2/smartknob/proto_gen
    nanopb_path = repo_root / "proto" / "thirdparty" / "nanopb"
    backup_path = output_path.parent / "proto_gen_backup"
    
    print(f"Script path: {script_path}")
    print(f"Proto path: {proto_path}")
    print(f"Output path: {output_path}")
    
    # Validate paths
    if not proto_path.exists():
        print(f"ERROR: Proto directory not found: {proto_path}", file=sys.stderr)
        return False
    
    if not nanopb_path.exists():
        print(f"WARNING: Nanopb submodule not found: {nanopb_path}")
        print("Some imports may not work. Run: git submodule update --init --recursive")
    
    # Check grpcio-tools
    if not check_grpcio_tools():
        return False
    
    # Find .proto files
    proto_files = list(proto_path.glob("*.proto"))
    if not proto_files:
        print("ERROR: No .proto files found!", file=sys.stderr)
        return False
    
    print(f"Found {len(proto_files)} proto files: {[f.name for f in proto_files]}")
    
    # Backup existing files for comparison
    if output_path.exists():
        if backup_path.exists():
            shutil.rmtree(backup_path)
        shutil.copytree(output_path, backup_path)
        print(f"📁 Backed up existing files to: {backup_path}")
        
        # Clean up old backups
        cleanup_old_backups(backup_path)
    
    # Create output directory
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Generate Python protobuf files using grpcio-tools
    print("Generating Python protobuf files using grpcio-tools...")
    try:
        from grpc_tools import protoc
        
        # Build protoc arguments
        protoc_args = [
            'protoc',
            f'--python_out={output_path}',
            f'--proto_path={proto_path}',
            f'--proto_path={script_path}'  # Include current directory for nanopb.proto
        ]
        
        # Add nanopb path if available (for completeness)
        nanopb_proto_path = nanopb_path / "generator" / "proto"
        if nanopb_proto_path.exists():
            protoc_args.append(f'--proto_path={nanopb_proto_path}')
            print("✅ Using nanopb proto path")
        else:
            print("ℹ️  Using local nanopb.proto file")
        
        # Add Google protobuf include path (needed for descriptor.proto)
        try:
            import grpc_tools
            grpc_tools_path = Path(grpc_tools.__file__).parent
            protobuf_include_path = grpc_tools_path / "_proto"
            if protobuf_include_path.exists():
                protoc_args.append(f'--proto_path={protobuf_include_path}')
                print(f"✅ Using grpcio-tools protobuf include path: {protobuf_include_path}")
            else:
                # Try alternative path
                protobuf_include_path = grpc_tools_path / "protoc_lib_deps" / "_proto"
                if protobuf_include_path.exists():
                    protoc_args.append(f'--proto_path={protobuf_include_path}')
                    print(f"✅ Using grpcio-tools protobuf include path (alt): {protobuf_include_path}")
                else:
                    print(f"⚠️  grpcio-tools protobuf include path not found: {protobuf_include_path}")
        except Exception as e:
            print(f"⚠️  Could not find grpcio-tools include path: {e}")
        
        # Add proto files
        protoc_args.extend([str(f) for f in proto_files])
        
        print(f"Running: {' '.join(protoc_args)}")
        
        # Run protoc via Python
        result = protoc.main(protoc_args)
        
        if result != 0:
            print(f"ERROR: Protobuf generation failed with code {result}", file=sys.stderr)
            return False
            
        print("✅ Python protobuf generation successful!")
        
    except Exception as e:
        print(f"ERROR: Protobuf generation failed: {e}", file=sys.stderr)
        return False
    
    # Copy nanopb_pb2.py if available
    if nanopb_path.exists():
        nanopb_pb2_source = nanopb_path / "generator" / "proto" / "nanopb_pb2.py"
        if nanopb_pb2_source.exists():
            nanopb_pb2_dest = output_path / "nanopb_pb2.py"
            shutil.copy2(nanopb_pb2_source, nanopb_pb2_dest)
            print("✅ Copied nanopb_pb2.py")
        else:
            print("⚠️  nanopb_pb2.py not found, skipping")
    
    # Fix import statements in generated files (convert absolute to relative imports)
    generated_files = [f for f in output_path.glob("*_pb2.py")]
    for pb_file in generated_files:
        if pb_file.name == "nanopb_pb2.py":
            continue  # Skip nanopb_pb2.py as it doesn't import other pb2 files
            
        with open(pb_file, 'r') as f:
            content = f.read()
        
        # Fix absolute imports to relative imports
        original_content = content
        content = content.replace('import nanopb_pb2 as nanopb__pb2', 'from . import nanopb_pb2 as nanopb__pb2')
        content = content.replace('import settings_pb2 as settings__pb2', 'from . import settings_pb2 as settings__pb2')
        content = content.replace('import smartknob_pb2 as smartknob__pb2', 'from . import smartknob_pb2 as smartknob__pb2')
        
        if content != original_content:
            with open(pb_file, 'w') as f:
                f.write(content)
            print(f"✅ Fixed imports in {pb_file.name}")
    
    # Create/update __init__.py
    init_file = output_path / "__init__.py"
    
    init_content = '"""\nGenerated Protobuf Classes\n\nThis module contains the generated protobuf classes for SmartKnob communication.\n"""\n\n'
    
    for pb_file in generated_files:
        module_name = pb_file.stem
        init_content += f"from . import {module_name}\n"
    
    init_content += f'\n__all__ = {[f.stem for f in generated_files]}\n'
    
    with open(init_file, 'w') as f:
        f.write(init_content)
    
    print(f"✅ Updated __init__.py with {len(generated_files)} modules")
    
    # Compare with backup if available
    if backup_path.exists():
        print("\n🔍 Comparing with previous files...")
        changes_detected = False
        
        for pb_file in generated_files:
            backup_file = backup_path / pb_file.name
            if backup_file.exists():
                if filecmp.cmp(pb_file, backup_file, shallow=False):
                    print(f"   ✅ {pb_file.name}: No changes")
                else:
                    print(f"   🔄 {pb_file.name}: Changes detected")
                    changes_detected = True
            else:
                print(f"   ➕ {pb_file.name}: New file")
                changes_detected = True
        
        if not changes_detected:
            print("✅ All files identical - data model unchanged")
        else:
            print("⚠️  Changes detected - data model may have been updated")
    
    # Summary
    print("\n" + "="*60)
    print("PROTOBUF GENERATION COMPLETE")
    print("="*60)
    print(f"Generated files in: {output_path}")
    for pb_file in generated_files:
        print(f"  - {pb_file.name}")
    
    print("\nTo use in your code:")
    print("  from smartknob.proto_gen import smartknob_pb2, settings_pb2")
    
    return True

def generate_cpp_protobuf():
    """
    Generate C++ nanopb protobuf files for firmware.
    
    Creates .pb.h and .pb.c files in firmware/src/proto/proto_gen/
    using the nanopb generator from the git submodule.
    
    Requires:
        - nanopb submodule checked out at ../../proto/thirdparty/nanopb/
        - Python 3.6+
        
    Generates:
        - smartknob.pb.h/c: Main protocol with AppComponent support
        - settings.pb.h/c: Settings protocol messages
    """
    print("\n🔧 Generating C++ nanopb files...")
    print("\nSTARTING C++ NANOPB GENERATION")
    print("="*60)
    
    # Get paths
    script_dir = Path(__file__).parent.absolute()
    workspace_root = script_dir.parent.parent
    proto_dir = workspace_root / "proto"
    nanopb_dir = proto_dir / "thirdparty" / "nanopb"
    firmware_proto_dir = workspace_root / "firmware" / "src" / "proto" / "proto_gen"
    
    print(f"Script dir: {script_dir}")
    print(f"Workspace root: {workspace_root}")
    print(f"Proto dir: {proto_dir}")
    print(f"Nanopb dir: {nanopb_dir}")
    print(f"Output dir: {firmware_proto_dir}")
    
    # Verify nanopb is available
    if not nanopb_dir.exists():
        print(f"❌ Nanopb directory not found: {nanopb_dir}")
        print("   Please ensure the nanopb submodule is checked out:")
        print("   git submodule update --init --recursive")
        return False
    
    nanopb_generator = nanopb_dir / "generator" / "nanopb_generator.py"
    if not nanopb_generator.exists():
        print(f"❌ Nanopb generator not found: {nanopb_generator}")
        return False
    
    # Verify proto files exist
    proto_files = ["smartknob.proto", "settings.proto"]
    for proto_file in proto_files:
        proto_path = proto_dir / proto_file
        if not proto_path.exists():
            print(f"❌ Proto file not found: {proto_path}")
            return False
        print(f"✅ Found: {proto_file}")
    
    # Create output directory
    firmware_proto_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate C++ files for each proto
    generated_files = []
    
    for proto_file in proto_files:
        print(f"\n📦 Generating C++ files for {proto_file}...")
        
        # Build nanopb generator command
        cmd = [
            sys.executable,
            str(nanopb_generator),
            f"--proto-path={proto_dir}",
            f"--proto-path={nanopb_dir}/generator/proto",
            f"--output-dir={firmware_proto_dir}",
            str(proto_dir / proto_file)
        ]
        
        print(f"Running: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print(f"✅ Generated C++ files for {proto_file}")
            if result.stdout:
                print(f"   Output: {result.stdout}")
                
            # Track generated files
            base_name = proto_file.replace('.proto', '')
            generated_files.extend([
                f"{base_name}.pb.h",
                f"{base_name}.pb.c"
            ])
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to generate C++ files for {proto_file}")
            print(f"   Error: {e.stderr}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error generating {proto_file}: {e}")
            return False
    
    # Verify generated files
    print("\n🔍 Verifying generated files...")
    for file_name in generated_files:
        file_path = firmware_proto_dir / file_name
        if file_path.exists():
            print(f"✅ {file_name}")
        else:
            print(f"❌ Missing: {file_name}")
            return False
    
    print("\nC++ NANOPB GENERATION COMPLETE")
    print("="*60)
    print(f"Generated files in: {firmware_proto_dir}")
    for file_name in generated_files:
        print(f"  - {file_name}")
    
    print("\nTo use in your C++ code:")
    print("  #include \"smartknob.pb.h\"")
    print("  #include \"settings.pb.h\"")
    
    return True

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="SmartKnob Protobuf Generator")
    parser.add_argument("--python", action="store_true", help="Generate Python files only")
    parser.add_argument("--cpp", action="store_true", help="Generate C++ files only")
    parser.add_argument("--all", action="store_true", help="Generate both Python and C++ files")
    
    args = parser.parse_args()
    
    # Default to Python only if no flags specified
    if not (args.python or args.cpp or args.all):
        args.python = True
    
    print("SmartKnob Protobuf Generator")
    print("="*50)
    
    success = True
    
    if args.python or args.all:
        print("🐍 Generating Python protobuf files...")
        if not generate_protobuf():
            success = False
    
    if args.cpp or args.all:
        print("🔧 Generating C++ nanopb files...")
        if not generate_cpp_protobuf():
            success = False
    
    if not success:
        sys.exit(1)
    
    print("\n🎉 All done! Protobuf files are ready to use.")
    print("\n📋 Next steps:")
    print("   1. Test Python components: cd .. && python examples/test_component_messages.py")
    print("   2. Build firmware: cd ../../firmware && platformio run")
    print("   3. Flash & test: platformio upload && platformio device monitor")

if __name__ == "__main__":
    main()

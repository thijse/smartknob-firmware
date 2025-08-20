#!/usr/bin/env python3
"""
SmartKnob Protobuf Generation Script (Python-Only)

This script generates Python protobuf files from the .proto definitions,
keeping them in sync with the firmware build process.

Uses grpcio-tools for Python-only protobuf compilation (no external protoc needed).

Usage:
    python generate_protobuf.py

Requirements:
    - grpcio-tools (pip install grpcio-tools)
    - Access to ../proto/ directory with .proto files
"""

import os
import sys
import shutil
import filecmp
from pathlib import Path

def check_grpcio_tools():
    """Check if grpcio-tools is available for Python-only protoc."""
    try:
        from grpc_tools import protoc
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
            print(f"✅ Copied nanopb_pb2.py")
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
    
    print(f"\nTo use in your code:")
    print(f"  from smartknob.proto_gen import smartknob_pb2, settings_pb2")
    
    return True

def main():
    """Main function."""
    print("SmartKnob Protobuf Generator (Python-Only)")
    print("="*50)
    
    if not generate_protobuf():
        sys.exit(1)
    
    print("\n🎉 All done! Protobuf files are ready to use.")

if __name__ == "__main__":
    main()

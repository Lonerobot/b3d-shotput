#!/usr/bin/env python3
"""
Release Automation Script for Shotput Blender Addon

This script automates the release process:
1. Reads version from shotput/__init__.py
2. Checks if a GitHub tag exists for this version (creates if not)
3. Updates RELEASE-TEMPLATE.md with version information
4. Zips the shotput directory
5. Copies the zip to the releases folder
"""

import os
import sys
import re
import shutil
import zipfile
import subprocess
from pathlib import Path
from datetime import datetime


def get_version_from_init():
    """Extract version tuple from __init__.py"""
    init_path = Path(__file__).parent / "shotput" / "__init__.py"
    
    if not init_path.exists():
        print(f"❌ Error: {init_path} not found")
        sys.exit(1)
    
    with open(init_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find version in bl_info
    match = re.search(r'"version":\s*\((\d+),\s*(\d+),\s*(\d+)\)', content)
    if not match:
        print("❌ Error: Could not find version in __init__.py")
        sys.exit(1)
    
    version = f"{match.group(1)}.{match.group(2)}.{match.group(3)}"
    print(f"📋 Found version: v{version}")
    return version


def check_git_repo():
    """Check if we're in a git repository"""
    try:
        subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            check=True,
            capture_output=True,
            text=True
        )
        return True
    except subprocess.CalledProcessError:
        print("⚠️  Warning: Not in a git repository")
        return False


def tag_exists(tag_name):
    """Check if a git tag exists locally or remotely"""
    try:
        # Check local tags
        result = subprocess.run(
            ["git", "tag", "-l", tag_name],
            check=True,
            capture_output=True,
            text=True
        )
        if result.stdout.strip():
            return True
        
        # Check remote tags
        result = subprocess.run(
            ["git", "ls-remote", "--tags", "origin", f"refs/tags/{tag_name}"],
            check=True,
            capture_output=True,
            text=True
        )
        return bool(result.stdout.strip())
    except subprocess.CalledProcessError:
        return False


def create_git_tag(version):
    """Create a git tag for the version"""
    tag_name = f"v{version}"
    
    if not check_git_repo():
        print("⏭️  Skipping tag creation (not a git repo)")
        return
    
    if tag_exists(tag_name):
        print(f"✅ Tag {tag_name} already exists")
        return
    
    try:
        # Create annotated tag
        subprocess.run(
            ["git", "tag", "-a", tag_name, "-m", f"Release version {version}"],
            check=True
        )
        print(f"✅ Created tag: {tag_name}")
        
        # Ask if user wants to push the tag
        response = input(f"Push tag {tag_name} to remote? (y/N): ").strip().lower()
        if response == 'y':
            subprocess.run(["git", "push", "origin", tag_name], check=True)
            print(f"✅ Pushed tag {tag_name} to remote")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error creating/pushing tag: {e}")


def update_release_template(version):
    """Update RELEASE-TEMPLATE.md with current version"""
    template_path = Path(__file__).parent / "releases" / "RELEASE-TEMPLATE.md"
    
    if not template_path.exists():
        print(f"⚠️  Warning: {template_path} not found, skipping template update")
        return
    
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace version numbers
    content = re.sub(r'v\d+\.\d+\.\d+', f'v{version}', content)
    
    with open(template_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Updated RELEASE-TEMPLATE.md with version {version}")


def zip_shotput_directory(version):
    """Create a zip file of the shotput directory"""
    shotput_dir = Path(__file__).parent / "shotput"
    releases_dir = Path(__file__).parent / "releases"
    zip_filename = f"Shotput-v{version}.zip"
    zip_path = releases_dir / zip_filename
    
    if not shotput_dir.exists():
        print(f"❌ Error: {shotput_dir} not found")
        sys.exit(1)
    
    # Ensure releases directory exists
    releases_dir.mkdir(exist_ok=True)
    
    # Remove existing zip if present
    if zip_path.exists():
        response = input(f"⚠️  {zip_filename} already exists. Overwrite? (y/N): ").strip().lower()
        if response != 'y':
            print("❌ Cancelled by user")
            sys.exit(0)
        zip_path.unlink()
    
    print(f"📦 Creating zip: {zip_filename}")
    
    # Create zip file
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(shotput_dir):
            # Skip __pycache__ and .pyc files
            dirs[:] = [d for d in dirs if d != '__pycache__']
            
            for file in files:
                if file.endswith('.pyc'):
                    continue
                
                file_path = Path(root) / file
                arcname = file_path.relative_to(shotput_dir.parent)
                zipf.write(file_path, arcname)
                print(f"  + {arcname}")
    
    file_size = zip_path.stat().st_size / 1024  # KB
    print(f"✅ Created {zip_filename} ({file_size:.1f} KB)")
    print(f"📁 Location: {zip_path}")
    
    return zip_path


def main():
    """Main execution function"""
    print("=" * 60)
    print("🚀 Shotput Release Automation")
    print("=" * 60)
    print()
    
    # Get version
    version = get_version_from_init()
    print()
    
    # Check/create git tag
    create_git_tag(version)
    print()
    
    # Update release template
    update_release_template(version)
    print()
    
    # Create zip
    zip_path = zip_shotput_directory(version)
    print()
    
    print("=" * 60)
    print("✨ Release preparation complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Review the zip file in the releases folder")
    print("2. Go to GitHub and create a new release")
    print(f"3. Upload {zip_path.name} as the release asset")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

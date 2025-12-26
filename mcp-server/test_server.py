#!/usr/bin/env python3
"""Test script for OpenTryOn MCP Server."""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import config


def test_configuration():
    """Test configuration loading and validation."""
    print("=" * 60)
    print("Testing Configuration")
    print("=" * 60)
    
    # Print configuration status
    print(config.get_status_message())
    
    # Validate configuration
    status = config.validate()
    
    print("\nConfiguration Validation:")
    for service, is_configured in status.items():
        status_icon = "✓" if is_configured else "✗"
        print(f"  {status_icon} {service}: {'Configured' if is_configured else 'Not configured'}")
    
    # Check if at least one service is configured
    if any(status.values()):
        print("\n✓ At least one service is configured")
        return True
    else:
        print("\n✗ No services are configured")
        print("Please configure API keys in .env file")
        return False


def test_imports():
    """Test that all modules can be imported."""
    print("\n" + "=" * 60)
    print("Testing Module Imports")
    print("=" * 60)
    
    modules_to_test = [
        ("config", "Configuration module"),
        ("utils", "Utilities module"),
        ("utils.image_utils", "Image utilities"),
        ("utils.validation", "Validation utilities"),
        ("tools", "Tools module"),
        ("tools.virtual_tryon", "Virtual try-on tools"),
        ("tools.image_gen", "Image generation tools"),
        ("tools.video_gen", "Video generation tools"),
        ("tools.preprocessing", "Preprocessing tools"),
        ("tools.datasets", "Dataset tools"),
    ]
    
    all_passed = True
    for module_name, description in modules_to_test:
        try:
            __import__(module_name)
            print(f"  ✓ {description}: OK")
        except ImportError as e:
            print(f"  ✗ {description}: FAILED - {e}")
            all_passed = False
        except Exception as e:
            print(f"  ✗ {description}: ERROR - {e}")
            all_passed = False
    
    return all_passed


def test_tool_definitions():
    """Test that tool definitions are valid."""
    print("\n" + "=" * 60)
    print("Testing Tool Definitions")
    print("=" * 60)
    
    try:
        from server import TOOLS
        
        print(f"\nFound {len(TOOLS)} tools:")
        
        categories = {
            "Virtual Try-On": [],
            "Image Generation": [],
            "Video Generation": [],
            "Preprocessing": [],
            "Datasets": []
        }
        
        for tool in TOOLS:
            if "virtual_tryon" in tool.name:
                categories["Virtual Try-On"].append(tool.name)
            elif "generate_image" in tool.name:
                categories["Image Generation"].append(tool.name)
            elif "generate_video" in tool.name:
                categories["Video Generation"].append(tool.name)
            elif tool.name in ["segment_garment", "extract_garment", "segment_human"]:
                categories["Preprocessing"].append(tool.name)
            elif "load_" in tool.name:
                categories["Datasets"].append(tool.name)
        
        for category, tools in categories.items():
            if tools:
                print(f"\n{category} ({len(tools)} tools):")
                for tool_name in tools:
                    print(f"  - {tool_name}")
        
        print(f"\n✓ All {len(TOOLS)} tools loaded successfully")
        return True
        
    except Exception as e:
        print(f"\n✗ Failed to load tools: {e}")
        return False


def test_opentryon_imports():
    """Test that OpenTryOn library can be imported."""
    print("\n" + "=" * 60)
    print("Testing OpenTryOn Library Imports")
    print("=" * 60)
    
    opentryon_modules = [
        ("tryon.api", "API adapters"),
        ("tryon.preprocessing", "Preprocessing"),
        ("tryon.datasets", "Datasets"),
    ]
    
    all_passed = True
    for module_name, description in opentryon_modules:
        try:
            __import__(module_name)
            print(f"  ✓ {description}: OK")
        except ImportError as e:
            print(f"  ✗ {description}: FAILED - {e}")
            print(f"     Make sure OpenTryOn is installed: pip install -e /path/to/opentryon")
            all_passed = False
        except Exception as e:
            print(f"  ✗ {description}: ERROR - {e}")
            all_passed = False
    
    return all_passed


def test_directory_structure():
    """Test that required directories exist."""
    print("\n" + "=" * 60)
    print("Testing Directory Structure")
    print("=" * 60)
    
    base_dir = Path(__file__).parent
    
    required_dirs = [
        (".", "MCP server root"),
        ("tools", "Tools directory"),
        ("utils", "Utils directory"),
        ("examples", "Examples directory"),
    ]
    
    required_files = [
        ("server.py", "Main server file"),
        ("config.py", "Configuration file"),
        ("requirements.txt", "Requirements file"),
        ("README.md", "README file"),
    ]
    
    all_passed = True
    
    print("\nDirectories:")
    for dir_path, description in required_dirs:
        full_path = base_dir / dir_path
        if full_path.exists() and full_path.is_dir():
            print(f"  ✓ {description}: {dir_path}")
        else:
            print(f"  ✗ {description}: {dir_path} (missing)")
            all_passed = False
    
    print("\nFiles:")
    for file_path, description in required_files:
        full_path = base_dir / file_path
        if full_path.exists() and full_path.is_file():
            print(f"  ✓ {description}: {file_path}")
        else:
            print(f"  ✗ {description}: {file_path} (missing)")
            all_passed = False
    
    return all_passed


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("OpenTryOn MCP Server - Test Suite")
    print("=" * 60)
    
    tests = [
        ("Directory Structure", test_directory_structure),
        ("Configuration", test_configuration),
        ("Module Imports", test_imports),
        ("OpenTryOn Library", test_opentryon_imports),
        ("Tool Definitions", test_tool_definitions),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n✗ {test_name} test crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"  {status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests passed! Server is ready to use.")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())


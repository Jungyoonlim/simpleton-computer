#!/usr/bin/env python3
"""
Quick test to see if the core functionality works without FastAPI
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

def test_imports():
    print("Testing imports...")
    
    try:
        from core.typesys.types import Type, Doc, List as TypeList, Comment
        print("✓ Core types imported successfully")
    except Exception as e:
        print(f"✗ Core types import failed: {e}")
        return False
    
    try:
        from core.actions import list_actions_for, run
        print("✓ Actions imported successfully")
    except Exception as e:
        print(f"✗ Actions import failed: {e}")
        return False
    
    try:
        from fileio.files import DocValue
        print("✓ File IO imported successfully")
    except Exception as e:
        print(f"✗ File IO import failed: {e}")
        return False
    
    return True

def test_type_system():
    print("\nTesting type system...")
    
    from core.typesys.types import Type, Doc, List as TypeList, unify
    
    # Test basic types
    doc_type = Doc
    list_doc_type = TypeList(Doc)
    
    print(f"✓ Doc type: {doc_type}")
    print(f"✓ List[Doc] type: {list_doc_type}")
    
    # Test unification
    result = unify(doc_type, doc_type)
    if result is not False:
        print("✓ Type unification works")
    else:
        print("✗ Type unification failed")
        return False
    
    return True

def test_actions():
    print("\nTesting actions...")
    
    from core.typesys.types import Doc
    from core.actions import list_actions_for
    from fileio.files import DocValue
    
    # Test action discovery
    actions = list_actions_for(Doc)
    print(f"✓ Found {len(actions)} actions for Doc type:")
    for name, action in actions.items():
        print(f"  - {name}: {action.input_t} -> {action.output_t}")
    
    if len(actions) == 0:
        print("⚠ No actions found - this might be expected if none are registered yet")
    
    return True

def test_file_processing():
    print("\nTesting file processing...")
    
    from fileio.files import DocValue
    
    # Create a test document
    test_doc = DocValue(path="test.md", text="# Test Document\n\nThis is a test.")
    print(f"✓ Created DocValue: {test_doc.path}")
    print(f"✓ Content preview: {test_doc.text[:50]}...")
    
    return True

def main():
    print("🔧 Testing Simpleton Computer Core Functionality\n")
    
    tests = [
        test_imports,
        test_type_system, 
        test_actions,
        test_file_processing
    ]
    
    passed = 0
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print(f"❌ {test.__name__} failed")
        except Exception as e:
            print(f"❌ {test.__name__} crashed: {e}")
    
    print(f"\n📊 Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All tests passed! Core functionality is working.")
        print("💡 The backend should work once FastAPI is installed.")
        return True
    else:
        print("🚨 Some tests failed. Need to fix core issues first.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

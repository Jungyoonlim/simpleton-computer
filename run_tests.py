#!/usr/bin/env python3
"""
Test runner script for simpleton-computer typesystem tests.

Usage:
    python run_tests.py              # Run all tests
    python run_tests.py basic        # Run basic type tests
    python run_tests.py containers   # Run container type tests  
    python run_tests.py unification  # Run unification tests
    python run_tests.py rows         # Run row type tests
    python run_tests.py effects      # Run effect system tests
    python run_tests.py --coverage   # Run with coverage report
"""
import sys
import subprocess
from pathlib import Path

def run_pytest(args):
    """Run pytest with given arguments."""
    cmd = ["python", "-m", "pytest"] + args
    return subprocess.run(cmd, cwd=Path(__file__).parent)

def main():
    if len(sys.argv) == 1:
        # Run all tests
        print("Running all typesystem tests...")
        result = run_pytest(["tests/", "-v"])
        
    elif sys.argv[1] == "--coverage":
        # Run with coverage
        print("Running tests with coverage...")
        result = run_pytest([
            "tests/", 
            "--cov=core.typesys", 
            "--cov-report=html", 
            "--cov-report=term-missing"
        ])
        
    elif sys.argv[1] == "basic":
        print("Running basic type tests...")
        result = run_pytest(["tests/test_types_basic.py", "-v"])
        
    elif sys.argv[1] == "containers":
        print("Running container type tests...")
        result = run_pytest(["tests/test_types_containers.py", "-v"])
        
    elif sys.argv[1] == "unification":
        print("Running unification tests...")
        result = run_pytest(["tests/test_types_unification.py", "-v"])
        
    elif sys.argv[1] == "rows":
        print("Running row type tests...")
        result = run_pytest([
            "tests/test_rows_basic.py",
            "tests/test_rows_collection.py", 
            "-v"
        ])
        
    elif sys.argv[1] == "effects":
        print("Running effect system tests...")
        result = run_pytest([
            "tests/test_effects_basic.py",
            "tests/test_effects_advanced.py",
            "-v"
        ])
        
    elif sys.argv[1] == "fast":
        print("Running fast tests only...")
        result = run_pytest(["tests/", "-v", "-m", "not slow"])
        
    else:
        print(f"Unknown test category: {sys.argv[1]}")
        print(__doc__)
        sys.exit(1)
        
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()

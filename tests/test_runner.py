#!/usr/bin/env python3
"""
Comprehensive test runner for Merlin Personal Knowledge Curator.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_tests(test_type="all", verbose=False, coverage=False):
    """Run tests based on the specified type."""
    
    # Set up pytest command
    cmd = ["python3", "-m", "pytest"]
    
    # Add verbosity
    if verbose:
        cmd.append("-v")
    
    # Add coverage
    if coverage:
        cmd.extend(["--cov=app", "--cov-report=html", "--cov-report=term"])
    
    # Select test directory based on type
    if test_type == "unit":
        cmd.append("tests/unit/")
    elif test_type == "integration":
        cmd.append("tests/integration/")
    elif test_type == "tools":
        cmd.append("tests/unit/tools/")
    elif test_type == "agents":
        cmd.append("tests/unit/agents/")
    elif test_type == "api":
        cmd.append("tests/unit/api/")
    elif test_type == "all":
        cmd.append("tests/")
    else:
        print(f"Unknown test type: {test_type}")
        return False
    
    print(f"🧪 Running {test_type} tests...")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 60)
    
    # Run the tests
    try:
        result = subprocess.run(cmd, cwd=project_root, capture_output=False)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False


def check_test_environment():
    """Check if the test environment is properly set up."""
    print("🔍 Checking test environment...")
    
    # Check if pytest is available
    try:
        subprocess.run(["python3", "-m", "pytest", "--version"], 
                      capture_output=True, check=True)
        print("✅ pytest is available")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ pytest is not available. Install with: pip install pytest")
        return False
    
    # Check if required packages are available
    required_packages = [
        "pytest",
        "pytest-cov",
        "fastapi",
        "pydantic"
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {package} is available")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} is missing")
    
    if missing_packages:
        print(f"\n📦 Install missing packages with:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    # Check if test files exist
    test_dirs = [
        "tests/unit/tools",
        "tests/unit/agents", 
        "tests/unit/api",
        "tests/integration"
    ]
    
    for test_dir in test_dirs:
        test_path = project_root / test_dir
        if test_path.exists() and any(test_path.glob("test_*.py")):
            print(f"✅ {test_dir} has test files")
        else:
            print(f"⚠️  {test_dir} has no test files")
    
    print("✅ Test environment check completed")
    return True


def generate_test_report():
    """Generate a comprehensive test report."""
    print("📊 Generating test report...")
    
    # Run tests with coverage
    cmd = [
        "python3", "-m", "pytest",
        "tests/",
        "--cov=app",
        "--cov-report=html",
        "--cov-report=term-missing",
        "--cov-report=json",
        "-v"
    ]
    
    try:
        result = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True)
        
        # Save report to file
        report_file = project_root / "test_report.txt"
        with open(report_file, "w") as f:
            f.write("Merlin Test Report\n")
            f.write("=" * 50 + "\n\n")
            f.write(result.stdout)
            if result.stderr:
                f.write("\nErrors:\n")
                f.write(result.stderr)
        
        print(f"✅ Test report saved to: {report_file}")
        
        # Print summary
        if "passed" in result.stdout:
            lines = result.stdout.split('\n')
            for line in lines:
                if "passed" in line or "failed" in line or "error" in line:
                    print(f"📈 {line.strip()}")
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error generating test report: {e}")
        return False


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="Merlin Test Runner")
    parser.add_argument(
        "--type", 
        choices=["all", "unit", "integration", "tools", "agents", "api"],
        default="all",
        help="Type of tests to run"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--coverage", "-c",
        action="store_true",
        help="Generate coverage report"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check test environment only"
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate comprehensive test report"
    )
    
    args = parser.parse_args()
    
    print("🧙‍♂️ Merlin Test Runner")
    print("=" * 50)
    
    # Check environment first
    if not check_test_environment():
        print("❌ Test environment check failed")
        sys.exit(1)
    
    if args.check:
        print("✅ Environment check completed")
        sys.exit(0)
    
    # Generate report if requested
    if args.report:
        success = generate_test_report()
        sys.exit(0 if success else 1)
    
    # Run tests
    success = run_tests(
        test_type=args.type,
        verbose=args.verbose,
        coverage=args.coverage
    )
    
    if success:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()

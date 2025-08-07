#!/usr/bin/env python3
"""
Test runner for the local agent system

This script provides various ways to run tests with different configurations.
"""
import argparse
import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd, description=""):
    """Run a command and handle errors"""
    print(f"\n{'='*60}")
    if description:
        print(f"🔄 {description}")
    print(f"Running: {' '.join(cmd)}")
    print('='*60)
    
    result = subprocess.run(cmd, capture_output=False)
    if result.returncode != 0:
        print(f"❌ Command failed with exit code {result.returncode}")
        return False
    else:
        print(f"✅ {description or 'Command'} completed successfully")
        return True


def check_ollama_available():
    """Check if Ollama is available"""
    try:
        result = subprocess.run(['curl', '-s', 'http://localhost:11434/api/tags'], 
                              capture_output=True, timeout=5)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Test runner for local agent system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py --unit                    # Run only unit tests
  python run_tests.py --integration             # Run integration tests (requires Ollama)
  python run_tests.py --mock                    # Run mock tests
  python run_tests.py --benchmark               # Run performance benchmarks
  python run_tests.py --all                     # Run all tests
  python run_tests.py --fast                    # Run fast tests only
  python run_tests.py --coverage                # Run with coverage report
  python run_tests.py --parallel                # Run tests in parallel
        """
    )
    
    # Test selection options
    parser.add_argument('--unit', action='store_true',
                       help='Run unit tests only')
    parser.add_argument('--integration', action='store_true',
                       help='Run integration tests (requires Ollama)')
    parser.add_argument('--mock', action='store_true',
                       help='Run mock tests only')
    parser.add_argument('--benchmark', action='store_true',
                       help='Run performance benchmarks')
    parser.add_argument('--all', action='store_true',
                       help='Run all tests')
    parser.add_argument('--fast', action='store_true',
                       help='Run only fast tests (unit + mock)')
    
    # Test execution options
    parser.add_argument('--coverage', action='store_true',
                       help='Generate coverage report')
    parser.add_argument('--parallel', action='store_true',
                       help='Run tests in parallel')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    parser.add_argument('--failfast', action='store_true',
                       help='Stop on first failure')
    parser.add_argument('--lf', '--last-failed', action='store_true',
                       help='Run only last failed tests')
    
    # Environment options
    parser.add_argument('--check-ollama', action='store_true',
                       help='Check Ollama availability before running tests')
    parser.add_argument('--install-deps', action='store_true',
                       help='Install test dependencies before running')
    
    args = parser.parse_args()
    
    # Change to the tests directory
    test_dir = Path(__file__).parent
    os.chdir(test_dir.parent)  # Go to the root project directory
    
    # Install dependencies if requested
    if args.install_deps:
        if not run_command([sys.executable, '-m', 'pip', 'install', '-r', 'tests/test_requirements.txt'],
                          "Installing test dependencies"):
            return 1
    
    # Check Ollama availability if requested or if running integration tests
    if args.check_ollama or args.integration or args.all:
        print("\n🔍 Checking Ollama availability...")
        ollama_available = check_ollama_available()
        if ollama_available:
            print("✅ Ollama is available")
        else:
            print("❌ Ollama is not available")
            if args.integration:
                print("Integration tests require Ollama. Please start Ollama or skip integration tests.")
                return 1
    
    # Build pytest command
    cmd = [sys.executable, '-m', 'pytest']
    
    # Add verbosity
    if args.verbose:
        cmd.append('-vv')
    else:
        cmd.append('-v')
    
    # Add test selection markers
    markers = []
    
    if args.unit:
        markers.append('unit')
    elif args.integration:
        markers.append('integration')
    elif args.mock:
        markers.append('mock')
    elif args.benchmark:
        markers.append('benchmark')
    elif args.fast:
        markers.extend(['unit', 'mock'])
    elif args.all:
        pass  # Run all tests
    else:
        # Default: run unit and mock tests
        markers.extend(['unit', 'mock'])
    
    if markers:
        marker_expr = ' or '.join(markers)
        cmd.extend(['-m', marker_expr])
    
    # Add coverage if requested
    if args.coverage:
        cmd.extend([
            '--cov=.',
            '--cov-report=html:htmlcov',
            '--cov-report=xml:coverage.xml',
            '--cov-report=term-missing',
            '--cov-fail-under=70'
        ])
    
    # Add parallel execution
    if args.parallel:
        cmd.extend(['-n', 'auto'])
    
    # Add other options
    if args.failfast:
        cmd.append('-x')
    
    if args.lf:
        cmd.append('--lf')
    
    # Add test directory
    cmd.append('tests')
    
    # Run the tests
    description = f"Running tests with markers: {marker_expr}" if markers else "Running all tests"
    success = run_command(cmd, description)
    
    if success:
        print(f"\n🎉 All tests completed successfully!")
        
        if args.coverage:
            print(f"\n📊 Coverage report generated:")
            print(f"  - HTML: htmlcov/index.html")
            print(f"  - XML: coverage.xml")
    else:
        print(f"\n💥 Some tests failed!")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
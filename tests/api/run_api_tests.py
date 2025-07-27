#!/usr/bin/env python3
"""
Master API test runner for FPAS
Executes all API tests with detailed reporting
"""

import sys
import os
import pytest
import argparse
import time
from typing import List, Dict, Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def run_tests(test_path: str = None, verbose: bool = False, show_output: bool = True) -> Dict[str, Any]:
    """
    Run all API tests with reporting
    
    Args:
        test_path: Specific test path to run (default: all API tests)
        verbose: Whether to show verbose output
        show_output: Whether to show output in terminal
        
    Returns:
        Dict with test results
    """
    start_time = time.time()
    
    # Default to all API tests if no specific path provided
    if test_path is None:
        test_path = os.path.dirname(os.path.abspath(__file__))
    
    # Build pytest arguments
    args = [test_path]
    if verbose:
        args.append("-v")
    
    # Add colored terminal output
    args.extend(["-xvs"])
    
    # Capture output if not showing
    if not show_output:
        args.append("--no-header")
        args.append("--quiet")
    
    # Run the tests
    result = pytest.main(args)
    
    # Calculate stats
    duration = time.time() - start_time
    
    # Return test results
    return {
        "success": result == 0,
        "exit_code": result,
        "duration_seconds": duration
    }


def main():
    """CLI entrypoint for running tests"""
    parser = argparse.ArgumentParser(description="FPAS API Test Runner")
    parser.add_argument(
        "--path", 
        "-p", 
        type=str, 
        help="Specific test file or directory to run"
    )
    parser.add_argument(
        "--verbose", 
        "-v", 
        action="store_true", 
        help="Show verbose output"
    )
    parser.add_argument(
        "--quiet", 
        "-q", 
        action="store_true", 
        help="Hide test output"
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("FPAS API TEST RUNNER")
    print("=" * 80)
    
    results = run_tests(
        test_path=args.path,
        verbose=args.verbose,
        show_output=not args.quiet
    )
    
    # Print summary
    print("\n" + "=" * 80)
    print(f"Test run completed in {results['duration_seconds']:.2f} seconds")
    if results["success"]:
        print("✅ All tests PASSED")
    else:
        print(f"❌ Tests FAILED with exit code {results['exit_code']}")
    print("=" * 80)
    
    # Return exit code for CI/CD pipelines
    return 0 if results["success"] else 1


if __name__ == "__main__":
    sys.exit(main())

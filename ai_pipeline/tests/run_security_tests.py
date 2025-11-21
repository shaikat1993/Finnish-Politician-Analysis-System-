#!/usr/bin/env python3
"""
Test Runner for OWASP LLM06 Security Tests

Runs all LLM06 (Excessive Agency Prevention) security tests and generates
a comprehensive test report for thesis validation.
"""

import sys
import os
import pytest
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def main():
    """Run all security tests with detailed reporting"""

    print("=" * 80)
    print("OWASP LLM06 Excessive Agency Prevention - Security Test Suite")
    print("Finnish Politician Analysis System")
    print("=" * 80)
    print(f"Test run started at: {datetime.now().isoformat()}")
    print()

    # Test configuration
    test_dir = os.path.join(os.path.dirname(__file__), "security")

    # pytest arguments for detailed output
    pytest_args = [
        test_dir,
        "-v",                    # Verbose output
        "--tb=short",           # Short traceback format
        "--durations=10",       # Show 10 slowest tests
        "-ra",                  # Show all test outcomes
        "--strict-markers",     # Strict marker checking
        "--color=yes",          # Colorized output
    ]

    # Add HTML report if pytest-html is available
    try:
        import pytest_html
        report_path = os.path.join(
            os.path.dirname(os.path.dirname(test_dir)),
            "test_reports",
            f"security_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        )
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        pytest_args.extend(["--html", report_path, "--self-contained-html"])
        print(f"HTML report will be generated at: {report_path}")
    except ImportError:
        print("pytest-html not installed - skipping HTML report generation")
        print("Install with: pip install pytest-html")

    print()
    print("Running tests...")
    print("-" * 80)

    # Run tests
    exit_code = pytest.main(pytest_args)

    # Summary
    print()
    print("=" * 80)
    print("Test Suite Summary")
    print("=" * 80)

    if exit_code == 0:
        print("✓ All tests passed successfully!")
        print()
        print("OWASP LLM06 (Excessive Agency) implementation validated:")
        print("  - Permission control system working correctly")
        print("  - Rate limiting enforced properly")
        print("  - Audit logging comprehensive")
        print("  - Anomaly detection functional")
        print("  - Security reporting operational")
    else:
        print("✗ Some tests failed. Review output above for details.")
        print()
        print("Common issues:")
        print("  - Missing dependencies (run: pip install -r requirements.txt)")
        print("  - LangChain version mismatch")
        print("  - Environment variables not set")

    print()
    print(f"Test run completed at: {datetime.now().isoformat()}")
    print("=" * 80)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())

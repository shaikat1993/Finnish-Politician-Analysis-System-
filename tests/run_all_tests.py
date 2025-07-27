#!/usr/bin/env python3
"""
Master Test Runner for FPAS
Senior-level test orchestration and reporting
"""

import asyncio
import subprocess
import sys
import os
import json
from datetime import datetime
from typing import Dict, List, Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class FPASTestRunner:
    """Senior-level test runner for comprehensive FPAS testing"""
    
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'test_suites': {},
            'overall_status': 'unknown',
            'summary': {},
            'recommendations': []
        }
    
    def run_test_suite(self, suite_name: str, test_path: str, markers: List[str] = None) -> Dict[str, Any]:
        """Run a specific test suite with proper reporting"""
        print(f"\n{'='*60}")
        print(f"🧪 Running {suite_name} Test Suite")
        print(f"{'='*60}")
        
        # Build pytest command
        cmd = ['python', '-m', 'pytest', test_path, '-v', '--tb=short']
        
        if markers:
            for marker in markers:
                cmd.extend(['-m', marker])
        
        # Add coverage if requested
        if '--coverage' in sys.argv:
            cmd.extend(['--cov=database', '--cov=ai_pipeline', '--cov=data_collection'])
        
        # Run tests
        start_time = datetime.now()
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__)))
        end_time = datetime.now()
        
        duration = (end_time - start_time).total_seconds()
        
        # Parse results
        stdout = result.stdout
        stderr = result.stderr
        return_code = result.returncode
        
        # Extract test counts from output
        passed = stdout.count(' PASSED')
        failed = stdout.count(' FAILED')
        skipped = stdout.count(' SKIPPED')
        errors = stdout.count(' ERROR')
        
        suite_result = {
            'suite_name': suite_name,
            'duration': duration,
            'return_code': return_code,
            'passed': passed,
            'failed': failed,
            'skipped': skipped,
            'errors': errors,
            'total': passed + failed + skipped + errors,
            'success_rate': (passed / max(passed + failed + errors, 1)) * 100,
            'stdout': stdout,
            'stderr': stderr
        }
        
        # Print summary
        status_emoji = '✅' if return_code == 0 else '❌' if failed > 0 or errors > 0 else '⚠️'
        print(f"\n{status_emoji} {suite_name} Results:")
        print(f"   Duration: {duration:.2f}s")
        print(f"   Passed: {passed}")
        print(f"   Failed: {failed}")
        print(f"   Skipped: {skipped}")
        print(f"   Errors: {errors}")
        print(f"   Success Rate: {suite_result['success_rate']:.1f}%")
        
        if failed > 0 or errors > 0:
            print(f"\n⚠️ {suite_name} Issues:")
            # Extract failure details
            lines = stdout.split('\n')
            for i, line in enumerate(lines):
                if 'FAILED' in line or 'ERROR' in line:
                    print(f"   • {line.strip()}")
        
        self.results['test_suites'][suite_name] = suite_result
        return suite_result
    
    def run_all_tests(self):
        """Run all test suites in proper order"""
        print("🎯 FPAS Comprehensive Test Suite")
        print("Senior-level testing for Finnish Political Analysis System")
        print("="*70)
        
        # Test Suite 1: Unit Tests (Fast)
        unit_result = self.run_test_suite(
            "Unit Tests",
            "tests/unit/",
            ["unit"]
        )
        
        # Test Suite 2: Database Tests (Core functionality)
        database_result = self.run_test_suite(
            "Database Tests",
            "tests/test_database.py",
            ["database"]
        )
        
        # Test Suite 3: Data Collection Tests
        data_collection_result = self.run_test_suite(
            "Data Collection Tests",
            "tests/test_data_collection.py",
            ["data_collection"]
        )
        
        # Test Suite 4: AI Pipeline Tests
        ai_pipeline_result = self.run_test_suite(
            "AI Pipeline Tests",
            "tests/test_ai_pipeline.py",
            ["ai_pipeline"]
        )
        
        # Test Suite 5: Integration Tests
        integration_result = self.run_test_suite(
            "Integration Tests",
            "tests/integration/",
            ["integration"]
        )
        
        # Test Suite 6: Feature/E2E Tests (Slow)
        if '--skip-slow' not in sys.argv:
            feature_result = self.run_test_suite(
                "Feature/E2E Tests",
                "tests/features/",
                ["features"]
            )
        else:
            print("\n⏭️ Skipping Feature/E2E Tests (--skip-slow flag)")
        
        # Generate overall summary
        self.generate_summary()
        self.print_final_report()
    
    def generate_summary(self):
        """Generate overall test summary"""
        total_passed = sum(suite['passed'] for suite in self.results['test_suites'].values())
        total_failed = sum(suite['failed'] for suite in self.results['test_suites'].values())
        total_skipped = sum(suite['skipped'] for suite in self.results['test_suites'].values())
        total_errors = sum(suite['errors'] for suite in self.results['test_suites'].values())
        total_tests = total_passed + total_failed + total_skipped + total_errors
        total_duration = sum(suite['duration'] for suite in self.results['test_suites'].values())
        
        overall_success_rate = (total_passed / max(total_passed + total_failed + total_errors, 1)) * 100
        
        self.results['summary'] = {
            'total_tests': total_tests,
            'total_passed': total_passed,
            'total_failed': total_failed,
            'total_skipped': total_skipped,
            'total_errors': total_errors,
            'total_duration': total_duration,
            'overall_success_rate': overall_success_rate,
            'suites_run': len(self.results['test_suites'])
        }
        
        # Determine overall status
        if total_failed == 0 and total_errors == 0:
            self.results['overall_status'] = 'all_passed'
        elif overall_success_rate >= 80:
            self.results['overall_status'] = 'mostly_passed'
        elif overall_success_rate >= 50:
            self.results['overall_status'] = 'mixed_results'
        else:
            self.results['overall_status'] = 'needs_attention'
        
        # Generate recommendations
        self.generate_recommendations()
    
    def generate_recommendations(self):
        """Generate recommendations based on test results"""
        summary = self.results['summary']
        
        if summary['total_failed'] > 0:
            self.results['recommendations'].append(
                f"Fix {summary['total_failed']} failing tests before deployment"
            )
        
        if summary['total_errors'] > 0:
            self.results['recommendations'].append(
                f"Resolve {summary['total_errors']} test errors"
            )
        
        if summary['total_skipped'] > 10:
            self.results['recommendations'].append(
                f"Review {summary['total_skipped']} skipped tests - may indicate missing dependencies"
            )
        
        # Suite-specific recommendations
        for suite_name, suite_result in self.results['test_suites'].items():
            if suite_result['success_rate'] < 50:
                self.results['recommendations'].append(
                    f"Focus on {suite_name} - low success rate ({suite_result['success_rate']:.1f}%)"
                )
        
        if not self.results['recommendations']:
            self.results['recommendations'].append("All tests passing - system ready for deployment!")
    
    def print_final_report(self):
        """Print comprehensive final report"""
        summary = self.results['summary']
        
        print(f"\n{'='*70}")
        print("🎯 FPAS TEST SUITE FINAL REPORT")
        print(f"{'='*70}")
        
        # Overall status
        status_emojis = {
            'all_passed': '✅',
            'mostly_passed': '⚠️',
            'mixed_results': '❌',
            'needs_attention': '🚨'
        }
        
        status_emoji = status_emojis.get(self.results['overall_status'], '❓')
        print(f"{status_emoji} Overall Status: {self.results['overall_status'].upper().replace('_', ' ')}")
        
        # Summary statistics
        print(f"\n📊 Test Summary:")
        print(f"   Total Tests: {summary['total_tests']}")
        print(f"   Passed: {summary['total_passed']} ✅")
        print(f"   Failed: {summary['total_failed']} ❌")
        print(f"   Skipped: {summary['total_skipped']} ⏭️")
        print(f"   Errors: {summary['total_errors']} 🚨")
        print(f"   Success Rate: {summary['overall_success_rate']:.1f}%")
        print(f"   Total Duration: {summary['total_duration']:.2f}s")
        print(f"   Test Suites: {summary['suites_run']}")
        
        # Suite breakdown
        print(f"\n📋 Suite Breakdown:")
        for suite_name, suite_result in self.results['test_suites'].items():
            suite_emoji = '✅' if suite_result['return_code'] == 0 else '❌'
            print(f"   {suite_emoji} {suite_name}: {suite_result['passed']}/{suite_result['total']} passed ({suite_result['success_rate']:.1f}%)")
        
        # Recommendations
        if self.results['recommendations']:
            print(f"\n💡 Recommendations:")
            for i, rec in enumerate(self.results['recommendations'], 1):
                print(f"   {i}. {rec}")
        
        # Next steps
        print(f"\n🚀 Next Steps:")
        if self.results['overall_status'] == 'all_passed':
            print("   • System is ready for deployment")
            print("   • Consider adding more edge case tests")
            print("   • Set up CI/CD pipeline with these tests")
        else:
            print("   • Address failing tests listed above")
            print("   • Re-run tests: python tests/run_all_tests.py")
            print("   • Check system dependencies and configuration")
        
        # Save results to file
        results_file = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: {results_file}")

def main():
    """Main test runner function"""
    runner = FPASTestRunner()
    
    # Check for flags
    if '--help' in sys.argv:
        print("""
FPAS Test Runner - Senior-level testing for Finnish Political Analysis System

Usage:
    python tests/run_all_tests.py [options]

Options:
    --help          Show this help message
    --skip-slow     Skip slow feature/E2E tests
    --coverage      Include code coverage reporting
    --unit-only     Run only unit tests
    --integration   Run only integration tests
    --database      Run only database tests

Examples:
    python tests/run_all_tests.py                    # Run all tests
    python tests/run_all_tests.py --skip-slow        # Skip E2E tests
    python tests/run_all_tests.py --unit-only        # Unit tests only
    python tests/run_all_tests.py --coverage         # With coverage
        """)
        return
    
    # Handle specific test categories
    if '--unit-only' in sys.argv:
        runner.run_test_suite("Unit Tests", "tests/unit/", ["unit"])
        runner.generate_summary()
        runner.print_final_report()
    elif '--integration' in sys.argv:
        runner.run_test_suite("Integration Tests", "tests/integration/", ["integration"])
        runner.generate_summary()
        runner.print_final_report()
    elif '--database' in sys.argv:
        runner.run_test_suite("Database Tests", "tests/test_database.py", ["database"])
        runner.generate_summary()
        runner.print_final_report()
    else:
        # Run all tests
        runner.run_all_tests()

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Comprehensive test runner for all Phase 2 implementation plans.
Runs tests with proper output, timeout protection, and detailed reporting.

Usage:
    conda activate vsm-hva
    python3 scripts/run_all_plan_tests.py
"""

import asyncio
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# ANSI color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

class TestRunner:
    def __init__(self):
        self.results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0

    def print_header(self, text):
        """Print a formatted header"""
        print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*80}{Colors.END}")
        print(f"{Colors.BLUE}{Colors.BOLD}{text:^80}{Colors.END}")
        print(f"{Colors.BLUE}{Colors.BOLD}{'='*80}{Colors.END}\n")

    def print_status(self, status, message):
        """Print a status message with color"""
        if status == "PASS":
            print(f"{Colors.GREEN}✅ PASS{Colors.END}: {message}")
        elif status == "FAIL":
            print(f"{Colors.RED}❌ FAIL{Colors.END}: {message}")
        elif status == "SKIP":
            print(f"{Colors.YELLOW}⏭️  SKIP{Colors.END}: {message}")
        elif status == "INFO":
            print(f"{Colors.BLUE}ℹ️  INFO{Colors.END}: {message}")
        else:
            print(f"    {message}")

    def run_test(self, test_name, test_command, timeout=120):
        """Run a single test with timeout protection"""
        self.total_tests += 1
        print(f"\n{Colors.BOLD}Running: {test_name}{Colors.END}")
        print(f"Command: {test_command}")
        print(f"Timeout: {timeout}s")
        print("-" * 80)

        start_time = time.time()
        try:
            result = subprocess.run(
                test_command,
                shell=True,
                capture_output=False,  # Show output in real-time
                text=True,
                timeout=timeout
            )

            duration = time.time() - start_time

            if result.returncode == 0:
                self.print_status("PASS", f"{test_name} completed in {duration:.1f}s")
                self.passed_tests += 1
                self.results.append({
                    'name': test_name,
                    'status': 'PASS',
                    'duration': duration,
                    'error': None
                })
                return True
            else:
                self.print_status("FAIL", f"{test_name} failed with exit code {result.returncode}")
                self.failed_tests += 1
                self.results.append({
                    'name': test_name,
                    'status': 'FAIL',
                    'duration': duration,
                    'error': f"Exit code {result.returncode}"
                })
                return False

        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            self.print_status("FAIL", f"{test_name} timed out after {timeout}s")
            self.failed_tests += 1
            self.results.append({
                'name': test_name,
                'status': 'TIMEOUT',
                'duration': duration,
                'error': f"Timeout after {timeout}s"
            })
            return False

        except Exception as e:
            duration = time.time() - start_time
            self.print_status("FAIL", f"{test_name} error: {e}")
            self.failed_tests += 1
            self.results.append({
                'name': test_name,
                'status': 'ERROR',
                'duration': duration,
                'error': str(e)
            })
            return False

    def print_summary(self):
        """Print final test summary"""
        self.print_header("TEST SUMMARY")

        print(f"Total Tests: {self.total_tests}")
        print(f"{Colors.GREEN}Passed: {self.passed_tests}{Colors.END}")
        print(f"{Colors.RED}Failed: {self.failed_tests}{Colors.END}")
        print(f"Success Rate: {(self.passed_tests/self.total_tests*100):.1f}%\n")

        print(f"{Colors.BOLD}Individual Results:{Colors.END}")
        for result in self.results:
            status_icon = "✅" if result['status'] == 'PASS' else "❌"
            print(f"  {status_icon} {result['name']}: {result['status']} ({result['duration']:.1f}s)")
            if result['error']:
                print(f"      Error: {result['error']}")

        print(f"\n{Colors.BOLD}Detailed Logs:{Colors.END}")
        print(f"  All test output is shown above in real-time")

        return self.failed_tests == 0


def main():
    """Run all plan tests in sequence"""
    runner = TestRunner()

    runner.print_header("VSM PHASE 2 PLAN TESTS")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Working directory: {Path.cwd()}")

    # Check environment
    runner.print_status("INFO", "Checking Python environment...")
    python_check = subprocess.run(
        "python3 --version && which python3",
        shell=True,
        capture_output=True,
        text=True
    )
    print(python_check.stdout)

    # Test Plan 1: WorldState Engine (pytest)
    runner.print_header("PLAN 1: WorldState Engine")
    runner.run_test(
        "Plan 1: WorldState Engine (pytest)",
        "pytest features/telemetry_vsm/tests/test_worldstate_engine.py -v --tb=short",
        timeout=60
    )

    # Test Plan 2: Simple Query Tools
    runner.print_header("PLAN 2: Simple Query Tools")
    runner.run_test(
        "Plan 2: GetAlarms, QueryTelemetryEvents, QueryVlogCases",
        "python3 scripts/test_plan2_tools.py",
        timeout=120
    )

    # Test Plan 3: SearchManualsBySMIDO
    runner.print_header("PLAN 3: SearchManualsBySMIDO Tool")
    runner.run_test(
        "Plan 3: SearchManualsBySMIDO",
        "python3 scripts/test_plan3_tools.py",
        timeout=120
    )

    # Test Plan 4: Advanced Diagnostic Tools
    runner.print_header("PLAN 4: Advanced Diagnostic Tools")
    runner.run_test(
        "Plan 4: GetAssetHealth, AnalyzeSensorPattern",
        "python3 scripts/test_plan4_tools.py",
        timeout=120
    )

    # Test Plan 5: SMIDO Tree Structure
    runner.print_header("PLAN 5: SMIDO Tree Structure")
    runner.print_status("INFO", "Checking if SMIDO tree structure exists...")
    tree_file = Path("features/vsm_tree/smido_tree.py")
    if tree_file.exists():
        runner.run_test(
            "Plan 5: SMIDO Tree Structure",
            "python3 -c \"from features.vsm_tree.smido_tree import create_vsm_tree; tree = create_vsm_tree(); print(f'✅ Tree created with {len(tree.tree_data.branches)} branches')\" 2>&1 | grep -v 'WARNING\\|DeprecationWarning\\|ResourceWarning'",
            timeout=30
        )
    else:
        runner.print_status("SKIP", f"Plan 5: SMIDO tree file not found at {tree_file}")
        runner.results.append({
            'name': 'Plan 5: SMIDO Tree Structure',
            'status': 'SKIP',
            'duration': 0,
            'error': 'File not found'
        })
        runner.total_tests += 1

    # Test Plan 6: Orchestrator (if implemented)
    runner.print_header("PLAN 6: Orchestrator + Context Manager")
    orchestrator_file = Path("features/vsm_tree/smido_orchestrator.py")
    if orchestrator_file.exists():
        runner.run_test(
            "Plan 6: SMIDO Orchestrator",
            "python3 -c \"from features.vsm_tree.smido_orchestrator import SMIDOOrchestrator; print('✅ Orchestrator imports successfully')\"",
            timeout=30
        )
    else:
        runner.print_status("SKIP", f"Plan 6: Orchestrator file not found at {orchestrator_file}")
        runner.results.append({
            'name': 'Plan 6: SMIDO Orchestrator',
            'status': 'SKIP',
            'duration': 0,
            'error': 'File not found'
        })
        runner.total_tests += 1

    # Test Plan 7: Full A3 Scenario (WARNING: Can take 2-5 minutes)
    runner.print_header("PLAN 7: A3 Frozen Evaporator End-to-End Test")
    runner.print_status("INFO", "⚠️  This test involves full LLM execution and may take 2-5 minutes")

    user_input = input(f"\n{Colors.YELLOW}Run Plan 7 full tree test? (y/n): {Colors.END}").strip().lower()
    if user_input == 'y':
        runner.run_test(
            "Plan 7: A3 Frozen Evaporator Full Tree",
            "python3 scripts/test_plan7_full_tree.py",
            timeout=300  # 5 minute timeout for LLM execution
        )
    else:
        runner.print_status("SKIP", "Plan 7: Skipped by user")
        runner.results.append({
            'name': 'Plan 7: A3 Frozen Evaporator Full Tree',
            'status': 'SKIP',
            'duration': 0,
            'error': 'Skipped by user'
        })
        runner.total_tests += 1

    # Print final summary
    success = runner.print_summary()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

"""
LLM09 Performance Investigation Script

This script investigates why LLM09 shows 0.01ms in benchmarks.
It demonstrates that the module has two operational modes:
- Baseline (no context): 0.016ms - fast-path return
- Production (with context): 1.8ms - full contradiction detection

Used for thesis performance analysis and documentation.
"""
import sys
import os
import time

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from ai_pipeline.security.llm09_misinformation.verification_system import VerificationSystem

print("🔍 Investigating LLM09 Performance")
print("=" * 70)

vs = VerificationSystem()
test_output = "Helsinki is the capital of Finland"

# Test 1: Without context (what benchmark does)
print("\n1️⃣ WITHOUT CONTEXT (what benchmark measures):")
start = time.perf_counter()
result1 = vs.verify_output(test_output)
time1 = (time.perf_counter() - start) * 1000

print(f"   Time: {time1:.3f}ms")
print(f"   Verified: {result1.is_verified}")
print(f"   Details: {result1.details}")

# Test 2: With context (real verification)
print("\n2️⃣ WITH CONTEXT (real verification):")
context = {"previous_outputs": ["Helsinki is in Sweden", "Finland is cold"]}
start = time.perf_counter()
result2 = vs.verify_output(test_output, context=context)
time2 = (time.perf_counter() - start) * 1000

print(f"   Time: {time2:.3f}ms")
print(f"   Verified: {result2.is_verified}")
print(f"   Details: {result2.details}")

print(f"\n📊 Difference: {time2/time1:.1f}x slower with real verification")
print(f"\n💡 Conclusion: Benchmark shows {time1:.3f}ms because it skips real work!")
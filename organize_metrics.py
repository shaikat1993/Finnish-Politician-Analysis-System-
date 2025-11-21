#!/usr/bin/env python3
"""
Organize Security Metrics Script
Run this to clean up and organize security_metrics directory
"""

from ai_pipeline.security.shared.metrics_organizer import organize_metrics

if __name__ == "__main__":
    print("🔧 Organizing security metrics...")
    print()

    report = organize_metrics()

    print()
    print("📊 Thesis Metrics Summary:")
    print(f"   Period: {report['period']['days']} days")
    print(f"   Total Events: {report['overview']['total_security_events']}")
    print(f"   Attack Prevention Rate: {report['attack_prevention']['prevention_rate']:.1f}%")
    print()
    print("✅ Done! Check security_metrics/ directory for organized data")

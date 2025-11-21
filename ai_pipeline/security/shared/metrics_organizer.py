"""
Security Metrics Organizer
Manages and organizes security metrics for research and analysis
"""

import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


class SecurityMetricsOrganizer:
    """
    Organizes security metrics into structured format for thesis/research

    Features:
    - Consolidates daily metrics into summary files
    - Archives old metrics
    - Generates analysis-ready reports
    - Cleans up redundant data
    """

    def __init__(self, metrics_dir: str = "security_metrics"):
        self.metrics_dir = Path(metrics_dir)
        self.events_dir = self.metrics_dir / "events"
        self.function_calls_dir = self.metrics_dir / "function_calls"
        self.daily_summaries_dir = self.metrics_dir / "daily_summaries"
        self.archive_dir = self.metrics_dir / "archive"

        # Create organized structure
        self._create_directories()

    def _create_directories(self):
        """Create organized directory structure"""
        self.daily_summaries_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)

    def consolidate_daily_metrics(self, date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Consolidate all metrics for a specific day into a single summary

        Args:
            date: Date to consolidate (defaults to yesterday)

        Returns:
            Dictionary with consolidated metrics
        """
        if date is None:
            date = datetime.now() - timedelta(days=1)

        date_str = date.strftime("%Y%m%d")

        # Collect all events for the day
        events = self._collect_events_for_date(date_str)
        function_calls = self._collect_function_calls_for_date(date_str)

        summary = {
            "date": date_str,
            "generated_at": datetime.now().isoformat(),
            "statistics": {
                "total_events": len(events),
                "total_function_calls": len(function_calls),
                "event_types": self._count_by_field(events, "event_type"),
                "components": self._count_by_field(events, "component"),
                "severities": self._count_by_field(events, "severity"),
                "results": self._count_by_field(events, "result"),
            },
            "function_call_stats": {
                "total_calls": len(function_calls),
                "unique_functions": len(set(fc.get("function_name") for fc in function_calls)),
                "by_function": self._count_by_field(function_calls, "function_name"),
            },
            "events": events[:100],  # Keep only first 100 for detail
            "sample_function_calls": function_calls[:50],  # Keep sample
        }

        # Save summary
        summary_file = self.daily_summaries_dir / f"summary_{date_str}.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)

        logger.info(f"Created daily summary: {summary_file}")
        return summary

    def _collect_events_for_date(self, date_str: str) -> List[Dict]:
        """Collect all security events for a specific date"""
        events = []

        if not self.events_dir.exists():
            return events

        for event_file in self.events_dir.glob("*.json"):
            try:
                with open(event_file, 'r') as f:
                    event = json.load(f)

                # Check if event is from this date
                timestamp = event.get("timestamp", "")
                if date_str in timestamp:
                    events.append(event)
            except Exception as e:
                logger.warning(f"Error reading event file {event_file}: {e}")

        return events

    def _collect_function_calls_for_date(self, date_str: str) -> List[Dict]:
        """Collect all function calls for a specific date"""
        calls = []

        if not self.function_calls_dir.exists():
            return calls

        for call_file in self.function_calls_dir.glob(f"*_{date_str}_*.json"):
            try:
                with open(call_file, 'r') as f:
                    call = json.load(f)
                    calls.append(call)
            except Exception as e:
                logger.warning(f"Error reading call file {call_file}: {e}")

        return calls

    def _count_by_field(self, items: List[Dict], field: str) -> Dict[str, int]:
        """Count occurrences of field values"""
        counts = defaultdict(int)
        for item in items:
            value = item.get(field, "unknown")
            counts[str(value)] += 1
        return dict(counts)

    def archive_old_metrics(self, days_to_keep: int = 7):
        """
        Archive metrics older than specified days

        Args:
            days_to_keep: Number of days to keep in active directory
        """
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        cutoff_str = cutoff_date.strftime("%Y%m%d")

        archived_count = 0

        # Archive old events
        if self.events_dir.exists():
            for event_file in self.events_dir.glob("*.json"):
                try:
                    with open(event_file, 'r') as f:
                        event = json.load(f)

                    timestamp = event.get("timestamp", "")
                    if timestamp < cutoff_str:
                        # Move to archive
                        archive_path = self.archive_dir / event_file.name
                        event_file.rename(archive_path)
                        archived_count += 1
                except Exception as e:
                    logger.warning(f"Error archiving {event_file}: {e}")

        # Archive old function calls
        if self.function_calls_dir.exists():
            for call_file in self.function_calls_dir.glob("*.json"):
                if cutoff_str not in str(call_file):
                    try:
                        archive_path = self.archive_dir / call_file.name
                        call_file.rename(archive_path)
                        archived_count += 1
                    except Exception as e:
                        logger.warning(f"Error archiving {call_file}: {e}")

        logger.info(f"Archived {archived_count} old metric files")
        return archived_count

    def generate_thesis_report(self, start_date: Optional[datetime] = None,
                               end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Generate comprehensive report for thesis

        Args:
            start_date: Start date for analysis
            end_date: End date for analysis

        Returns:
            Comprehensive metrics report
        """
        if end_date is None:
            end_date = datetime.now()
        if start_date is None:
            start_date = end_date - timedelta(days=30)

        # Collect all summaries in date range
        all_events = []
        all_calls = []

        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime("%Y%m%d")
            all_events.extend(self._collect_events_for_date(date_str))
            all_calls.extend(self._collect_function_calls_for_date(date_str))
            current_date += timedelta(days=1)

        # Generate comprehensive statistics
        report = {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": (end_date - start_date).days
            },
            "overview": {
                "total_security_events": len(all_events),
                "total_function_calls": len(all_calls),
                "average_events_per_day": len(all_events) / max(1, (end_date - start_date).days),
            },
            "security_events": {
                "by_type": self._count_by_field(all_events, "event_type"),
                "by_component": self._count_by_field(all_events, "component"),
                "by_severity": self._count_by_field(all_events, "severity"),
                "by_result": self._count_by_field(all_events, "result"),
            },
            "function_calls": {
                "total": len(all_calls),
                "unique_functions": len(set(c.get("function_name") for c in all_calls)),
                "by_function": self._count_by_field(all_calls, "function_name"),
            },
            "attack_prevention": {
                "blocked_attacks": sum(1 for e in all_events if e.get("result") == "blocked"),
                "allowed_operations": sum(1 for e in all_events if e.get("result") == "allowed"),
                "prevention_rate": self._calculate_prevention_rate(all_events),
            },
            "performance": {
                "average_response_time": self._calculate_avg_response_time(all_events),
                "total_monitored_operations": len(all_events) + len(all_calls),
            }
        }

        # Save thesis report
        report_file = self.metrics_dir / f"thesis_report_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        logger.info(f"Generated thesis report: {report_file}")
        return report

    def _calculate_prevention_rate(self, events: List[Dict]) -> float:
        """Calculate attack prevention rate"""
        total_security_checks = sum(1 for e in events if e.get("event_type") in ["attack_detected", "permission_denied"])
        blocked = sum(1 for e in events if e.get("result") == "blocked" or e.get("result") == "denied")

        if total_security_checks == 0:
            return 100.0

        return (blocked / total_security_checks) * 100

    def _calculate_avg_response_time(self, events: List[Dict]) -> float:
        """Calculate average response time"""
        response_times = [e.get("response_time", 0) for e in events if e.get("response_time")]

        if not response_times:
            return 0.0

        return sum(response_times) / len(response_times)

    def cleanup(self, keep_days: int = 30):
        """
        Clean up old metrics (keeps summaries, removes raw data)

        Args:
            keep_days: Number of days to keep
        """
        # First, consolidate recent days into summaries
        for i in range(keep_days):
            date = datetime.now() - timedelta(days=i)
            try:
                self.consolidate_daily_metrics(date)
            except Exception as e:
                logger.warning(f"Error consolidating {date}: {e}")

        # Archive old raw data
        self.archive_old_metrics(days_to_keep=keep_days)

        logger.info(f"Cleanup complete - kept last {keep_days} days")


def organize_metrics(metrics_dir: str = "security_metrics"):
    """Convenience function to organize metrics"""
    organizer = SecurityMetricsOrganizer(metrics_dir)

    # Consolidate yesterday's metrics
    organizer.consolidate_daily_metrics()

    # Archive metrics older than 7 days
    organizer.archive_old_metrics(days_to_keep=7)

    # Generate thesis report for last 30 days
    report = organizer.generate_thesis_report()

    print(f"✅ Metrics organized!")
    print(f"   - Events: {report['overview']['total_security_events']}")
    print(f"   - Function calls: {report['overview']['total_function_calls']}")
    print(f"   - Attack prevention rate: {report['attack_prevention']['prevention_rate']:.1f}%")

    return report


if __name__ == "__main__":
    # Run organization
    organize_metrics()

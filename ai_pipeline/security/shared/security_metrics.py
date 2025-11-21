"""
OWASP LLM Security Metrics Collection
Provides metrics collection and visualization for security controls.
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

# Initialize logger
logger = logging.getLogger(__name__)

class SecurityMetricsCollector:
    """
    Collects and manages security metrics for OWASP LLM security controls.
    Provides functionality for visualization and research analysis.
    """
    
    def __init__(self, metrics_dir: Optional[str] = None):
        """
        Initialize the security metrics collector.
        
        Args:
            metrics_dir: Directory to store metrics data (defaults to ./security_metrics)
        """
        self.metrics_dir = metrics_dir or Path("./security_metrics")
        self._ensure_metrics_dir()
        
        self.events = []
        self.function_calls = []
        self.timings = {}
        self.start_times = {}
        
        logger.info(f"SecurityMetricsCollector initialized with metrics directory: {self.metrics_dir}")
    
    def _ensure_metrics_dir(self) -> None:
        """Ensure metrics directory exists"""
        if isinstance(self.metrics_dir, str):
            self.metrics_dir = Path(self.metrics_dir)
        
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (self.metrics_dir / "events").mkdir(exist_ok=True)
        (self.metrics_dir / "function_calls").mkdir(exist_ok=True)
        (self.metrics_dir / "visualizations").mkdir(exist_ok=True)
    
    def record_security_event(self, event_type: str, metadata: Dict[str, Any]) -> None:
        """
        Record a security event with metadata.
        
        Args:
            event_type: Type of security event (prompt_security, output_security, etc.)
            metadata: Event metadata
        """
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            **metadata
        }
        
        self.events.append(event)
        
        # Save event to file
        self._save_event(event)
        
        logger.debug(f"Recorded security event: {event_type}")
    
    def record_function_call(self, function_name: str, metadata: Dict[str, Any]) -> None:
        """
        Record a function call with metadata.
        
        Args:
            function_name: Name of the function
            metadata: Function call metadata
        """
        call = {
            "timestamp": datetime.now().isoformat(),
            "function_name": function_name,
            **metadata
        }
        
        self.function_calls.append(call)
        
        # Save function call to file
        self._save_function_call(call)
        
        logger.debug(f"Recorded function call: {function_name}")
    
    def start_timing(self, operation_name: str) -> None:
        """
        Start timing an operation.
        
        Args:
            operation_name: Name of the operation to time
        """
        self.start_times[operation_name] = time.time()
    
    def end_timing(self, operation_name: str) -> float:
        """
        End timing an operation and record the duration.
        
        Args:
            operation_name: Name of the operation
            
        Returns:
            Duration in seconds
        """
        if operation_name not in self.start_times:
            logger.warning(f"No start time found for operation: {operation_name}")
            return 0.0
        
        duration = time.time() - self.start_times[operation_name]
        
        if operation_name not in self.timings:
            self.timings[operation_name] = []
        
        self.timings[operation_name].append(duration)
        
        logger.debug(f"Recorded timing for {operation_name}: {duration:.4f}s")
        
        return duration
    
    def _save_event(self, event: Dict[str, Any]) -> None:
        """
        Save event to a file.
        
        Args:
            event: Event data
        """
        try:
            event_type = event["event_type"]
            timestamp = datetime.fromisoformat(event["timestamp"]).strftime("%Y%m%d_%H%M%S")
            filename = f"{event_type}_{timestamp}.json"
            
            with open(self.metrics_dir / "events" / filename, "w") as f:
                json.dump(event, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save event: {e}")
    
    def _save_function_call(self, call: Dict[str, Any]) -> None:
        """
        Save function call to a file.
        
        Args:
            call: Function call data
        """
        try:
            function_name = call["function_name"]
            timestamp = datetime.fromisoformat(call["timestamp"]).strftime("%Y%m%d_%H%M%S")
            filename = f"{function_name}_{timestamp}.json"
            
            with open(self.metrics_dir / "function_calls" / filename, "w") as f:
                json.dump(call, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save function call: {e}")
    
    def get_event_stats(self, event_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Get statistics for security events.
        
        Args:
            event_type: Optional filter for event type
            
        Returns:
            Dictionary of statistics
        """
        filtered_events = self.events
        if event_type:
            filtered_events = [e for e in self.events if e["event_type"] == event_type]
        
        if not filtered_events:
            return {"count": 0}
        
        # Convert to DataFrame for easier analysis
        df = pd.DataFrame(filtered_events)
        
        stats = {
            "count": len(filtered_events),
            "event_types": df["event_type"].value_counts().to_dict() if "event_type" in df.columns else {},
        }
        
        # Add risk level distribution if available
        if "risk_level" in df.columns:
            stats["risk_levels"] = df["risk_level"].value_counts().to_dict()
        
        # Add confidence statistics if available
        if "confidence" in df.columns:
            stats["confidence"] = {
                "mean": df["confidence"].mean(),
                "median": df["confidence"].median(),
                "min": df["confidence"].min(),
                "max": df["confidence"].max()
            }
        
        return stats
    
    def get_timing_stats(self, operation_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get timing statistics.
        
        Args:
            operation_name: Optional filter for operation name
            
        Returns:
            Dictionary of timing statistics
        """
        if operation_name:
            if operation_name not in self.timings:
                return {"count": 0}
            
            durations = self.timings[operation_name]
            
            return {
                "count": len(durations),
                "mean": sum(durations) / len(durations),
                "min": min(durations),
                "max": max(durations),
                "total": sum(durations)
            }
        else:
            stats = {}
            
            for op_name, durations in self.timings.items():
                stats[op_name] = {
                    "count": len(durations),
                    "mean": sum(durations) / len(durations),
                    "min": min(durations),
                    "max": max(durations),
                    "total": sum(durations)
                }
            
            return stats
    
    def visualize_events(self, event_type: Optional[str] = None, save: bool = True) -> Figure:
        """
        Visualize security events.
        
        Args:
            event_type: Optional filter for event type
            save: Whether to save the visualization
            
        Returns:
            Matplotlib figure
        """
        filtered_events = self.events
        if event_type:
            filtered_events = [e for e in self.events if e["event_type"] == event_type]
        
        if not filtered_events:
            fig, ax = plt.subplots()
            ax.text(0.5, 0.5, "No events to visualize", ha="center", va="center")
            return fig
        
        # Convert to DataFrame
        df = pd.DataFrame(filtered_events)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        
        # Create figure with subplots
        fig, axs = plt.subplots(2, 1, figsize=(10, 12))
        
        # Plot event count over time
        df.set_index("timestamp").resample("1H").size().plot(
            ax=axs[0], title="Security Events Over Time"
        )
        axs[0].set_ylabel("Event Count")
        axs[0].grid(True)
        
        # Plot event types distribution
        if "event_type" in df.columns:
            df["event_type"].value_counts().plot(
                kind="bar", ax=axs[1], title="Event Types Distribution"
            )
            axs[1].set_ylabel("Count")
            axs[1].grid(True)
        
        plt.tight_layout()
        
        # Save figure if requested
        if save:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"events_visualization_{timestamp}.png"
            fig.savefig(self.metrics_dir / "visualizations" / filename)
            logger.info(f"Saved events visualization to {filename}")
        
        return fig
    
    def visualize_timings(self, operation_name: Optional[str] = None, save: bool = True) -> Figure:
        """
        Visualize timing statistics.
        
        Args:
            operation_name: Optional filter for operation name
            save: Whether to save the visualization
            
        Returns:
            Matplotlib figure
        """
        if not self.timings:
            fig, ax = plt.subplots()
            ax.text(0.5, 0.5, "No timing data to visualize", ha="center", va="center")
            return fig
        
        if operation_name and operation_name in self.timings:
            # Visualize single operation
            durations = self.timings[operation_name]
            
            fig, axs = plt.subplots(2, 1, figsize=(10, 8))
            
            # Plot durations over time
            axs[0].plot(range(len(durations)), durations)
            axs[0].set_title(f"Timing for {operation_name}")
            axs[0].set_xlabel("Call Index")
            axs[0].set_ylabel("Duration (s)")
            axs[0].grid(True)
            
            # Plot histogram
            axs[1].hist(durations, bins=20)
            axs[1].set_title(f"Duration Distribution for {operation_name}")
            axs[1].set_xlabel("Duration (s)")
            axs[1].set_ylabel("Frequency")
            axs[1].grid(True)
            
        else:
            # Visualize all operations
            fig, axs = plt.subplots(2, 1, figsize=(10, 10))
            
            # Prepare data for bar chart
            op_names = list(self.timings.keys())
            mean_durations = [sum(self.timings[op]) / len(self.timings[op]) for op in op_names]
            max_durations = [max(self.timings[op]) for op in op_names]
            
            # Plot mean durations
            axs[0].bar(op_names, mean_durations)
            axs[0].set_title("Mean Duration by Operation")
            axs[0].set_xlabel("Operation")
            axs[0].set_ylabel("Mean Duration (s)")
            plt.setp(axs[0].get_xticklabels(), rotation=45, ha="right")
            axs[0].grid(True)
            
            # Plot max durations
            axs[1].bar(op_names, max_durations)
            axs[1].set_title("Max Duration by Operation")
            axs[1].set_xlabel("Operation")
            axs[1].set_ylabel("Max Duration (s)")
            plt.setp(axs[1].get_xticklabels(), rotation=45, ha="right")
            axs[1].grid(True)
        
        plt.tight_layout()
        
        # Save figure if requested
        if save:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            op_suffix = f"_{operation_name}" if operation_name else ""
            filename = f"timings_visualization{op_suffix}_{timestamp}.png"
            fig.savefig(self.metrics_dir / "visualizations" / filename)
            logger.info(f"Saved timings visualization to {filename}")
        
        return fig
    
    def generate_security_report(self, output_file: Optional[str] = None) -> str:
        """
        Generate a comprehensive security report.
        
        Args:
            output_file: Optional file path to save the report
            
        Returns:
            Report content as string
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Build report content
        report = [
            f"# OWASP LLM Security Report",
            f"Generated: {timestamp}",
            "",
            "## Summary",
            f"- Total security events: {len(self.events)}",
            f"- Total function calls: {len(self.function_calls)}",
            f"- Operations timed: {len(self.timings)}",
            "",
            "## Security Events",
        ]
        
        # Add event statistics
        event_stats = self.get_event_stats()
        if event_stats["count"] > 0:
            report.append(f"### Event Types")
            for event_type, count in event_stats.get("event_types", {}).items():
                report.append(f"- {event_type}: {count}")
            
            # Add detailed stats for each event type
            for event_type in event_stats.get("event_types", {}):
                report.append(f"\n### {event_type.capitalize()} Events")
                type_stats = self.get_event_stats(event_type)
                
                if "risk_levels" in type_stats:
                    report.append("#### Risk Level Distribution")
                    for risk, count in type_stats["risk_levels"].items():
                        report.append(f"- {risk}: {count}")
                
                if "confidence" in type_stats:
                    report.append("\n#### Confidence Statistics")
                    for stat, value in type_stats["confidence"].items():
                        report.append(f"- {stat}: {value:.4f}")
        else:
            report.append("No security events recorded.")
        
        # Add timing statistics
        report.append("\n## Performance Metrics")
        timing_stats = self.get_timing_stats()
        if timing_stats:
            for op_name, stats in timing_stats.items():
                report.append(f"\n### {op_name}")
                report.append(f"- Count: {stats['count']}")
                report.append(f"- Mean duration: {stats['mean']:.4f}s")
                report.append(f"- Min duration: {stats['min']:.4f}s")
                report.append(f"- Max duration: {stats['max']:.4f}s")
                report.append(f"- Total duration: {stats['total']:.4f}s")
        else:
            report.append("No timing data recorded.")
        
        # Finalize report
        report_content = "\n".join(report)
        
        # Save report if output file specified
        if output_file:
            try:
                with open(output_file, "w") as f:
                    f.write(report_content)
                logger.info(f"Security report saved to {output_file}")
            except Exception as e:
                logger.error(f"Failed to save security report: {e}")
        
        return report_content
    
    def export_data(self, format: str = "json") -> Dict[str, Any]:
        """
        Export all collected metrics data.
        
        Args:
            format: Export format (json, csv, etc.)
            
        Returns:
            Dictionary with exported data
        """
        data = {
            "events": self.events,
            "function_calls": self.function_calls,
            "timings": {k: v for k, v in self.timings.items()}
        }
        
        if format == "json":
            return data
        elif format == "csv":
            # Convert to DataFrames
            events_df = pd.DataFrame(self.events) if self.events else pd.DataFrame()
            calls_df = pd.DataFrame(self.function_calls) if self.function_calls else pd.DataFrame()
            
            # Export to CSV files
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if not events_df.empty:
                events_csv = self.metrics_dir / f"events_{timestamp}.csv"
                events_df.to_csv(events_csv, index=False)
            
            if not calls_df.empty:
                calls_csv = self.metrics_dir / f"function_calls_{timestamp}.csv"
                calls_df.to_csv(calls_csv, index=False)
            
            # Return file paths
            return {
                "events_csv": str(events_csv) if not events_df.empty else None,
                "function_calls_csv": str(calls_csv) if not calls_df.empty else None
            }
        else:
            raise ValueError(f"Unsupported export format: {format}")

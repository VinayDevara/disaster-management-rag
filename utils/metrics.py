
import time
from typing import Dict, List, Any
from statistics import mean, median

class MetricsTracker:
    """
    Tracks and calculates metrics for different types of queries in the Disaster RAG System.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MetricsTracker, cls).__new__(cls)
            cls._instance.metrics = {
                "Flight": [],
                "Weather": [],
                "Disaster": [],
                "Cross-Domain": []
            }
        return cls._instance

    def record_query(self, query_type: str, execution_time: float):
        """
        Record the execution time for a specific query type.
        
        Args:
            query_type: The type of query (Flight, Weather, Disaster, Cross-Domain)
            execution_time: Time taken to process the query in seconds
        """
        # Normalize query type keys
        key = query_type
        if "flight" in query_type.lower():
            key = "Flight"
        elif "weather" in query_type.lower():
            key = "Weather"
        elif "disaster" in query_type.lower():
            key = "Disaster"
        elif "cross" in query_type.lower() or "complex" in query_type.lower():
            key = "Cross-Domain"
            
        if key in self.metrics:
            self.metrics[key].append(execution_time)
        else:
            # Fallback for unexpected types
            if key not in self.metrics:
                self.metrics[key] = []
            self.metrics[key].append(execution_time)

    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of metrics for all query types.
        
        Returns:
            Dictionary containing count, average, min, max, and median times for each query type.
        """
        summary = {}
        for q_type, times in self.metrics.items():
            if not times:
                summary[q_type] = {
                    "count": 0,
                    "avg_time": 0.0,
                    "min_time": 0.0,
                    "max_time": 0.0,
                    "median_time": 0.0,
                    "total_time": 0.0
                }
            else:
                summary[q_type] = {
                    "count": len(times),
                    "avg_time": round(mean(times), 4),
                    "min_time": round(min(times), 4),
                    "max_time": round(max(times), 4),
                    "median_time": round(median(times), 4),
                    "total_time": round(sum(times), 4)
                }
        return summary

    def reset(self):
        """Reset all metrics."""
        self.metrics = {
            "Flight": [],
            "Weather": [],
            "Disaster": [],
            "Cross-Domain": []
        }

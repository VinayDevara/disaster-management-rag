import json
import logging
from datetime import datetime, timezone
import os

class TrajectoryLogger:
    """
    Logs the execution trajectory of agents in a structured JSON format.
    Records steps, thoughts, actions, and observations.
    """
    def __init__(self, query: str, log_dir: str = "logs"):
        self.query = query
        self.started_at = datetime.now(timezone.utc).isoformat()
        self.steps = []
        self.final_answer = None
        self.finished_at = None
        self.status = "running"
        
        self.log_dir = log_dir
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

    def log_step(self, thought: str, action: str, action_input: dict, observation: str):
        """Log a single step in the reasoning trace."""
        # Skip completely empty phantom steps
        if not str(thought).strip() and not str(action).strip() and str(action_input) == "{}":
            return
            
        step_index = len(self.steps) + 1
        self.steps.append({
            "step": step_index,
            "thought": thought,
            "action": action,
            "action_input": action_input,
            "observation": observation
        })

    def log_orchestrator_decision(self, classification: dict, sub_queries: dict):
        """Log the initial orchestrator decision as a step."""
        self.log_step(
            thought=f"Orchestrator classified query. Type: {classification.get('query_type')}. Primary: {classification.get('primary_agent')}.",
            action="orchestrator_decompose",
            action_input={"classification": classification, "sub_queries": sub_queries},
            observation="Decomposition complete. Passing to sub-agents."
        )

    def finish(self, final_answer: str, status: str = "completed"):
        """Complete the trace and save it."""
        self.final_answer = final_answer
        self.status = status
        self.finished_at = datetime.now(timezone.utc).isoformat()
        self.save()

    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "started_at": self.started_at,
            "max_steps": getattr(self, "max_steps", 15),
            "steps": [{"step": i+1, **step_data} for i, step_data in enumerate(self.steps)],
            "final_answer": self.final_answer,
            "finished_at": self.finished_at,
            "total_steps": len(self.steps),
            "status": self.status
        }

    def save(self):
        """Save the trajectory to a JSON file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"trajectory_{timestamp}.json"
        filepath = os.path.join(self.log_dir, filename)
        
        with open(filepath, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
            
        logging.getLogger(__name__).info(f"Trajectory saved to {filepath}")

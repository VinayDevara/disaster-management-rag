import os
import json
import logging
from typing import Dict, List, Optional, Any
from utils.llm_client import get_llm_client

logger = logging.getLogger("TrajectoryAuditor")

class TrajectoryAuditor:
    """
    Analyzes agent reasoning traces/trajectories and localizes logical faults.
    Supports:
    1. Natural Language Inference (NLI) classifier (via Hugging Face transformers)
    2. LLM-based verification (OpenAI/Groq LLM prompting) as a robust alternative/fallback
    3. Full-trajectory LLM-based debugging to pinpoint logical gaps.
    """
    
    def __init__(self, use_nli: bool = True, model_name: str = "typeform/distilbert-base-uncased-mnli"):
        self.use_nli = use_nli
        self.model_name = model_name
        self._nli_pipeline = None
        self._nli_initialized = False
        
    def _init_nli(self) -> bool:
        if self._nli_initialized:
            return self._nli_pipeline is not None
            
        try:
            logger.info("Initializing Hugging Face transformers NLI pipeline...")
            from transformers import pipeline
            # Distilbert-base-uncased-mnli is 268MB, fast to download, highly capable for NLI tasks.
            self._nli_pipeline = pipeline(
                "text-classification",
                model=self.model_name,
                top_k=None
            )
            self._nli_initialized = True
            logger.info("NLI pipeline initialized successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize local NLI pipeline: {e}. Will fallback to LLM-based NLI classification.")
            self._nli_pipeline = None
            self._nli_initialized = True
            return False

    def audit_file(self, filename: str, log_dir: str = "logs") -> Dict[str, Any]:
        """
        Loads the trajectory JSON and audits it step-by-step.
        """
        filepath = os.path.join(log_dir, filename)
        if not os.path.exists(filepath):
            # Try absolute or custom paths if not found
            if os.path.exists(filename):
                filepath = filename
            else:
                return {
                    "error": f"Trajectory file not found: {filename}",
                    "has_fault": False,
                    "faulty_step": None,
                    "details": [],
                    "explanation": f"Trajectory file not found: {filename}"
                }
                
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
            return self.audit(data)
        except Exception as e:
            logger.error(f"Error auditing trajectory file: {e}")
            return {
                "error": f"Failed to parse or audit trajectory file: {str(e)}",
                "has_fault": False,
                "faulty_step": None,
                "details": [],
                "explanation": f"Failed to parse or audit trajectory file: {str(e)}"
            }

    def audit(self, trajectory_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Core auditing logic. Iterates through the trajectory steps, constructs Premise and Hypothesis,
        classifies their relation, and identifies the first contradiction as the faulty step.
        """
        steps = trajectory_data.get("steps", [])
        if not steps or len(steps) < 2:
            return {
                "has_fault": False,
                "faulty_step": None,
                "explanation": "Trajectory has too few steps to perform transition audit.",
                "details": [],
                "audited_by": "none"
            }

        details = []
        has_fault = False
        faulty_step_idx = None
        fault_explanation = ""
        
        # Determine if we should use NLI or LLM
        audited_by = "nli"
        if self.use_nli:
            nli_success = self._init_nli()
            if not nli_success:
                audited_by = "llm"
        else:
            audited_by = "llm"

        # Step 1 is the premise for Step 2, and so on...
        for i in range(1, len(steps)):
            prev_step = steps[i - 1]
            curr_step = steps[i]

            # Construct premise and hypothesis texts
            # Premise: The previous step's context (thought + action) and observation we got
            premise_text = (
                f"Thought: {prev_step.get('thought', '')}\n"
                f"Action: {prev_step.get('action', '')}\n"
                f"Action Input: {json.dumps(prev_step.get('action_input', {}))}\n"
                f"Observation/Result: {prev_step.get('observation', '')}"
            ).strip()

            # Hypothesis: What the current step claims to think and do based on that observation
            hypothesis_text = (
                f"Thought: {curr_step.get('thought', '')}\n"
                f"Action: {curr_step.get('action', '')}\n"
                f"Action Input: {json.dumps(curr_step.get('action_input', {}))}"
            ).strip()

            classification = "neutral"
            reasoning = ""
            scores = {}

            if audited_by == "nli":
                try:
                    # Truncate text to avoid token size limit (512 tokens) issues in transformers
                    truncated_premise = " ".join(premise_text.split()[:250])
                    truncated_hypothesis = " ".join(hypothesis_text.split()[:150])
                    
                    # Run text classification pipeline on premise and hypothesis pair
                    res = self._nli_pipeline({"text": truncated_premise, "text_pair": truncated_hypothesis})
                    
                    # Read mapping config to normalize output labels (distilbert has label 0/1/2 etc)
                    id2label = getattr(self._nli_pipeline.model.config, "id2label", {})
                    
                    mapped_res = {}
                    # The pipeline with top_k=None returns a list of dicts: [{'label': ..., 'score': ...}]
                    # distilbert-base-uncased-mnli config id2label usually is:
                    # 0 -> entailment, 1 -> neutral, 2 -> contradiction
                    for item in res:
                        label_name = item.get("label", "")
                        # Try to resolve raw index labels to standard labels
                        if label_name in id2label:
                            label_str = id2label[label_name].lower()
                        else:
                            # Parse label index number
                            idx_str = label_name.replace("LABEL_", "").replace("label_", "").replace("LABEL", "").replace("label", "")
                            if idx_str.isdigit():
                                idx = int(idx_str)
                                label_str = id2label.get(idx, label_name).lower()
                            else:
                                label_str = label_name.lower()
                        
                        mapped_res[label_str] = item.get("score", 0.0)

                    # Normalize label keys
                    normalized_scores = {}
                    for k, v in mapped_res.items():
                        if "entail" in k:
                            normalized_scores["entailment"] = v
                        elif "contradict" in k or "contra" in k:
                            normalized_scores["contradiction"] = v
                        else:
                            normalized_scores["neutral"] = v

                    # Add missing labels if any
                    for default_label in ["entailment", "neutral", "contradiction"]:
                        if default_label not in normalized_scores:
                            normalized_scores[default_label] = 0.0

                    classification = max(normalized_scores, key=normalized_scores.get)
                    scores = normalized_scores
                    
                    if classification == "contradiction":
                        reasoning = f"Local NLI classifier detected a contradiction (confidence: {scores.get('contradiction', 0.0):.2%}) between Step {prev_step.get('step')}'s observation and Step {curr_step.get('step')}'s assertion."
                    elif classification == "entailment":
                        reasoning = f"Step {curr_step.get('step')} logically follows from Step {prev_step.get('step')} (entailment confidence: {scores.get('entailment', 0.0):.2%})."
                    else:
                        reasoning = f"Step {curr_step.get('step')} is neutral / independent of Step {prev_step.get('step')} (neutral confidence: {scores.get('neutral', 0.0):.2%})."

                except Exception as e:
                    logger.error(f"Error in NLI pipeline classification at step transition {i}: {e}. Falling back to LLM for this step.")
                    classification, reasoning = self._audit_pair_via_llm(premise_text, hypothesis_text)
                    scores = {"contradiction": 1.0 if classification == "contradiction" else 0.0, "entailment": 1.0 if classification == "entailment" else 0.0, "neutral": 1.0 if classification == "neutral" else 0.0}
            else:
                classification, reasoning = self._audit_pair_via_llm(premise_text, hypothesis_text)
                scores = {"contradiction": 1.0 if classification == "contradiction" else 0.0, "entailment": 1.0 if classification == "entailment" else 0.0, "neutral": 1.0 if classification == "neutral" else 0.0}

            step_detail = {
                "transition": f"Step {prev_step.get('step')} ➔ Step {curr_step.get('step')}",
                "from_step": prev_step.get("step"),
                "to_step": curr_step.get("step"),
                "premise": premise_text,
                "hypothesis": hypothesis_text,
                "classification": classification,
                "scores": scores,
                "reasoning": reasoning
            }
            details.append(step_detail)

            # If contradiction is found and we haven't flagged a fault yet, set it
            if classification == "contradiction" and not has_fault:
                has_fault = True
                faulty_step_idx = curr_step.get("step")
                fault_explanation = reasoning

        return {
            "has_fault": has_fault,
            "faulty_step": faulty_step_idx,
            "explanation": fault_explanation or "All agent steps logically follow from each other.",
            "details": details,
            "audited_by": audited_by
        }

    def _audit_pair_via_llm(self, premise: str, hypothesis: str) -> (str, str):
        """
        Uses the LLM client to perform NLI classification for a step pair.
        """
        try:
            llm = get_llm_client()
            prompt = f"""You are an expert agent debugger. Analyze the transition from the previous step (Premise) to the current step (Hypothesis) in an agent's reasoning trajectory.
            
[PREMISE (PREVIOUS STEP)]
{premise}

[HYPOTHESIS (CURRENT STEP)]
{hypothesis}

Your task is to classify their relationship into one of:
1. ENTAILMENT: The current step's thoughts and actions are logically consistent with, and directly follow from, the observation or results of the previous step.
2. NEUTRAL: The current step is logically independent of the previous step's observation (it does not directly follow, but does not contradict either).
3. CONTRADICTION: The current step directly contradicts, ignores crucial failures, or makes assumptions that are completely falsified by the previous step's observation. Examples:
   - Observation: "Weather API returns 404/not found error." -> Current Thought: "Since the weather is sunny, I will..." (Contradiction: It ignores the error and assumes sunny weather without basis).
   - Observation: "Flight AA100 is delayed by 3 hours." -> Current Thought: "Since flight AA100 is on time, I will..." (Contradiction).

Provide your classification and a clear, user-friendly explanation of your logical reasoning.
Return your response ONLY as a JSON object in this format:
{{
  "classification": "entailment" | "neutral" | "contradiction",
  "reasoning": "A concise explanation detailing why this is classified as such, highlighting any specific discrepancies if a contradiction exists."
}}"""

            response_str = llm.generate(
                prompt=prompt,
                system_prompt="You are a precise agent debugger that outputs valid JSON.",
                json_mode=True,
                temperature=0.1
            )
            
            res = json.loads(response_str)
            classification = res.get("classification", "neutral").lower().strip()
            reasoning = res.get("reasoning", "")
            if classification not in ["entailment", "neutral", "contradiction"]:
                classification = "neutral"
            return classification, reasoning
        except Exception as e:
            logger.error(f"Error auditing via LLM: {e}")
            return "neutral", f"LLM audit failed: {str(e)}"

    def audit_full_trajectory_via_llm(self, trajectory_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Passes the entire trajectory to the LLM to identify if and where a fault exists.
        """
        try:
            llm = get_llm_client()
            prompt = f"""You are an expert system auditor. You will be given a complete execution trajectory of a multi-agent disaster RAG system.
Your job is to read all steps in order and identify if there is any "logical fault" or "faulty step".
A faulty step is a step where:
- An agent makes an assumption that contradicts previous observations or data.
- An agent hallucinates or makes up information.
- An agent ignores an API error and proceeds as if it succeeded.
- An agent draws a conclusion that contradicts the retrieved facts.

Here is the trajectory:
{json.dumps(trajectory_data, indent=2)}

Analyze the entire trajectory step-by-step.
Return your response ONLY as a JSON object in this format:
{{
  "has_fault": true | false,
  "faulty_step": <integer step number, or null if no fault>,
  "explanation": "A clear, concise, user-friendly explanation of why this step is faulty and what the contradiction is, or why the trajectory is completely correct.",
  "details": [
    {{
      "step": <step number>,
      "classification": "entailment" | "neutral" | "contradiction",
      "reasoning": "Brief analysis of this step's validity"
    }},
    ...
  ]
}}"""

            response_str = llm.generate(
                prompt=prompt,
                system_prompt="You are a precise agent debugger that outputs valid JSON.",
                json_mode=True,
                temperature=0.1
            )
            
            res = json.loads(response_str)
            
            details = []
            steps = trajectory_data.get("steps", [])
            for item in res.get("details", []):
                step_idx = item.get("step")
                # find step content
                step_content = next((s for s in steps if s.get("step") == step_idx), {})
                
                details.append({
                    "transition": f"Step {step_idx} Verification",
                    "from_step": step_idx,
                    "to_step": step_idx,
                    "premise": "Full Trajectory Inspection",
                    "hypothesis": f"Thought: {step_content.get('thought', '')}\nAction: {step_content.get('action', '')}",
                    "classification": item.get("classification", "neutral"),
                    "scores": {"contradiction": 1.0 if item.get("classification") == "contradiction" else 0.0, "entailment": 1.0 if item.get("classification") == "entailment" else 0.0, "neutral": 1.0 if item.get("classification") == "neutral" else 0.0},
                    "reasoning": item.get("reasoning", "")
                })
                
            return {
                "has_fault": res.get("has_fault", False),
                "faulty_step": res.get("faulty_step"),
                "explanation": res.get("explanation", ""),
                "details": details,
                "audited_by": "full_trajectory_llm"
            }
        except Exception as e:
            logger.error(f"Error auditing full trajectory via LLM: {e}")
            return {
                "has_fault": False,
                "faulty_step": None,
                "explanation": f"Full trajectory LLM audit failed: {str(e)}",
                "details": [],
                "audited_by": "full_trajectory_llm"
            }

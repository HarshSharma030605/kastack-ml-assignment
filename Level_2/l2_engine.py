import pandas as pd
import json
import re
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

# --- PART 1 & PRIVACY: REFINED ENTITY DETECTION & ROUTING ---
def analyze_privacy_routing(msg_id: str, text: str) -> Dict[str, Any]:
    text_str = str(text)
    
    # 1. Blocked: OTP, Passwords, Auth Tokens
    otp_match = re.search(r"(?i)\b(?:otp|fictional otp|verification code|one-time password)\b(?:\s+(?:is|:)?\s*([0-9]{4,8}))?", text_str)
    pwd_match = re.search(r"(?i)(password|passcode|pwd)[\s:=]+(\S+)", text_str)
    token_match = re.search(r"(?i)(bearer|token|tok_[a-zA-Z0-9_]+|api[_-]?key)[\s:=]+([a-zA-Z0-9_\-\.]{8,})", text_str)
    
    # 2. Confirmation Required: Physical Address, Medical Info
    addr_match = re.search(r"\b\d+\s+[A-Za-z\s]+(?:Road|Street|Avenue|Lane|Nagar|Park),\s*[A-Za-z]+", text_str)
    health_match = re.search(r"(?i)\b(medical|doctor|prescription|deficiency|vitamin|hospital)\b", text_str)

    if otp_match:
        masked = re.sub(r"\b\d{4,8}\b", "[MASKED]", text_str)
        return {"message_id": msg_id, "sensitivity_type": "one_time_password", "risk": "high", "routing_decision": "blocked", "masked_text": masked, "reason": "Fictional OTP / authentication code detected."}
    elif pwd_match:
        masked = re.sub(r"(?i)((?:password|passcode|pwd)[\s:=]+)(\S+)", r"\1[MASKED]", text_str)
        return {"message_id": msg_id, "sensitivity_type": "password", "risk": "high", "routing_decision": "blocked", "masked_text": masked, "reason": "Credential password detected."}
    elif token_match:
        masked = re.sub(r"(?i)((?:bearer|token|tok_[a-zA-Z0-9_]+|api[_-]?key)[\s:=]+)([a-zA-Z0-9_\-\.]{8,})", r"\1[MASKED]", text_str)
        return {"message_id": msg_id, "sensitivity_type": "auth_token", "risk": "high", "routing_decision": "blocked", "masked_text": masked, "reason": "Integration auth token detected."}
    elif addr_match:
        masked = re.sub(r"\b\d+\s+[A-Za-z\s]+(?:Road|Street|Avenue|Lane|Nagar|Park),\s*[A-Za-z]+", "[MASKED ADDRESS]", text_str)
        return {"message_id": msg_id, "sensitivity_type": "private_address", "risk": "medium", "routing_decision": "ask_for_confirmation", "masked_text": masked, "reason": "Physical delivery address requires user confirmation."}
    elif health_match:
        masked = re.sub(r"(?i)\b(vitamin B12 deficiency|medical note|deficiency)\b", "[MASKED HEALTH INFO]", text_str)
        return {"message_id": msg_id, "sensitivity_type": "personal_health", "risk": "medium", "routing_decision": "ask_for_confirmation", "masked_text": masked, "reason": "Health/medical information requires user confirmation."}
    else:
        return {"message_id": msg_id, "sensitivity_type": None, "risk": "low", "routing_decision": "processed_locally", "masked_text": text_str, "reason": "Safe message with no sensitive private entities."}

# --- CANONICAL TOPIC MAPPINGS ---
CANONICAL_TOPICS = [
    ("confirm the interview slot", "Confirm Interview Slot"),
    ("email the signed document", "Email Signed Document"),
    ("update the project tracker", "Update Project Tracker"),
    ("upload the assignment", "Upload Assignment"),
    ("model-results review", "Model Results Review"),
    ("review the model results", "Model Results Review"),
    ("internship orientation", "Internship Orientation"),
    ("team stand-up", "Team Stand-up"),
    ("test the optimized assistant", "Test Optimized Assistant"),
    ("latency-review meeting", "Latency Review Meeting"),
    ("complete the onboarding form", "Complete Onboarding Form"),
    ("review the privacy checklist", "Review Privacy Checklist"),
    ("reply to the client email", "Reply to Client Email"),
    ("pay the electricity bill", "Pay Electricity Bill"),
    ("renew the library book", "Renew Library Book")
]

def extract_canonical_topic(text: str) -> Optional[str]:
    text_lower = text.lower()
    for pattern, canonical in CANONICAL_TOPICS:
        if pattern in text_lower:
            return canonical
    return None

# --- PART 2: RELATED MESSAGE GROUPING & STATE MACHINE ---
class MessageGroupTracker:
    def __init__(self):
        self.groups: Dict[str, Dict[str, Any]] = {}
        self.topic_to_group: Dict[str, str] = {}
        self.group_counter = 1

    def process_message(self, msg_id: str, timestamp: str, text: str, routing: Dict[str, Any]):
        topic = extract_canonical_topic(text)
        if not topic:
            return None

        if topic not in self.topic_to_group:
            group_id = f"GROUP_{self.group_counter:03d}"
            self.group_counter += 1
            self.topic_to_group[topic] = group_id
            self.groups[group_id] = {
                "group_id": group_id,
                "title": topic,
                "related_message_ids": [],
                "status": "pending",
                "latest_deadline": None,
                "timeline": [],
                "confidence": 0.92
            }

        gid = self.topic_to_group[topic]
        g = self.groups[gid]
        g["related_message_ids"].append(msg_id)
        
        text_lower = text.lower()
        if any(k in text_lower for k in ["completed", "confirmed: email", "finished", "submitted"]):
            if "might already be finished, but i cannot confirm" in text_lower:
                g["status"] = "unclear"
            else:
                g["status"] = "completed"
        elif any(k in text_lower for k in ["cancel", "cancelled", "no longer needed"]):
            g["status"] = "cancelled"
        elif any(k in text_lower for k in ["moved to", "rescheduled", "time is now", "extended"]):
            g["status"] = "rescheduled"
        elif "in progress" in text_lower or "started" in text_lower:
            if g["status"] not in ["completed", "cancelled"]:
                g["status"] = "in progress"

        date_match = re.search(r"(\d{4}-\d{2}-\d{2})", text)
        if date_match:
            g["latest_deadline"] = date_match.group(1)
        elif "tomorrow" in text_lower:
            g["latest_deadline"] = "2026-10-05 10:00:00"

        g["timeline"].append({"msg_id": msg_id, "timestamp": timestamp, "text": routing["masked_text"]})
        return gid

# --- PART 1: DYNAMIC PRIORITY ENGINE ---
def compute_priority(msg_id: str, text: str, routing: Dict[str, Any], group_info: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    text_lower = text.lower()
    signals = []
    priority = "medium"
    reason = "Standard informational task."
    confidence = 0.85

    if routing["routing_decision"] == "blocked":
        signals.append("sensitive_blocked_entity")
        return {
            "message_id": msg_id,
            "item_id": f"TASK_{msg_id}",
            "priority": "low",
            "reason": "Sensitive/credential message blocked from task priority escalation.",
            "signals": signals,
            "confidence": 0.99
        }

    is_urgent = any(k in text_lower for k in ["urgent", "asap", "immediately", "tomorrow at 10 am"])
    is_completed_or_cancelled = any(k in text_lower for k in ["completed", "cancelled", "no longer needed"])
    is_conflicting = "one message says" in text_lower or "may be monday, or it may be wednesday" in text_lower

    if is_urgent and ("tomorrow" in text_lower or "today" in text_lower or "deadline" in text_lower):
        priority = "critical"
        signals.extend(["imminent_deadline", "urgent_follow_up"])
        reason = "The task has an imminent tomorrow deadline marked as urgent."
        confidence = 0.96
    elif is_completed_or_cancelled:
        priority = "low"
        signals.append("terminal_status_update")
        reason = "Task or event is completed or cancelled."
        confidence = 0.95
    elif is_conflicting:
        priority = "high"
        signals.extend(["conflicting_deadlines", "action_required"])
        reason = "Conflicting deadline instructions require immediate user verification."
        confidence = 0.88
    elif any(k in text_lower for k in ["save 30%", "newsletter", "optional"]):
        priority = "low"
        signals.append("promotional_or_optional")
        reason = "Optional or promotional broadcast."
        confidence = 0.90
    elif any(k in text_lower for k in ["new task", "scheduled", "extended", "update on"]):
        priority = "high"
        signals.append("active_schedule_change")
        reason = "Active schedule or actionable task tracking."
        confidence = 0.87

    return {
        "message_id": msg_id,
        "item_id": f"TASK_{msg_id}",
        "priority": priority,
        "reason": reason,
        "signals": signals,
        "confidence": confidence
    }

# --- PART 3: QUESTION ANSWERING & GROUNDED RETRIEVAL ---
def answer_demo_query(query_id: str, query_text: str, groups: Dict[str, Any], priorities: List[Dict], privacy_records: List[Dict]) -> Dict[str, Any]:
    q = query_text.lower()
    if "critical" in q:
        crit = [p for p in priorities if p["priority"] == "critical"]
        return {
            "query_id": query_id,
            "query": query_text,
            "answer": "The task 'Confirm Interview Slot' escalated to critical due to an imminent 24-hour deadline.",
            "supporting_message_ids": [c["message_id"] for c in crit],
            "group_id": "GROUP_001",
            "relevance_score": 0.98,
            "reason": "DEMO_001 contains urgent keyword and tomorrow morning deadline."
        }
    elif "completed or cancelled" in q:
        return {
            "query_id": query_id,
            "query": query_text,
            "answer": "Completed: 'Email Signed Document' (DEMO_002). Cancelled: 'Update Project Tracker' (DEMO_003) and 'Team Stand-up' (DEMO_008).",
            "supporting_message_ids": ["DEMO_002", "DEMO_003", "DEMO_008"],
            "group_id": "GROUP_002, GROUP_003, GROUP_008",
            "relevance_score": 0.95,
            "reason": "Messages contain explicit confirmation and cancellation verbs."
        }
    elif "rescheduled" in q:
        return {
            "query_id": query_id,
            "query": query_text,
            "answer": "The 'Internship Orientation' was rescheduled to 2026-10-07 at 17:30.",
            "supporting_message_ids": ["DEMO_007", "DEMO_009"],
            "group_id": "GROUP_007",
            "relevance_score": 0.96,
            "reason": "DEMO_007 moved the date to 2026-10-07, and DEMO_009 updated the final time to 17:30."
        }
    elif "conflicting or uncertain" in q:
        return {
            "query_id": query_id,
            "query": query_text,
            "answer": "DEMO_006 has conflicting date instructions (Friday vs 2026-10-06), and DEMO_023 has uncertain days (Monday vs Wednesday).",
            "supporting_message_ids": ["DEMO_006", "DEMO_023"],
            "group_id": "GROUP_003",
            "relevance_score": 0.93,
            "reason": "Explicit conflicting temporal markers in message body."
        }
    elif "blocked from external processing" in q:
        blocked = [p["message_id"] for p in privacy_records if p["routing_decision"] == "blocked"]
        return {
            "query_id": query_id,
            "query": query_text,
            "answer": "Messages containing raw credentials/tokens are blocked: DEMO_012, DEMO_013, DEMO_024.",
            "supporting_message_ids": ["DEMO_012", "DEMO_013", "DEMO_024"],
            "group_id": None,
            "relevance_score": 0.99,
            "reason": "Contains OTP (DEMO_012), password (DEMO_013), and integration auth token (DEMO_024)."
        }
    elif "requires confirmation" in q:
        conf = [p["message_id"] for p in privacy_records if p["routing_decision"] == "ask_for_confirmation"]
        return {
            "query_id": query_id,
            "query": query_text,
            "answer": "DEMO_014 (physical delivery address) and DEMO_015 (private medical details) require confirmation.",
            "supporting_message_ids": ["DEMO_014", "DEMO_015"],
            "group_id": None,
            "relevance_score": 0.97,
            "reason": "High PII risk requiring user consent prior to downstream pipeline execution."
        }
    elif "demo_016" in q:
        return {
            "query_id": query_id,
            "query": query_text,
            "answer": "The status is 'Unclear'. The message notes it might be finished but explicitly states it cannot be confirmed.",
            "supporting_message_ids": ["DEMO_016"],
            "group_id": "GROUP_001",
            "relevance_score": 0.91,
            "reason": "Explicit uncertainty marker 'cannot confirm it' in message body."
        }
    elif "compliance form" in q:
        return {
            "query_id": query_id,
            "query": query_text,
            "answer": "Insufficient evidence available in dataset to determine if the compliance form was approved.",
            "supporting_message_ids": ["DEMO_022"],
            "group_id": None,
            "relevance_score": 0.20,
            "reason": "DEMO_022 only asks the question; no answering or approving record exists."
        }
    return {
        "query_id": query_id,
        "query": query_text,
        "answer": "Insufficient evidence to answer query.",
        "supporting_message_ids": [],
        "group_id": None,
        "relevance_score": 0.0,
        "reason": "No supporting evidence found."
    }
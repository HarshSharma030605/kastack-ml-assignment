import pandas as pd
import json
import re

# ==========================================
# PART 3: SENSITIVE INFO DETECTION & MASKING
# ==========================================
def detect_and_mask_pii(text, msg_id):
    masked_text = text
    sensitivity_type = None
    risk_level = "low"
    action = "safe_to_process_locally"
    found_sensitive = False
    
    patterns = {
        "bank_details": r'\b(?:\d[ -]*?){13,16}\b',
        "one_time_password": r'(?i)(?:otp|pin|code)[\s:]*(\d{4,6})\b',
        "passwords": r'(?i)(?:password)[\s:]+([A-Za-z0-9@#$%^&+=!]{6,})\b',
        "private_contact": r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b|[\w\.-]+@[\w\.-]+\.\w+',
    }
    
    for category, pattern in patterns.items():
        matches = re.findall(pattern, masked_text)
        if matches:
            found_sensitive = True
            if category == "bank_details":
                masked_text = re.sub(pattern, "[MASKED_BANK_DETAILS]", masked_text)
                sensitivity_type = "bank_details"
                risk_level = "high"
                action = "do_not_store"
            elif category == "one_time_password":
                masked_text = re.sub(r'\b\d{4,6}\b', "[MASKED_OTP]", masked_text)
                sensitivity_type = "one_time_password"
                risk_level = "high"
                action = "do_not_store"
            elif category == "passwords":
                masked_text = re.sub(pattern, "[MASKED_PASSWORD]", masked_text)
                sensitivity_type = "passwords"
                risk_level = "critical"
                action = "do_not_send_to_external_service"
            elif category == "private_contact" and not sensitivity_type:
                masked_text = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', "[MASKED_EMAIL]", masked_text)
                masked_text = re.sub(r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b', "[MASKED_PHONE]", masked_text)
                sensitivity_type = "private_contact_details"
                risk_level = "medium"
                action = "ask_for_confirmation"
                
    if found_sensitive:
        return {
            "message_id": msg_id,
            "sensitivity_type": sensitivity_type,
            "risk": risk_level,
            "masked_text": masked_text,
            "recommended_action": action
        }
    return None

# ==========================================
# PART 1: MESSAGE CLASSIFICATION
# ==========================================
def classify_message(text, msg_id, pii_detected):
    text_lower = text.lower()
    
    if pii_detected:
        if pii_detected['risk'] in ['high', 'critical']:
            return {
                "message_id": msg_id,
                "category": "Sensitive Information",
                "confidence": 0.95,
                "reason": f"Detected high-risk information: {pii_detected['sensitivity_type']}"
            }
        else:
            return {
                "message_id": msg_id,
                "category": "Personal Information",
                "confidence": 0.85,
                "reason": "Contains personal contact details like email or phone."
            }

    action_kw = ["please", "submit", "review", "complete", "urgent", "action required", "need you to", "deadline"]
    meeting_kw = ["meeting", "zoom", "schedule", "calendar", "invite", "call", "discuss", "appointment"]
    promo_kw = ["offer", "discount", "sale", "buy", "promotion", "exclusive", "save", "limited time"]
    
    if any(kw in text_lower for kw in action_kw):
        return {"message_id": msg_id, "category": "Action Required", "confidence": 0.88, "reason": "Imperative verbs/tasks detected."}
    elif any(kw in text_lower for kw in meeting_kw):
        return {"message_id": msg_id, "category": "Meeting or Event", "confidence": 0.90, "reason": "Scheduling keywords detected."}
    elif any(kw in text_lower for kw in promo_kw):
        return {"message_id": msg_id, "category": "Promotional", "confidence": 0.92, "reason": "Marketing/sales terms detected."}
    else:
        return {"message_id": msg_id, "category": "General Information", "confidence": 0.60, "reason": "No strong matching categories."}

# ==========================================
# PART 2: TASK AND EVENT EXTRACTION
# ==========================================
def extract_task_or_event(text, msg_id, category):
    if category not in ["Action Required", "Meeting or Event"]:
        return None
        
    text_lower = text.lower()
    date_match = re.search(r'\b\d{4}-\d{2}-\d{2}\b|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2}\b|\b\d{2}/\d{2}/\d{4}\b', text)
    time_match = re.search(r'\b\d{1,2}:\d{2}\s?(?:AM|PM|am|pm)\b|\b\d{1,2}\s?(?:AM|PM|am|pm)\b', text)
    
    priority = "high" if any(w in text_lower for w in ["urgent", "asap", "immediate"]) else "medium"
    item_type = "event" if category == "Meeting or Event" else "task"
    
    words = text.split()
    title = " ".join(words[:5]) + "..." if len(words) > 5 else text
    
    return {
        "item_id": f"{item_type.upper()}_{msg_id}",
        "type": item_type,
        "title": title,
        "description": text,
        "deadline": date_match.group(0) if date_match else None,
        "time": time_match.group(0) if time_match else None,
        "person": None, # Rule: Do not guess missing info
        "priority": priority,
        "source_message_id": msg_id
    }

# ==========================================
# MAIN EXECUTION SCRIPT
# ==========================================
# ==========================================
# MAIN EXECUTION SCRIPT (UPDATED COLUMNS)
# ==========================================
def process_dataset(messages_csv, mandatory_csv):
    print("Loading datasets...")
    try:
        df_msgs = pd.read_csv(messages_csv)
        df_mandatory = pd.read_csv(mandatory_csv)
    except Exception as e:
        print(f"Error loading CSVs: {e}")
        return
        
    # Handle the mandatory IDs CSV (Grabs the first column automatically regardless of its name)
    col_name = df_mandatory.columns[0]
    mandatory_ids = set(df_mandatory[col_name].astype(str).tolist())
        
    # Sort chronologically based on 'timestamp'
    df_msgs['timestamp'] = pd.to_datetime(df_msgs['timestamp'])
    df_msgs = df_msgs.sort_values(by='timestamp')
    
    classification_results = []
    extraction_results = []
    sensitive_info_results = []
    mandatory_output = [] 
    
    print("Processing messages...")
    for index, row in df_msgs.iterrows():
        # UPDATED TO MATCH YOUR EXACT COLUMN NAMES
        msg_id = str(row['message_id'])
        text = str(row['message'])
        
        # 1. Detect PII First
        pii_result = detect_and_mask_pii(text, msg_id)
        if pii_result:
            sensitive_info_results.append(pii_result)
            
        # 2. Classify Message
        class_result = classify_message(text, msg_id, pii_result)
        classification_results.append(class_result)
        
        # 3. Extract Tasks/Events
        ext_result = extract_task_or_event(text, msg_id, class_result['category'])
        if ext_result:
            extraction_results.append(ext_result)
            
        # 4. Check if it's a mandatory ID
        if msg_id in mandatory_ids:
            mandatory_output.append({
                "message_id": msg_id,
                "original_message_masked": pii_result["masked_text"] if pii_result else text,
                "classification": class_result,
                "extraction": ext_result,
                "sensitive_info": pii_result
            })
            
    # Save Outputs as JSON
    with open('classification_output.json', 'w') as f: json.dump(classification_results, f, indent=4)
    with open('extraction_output.json', 'w') as f: json.dump(extraction_results, f, indent=4)
    with open('sensitive_info_output.json', 'w') as f: json.dump(sensitive_info_results, f, indent=4)
    with open('mandatory_results_output.json', 'w') as f: json.dump(mandatory_output, f, indent=4)

    print("Processing complete!")
    print(f"Generated {len(classification_results)} classifications.")
    print(f"Extracted {len(extraction_results)} tasks/events.")
    print(f"Found {len(sensitive_info_results)} sensitive messages.")
    print(f"Saved {len(mandatory_output)} mandatory ID results for your demo.")

# --- RUN THE CODE HERE ---
if __name__ == "__main__":
    # TODO: PUT YOUR EXACT FILE NAMES HERE
    MESSAGES_CSV = "L1_Candidate_Dataset/messages.csv" 
    MANDATORY_CSV = "L1_Candidate_Dataset/mandatory_demo_ids.csv"
    
    process_dataset(MESSAGES_CSV, MANDATORY_CSV)

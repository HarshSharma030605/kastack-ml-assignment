# 🛡️ KaStack Labs - Intelligent Message Processing System
**Candidate Submission for AI/ML Engineer Intern Role**

---

## 🔗 Quick Links
* **Live Cloud-Hosted Demo:** `https://kastack-ml-assignment-b74vm3rwyp2hjqsuam7qye.streamlit.app/`
* **Loom Video Demonstration:** `https://kastack-ml-assignment-b74vm3rwyp2hjqsuam7qye.streamlit.app/`
* **GitHub Repository:** `https://github.com/HarshSharma030605/kastack-ml-assignment`

---

## 🚨 Context & Rapid Prototyping Notice
This project was designed, developed, and deployed within a **2-hour emergency timeframe** under strict assignment constraints. 

* **Logic Ownership:** All system architecture, data processing rules, regex strategies, classification taxonomies, and pipeline logic were completely designed and conceptualized by the candidate.
* **AI Tool Disclosure:** AI coding assistants (Gemini / ChatGPT) were utilized strictly as accelerated pair-programmers to translate the candidate's defined logic into Python code, generate Streamlit UI components, and format documentation.

---

## 🏗️ Architecture & Processing Pipeline

The solution operates as a completely **local, deterministic, zero-data-leakage pipeline**. In strict compliance with the rule prohibiting raw messages from being sent to external AI APIs, processing is handled using local keyword heuristics, structured regular expressions (Regex), and rule engines.

### 1. Message Classification (`Part 1`)
- **Methodology:** The system scans normalized text against specialized lexicons:
  - **Action Required:** Triggered by imperative verbs (`submit`, `review`, `complete`, `asap`).
  - **Meeting or Event:** Triggered by scheduling terminology (`meeting`, `zoom`, `calendar`, `invite`).
  - **Promotional:** Triggered by sales terms (`discount`, `offer`, `sale`, `limited time`).
  - **Sensitive / Personal Information:** Automatically assigned if PII or sensitive contact details are detected.
  - **General Information:** Default category for messages without actionable or sensitive signals.
- **Output:** Returns `message_id`, `category`, `confidence`, and a clear justification string.

### 2. Task and Event Extraction (`Part 2`)
- **Methodology:** Uses structured Regular Expressions to parse exact dates (`YYYY-MM-DD`, `DD/MM/YYYY`, `Month DD`) and times (`12h/24h AM/PM`).
- **Strict Anti-Hallucination Rule:** As instructed, the system **never guesses missing information**. Any missing field (person involved, specific deadline, exact time) is stored as `null`.

### 3. Sensitive Information Detection & Masking (`Part 3`)
- **Methodology:** Identifies high-risk data patterns (Credit Cards, One-Time Passwords/OTPs, Passwords, Emails, Phone Numbers) using pattern matching.
- **Data Protection:** Detected sensitive tokens are dynamically replaced with bracketed masks (e.g., `[MASKED_OTP]`, `[MASKED_BANK_DETAILS]`).
- **Risk Assessment:** Assigns risk levels (`high`, `critical`, `medium`) and recommended actions (`do_not_store`, `ask_for_confirmation`, `do_not_send_to_external_service`).

---

## 📋 Mandatory Message IDs
The 15 mandatory message IDs provided in the secondary dataset have been processed, cross-referenced, and stored separately in `mandatory_results_output.json`. These are visibly demonstrated in the live cloud dashboard and video recording.

---

## ⚠️ Assumptions & Limitations
1. **Rule-Based Ambiguity:** Keyword heuristics do not account for natural language sarcasm or subtle context (e.g., *"I am not holding a meeting"* might trigger a meeting keyword).
2. **Entity Extraction Limitations:** Without heavy local NLP models (like spaCy NER), extracting specific person names deterministically without high false positives is unreliable. Thus, `person` fields default to `null` to adhere to the strict "do not guess" constraint.
3. **Future Improvements:** Given additional time, the heuristic output could serve as weak supervision pseudo-labels to train a local `scikit-learn` TF-IDF + Logistic Regression model, or run a local quantized LLM (e.g., Llama-3-8B via Ollama).

---

## 📂 Repository Structure
```text
├── process_data.py               # Core processing pipeline script
├── app.py                         # Streamlit dashboard interface
├── requirements.txt               # App dependencies for cloud deployment
├── classification_output.json     # Generated Part 1 results
├── extraction_output.json         # Generated Part 2 results
├── sensitive_info_output.json     # Generated Part 3 results
├── mandatory_results_output.json  # Structured output for 15 mandatory IDs
├── .gitignore                     # Excludes dataset CSV files
└── README.md                      # Project documentation
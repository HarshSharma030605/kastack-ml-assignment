import streamlit as st
import pandas as pd
import json

st.set_page_config(page_title="AI Message Processor", layout="wide")

st.title("🛡️ KaStack Labs: Intelligent Message Processing System")
st.markdown("### Processed Offline via Local Rule-Based Engine")

# Load Data
@st.cache_data
def load_data():
    try:
        with open('classification_output.json', 'r') as f: class_data = json.load(f)
        with open('extraction_output.json', 'r') as f: ext_data = json.load(f)
        with open('sensitive_info_output.json', 'r') as f: sens_data = json.load(f)
        with open('mandatory_results_output.json', 'r') as f: mand_data = json.load(f)
        return class_data, ext_data, sens_data, mand_data
    except Exception as e:
        st.error(f"Error loading JSON files. Did you run process_data.py first? {e}")
        return [], [], [], []

class_data, ext_data, sens_data, mand_data = load_data()

tabs = st.tabs(["📊 Dashboard & Overview", "🎯 Mandatory IDs", "📅 Extracted Tasks/Events", "🔒 PII Detection"])

with tabs[0]:
    st.header("System Overview")
    st.write(f"Total Messages Processed: **900**")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Classifications Made", len(class_data))
    col2.metric("Tasks/Events Extracted", len(ext_data))
    col3.metric("Sensitive Messages Masked", len(sens_data))
    
    st.subheader("Classification Sample (All 6 Categories)")
    if class_data:
        df_class = pd.DataFrame(class_data)
        st.dataframe(df_class.head(15), use_container_width=True)

with tabs[1]:
    st.header("15 Mandatory Message IDs Results")
    st.info("These are the specific messages requested in the assignment.")
    if mand_data:
        st.json(mand_data)

with tabs[2]:
    st.header("Tasks and Events Extraction")
    if ext_data:
        df_ext = pd.DataFrame(ext_data)
        
        st.subheader("Extracted Tasks")
        st.dataframe(df_ext[df_ext['type'] == 'task'].head(5), use_container_width=True)
        
        st.subheader("Extracted Meetings/Events")
        st.dataframe(df_ext[df_ext['type'] == 'event'].head(5), use_container_width=True)
        
        st.subheader("Example with Missing/Unclear Information (Null Values)")
        st.write("Rule: Do not guess missing information.")
        # Show rows where deadline or time is None
        null_examples = df_ext[df_ext['deadline'].isnull() | df_ext['time'].isnull()]
        st.dataframe(null_examples.head(3), use_container_width=True)

with tabs[3]:
    st.header("Sensitive Information Detection & Masking")
    st.warning("All raw PII has been masked to ensure compliance.")
    if sens_data:
        df_sens = pd.DataFrame(sens_data)
        st.dataframe(df_sens[['message_id', 'sensitivity_type', 'risk', 'recommended_action', 'masked_text']], use_container_width=True)
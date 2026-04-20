import streamlit as st


# Session state keeps results available after Streamlit reruns the script.
#
# Note: Streamlit reruns the file every time the user interacts with the app
#       such as uploading a file, clicking a button, etc.
#       so we need to use st.session_state to store important data.
def init_state():
    defaults = {
        "processed": False,
        "new_master": None,
        "log_lines": [],
        "duplicates_within_credly": None,
        "duplicates_against_master": None,
        "rows_added": None,
        "date_processed": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# Save results so they remain visible after Streamlit reruns the script.
def save_results(result):
    st.session_state.processed = True
    st.session_state.new_master = result["new_master"]
    st.session_state.log_lines = result["log_lines"]
    st.session_state.duplicates_within_credly = result["duplicates_within_credly"]
    st.session_state.duplicates_against_master = result["duplicates_against_master"]
    st.session_state.rows_added = result["rows_added"]
    st.session_state.date_processed = result["date_processed"]

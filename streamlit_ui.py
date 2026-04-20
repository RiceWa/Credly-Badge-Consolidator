import streamlit as st
from smtp_notifier import send_email

from data_helpers import dataframe_to_excel_bytes

MILESTONE_LOG_HEADER = "Milestones and Micro-Credentials:"


def configure_page():
    st.set_page_config(page_title="Credly Badge Consolidator", layout="wide")
    st.title("Credly Badge Consolidator")


# Shows the two uploaders side by side.
def render_uploaders():
    col1, col2 = st.columns(2)

    with col1:
        master_file = st.file_uploader(
            "Browse Master Sheet",
            type=["xlsx", "xls"],
            key="master_file",
        )

    with col2:
        credly_file = st.file_uploader(
            "Browse Credly Sheet",
            type=["xlsx", "xls"],
            key="credly_file",
        )

    return master_file, credly_file


def render_results():
    # Show the updated master sheet immediately after a successful run.
    st.subheader("New Master Sheet")
    st.dataframe(st.session_state.new_master, width='stretch')

    st.subheader("New Rows Added")
    if st.session_state.rows_added is not None and not st.session_state.rows_added.empty:
        st.dataframe(st.session_state.rows_added, width='stretch')
    else:
        st.write("No new rows were added.")

    # Prepare the updated master sheet as an Excel download.
    excel_bytes = dataframe_to_excel_bytes(st.session_state.new_master, sheet_name="Master", date_processed=st.session_state.date_processed)

    st.subheader("Update Log")
    st.text_area(
        "Processing log",
        value="\n".join(st.session_state.log_lines),
        height=250,
        disabled=True,
    )

    # Keep the download and email buttons right next to each other at the bottom.
    download_col, email_col, _ = st.columns([1, 1, 6])
    with download_col:
        st.download_button(
            "Download New Master",
            data=excel_bytes,
            file_name="new_master.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    with email_col:
        render_email_button()


def render_email_button():
    if st.button("Send Email"):
        email_body = build_milestone_email_body(st.session_state.log_lines)
        if not email_body:
            st.warning("Process files first so there is a milestone log to email.")
            return

        email_sent, error_message = send_email(email_body)
        if email_sent:
            st.success("Email sent successfully.")
        else:
            st.error(f"Error sending email: {error_message}")


def build_milestone_email_body(log_lines):
    # Use only the milestone and micro-credential part of the processing log.
    if MILESTONE_LOG_HEADER not in log_lines:
        return ""

    header_index = log_lines.index(MILESTONE_LOG_HEADER)
    milestone_lines = log_lines[header_index:]
    return "\n".join(milestone_lines)

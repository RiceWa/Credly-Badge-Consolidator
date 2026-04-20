import streamlit as st
from smtp_notifier import send_email

from data_helpers import dataframe_to_excel_bytes


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
    excel_bytes = dataframe_to_excel_bytes(st.session_state.new_master, sheet_name="Master")

    st.subheader("Update Log")
    st.text_area(
        "Processing log",
        value="\n".join(st.session_state.log_lines),
        height=250,
        disabled=True,
    )

    # Create a download button for the updated master sheet.
    st.download_button(
        "Download New Master",
        data=excel_bytes,
        file_name="new_master.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

# button for sending test email
def render_emailer():
    st.subheader("Test Email Functionality")
    if st.button("Send Test Email"):
        send_email()
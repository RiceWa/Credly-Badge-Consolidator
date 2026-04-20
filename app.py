import pandas as pd
import streamlit as st

from merge_logic import process_dataframes, validate_required_columns
from session_state import init_state, save_results
from streamlit_ui import configure_page, render_results, render_uploaders, render_emailer


configure_page()
init_state()
render_emailer()  # Add the email test button to the UI

# app.py is now the central controller that runs the other modules in order.
master_file, credly_file = render_uploaders()

if master_file and credly_file:
    try:
        # Read both uploaded Excel workbooks into pandas DataFrames.
        master_df = pd.read_excel(master_file)
        credly_df = pd.read_excel(credly_file)
        process_clicked = st.button("Process")

        if process_clicked:
            validation_error = validate_required_columns(master_df, credly_df)
            if validation_error:
                st.error(validation_error)
            else:
                result, processing_error = process_dataframes(master_df, credly_df)
                if processing_error:
                    st.error(processing_error)
                else:
                    save_results(result)
                    st.success("Processing complete.")

    except Exception as e:
        st.error(f"Error reading Excel files: {e}")

if st.session_state.processed and st.session_state.new_master is not None:
    render_results()

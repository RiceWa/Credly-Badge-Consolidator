from io import BytesIO

import pandas as pd


# Replace missing values with blank text and trim the rest.
def normalize_text(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


# Combine badge name and email to create a key to check for duplicates.
def build_key(df):
    temp = df.copy()
    temp["Badge Name"] = temp["Badge Name"].apply(normalize_text).str.lower()
    temp["Issued to Email"] = temp["Issued to Email"].apply(normalize_text).str.lower()
    return temp[["Badge Name", "Issued to Email"]].astype(str).agg("||".join, axis=1)


# Convert the DataFrame into an in-memory Excel file for the download button.
def dataframe_to_excel_bytes(df, sheet_name="Sheet1", date_processed="NA"):
    output = BytesIO()

    # Added last updated timestamp to master list Last Updated tab
    dfUpdated = pd.DataFrame([[date_processed]])

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Report")
        dfUpdated.to_excel(writer, index=False, sheet_name="Last Updated", header=False)
    output.seek(0)
    return output.getvalue()

import pandas as pd

from data_helpers import build_key, normalize_text

REQUIRED_KEY_COLS = ["Badge Name", "Issued to Email"]


# Check that both uploaded sheets have the columns needed for duplicate checks.
def validate_required_columns(master_df, credly_df):
    missing_master_cols = [col for col in REQUIRED_KEY_COLS if col not in master_df.columns]
    missing_credly_cols = [col for col in REQUIRED_KEY_COLS if col not in credly_df.columns]

    if missing_master_cols:
        return f"Master sheet is missing required column(s): {', '.join(missing_master_cols)}"
    if missing_credly_cols:
        return f"Credly sheet is missing required column(s): {', '.join(missing_credly_cols)}"
    return None


# Clean the uploaded data and return only the rows that should be added to the master sheet.
def process_dataframes(master_df, credly_df):
    # Keep only columns that exist in both sheets so appended rows fit the master schema.
    master_cols = list(master_df.columns)
    matching_cols = [col for col in credly_df.columns if col in master_cols]

    if not matching_cols:
        return None, "No matching columns found between master and credly sheets."

    # Drop Credly-only columns that do not exist in the master sheet.
    truncated_credly_df = credly_df[matching_cols].copy()

    # Make the Credly sheet use the same columns and column order as the master sheet.
    cleaned_credly = truncated_credly_df.reindex(columns=master_cols)
    cleaned_master = master_df.copy()

    # Ignore rows that are missing either part of the duplicate key.
    blank_key_mask = (
        cleaned_credly["Badge Name"].apply(normalize_text).eq("")
        | cleaned_credly["Issued to Email"].apply(normalize_text).eq("")
    )
    cleaned_credly = cleaned_credly.loc[~blank_key_mask].copy()

    # Remove duplicate rows inside the Credly file, keeping the first copy.
    credly_keys = build_key(cleaned_credly)
    dup_within_mask = credly_keys.duplicated(keep=False)
    duplicates_within = cleaned_credly.loc[dup_within_mask].copy()
    deduped_credly = cleaned_credly.loc[~credly_keys.duplicated(keep="first")].copy()

    # Compare Credly rows against the master and keep only truly new records.
    master_keys = build_key(cleaned_master)
    deduped_credly_keys = build_key(deduped_credly)
    exists_in_master_mask = deduped_credly_keys.isin(set(master_keys))
    duplicates_against_master = deduped_credly.loc[exists_in_master_mask].copy()
    rows_to_append = deduped_credly.loc[~exists_in_master_mask].copy()

    # Append only the new and cleaned Credly rows to create the updated master sheet.
    new_master = pd.concat([cleaned_master, rows_to_append], ignore_index=True)

    result = {
        "new_master": new_master,
        "log_lines": build_log_lines(rows_to_append),
        "duplicates_within_credly": duplicates_within,
        "duplicates_against_master": duplicates_against_master,
        "rows_added": rows_to_append,
    }
    return result, None


# Build a human readable update log for the rows that were added.
def build_log_lines(rows_to_append):
    if rows_to_append.empty:
        return ["No new rows were added."]

    log_lines = []
    for _, row in rows_to_append.iterrows():
        first = normalize_text(row.get("Issued to First Name", ""))
        last = normalize_text(row.get("Issued to Last Name", ""))
        badge = normalize_text(row.get("Badge Name", ""))

        # Fallback to email if the first/last name columns are empty.
        if not first and not last:
            name = normalize_text(row.get("Issued to Email", "Unknown User"))
        else:
            name = f"{first} {last}".strip()

        log_lines.append(f"{name} has gotten the badge: {badge}.")

    return log_lines

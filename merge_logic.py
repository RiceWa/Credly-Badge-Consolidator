import pandas as pd

from data_helpers import build_key, normalize_text
from datetime import datetime

REQUIRED_KEY_COLS = ["Badge Name", "Issued to Email"]

# These are the 8 Emerging badges someone needs to finish the Emerging group.
EMERGING_BADGES = [
    "Emerging Designer",
    "Emerging Researcher",
    "Emerging Inclusive Practitioner",
    "Emerging Changemaker",
    "Emerging Digital Navigator",
    "Emerging Collaborator",
    "Emerging Reflector",
    "Emerging Mentor",
]

# These are the 8 Performing badges someone needs to finish the Performing group.
PERFORMING_BADGES = [
    "Performing Designer",
    "Performing Researcher",
    "Performing Inclusive Practitioner",
    "Performing Changemaker",
    "Performing Digital Navigator",
    "Performing Collaborator",
    "Performing Reflector",
    "Performing Mentor",
]

# These are the 8 Transforming badges someone needs to finish the Transforming group.
TRANSFORMING_BADGES = [
    "Transforming Designer",
    "Transforming Researcher",
    "Transforming Inclusive Practitioner",
    "Transforming Changemaker",
    "Transforming Digital Navigator",
    "Transforming Collaborator",
    "Transforming Reflector",
    "Transforming Mentor",
]

# This connects what we want to log to the badges we need to check for.
BADGE_GROUPS = {
    "Milestone: Emerging": EMERGING_BADGES,
    "Milestone: Performing": PERFORMING_BADGES,
    "Milestone: Transforming": TRANSFORMING_BADGES,
    "the Micro-Credential": EMERGING_BADGES + PERFORMING_BADGES + TRANSFORMING_BADGES,
}


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
    rows_to_append = sort_master_by_last_name(rows_to_append)

    # Append only the new and cleaned Credly rows to create the updated master sheet.
    new_master = pd.concat([cleaned_master, rows_to_append], ignore_index=True)
    new_master = sort_master_by_last_name(new_master)

    result = {
        "new_master": new_master,
        "log_lines": build_log_lines(rows_to_append, new_master),
        "duplicates_within_credly": duplicates_within,
        "duplicates_against_master": duplicates_against_master,
        "rows_added": rows_to_append,
        "date_processed": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "date_processed_str": datetime.now().strftime("%b-%d-%Y_%H-%M"),
    }
    return result, None


# Build a human readable update log for the rows that were added.
def build_log_lines(rows_to_append, new_master):
    if rows_to_append.empty:
        return ["Badges:", "No new rows were added."]

    # Add a header above the list of badges gained.
    log_lines = ["Badges:"]
    for _, row in rows_to_append.iterrows():
        name = get_recipient_name(row)
        badge = normalize_text(row.get("Badge Name", ""))

        log_lines.append(f"{name} has gotten the badge: {badge}.")

    # Put the completion check under the normal list of badges gained.
    log_lines.extend(build_badge_completion_log(rows_to_append, new_master))
    return log_lines


def get_recipient_name(row):
    # Use the person's name in the log when we have it.
    first = normalize_text(row.get("Issued to First Name", ""))
    last = normalize_text(row.get("Issued to Last Name", ""))

    # If we do not have their name, use their email instead.
    if not first and not last:
        return normalize_text(row.get("Issued to Email", "Unknown User"))
    return f"{first} {last}".strip()


def sort_master_by_last_name(new_master):
    # Sort the updated master sheet by last name so the excel sheet is in alphabetical order.
    if "Issued to Last Name" not in new_master.columns:
        return new_master

    sorted_master = new_master.copy()
    sorted_master["_sort_last_name"] = (
        sorted_master["Issued to Last Name"].apply(normalize_text).str.lower()
    )
    sorted_master = sorted_master.sort_values(
        by="_sort_last_name",
        kind="stable",
        ignore_index=True,
    )
    return sorted_master.drop(columns="_sort_last_name")


def normalize_badge_set(badges):
    # Make badge names easier to compare by ignoring capitals and extra spaces.
    return {normalize_text(badge).lower() for badge in badges}


def build_badge_completion_log(rows_to_append, new_master):
    # Only check people who got at least one new badge in this upload.
    session_recipients = get_session_recipients(rows_to_append)
    if not session_recipients:
        return []

    # Get all badges from the new master sheet, and names from the new rows added.
    badge_sets_by_email = build_badge_sets_by_email(new_master)
    names_by_email = build_names_by_email(rows_to_append)
    completion_lines = []

    for email in session_recipients:
        earned_badges = badge_sets_by_email.get(email, set())
        name = names_by_email.get(email, email)

        # If this person has every badge in a group, add that to the log.
        for completion_label, required_badges in BADGE_GROUPS.items():
            if normalize_badge_set(required_badges).issubset(earned_badges):
                completion_lines.append(f"{name} has completed {completion_label}.")

    # Give a no changes made message if nobody achieved a milestone or the micro-credential
    if not completion_lines:
        completion_lines.append("No Milestone were achieved for this session's recipients.")

    # Add a blank line so this part is separated from the badges gained list.
    return ["", "Milestones and Micro-Credentials:"] + completion_lines


def get_session_recipients(rows_to_append):
    # Make a list of people from this upload, without repeating the same email.
    recipients = []
    seen = set()

    for email in rows_to_append["Issued to Email"].apply(normalize_text).str.lower():
        if email and email not in seen:
            recipients.append(email)
            seen.add(email)

    return recipients


def build_badge_sets_by_email(new_master):
    # Make a list of every badge each person has in the updated master sheet.
    badge_sets_by_email = {}

    for _, row in new_master.iterrows():
        # Skip rows that are missing either the email or the badge name.
        email = normalize_text(row.get("Issued to Email", "")).lower()
        badge = normalize_text(row.get("Badge Name", "")).lower()
        if not email or not badge:
            continue

        if email not in badge_sets_by_email:
            badge_sets_by_email[email] = set()
        badge_sets_by_email[email].add(badge)

    return badge_sets_by_email


def build_names_by_email(rows_to_append):
    # Save names for the people who got new badges in this upload.
    names_by_email = {}

    for _, row in rows_to_append.iterrows():
        # If someone has multiple new badges, just use the name from their first row.
        email = normalize_text(row.get("Issued to Email", "")).lower()
        if email and email not in names_by_email:
            names_by_email[email] = get_recipient_name(row)

    return names_by_email

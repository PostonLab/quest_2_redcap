import pandas as pd
import os
import re
import argparse


# ----------------------------
# Utility functions
# ----------------------------
def load_csv_safely(file_path: str, skiprows: int = 0) -> pd.DataFrame:
    """Safely load a CSV file with optional skiprows."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    return pd.read_csv(file_path, skiprows=skiprows)


# ----------------------------
# Pivoting function
# ----------------------------
def pivot_patient_results(patient_df: pd.DataFrame) -> pd.DataFrame:
    cols_to_keep = [
        'Patient ID', 'lr_blood_draw_date', 'lr_blood_draw_time',
        'Result Name', 'Result Value', 'Reported Date', 'Test Order Name'
    ]
    missing_cols = [col for col in cols_to_keep if col not in patient_df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    sub = patient_df[cols_to_keep].copy()

    # --- Handle Absolute Lymphocytes ---
    sub.columns = sub.columns.str.strip()
    sub['Test Order Name'] = sub['Test Order Name'].fillna("").astype(str)

    mask = sub['Result Name'] == "Absolute Lymphocytes"
    sub.loc[mask & (sub['Test Order Name'] == "CBC (Includes Diff/Plt)"),
            "Result Name"] = "Absolute Lymphocytes_wbc"
    sub.loc[mask & (sub['Test Order Name'] == "Lymphocyte Subset Panel 3"),
            "Result Name"] = "Absolute Lymphocytes_lymph"

    # --- Handle duplicates ---
    duplicates = sub.duplicated(
        subset=['Patient ID', 'lr_blood_draw_date', 'lr_blood_draw_time', 'Result Name'],
        keep=False
    )
    if duplicates.any():
        duplicate_rows = sub[duplicates]
        sub['Reported Date'] = pd.to_datetime(sub['Reported Date'], errors='coerce')
        sub = sub.sort_values('Reported Date').drop_duplicates(
            subset=['Patient ID', 'lr_blood_draw_date', 'lr_blood_draw_time', 'Result Name'],
            keep='last'
        )
        for _, row in duplicate_rows.drop_duplicates(
            subset=['Patient ID', 'lr_blood_draw_date', 'lr_blood_draw_time', 'Result Name']
        ).iterrows():
            patient_id = row['Patient ID']
            result_name = row['Result Name']
            kept_date = sub[
                (sub['Patient ID'] == patient_id) &
                (sub['Result Name'] == result_name) &
                (sub['lr_blood_draw_date'] == row['lr_blood_draw_date']) &
                (sub['lr_blood_draw_time'] == row['lr_blood_draw_time'])
            ]['Reported Date'].iloc[0]
            print(
                f"Warning: Duplicate entries found for patient {patient_id}, "
                f"Result Name: {result_name}, Date: {row['lr_blood_draw_date']} {row['lr_blood_draw_time']}. "
                f"Keeping latest entry with Reported Date: {kept_date}"
            )

    # --- Pivot ---
    pivoted = sub.pivot_table(
        index=['Patient ID', 'lr_blood_draw_date', 'lr_blood_draw_time'],
        columns='Result Name',
        values='Result Value',
        aggfunc='first'
    ).reset_index()

    pivoted.columns.name = None

    # Ensure lymphocyte cols always exist
    required_cols = ["Absolute Lymphocytes_wbc", "Absolute Lymphocytes_lymph"]
    for col in required_cols:
        if col not in pivoted.columns:
            pivoted[col] = pd.NA

    return pivoted


# ----------------------------
# Rename and align columns
# ----------------------------
def rename_and_align_columns(pivoted_df: pd.DataFrame, mapping: dict, all_redcap_cols: list, df: pd.DataFrame) -> pd.DataFrame:
    unmapped_cols = [col for col in pivoted_df.columns if col in df['Result Name'].unique() and col not in mapping]
    if unmapped_cols:
        print(f"Warning: Unmapped columns found: {unmapped_cols}")

    renamed = pivoted_df.rename(columns=mapping)

    # Add missing columns
    for col in all_redcap_cols:
        if col not in renamed.columns:
            renamed[col] = pd.NA

    # Required REDCap structure
    renamed['id'] = renamed['Patient ID']
    renamed = renamed.drop(columns=['Patient ID'])

    renamed['redcap_event_name'] = "hivpd23_visit_1_arm_1"
    renamed['redcap_repeat_instrument'] = "labs"
    renamed['redcap_repeat_instance'] = 1
    renamed['lr_missing'] = 0

    id_cols = [
        'id', 'redcap_event_name', 'redcap_repeat_instrument',
        'redcap_repeat_instance', 'lr_missing',
        'lr_blood_draw_date', 'lr_blood_draw_time'
    ]
    final_cols = id_cols + [col for col in all_redcap_cols if col not in id_cols]

    return renamed[final_cols]

# ----------------------------
# Matching IDs with IDs in the ID file
# ----------------------------
def load_and_clean_ids(id_file: str) -> list:
    id_df = pd.read_csv(id_file)
    if 'ID' not in id_df.columns:
        raise ValueError("The ID file must contain a column named 'ID'")

    cleaned_ids = []
    for raw_id in id_df['ID']:
        if isinstance(raw_id, str):
            match = re.search(r'(\d+)', raw_id)
            if match:
                num_id = match.group(1).lstrip('0')  # remove leading zeros
                cleaned_ids.append(num_id)
    return cleaned_ids


# ----------------------------
# Main function
# ----------------------------
def main(input_file: str, lookup_file: str, output_file: str):
    # Load files
    df = load_csv_safely(input_file, skiprows=19)
    lookup = load_csv_safely(lookup_file)

    # Validate
    required_cols = ['Patient ID', 'Reported Date', 'Result Name', 'Result Value']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column in input CSV: {col}")

    required_lookup_cols = ['quest_col', 'redcap_col']
    for col in required_lookup_cols:
        if col not in lookup.columns:
            raise ValueError(f"Missing required column in lookup CSV: {col}")

    # Clean Patient ID
    df.columns = df.columns.str.strip()
    df['Patient ID'] = df['Patient ID'].fillna('')
    df['Patient ID'] = df['Patient ID'].str.replace('LAB_S0', '', regex=False).str.replace('LAB-S0', '', regex=False)

    # Mapping
    mapping = dict(zip(lookup['quest_col'], lookup['redcap_col']))
    all_redcap_cols = list(lookup['redcap_col'])

    # Split dates
    df['Reported Date'] = df['Reported Date'].fillna('')
    df[['lr_blood_draw_date', 'lr_blood_draw_time']] = df['Reported Date'].str.split(' ', n=1, expand=True)

    # Clean results
    df['Result Value'] = df['Result Value'].fillna('')
    comment_patterns = [r'^SEE NOTE.*', r'^NON-REACTIVE$', r'^REACTIVE$', r'^\s*$']
    for pattern in comment_patterns:
        df['Result Value'] = df['Result Value'].str.replace(pattern, '', regex=True)
    df['Result Value'] = df['Result Value'].str.split(' ', n=1, expand=True)[0]
    df['Result Value'] = df['Result Value'].str.split('%', n=1, expand=True)[0]
    df['Result Value'] = pd.to_numeric(df['Result Value'], errors='coerce')

    # Process patients
    all_patients = []
    for patient_id in df['Patient ID'].unique():
        if patient_id:
            patient_df = df[df['Patient ID'] == patient_id]
            if not patient_df.empty:
                pivoted = pivot_patient_results(patient_df)
                final = rename_and_align_columns(pivoted, mapping, all_redcap_cols, df)
                all_patients.append(final)

    if all_patients:
        final_df = pd.concat(all_patients, ignore_index=True)
        if args.id_file:
            allowed_ids = load_and_clean_ids(args.id_file)
            final_df = final_df[final_df['id'].astype(str).isin(allowed_ids)]
        final_df.to_csv(output_file, index=False)
        print(f"✅ Output saved successfully to {output_file}")
    else:
        print("⚠️ No valid patient data to process")


# ----------------------------
# Entry point
# ----------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process Quest labs into REDCap format.")

    parser.add_argument("--input_file", help="Path to input CSV (Quest export).")
    parser.add_argument("--id_file", help="Optional path to a CSV file containing IDs to filter results.")
    parser.add_argument("--output_file", help="Path to save processed CSV.")

    # Optional argument with default
    parser.add_argument(
        "--lookup_file",
        default="redcap_datadict.csv",
        help="Path to lookup CSV (quest_col → redcap_col). Default: redcap_datadict.csv"
    )

    args = parser.parse_args()

    main(args.input_file, args.lookup_file, args.output_file)

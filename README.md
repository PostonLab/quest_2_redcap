# Quest Labs → REDCap Converter

This script processes Quest Diagnostics CSV exports and reformats them into a structure suitable for REDCap import.  
It handles cleaning, pivoting test results, renaming columns using a lookup dictionary, and generating a final CSV with REDCap-compatible fields.

---

## Features
- Skips Quest CSV headers and reads real data.
- Cleans patient IDs (removes `LAB_S0`/`LAB-S0` prefixes).
- Splits `Reported Date` into `lr_blood_draw_date` and `lr_blood_draw_time`.
- Handles duplicate test results (keeps the latest).
- Special handling for **Absolute Lymphocytes**:
  - Renames results based on `Test Order Name`.
  - Ensures both `Absolute Lymphocytes_wbc` and `Absolute Lymphocytes_lymph` columns always exist.
- Uses a lookup CSV (`quest_col → redcap_col`) to rename columns and align with REDCap.
- Adds required REDCap fields:
  - `id`
  - `redcap_event_name`
  - `redcap_repeat_instrument`
  - `redcap_repeat_instance`
  - `lr_missing`
- Outputs a single CSV file with all patients merged.

---

## Installation

### Option 1: Quick setup with `setup.sh`
```bash
git clone <your-repo-url>
cd <your-repo-folder>
chmod +x setup.sh
./setup.sh
```

This will:
- Create a Python virtual environment in `./quest`
- Install all required dependencies from `requirements.txt`

To activate the environment later:
```bash
source quest/bin/activate
```

---

### Option 2: Manual installation
If you don’t want to use `setup.sh`:

```bash
python3 -m venv quest
source quest/bin/activate
pip install -r requirements.txt
```

---

## Usage

Run the script with:

```bash
python process_labs.py INPUT_FILE OUTPUT_FILE [--lookup_file LOOKUP_FILE]
```

- `INPUT_FILE`: Quest CSV export (raw data)
- `OUTPUT_FILE`: Path to save the REDCap-ready CSV
- `--lookup_file`: (optional) CSV file mapping Quest → REDCap columns  
  - Defaults to `redcap_datadict.csv`

Example:
```bash
python process_labs.py HIVPD23_2025-03-13_16-58-07.csv all_patients.csv --lookup_file new_redcap_datadict.csv
```

---

## File Structure

```
project/
│── process_labs.py        # Main script
│── setup.sh               # Setup script (creates venv + installs dependencies)
│── requirements.txt       # Python dependencies
│── README.md              # Documentation
│── redcap_datadict.csv    # Default lookup table (Quest → REDCap)
```

---

## Requirements
- Python 3.8+
- pandas


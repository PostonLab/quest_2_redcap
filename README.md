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
git clone https://github.com/PostonLab/quest_2_redcap
cd quest_2_redcap
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

## 🚀 Usage

```bash
python process_labs.py <input_file> [--lookup_file LOOKUP] [--output_file OUTPUT] [--id_file IDLIST]
```

### **Arguments**

| Argument | Description | Default |
|-----------|--------------|----------|
| `<input_file>` | Path to the main Quest lab CSV file | *Required* |
| `--lookup_file` | Path to the lookup CSV mapping Quest → REDCap columns | `redcap_datadict.csv` |
| `--output_file` | Path to save the processed output CSV | `all_patients.csv` |
| `--id_file` | Optional path to CSV containing IDs to filter by | *None* |

---

## 📄 Example ID File Format

```
ID
ID, 01447-BB-F
ID, 01507-MI-F
ID, 00325-SS-F
```

The script extracts numeric parts (e.g., `01447` → `1447`) and keeps only those patients in the final CSV.

---

## 🧩 Example Run

```bash
python process_labs.py HIVPD23_2025-03-13_16-58-07.csv --lookup_file redcap_datadict.csv --output_file filtered_labs.csv --id_file id_list.csv
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

## 🧑‍💻 Author

Developed by Dimuthu Hemachandra (2025)

For issues or questions, please contact at dimuthu@stanford.edu

---


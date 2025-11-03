# helper.py

import os
import sys
import platform
import re
import json
from datetime import datetime

# ===============================================================
# RUNTIME INFORMATION
# ===============================================================

class RuntimeData:
    """
    Collects and stores runtime environment information.
    Useful for logging, stamping, or debugging.
    """

    def __init__(self):
        self.data = self._collect()

    def _collect(self):
        """Gather runtime information at initialization or refresh."""
        return {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": datetime.now().strftime("%H:%M:%S"),
            "python_version": sys.version.split()[0],
            "os": platform.system(),
            "os_version": platform.version(),
            "platform_release": platform.release(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "cwd": os.getcwd(),
        }

    def get(self, key, default=None):
        """Dictionary-like getter."""
        return self.data.get(key, default)

    def refresh(self):
        """Refresh runtime data (updates timestamp, cwd, etc.)."""
        self.data = self._collect()


# Global instance for convenience
collect_runtime_data = RuntimeData()


# ===============================================================
# FILE / PATH HELPERS
# ===============================================================

TEXT_EXTS = (".txt", ".md", ".csv", ".log", ".res")
IMG_EXTS = (".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".gif")
PDF_EXTS = (".pdf",)
ALL_KNOWN_EXTS = TEXT_EXTS + IMG_EXTS + PDF_EXTS


def ensure_dir(path):
    """
    Create a directory if it doesn’t exist.
    Returns the same path (safe to chain).
    """
    if not os.path.isdir(path):
        os.makedirs(path, exist_ok=True)
    return path


def get_file_ext(path):
    """
    Return lowercase extension including the dot ('.pdf').
    If path has no extension, return empty string.
    """
    return os.path.splitext(path)[1].lower()


def safe_basename(path):
    """
    Safe version of os.path.basename.
    Returns an empty string if path is None.
    """
    if not path:
        return ""
    return os.path.basename(path)


def is_text_file(path):
    """Return True if the file has a recognized text extension."""
    return get_file_ext(path) in TEXT_EXTS


def is_image_file(path):
    """Return True if the file has an image extension."""
    return get_file_ext(path) in IMG_EXTS


def is_pdf_file(path):
    """Return True if the file has a .pdf extension."""
    return get_file_ext(path) in PDF_EXTS


def list_files_with_exts(folder_path, allowed_exts):
    """
    Return sorted list of full paths in folder matching given extensions.
    Non-recursive. Ignores subfolders.
    """
    out = []
    try:
        for name in os.listdir(folder_path):
            full = os.path.join(folder_path, name)
            if os.path.isfile(full) and get_file_ext(full) in allowed_exts:
                out.append(full)
    except Exception:
        return []
    out.sort()
    return out


def safe_join(base, *parts):
    """
    Join a base path with additional parts, ensuring
    the result doesn’t escape the base directory.
    """
    joined = os.path.abspath(os.path.join(base, *parts))
    base_abs = os.path.abspath(base)
    if not joined.startswith(base_abs):
        raise ValueError("Attempted to join outside base directory.")
    return joined


# ===============================================================
# STRING HELPERS
# ===============================================================

INVALID_CHARS = r'[^A-Za-z0-9_\-\. ]+'


def clean_string(value, invalid_pattern=None):
    """
    Clean and normalize a string for safe filenames, labels, etc.
    - Removes invalid characters (using provided or default regex)
    - Collapses whitespace
    """
    if value is None:
        return ""
    s = str(value).strip()
    s = re.sub(r"\s+", " ", s)

    pattern = invalid_pattern or INVALID_CHARS
    s = re.sub(pattern, "", s)

    return s.strip(" .")


def normalize_spaces(value):
    """Collapse multiple spaces/tabs/newlines into single spaces."""
    if not value:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def safe_truncate(value, length=40, ellipsis=True):
    """Truncate a string safely; append '...' if needed."""
    if value is None:
        return ""
    text = str(value)
    if len(text) <= length:
        return text
    if ellipsis and length > 3:
        return text[: length - 3] + "..."
    return text[:length]


def slugify(value):
    """
    Create a filesystem-friendly lowercase slug.
    Example: 'John Smith Jr.' -> 'john_smith_jr'
    """
    if not value:
        return ""
    s = str(value).lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s)
    return s.strip("_")


# --- job/intake specific string helpers ---

JOB_ID_INVALID_CHARS = r'[^A-Za-z0-9_\-]+'  # allow A-Z a-z 0-9 underscore and dash only


def clean_job_id(value):
    """
    Sanitize a job ID / job number.
    - Keeps letters, numbers, _ and -
    - Trims spaces
    """
    return clean_string(value, invalid_pattern=JOB_ID_INVALID_CHARS)


def suggest_next(prev_id):
    """
    Given the previous job id like '2025-0012' or '0012',
    try to increment the trailing number and preserve zero padding.

    If we can't parse a trailing number, just echo prev_id.
    """
    if not prev_id:
        return ""
    prev_id = str(prev_id).strip()
    m = re.search(r"(\d+)$", prev_id)
    if not m:
        return prev_id
    num = m.group(1)
    width = len(num)
    try:
        nxt = str(int(num) + 1).zfill(width)
        return prev_id[:-width] + nxt
    except Exception:
        return prev_id


# ===============================================================
# JSON HELPERS
# ===============================================================

def read_json(path, default=None):
    """
    Safely read and parse a JSON file.

    Args:
        path (str): File path.
        default: Value to return if file doesn't exist or fails to load.
    Returns:
        dict | list | default
    """
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def write_json(path, data, indent=2):
    """
    Write Python data to a JSON file (pretty-printed).

    Args:
        path (str): File path.
        data (dict or list): Data to write.
        indent (int): JSON indentation level.
    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        ensure_dir(os.path.dirname(path))
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        return True
    except Exception:
        return False


def append_json_list(path, item):
    """
    Append an item to a JSON list file.
    Creates the file if it doesn’t exist.

    Example:
        append_json_list("history.json", {"user": "Admin"})
    """
    data = read_json(path, default=[])
    if not isinstance(data, list):
        data = []
    data.append(item)
    write_json(path, data)


def safe_backup_json(path):
    """
    Create a timestamped backup of a JSON file in the same directory.
    Returns backup path or None if original missing.
    """
    if not os.path.exists(path):
        return None
    root, ext = os.path.splitext(path)
    backup_name = root + "_backup_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ext
    try:
        with open(path, "r", encoding="utf-8") as src, open(backup_name, "w", encoding="utf-8") as dst:
            dst.write(src.read())
        return backup_name
    except Exception:
        return None


# ===============================================================
#  R&M JOB RECORD HELPERS
# ===============================================================

def build_job_record(
    job_id,
    addr_line1,
    addr_line2="",
    city="",
    state="",
    zipcode="",
    client_name="",
    notes="",
    extra=None,
):
    """
    Build a normalized R&M job record dict that we will save to disk.

    Fields:
        job_id (clean_job_id)
        address (broken out)
        client_name
        notes
        created (runtime snapshot w/ timestamp)
        extra (anything else you want to stash)
    """
    job_id_clean = clean_job_id(job_id)
    now = RuntimeData()  # fresh timestamp snapshot

    rec = {
        "job_id": job_id_clean,
        "address": {
            "line1": normalize_spaces(addr_line1),
            "line2": normalize_spaces(addr_line2),
            "city": normalize_spaces(city),
            "state": normalize_spaces(state),
            "zip": normalize_spaces(zipcode),
        },
        "client_name": normalize_spaces(client_name),
        "notes": normalize_spaces(notes),
        "created": now.data,  # timestamp, machine, cwd, etc.
    }

    if extra:
        rec["extra"] = extra

    return rec


def save_job_record(job_record, base_jobs_dir):
    """
    Persist a job record on disk under base_jobs_dir.

    - Makes a subfolder using slugified job_id
    - Writes job.json in that folder
    - Appends summary to jobs_index.json at the root for quick lookup

    Returns:
        full path to the job.json file
    """
    job_id = job_record.get("job_id", "")
    folder_name = slugify(job_id) or "unnamed_job"
    job_folder = ensure_dir(os.path.join(base_jobs_dir, folder_name))

    job_json_path = os.path.join(job_folder, "job.json")
    write_json(job_json_path, job_record, indent=2)

    # lightweight summary for dashboard/index
    addr_bits = [
        job_record.get("address", {}).get("line1", ""),
        job_record.get("address", {}).get("city", ""),
        job_record.get("address", {}).get("state", ""),
    ]
    addr_summary = normalize_spaces(", ".join([a for a in addr_bits if a]))

    summary_item = {
        "job_id": job_id,
        "address": addr_summary,
        "created": job_record.get("created", {}).get("timestamp", ""),
        "folder": folder_name,
    }

    index_path = os.path.join(base_jobs_dir, "jobs_index.json")
    append_json_list(index_path, summary_item)

    return job_json_path



# ===============================================================
# CONSTANTS / LOOKUPS
# ===============================================================

import re  # make sure you have this at top of helper.py

# -------------------------
# CONSTANTS / LOOKUPS
# -------------------------

US_STATES = [
    "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA",
    "HI","ID","IL","IN","IA","KS","KY","LA","ME","MD",
    "MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ",
    "NM","NY","NC","ND","OH","OK","OR","PA","RI","SC",
    "SD","TN","TX","UT","VT","VA","WA","WV","WI","WY",
    "DC","PR"
]


def build_maps_query(address_line1, city, state, zipcode):
    """
    Return a Google Maps query URL from address parts.
    Example:
    https://maps.google.com/?q=123+Main+St+Springfield+MA+01101
    """
    # normalize_spaces should already be defined earlier in helper.py
    parts = [
        normalize_spaces(address_line1),
        normalize_spaces(city),
        normalize_spaces(state),
        normalize_spaces(zipcode),
    ]
    joined = " ".join([p for p in parts if p])
    q = re.sub(r"\s+", "+", joined.strip())
    if q == "":
        return "https://maps.google.com/"
    return "https://maps.google.com/?q=" + q


def push_recent_value(lst, value, max_len=15):
    """
    Maintain a most-recently-used list:
    - Put new value at front
    - Dedupe
    - Trim to max_len
    """
    if value is None:
        return lst or []
    v = normalize_spaces(value)
    if v == "":
        return lst or []
    out = [v]
    for item in lst or []:
        if normalize_spaces(item) != v:
            out.append(item)
    return out[:max_len]

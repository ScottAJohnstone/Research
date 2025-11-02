#!/usr/bin/env python3
import json
import os
from datetime import datetime

def build_default_payload():
    # --- Viewer Section ---
    data_file_viewer = {
        "files": [],
        "current_index": None,
        "current_path": None,
        "page_index": 0,
        "current_dir": None,
    }

    # --- Research Section ---
    data_research = {
        "test": None,
    }

    # --- Job Data (Grouped and future-proof) ---
    job_data = {
        "info": {
            "job_number": "",
            "pid": "",
            "address": "",
            "client": ""
        },
        "metadata": {
            "date_created": datetime.now().strftime("%Y-%m-%d"),
            "last_modified": "",
            "created_by": "Scott"
        }
    }

    # --- Full session structure ---
    full_payload = {
        "data_file_viewer": data_file_viewer,
        "data_research": data_research,
        "job_data": job_data,
        "_meta": {
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "version": 1,
        }
    }

    return full_payload


def save_new_session_file(dest_path: str):
    """Creates a new blank .research session file at dest_path."""
    payload = build_default_payload()
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)

    with open(dest_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print(f"[OK] Session file created at: {dest_path}")


if __name__ == "__main__":
    # Customize where your blank job file goes
    dest_path = "/Users/sjohnstone/Python/RESEARCHV2/config/default_session.rdata"
    save_new_session_file(dest_path)

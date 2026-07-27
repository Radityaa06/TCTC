from pathlib import Path
from typing import List, Dict, Any
import pandas as pd


def generate_excel_template(fields: List[Dict[str, Any]], output_path: Path) -> Path:
    """
    Generates a sample Excel template (.xlsx) with columns matching
    the exact required form field labels.
    """
    sample_data = {}
    for f in fields:
        label = f.get("label", f.get("name", "Field"))
        ftype = f.get("type", "text")
        if "email" in label.lower() or ftype == "email":
            sample_data[label] = ["student001@example.com"]
        elif "phone" in label.lower():
            sample_data[label] = ["9876543210"]
        elif "pass" in label.lower():
            sample_data[label] = ["Password123!"]
        elif "pin" in label.lower():
            sample_data[label] = ["500001"]
        elif "class" in label.lower():
            sample_data[label] = ["Grade 5"]
        else:
            sample_data[label] = [f"Sample {label}"]

    df = pd.DataFrame(sample_data)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(output_path, index=False)
    return output_path

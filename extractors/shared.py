import pandas as pd
from pathlib import Path
from datetime import date, datetime

def save_raw(df: pd.DataFrame, source: str, file_name: str, base_dir: str = "raw") -> Path:
    out_dir = Path("data")/ Path(base_dir) / source / file_name / date.today().isoformat()
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{file_name}.parquet"

    df = df.copy()
    df["source_id"] = source
    df["retrieved_at"] = datetime.now()

    df.to_parquet(out_path, index=False)
    return out_path
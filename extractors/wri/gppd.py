import io
import zipfile
import requests
import pandas as pd

from extractors.shared import save_raw

url = "https://datasets.wri.org/private-admin/dataset/53623dfd-3df6-4f15-a091-67457cdb571f/resource/66bcdacc-3d0e-46ad-9271-a5a76b1853d2/download/globalpowerplantdatabasev130.zip"


if __name__ == "__main__":
    resp = requests.get(url)
    resp.raise_for_status()

    # open zip from bytes in memory
    zf = zipfile.ZipFile(io.BytesIO(resp.content))

    print("Files in zip:", zf.namelist())

    # pick the first CSV (adjust if needed)
    csv_name = next(n for n in zf.namelist() if n.lower().endswith(".csv"))

    with zf.open(csv_name) as f:
        df = pd.read_csv(f)

    out_path = save_raw(df, source="wri", file_name="gppd")
    print(f"saved to {out_path}")

    
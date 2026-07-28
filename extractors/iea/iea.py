import pymupdf
import requests
import pandas as pd

from extractors.shared import save_raw



TABLES = {
    "energy_technologies": "https://iea.blob.core.windows.net/assets/5cdf3c1f-43ba-4a11-b14d-990639c51321/IEAEnergyTechnologyClassification_2025.pdf",
}

if __name__ == "__main__":
    for file_name, table_file in TABLES.items():
        r = requests.get(table_file)
        data = r.content
        doc = pymupdf.Document(stream=data)
        filtered_toc_dict=list(filter(lambda listing: listing[1].split('–')[0][0] in ['B', 'C', 'D', 'E', 'F'], [listing for listing in doc.get_toc()]))
        energy_technologies = [
            listing[1].split(' – ') for listing in filtered_toc_dict
        ]
        df = pd.DataFrame([['Category Code', 'Category Name']]  + energy_technologies)
        out_path = save_raw(df, source="irenastat", file_name=file_name)
        print(f"saved to {out_path}")


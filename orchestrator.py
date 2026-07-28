from prefect import flow, task
import subprocess, duckdb
from pathlib import Path

from prefect_dbt import PrefectDbtRunner, PrefectDbtSettings

@task
def extract():
    subprocess.run(["python", '-m', "extractors.irenastat.irenastat"], check=True)
    subprocess.run(["python", '-m', "extractors.wri.gppd"], check=True)

@task
def resolve_paths():
    gppd = sorted(Path("data/raw/wri/gppd").iterdir())[-1]
    irena = sorted(Path("data/raw/irenastat/country_eleccap").iterdir())[-1]
    return f"{gppd}/*.parquet", f"{irena}/*.parquet"

@task
def dbt_build(gppd_path, irena_path):
    PrefectDbtRunner(settings=PrefectDbtSettings(project_dir="./edim")).invoke([
        "build",
        "--select", "+mart_calliope_capacity",
        "--vars", f'{{gppd_path: "{gppd_path}", irena_path: "{irena_path}"}}'
    ])

@task
def export_csv():
    conn = duckdb.connect("data/edim.duckdb")
    conn.execute(
        "COPY (SELECT * FROM mart_calliope_capacity) "
        "TO 'output/calliope_capacity.csv' (HEADER, DELIMITER ',')"
    )
    conn.close()

@flow
def edim_pipeline():
    extract()
    gppd_path, irena_path = resolve_paths()
    dbt_build(gppd_path, irena_path)
    export_csv()

if __name__ == "__main__":
    edim_pipeline()
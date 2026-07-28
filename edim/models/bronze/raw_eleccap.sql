with eleccap as (
    select
        source_id,
        retrieved_at,
        "Country/area" as country,
        "Technology" as technology,
        "value" as capacity_mw,
        "Year" as year
    from read_parquet('{{ var("irena_path") }}')
)
select * from eleccap
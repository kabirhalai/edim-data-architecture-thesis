with gppd as (
    select
        source_id,
        retrieved_at, 
        country,
        primary_fuel,
        capacity_mw,
        year_of_capacity_data
    from read_parquet('{{ var("gppd_path") }}')
)

select * from gppd
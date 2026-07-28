-- models/silver/canonical_capacity.sql

with gppd as (
    select
        country as country_iso3,
        primary_fuel as technology,
        year_of_capacity_data as year,
        sum(capacity_mw) as capacity_mw,
        'gppd' as source_id
    from {{ ref('raw_gppd') }}
    where year_of_capacity_data is not null
    group by country, primary_fuel, year_of_capacity_data
),

irena as (
    select
        iso.ISO3 as country_iso3,
    case technology
        when 'Coal' then 'Coal'
        when 'Natural gas' then 'Gas'
        when 'Gas biofuels' then 'Biomass'
        when 'Oil' then 'Oil'
        when 'Nuclear energy' then 'Nuclear'
        when 'Geothermal energy' then 'Geothermal'
        when 'Marine energy' then 'Wave and Tidal'
        when 'Mixed hydropower' then 'Hydro'
        when 'Renewable hydropower' then 'Hydro'
        when 'Pumped hydro' then 'Storage'
        when 'Offshore wind energy' then 'Wind'
        when 'Onshore wind energy' then 'Wind'
        when 'Solar photovoltaic' then 'Solar'
        when 'Solar thermal energy' then 'Solar'
        when 'Liquid biofuels' then 'Biomass'
        when 'Solid biofuels' then 'Biomass'
        when 'Renewable waste' then 'Waste'
        when 'Non-renewable waste' then 'Waste'
        when 'Other non-renewable energy' then 'Other'
        when 'Other non-renewable energy n.e.s.' then 'Other'
    end as technology,
        year,
        sum(capacity_mw) as capacity_mw,
        'irena' as source_id
    from {{ ref('raw_eleccap') }} e
    left join {{ ref('countryiso3') }} iso
        on e.country = iso.Country
    where technology not in (
        'Total renewable energy',
        'Total non-renewable energy',
        'Fossil fuels',
        'Solar energy',
        'Wind energy',
        'Bioenergy'
    ) 
    and iso.iso3 is not null
    group by 1, 2, 3
)

select country_iso3, year, technology, capacity_mw, source_id
from gppd

union all

select country_iso3, year, technology, capacity_mw, source_id
from irena
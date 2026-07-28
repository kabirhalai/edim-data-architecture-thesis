with ranked as (
    select *,
        row_number() over (
            partition by country_iso3, technology
            order by
                case source_id when 'irena' then 1 when 'gppd' then 2 end,
                year desc
        ) as rn
    from {{ ref('canonical_capacity') }}
)
select country_iso3 as nodes, technology as techs, capacity_mw as value
from ranked where rn = 1
-- Clean base table for every analysis.
--
-- Rules:
--   * Category A only: standard market sales. Category B (repossessions, buy-to-let
--     companies, non-private buyers) would distort prices, so it is studied separately.
--   * Record status D means "deleted" in update files; those rows are dropped.
--   * Property type O ("Other") is mostly commercial or mixed use, so it is excluded.
--   * London means the county GREATER LONDON; its districts are the 33 boroughs.

-- DuckDB has no initcap(), so a small macro turns 'KENSINGTON AND CHELSEA' into
-- 'Kensington and Chelsea'. Short joining words stay lower case.
create or replace macro title_case(s) as list_aggr(
    list_transform(
        string_split(lower(trim(s)), ' '),
        w -> case when w in ('and', 'of', 'upon', 'on', 'the') then w
                  else upper(left(w, 1)) || substr(w, 2) end
    ),
    'string_agg', ' '
);

create or replace table sales as
select
    transaction_id,
    price,
    cast(transfer_date as date)                               as sale_date,
    year(transfer_date)                                       as sale_year,
    cast(date_trunc('month', transfer_date) as date)          as sale_month,
    upper(trim(postcode))                                     as postcode,
    split_part(upper(trim(postcode)), ' ', 1)                 as outcode,
    case property_type
        when 'D' then 'Detached'
        when 'S' then 'Semi-detached'
        when 'T' then 'Terraced'
        when 'F' then 'Flat'
    end                                                       as property_type,
    old_new = 'Y'                                             as is_new_build,
    case duration when 'F' then 'Freehold' when 'L' then 'Leasehold' end as tenure,
    upper(trim(paon))                                         as paon,
    upper(trim(coalesce(saon, '')))                           as saon,
    upper(trim(coalesce(street, '')))                         as street,
    title_case(town_city)                                     as town_city,
    title_case(district)                                      as district,
    upper(trim(county))                                       as county,
    upper(trim(county)) = 'GREATER LONDON'                    as is_london
from ppd
where ppd_category = 'A'
  and coalesce(record_status, 'A') <> 'D'
  and property_type in ('D', 'S', 'T', 'F')
  and price > 0;

-- Two "areas" used throughout: London and the rest of England and Wales.
create or replace view sales_by_area as
select *, 'England and Wales' as area from sales
union all
select *, case when is_london then 'London' else 'Outside London' end as area from sales;

-- Years that are complete (all 12 months present), so year-on-year numbers are fair.
create or replace table complete_years as
select sale_year
from sales
group by 1
having count(distinct month(sale_date)) = 12;

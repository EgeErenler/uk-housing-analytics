-- output: property_types
-- Median price and market share by property type.
create or replace table out_property_types as
select
    area,
    sale_year,
    property_type,
    count(*)                                                        as transactions,
    median(price)                                                   as median_price,
    round(count(*) / sum(count(*)) over (partition by area, sale_year), 4) as share_of_sales
from sales_by_area
group by 1, 2, 3
order by 1, 2, 3;

-- output: new_build_premium
-- How much more do buyers pay for a new build than for an existing home of the same type?
-- Comparing within each property type avoids a mix effect (new builds are more often flats).
create or replace table out_new_build_premium as
with by_type as (
    select
        area,
        sale_year,
        property_type,
        median(price) filter (where is_new_build)       as median_new,
        median(price) filter (where not is_new_build)   as median_existing,
        count(*) filter (where is_new_build)            as new_builds
    from sales_by_area
    group by 1, 2, 3
)
select
    area,
    sale_year,
    property_type,
    median_new,
    median_existing,
    new_builds,
    round(median_new / nullif(median_existing, 0) - 1, 4)  as premium
from by_type
where new_builds >= 30   -- too few sales gives a noisy premium
order by 1, 2, 3;

-- output: tenure
-- Leasehold share. In England and Wales almost all flats are leasehold, so this mostly
-- tracks the flat share, but new-build leasehold houses were a known issue before 2022.
create or replace table out_tenure as
select
    area,
    sale_year,
    round(avg((tenure = 'Leasehold')::int), 4)                                  as leasehold_share,
    round(avg((tenure = 'Leasehold')::int) filter (where property_type <> 'Flat'), 4)
                                                                                as leasehold_house_share
from sales_by_area
group by 1, 2
order by 1, 2;

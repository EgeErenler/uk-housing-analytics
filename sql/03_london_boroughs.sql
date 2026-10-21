-- output: london_boroughs
-- A league table of the 33 London boroughs for the latest complete year,
-- with five-year change and rankings from window functions.
create or replace table out_london_boroughs as
with latest as (
    select max(sale_year) as y from complete_years
),

borough_year as (
    select
        district                                    as borough,
        sale_year,
        count(*)                                    as transactions,
        median(price)                               as median_price,
        avg((property_type = 'Flat')::int)          as flat_share
    from sales
    where is_london
    group by 1, 2
),

pivoted as (
    select
        b.borough,
        max(b.median_price)  filter (where b.sale_year = l.y)       as median_price,
        max(b.transactions)  filter (where b.sale_year = l.y)       as transactions,
        max(b.flat_share)    filter (where b.sale_year = l.y)       as flat_share,
        max(b.median_price)  filter (where b.sale_year = l.y - 5)   as median_price_5y_ago,
        max(b.transactions)  filter (where b.sale_year = l.y - 5)   as transactions_5y_ago,
        any_value(l.y)                                              as latest_year
    from borough_year b
    cross join latest l
    group by 1
)

select
    borough,
    latest_year,
    median_price,
    transactions,
    round(flat_share, 4)                                            as flat_share,
    median_price_5y_ago,
    round(median_price / nullif(median_price_5y_ago, 0) - 1, 4)     as change_5y,
    round(transactions / nullif(transactions_5y_ago, 0) - 1, 4)     as transactions_change_5y,
    dense_rank() over (order by median_price desc)                  as price_rank,
    dense_rank() over (order by median_price / nullif(median_price_5y_ago, 0) desc)
                                                                    as growth_rank
from pivoted
where median_price is not null
order by price_rank;

-- output: borough_yearly
-- The full history per borough, for the dashboard's borough explorer.
create or replace table out_borough_yearly as
select
    district                                        as borough,
    sale_year,
    count(*)                                        as transactions,
    median(price)                                   as median_price
from sales
where is_london
group by 1, 2
order by 1, 2;

-- output: top_outcodes
-- The most and least expensive London postcode districts (e.g. W8, E13), at least 100 sales.
create or replace table out_top_outcodes as
with latest as (select max(sale_year) as y from complete_years),
outcodes as (
    select
        outcode,
        any_value(district)                         as borough,
        count(*)                                    as transactions,
        median(price)                               as median_price
    from sales, latest
    where is_london and sale_year = latest.y and outcode <> ''
    group by 1
    having count(*) >= 100
)
select
    *,
    row_number() over (order by median_price desc)  as rank_most_expensive,
    row_number() over (order by median_price asc)   as rank_least_expensive
from outcodes
qualify rank_most_expensive <= 10 or rank_least_expensive <= 10
order by median_price desc;

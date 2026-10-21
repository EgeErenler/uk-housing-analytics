-- output: yearly_summary
-- Price level and activity per year, with year-on-year change computed by window functions.
create or replace table out_yearly_summary as
with yearly as (
    select
        area,
        sale_year,
        count(*)                                        as transactions,
        median(price)                                   as median_price,
        round(avg(price))                               as mean_price,
        quantile_cont(price, 0.25)                      as p25_price,
        quantile_cont(price, 0.75)                      as p75_price,
        sale_year in (select sale_year from complete_years) as is_complete_year
    from sales_by_area
    group by 1, 2
)
select
    *,
    round(median_price / lag(median_price) over w - 1, 4)   as median_price_yoy,
    round(transactions / lag(transactions) over w - 1, 4)   as transactions_yoy
from yearly
window w as (partition by area order by sale_year)
order by area, sale_year;

-- output: monthly_activity
-- Monthly volumes and prices. Policy events (the stamp duty holiday, the September 2022
-- mini-budget) show up clearly at this grain.
create or replace table out_monthly_activity as
select
    area,
    sale_month,
    count(*)                                            as transactions,
    median(price)                                       as median_price,
    -- 12-month rolling median of monthly medians smooths out seasonality.
    round(median(median(price)) over (
        partition by area order by sale_month rows between 11 preceding and current row
    ))                                                  as median_price_12m
from sales_by_area
group by 1, 2
order by area, sale_month;

-- output: price_bands
-- Share of sales in each price band. £250k is the stamp duty nil-rate threshold that applied
-- for most of the period; £1m marks the top of the market.
create or replace table out_price_bands as
select
    area,
    sale_year,
    round(avg((price < 250000)::int), 4)                        as share_under_250k,
    round(avg((price >= 250000 and price < 500000)::int), 4)    as share_250k_500k,
    round(avg((price >= 500000 and price < 1000000)::int), 4)   as share_500k_1m,
    round(avg((price >= 1000000)::int), 4)                      as share_over_1m
from sales_by_area
group by 1, 2
order by 1, 2;

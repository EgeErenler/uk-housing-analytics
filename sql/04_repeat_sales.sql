-- Repeat-sales analysis.
--
-- Median prices can move just because a different mix of homes sold. A repeat-sales view
-- compares the *same* home with itself: we find every property that sold twice and compute
-- the annualised return between the two sales.

create or replace table repeat_sale_pairs as
with keyed as (
    select
        -- A home is identified by its postcode and full address.
        concat_ws('|', postcode, paon, saon, street)  as property_key,
        *
    from sales
    where postcode <> '' and paon is not null
),

ordered as (
    select
        *,
        lag(price)          over w as prev_price,
        lag(sale_date)      over w as prev_sale_date,
        lag(property_type)  over w as prev_property_type
    from keyed
    window w as (partition by property_key order by sale_date, transaction_id)
)

select
    property_key,
    district,
    is_london,
    property_type,
    prev_sale_date,
    sale_date,
    prev_price,
    price,
    date_diff('day', prev_sale_date, sale_date) / 365.25           as years_held,
    power(price / prev_price, 1 / (date_diff('day', prev_sale_date, sale_date) / 365.25)) - 1
                                                                    as annual_return
from ordered
where prev_price is not null
  and property_type = prev_property_type                 -- same kind of home both times
  and date_diff('day', prev_sale_date, sale_date) >= 365 -- under a year is usually a flip
  and price between prev_price * 0.3 and prev_price * 5;  -- drop likely data errors

-- output: repeat_sales_summary
create or replace table out_repeat_sales_summary as
select
    case when is_london then 'London' else 'Outside London' end     as area,
    property_type,
    count(*)                                                        as pairs,
    round(median(years_held), 1)                                    as median_years_held,
    round(median(annual_return), 4)                                 as median_annual_return,
    round(avg((price < prev_price)::int), 4)                        as share_sold_at_loss
from repeat_sale_pairs
group by grouping sets ((1, 2), (1))
order by 1, 2 nulls first;

-- output: repeat_sales_boroughs
create or replace table out_repeat_sales_boroughs as
select
    district                                                        as borough,
    count(*)                                                        as pairs,
    round(median(annual_return), 4)                                 as median_annual_return,
    round(avg((price < prev_price)::int), 4)                        as share_sold_at_loss,
    rank() over (order by median(annual_return) desc)               as return_rank
from repeat_sale_pairs
where is_london
group by 1
having count(*) >= 200
order by median_annual_return desc;

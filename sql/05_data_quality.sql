-- output: data_quality
-- What did the cleaning rules remove? Shown in the report so the numbers can be trusted.
create or replace table out_data_quality as
select 'All rows in the source files'                       as check_name, count(*) as row_count
from ppd
union all
select 'Category B (additional price paid) rows', count(*)  from ppd where ppd_category = 'B'
union all
select 'Property type O (other) rows', count(*)             from ppd where property_type = 'O'
union all
select 'Rows flagged as deleted', count(*)                  from ppd where record_status = 'D'
union all
select 'Rows without a postcode', count(*)                  from ppd where coalesce(trim(postcode), '') = ''
union all
select 'Rows used in the analysis', count(*)                from sales
union all
select 'Repeat-sale pairs', count(*)                        from repeat_sale_pairs;

-- output: coverage
create or replace table out_coverage as
select
    min(sale_date)                                          as first_sale,
    max(sale_date)                                          as last_sale,
    count(*)                                                as sales,
    count(distinct district) filter (where is_london)       as london_boroughs,
    (select max(sale_year) from complete_years)             as latest_complete_year
from sales;

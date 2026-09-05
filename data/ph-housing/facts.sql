-- Facts published on projects/housing-analysis.html
--
-- Two universes, kept apart on purpose. Anything named listing.* describes
-- 1,500 asking prices scraped from one property portal and nothing else.
-- Anything named ph.* is a national figure with a year attached.

-- ---- the scrape -------------------------------------------------------------

-- fact: listing.n
select count(*) from ph_housing_listings;

-- fact: listing.priced
select count(*) from ph_housing_listings where price_php is not null;

-- fact: listing.unpriced
select count(*) from ph_housing_listings where price_php is null;

-- fact: listing.repeats
select count(*) from ph_housing_listings where occurrence = 'repeat';

-- fact: listing.cities
select count(*) from ph_housing_by_city;

-- fact: listing.mean
-- The figure the old page led with, as "Average Price". It is arithmetically
-- right and descriptively useless; the page now shows it beside the median.
select round(avg(price_php)) from ph_housing_listings where price_php is not null;

-- fact: listing.median
select median(price_php) from ph_housing_listings where price_php is not null;

-- fact: listing.skew
select round(avg(price_php) / median(price_php), 2)
from ph_housing_listings where price_php is not null;

-- fact: listing.max
select max(price_php) from ph_housing_listings;

-- fact: listing.min
select min(price_php) from ph_housing_listings;

-- fact: listing.p90
select round(quantile_cont(price_php, 0.9))
from ph_housing_listings where price_php is not null;

-- fact: listing.p99
select round(quantile_cont(price_php, 0.99))
from ph_housing_listings where price_php is not null;

-- fact: listing.over100m
select listings from ph_housing_price_bands where band = '₱100M and up';

-- fact: listing.over100m.pct
select pct_of_priced from ph_housing_price_bands where band = '₱100M and up';

-- fact: listing.under6m.pct
select round(sum(pct_of_priced), 2) from ph_housing_price_bands
where upper_php is not null and upper_php <= 6000000;

-- fact: listing.psm
-- Median asking price per square metre of floor area. The only figure in the
-- scrape that survives comparison across a mansion and a townhouse.
select round(median(price_php / floor_area_sqm)) from ph_housing_listings
where price_php is not null and floor_area_sqm > 0;

-- fact: listing.psm.n
select count(*) from ph_housing_listings
where price_php is not null and floor_area_sqm > 0;

-- fact: listing.top.city
select city_token from ph_housing_by_city order by listings desc, city_token limit 1;

-- fact: listing.top.city.n
select listings from ph_housing_by_city order by listings desc, city_token limit 1;

-- fact: listing.top.city.median
select median_price_php from ph_housing_by_city
order by listings desc, city_token limit 1;

-- fact: listing.top3.pct
-- How much of a "national" dataset sits in three city tokens.
select round(100.0 * (select sum(listings) from (
           select listings from ph_housing_by_city
           order by listings desc, city_token limit 3))
     / (select count(*) from ph_housing_listings), 2);

-- fact: listing.bed3.median
select median_price_php from ph_housing_by_bedroom where bedrooms = 3;

-- fact: listing.bed3.n
select listings from ph_housing_by_bedroom where bedrooms = 3;

-- fact: listing.bed.monotone.upto
-- The bedroom count above which medians stop rising, because the sample runs
-- out rather than because bigger houses get cheaper.
select max(bedrooms) from (
  select bedrooms, median_price_php,
         lag(median_price_php) over (order by bedrooms) prev
  from ph_housing_by_bedroom)
where bedrooms = 1 or (prev is not null and median_price_php > prev
  and bedrooms <= (select min(bedrooms) from (
        select bedrooms, median_price_php,
               lag(median_price_php) over (order by bedrooms) p2
        from ph_housing_by_bedroom)
      where p2 is not null and median_price_php < p2));

-- fact: listing.south
select round(min(latitude), 2) from ph_housing_listings where latitude is not null;

-- fact: listing.north
select round(max(latitude), 2) from ph_housing_listings where latitude is not null;

-- ---- how households actually live -------------------------------------------

-- fact: ph.water.basic
select basic_water_pct from ph_housing_conditions
where basic_water_pct is not null order by year desc limit 1;

-- fact: ph.water.safe
select safe_water_pct from ph_housing_conditions
where safe_water_pct is not null order by year desc limit 1;

-- fact: ph.water.gap
-- Households with an improved source they can reach in half an hour, but not
-- one on the premises, available when needed and free of contamination.
select round(basic_water_pct - safe_water_pct, 2) from ph_housing_conditions
where safe_water_pct is not null order by year desc limit 1;

-- fact: ph.water.year
select year from ph_housing_conditions
where safe_water_pct is not null order by year desc limit 1;

-- fact: ph.sani.basic
select basic_sanitation_pct from ph_housing_conditions
where basic_sanitation_pct is not null order by year desc limit 1;

-- fact: ph.sani.safe
select safe_sanitation_pct from ph_housing_conditions
where safe_sanitation_pct is not null order by year desc limit 1;

-- fact: ph.sani.gap
select round(basic_sanitation_pct - safe_sanitation_pct, 2)
from ph_housing_conditions
where safe_sanitation_pct is not null order by year desc limit 1;

-- fact: ph.elec
select electricity_pct from ph_housing_conditions
where electricity_pct is not null order by year desc limit 1;

-- fact: ph.elec.year
select year from ph_housing_conditions
where electricity_pct is not null order by year desc limit 1;

-- fact: ph.elec.2000
select electricity_pct from ph_housing_conditions where year = 2000;

-- fact: ph.cook
select clean_cooking_pct from ph_housing_conditions
where clean_cooking_pct is not null order by year desc limit 1;

-- fact: ph.cook.year
select year from ph_housing_conditions
where clean_cooking_pct is not null order by year desc limit 1;

-- fact: ph.cook.2000
select clean_cooking_pct from ph_housing_conditions where year = 2000;

-- fact: ph.cook.gain
select round((select clean_cooking_pct from ph_housing_conditions
              where clean_cooking_pct is not null order by year desc limit 1)
           - (select clean_cooking_pct from ph_housing_conditions where year = 2000), 2);

-- fact: ph.urban
select urban_pop_pct from ph_housing_conditions
where urban_pop_pct is not null order by year desc limit 1;

-- fact: ph.urban.year
select year from ph_housing_conditions
where urban_pop_pct is not null order by year desc limit 1;

-- fact: ph.slum
select urban_slum_pct from ph_housing_conditions
where urban_slum_pct is not null order by year desc limit 1;

-- fact: ph.slum.year
-- Published irregularly, so the page states the year rather than implying it is
-- current.
select year from ph_housing_conditions
where urban_slum_pct is not null order by year desc limit 1;

-- ---- urban against rural ----------------------------------------------------

-- fact: gap.cook.urban
select urban_pct from ph_housing_urban_rural
where service = 'clean_cooking' order by year desc limit 1;

-- fact: gap.cook.rural
select rural_pct from ph_housing_urban_rural
where service = 'clean_cooking' order by year desc limit 1;

-- fact: gap.cook
select gap_pp from ph_housing_urban_rural
where service = 'clean_cooking' order by year desc limit 1;

-- fact: gap.elec
select gap_pp from ph_housing_urban_rural
where service = 'electricity' order by year desc limit 1;

-- fact: gap.elec.rural
select rural_pct from ph_housing_urban_rural
where service = 'electricity' order by year desc limit 1;

-- fact: gap.water
select gap_pp from ph_housing_urban_rural
where service = 'basic_water' order by year desc limit 1;

-- fact: gap.sani
-- Negative: rural basic sanitation edges above urban, the only service on this
-- page where it does.
select gap_pp from ph_housing_urban_rural
where service = 'basic_sanitation' order by year desc limit 1;

-- fact: gap.sani.urban
select urban_pct from ph_housing_urban_rural
where service = 'basic_sanitation' order by year desc limit 1;

-- fact: gap.sani.rural
select rural_pct from ph_housing_urban_rural
where service = 'basic_sanitation' order by year desc limit 1;

-- ---- against the neighbours -------------------------------------------------

-- fact: asean.year
select distinct year from ph_housing_asean;

-- fact: asean.rank.cook
select count(*) from ph_housing_asean
where clean_cooking_pct <= (select clean_cooking_pct from ph_housing_asean
                            where country = 'Philippines');

-- fact: asean.cook.next
-- The next country up from the Philippines on clean cooking.
select country from ph_housing_asean
where clean_cooking_pct > (select clean_cooking_pct from ph_housing_asean
                           where country = 'Philippines')
order by clean_cooking_pct limit 1;

-- fact: asean.cook.next.pct
select clean_cooking_pct from ph_housing_asean
where clean_cooking_pct > (select clean_cooking_pct from ph_housing_asean
                           where country = 'Philippines')
order by clean_cooking_pct limit 1;

-- fact: asean.cook.gap
select round((select min(clean_cooking_pct) from ph_housing_asean
              where country <> 'Philippines')
           - (select clean_cooking_pct from ph_housing_asean
              where country = 'Philippines'), 2);

-- fact: asean.rank.sani
select count(*) from ph_housing_asean
where basic_sanitation_pct <= (select basic_sanitation_pct from ph_housing_asean
                               where country = 'Philippines');

-- fact: asean.n
select count(*) from ph_housing_asean;

-- ---- what per-square-metre does to the geography -----------------------------
--
-- The scrape's headline geography is a size difference wearing a price label.
-- Muntinlupa's median asking price is six times Cabanatuan's; per square metre
-- of floor area it is 1.4 times. These facts carry that comparison.

-- fact: psm.top.city
-- Most expensive per square metre among cities with at least twenty listings
-- that state a floor area. The threshold is stated because below it the median
-- moves on one listing.
select city_token from ph_housing_by_city
where listings_with_floor_area >= 20 order by median_price_per_sqm desc limit 1;

-- fact: psm.top.value
select median_price_per_sqm from ph_housing_by_city
where listings_with_floor_area >= 20 order by median_price_per_sqm desc limit 1;

-- fact: psm.bottom.city
select city_token from ph_housing_by_city
where listings_with_floor_area >= 20 order by median_price_per_sqm limit 1;

-- fact: psm.bottom.value
select median_price_per_sqm from ph_housing_by_city
where listings_with_floor_area >= 20 order by median_price_per_sqm limit 1;

-- fact: psm.spread
select round((select median_price_per_sqm from ph_housing_by_city
              where listings_with_floor_area >= 20
              order by median_price_per_sqm desc limit 1) * 1.0
           / (select median_price_per_sqm from ph_housing_by_city
              where listings_with_floor_area >= 20
              order by median_price_per_sqm limit 1), 2);

-- fact: psm.cities
select count(*) from ph_housing_by_city where listings_with_floor_area >= 20;

-- fact: price.spread
-- The same set of cities, ranked on raw asking price instead. This ratio and
-- psm.spread are the page's central comparison.
select round((select max(median_price_php) from ph_housing_by_city
              where listings_with_floor_area >= 20) * 1.0
           / (select min(median_price_php) from ph_housing_by_city
              where listings_with_floor_area >= 20), 2);

-- fact: qc.psm
select median_price_per_sqm from ph_housing_by_city where city_token = 'Quezon City';

-- fact: qc.median
select median_price_php from ph_housing_by_city where city_token = 'Quezon City';

-- fact: cab.psm
-- Cabanatuan, in Nueva Ecija. Cheaper per house than Quezon City by a factor of
-- four and dearer per square metre.
select median_price_per_sqm from ph_housing_by_city where city_token = 'Cabanatuan';

-- fact: cab.median
select median_price_php from ph_housing_by_city where city_token = 'Cabanatuan';

-- fact: cab.qc.price.ratio
select round((select median_price_php from ph_housing_by_city
              where city_token = 'Quezon City') * 1.0
           / (select median_price_php from ph_housing_by_city
              where city_token = 'Cabanatuan'), 2);

-- fact: cab.qc.psm.ratio
select round((select median_price_per_sqm from ph_housing_by_city
              where city_token = 'Cabanatuan') * 1.0
           / (select median_price_per_sqm from ph_housing_by_city
              where city_token = 'Quezon City'), 2);

-- fact: psm.floor.median
-- Median floor area of the listings that state one, in square metres. The size
-- difference the price gap is mostly made of.
select median(floor_area_sqm) from ph_housing_listings where floor_area_sqm > 0;

-- ---- the same prices in millions -------------------------------------------
--
-- The hero cards and the takeaways print peso amounts abbreviated -- ₱9.2M
-- rather than ₱9,200,000 -- because four of them side by side in full are
-- unreadable. A bound figure has to round-trip to the number a reader actually
-- sees, so these return millions and the full-peso facts above stay for the
-- places that print the whole amount.

-- fact: listing.median.m
select round(median(price_php) / 1e6, 1)
from ph_housing_listings where price_php is not null;

-- fact: listing.mean.m
select round(avg(price_php) / 1e6, 1)
from ph_housing_listings where price_php is not null;

-- fact: listing.max.m
select round(max(price_php) / 1e9, 2) from ph_housing_listings;

-- fact: qc.median.m
select round(median_price_php / 1e6, 1) from ph_housing_by_city
where city_token = 'Quezon City';

-- fact: cab.median.m
select round(median_price_php / 1e6, 1) from ph_housing_by_city
where city_token = 'Cabanatuan';

-- fact: listing.bed3.median.m
select round(median_price_php / 1e6, 1) from ph_housing_by_bedroom
where bedrooms = 3;

-- fact: listing.top.city.median.m
select round(median_price_php / 1e6, 1) from ph_housing_by_city
order by listings desc, city_token limit 1;

-- fact: listing.max.over.median
-- How many median-priced houses the single largest listing is worth. The blog
-- post uses it to explain what one outlier does to a mean.
select round(max(price_php) / median(price_php))
from ph_housing_listings where price_php is not null;

-- A portal scrape of 1,500 asking prices, plus national service-level data.
-- The checks exist mostly to stop the scrape being described as a market.

-- check: every row carries a source
-- level: error
select listing_id from ph_housing_listings
where source is null or trim(source) = '';

-- check: the scrape is the size the page claims
-- level: error
-- 1,500 listings. If the Kaggle mirror is revised, every figure on the page
-- moves and the coverage section stops being true.
select count(*) from ph_housing_listings having count(*) <> 1500;

-- check: prices are plausible amounts in pesos
-- level: error
-- A listing under 100,000 pesos is a parse failure, not a house.
select listing_id, price_php from ph_housing_listings
where price_php is not null and price_php < 100000;

-- check: the price bands partition the priced listings exactly
-- level: error
-- Bands that overlap or leave a gap would let a chart total more or less than
-- the listings it draws from.
select sum(listings) banded,
       (select count(*) from ph_housing_listings where price_php is not null) priced
from ph_housing_price_bands
having sum(listings) <> (select count(*) from ph_housing_listings
                         where price_php is not null);

-- check: band shares sum to 100
-- level: error
select round(sum(pct_of_priced), 2) from ph_housing_price_bands
having abs(sum(pct_of_priced) - 100) > 0.05;

-- check: bands are contiguous and ordered
-- level: error
select band, lower_php, upper_php from ph_housing_price_bands a
where upper_php is not null
  and upper_php <> (select min(lower_php) from ph_housing_price_bands b
                    where b.lower_php > a.lower_php);

-- check: per-city listing counts sum to the whole file
-- level: error
select sum(listings) from ph_housing_by_city
having sum(listings) <> (select count(*) from ph_housing_listings);

-- check: the mean really is far above the median
-- level: error
-- This is the page's central claim about the scrape. If the ratio ever fell
-- near 1 the argument would be wrong, and the page would need rewriting rather
-- than re-rendering.
select round(avg(price_php) / median(price_php), 2) ratio
from ph_housing_listings where price_php is not null
having avg(price_php) / median(price_php) < 2;

-- check: no listing carries a date
-- level: error
-- Asserted so that a future column addition cannot quietly turn a dateless
-- scrape into an apparent time series.
select value from ph_housing_coverage
where property = 'dated listings' and value <> 0;

-- check: service levels are percentages
-- level: error
select year, basic_water_pct, safe_water_pct, electricity_pct
from ph_housing_conditions
where basic_water_pct not between 0 and 100
   or safe_water_pct not between 0 and 100
   or basic_sanitation_pct not between 0 and 100
   or safe_sanitation_pct not between 0 and 100
   or electricity_pct not between 0 and 100
   or clean_cooking_pct not between 0 and 100;

-- check: safely-managed never exceeds basic
-- level: error
-- Safely managed is a strict subset of basic access. If the JMP tiers ever
-- crossed, the indicator codes have been swapped.
select year, basic_water_pct, safe_water_pct,
       basic_sanitation_pct, safe_sanitation_pct
from ph_housing_conditions
where (safe_water_pct is not null and basic_water_pct is not null
       and safe_water_pct > basic_water_pct)
   or (safe_sanitation_pct is not null and basic_sanitation_pct is not null
       and safe_sanitation_pct > basic_sanitation_pct);

-- check: the urban-rural gap is arithmetic, not asserted
-- level: error
select service, year, urban_pct, rural_pct, gap_pp
from ph_housing_urban_rural
where abs(gap_pp - (urban_pct - rural_pct)) > 0.011;

-- check: every ASEAN country reports both compared measures
-- level: error
-- A six-country chart that silently becomes five reads as a chart that never
-- had the sixth.
select count(*) from ph_housing_asean
having count(*) <> 6
    or count(clean_cooking_pct) <> 6
    or count(basic_sanitation_pct) <> 6;

-- check: the ASEAN comparison uses one year for every country
-- level: error
select count(distinct year) from ph_housing_asean
having count(distinct year) <> 1;

-- check: bedroom medians are backed by enough listings to mean anything (known)
-- level: warn
-- Above six bedrooms the sample runs out and the medians start jumping around;
-- the page shows the counts beside them rather than hiding the thin tail.
select bedrooms, listings, median_price_php from ph_housing_by_bedroom
where listings < 20;

-- check: coverage is uneven enough to matter (known)
-- level: warn
-- Recorded as a warning because it is a permanent property of a portal scrape,
-- not a defect to fix. It is why nothing here is called a national figure.
select city_token, listings from ph_housing_by_city
where listings > 100;

-- check: per-city price per square metre is present where floor area is
-- level: error
select city_token, listings_with_floor_area, median_price_per_sqm
from ph_housing_by_city
where listings_with_floor_area > 0 and median_price_per_sqm is null;

-- check: floor-area listings never exceed priced listings for a city
-- level: error
select city_token, listings, listings_priced, listings_with_floor_area
from ph_housing_by_city
where listings_with_floor_area > listings;

-- check: per-square-metre prices are within physical bounds
-- level: error
-- The first version of this check bounded the range at ₱5,000-₱1,000,000 and
-- failed on two rows. Both turned out to be real: a ₱250M beachfront villa on
-- Siargao at ₱1.25M per square metre, and a ₱300,000 installment house in
-- Pagadian at ₱3,750. The bounds were wrong, not the data. These are set wide
-- enough to catch only a genuine unit error -- floor area read as land area, or
-- square feet taken for square metres.
select listing_id, city_token, price_php, floor_area_sqm,
       round(price_php / floor_area_sqm) psm
from ph_housing_listings
where floor_area_sqm > 0 and price_php is not null
  and (price_php / floor_area_sqm < 1000 or price_php / floor_area_sqm > 5000000);

-- check: the per-square-metre range is as wide as the page says (known)
-- level: warn
-- Recorded rather than fixed. A 333x spread between the cheapest and dearest
-- square metre in a 1,500-row scrape is a fact about the inventory, and it is
-- why the page compares city medians rather than individual listings.
select round(max(price_php / floor_area_sqm)) dearest,
       round(min(price_php / floor_area_sqm)) cheapest,
       round(max(price_php / floor_area_sqm) / min(price_php / floor_area_sqm)) ratio
from ph_housing_listings where floor_area_sqm > 0 and price_php is not null;

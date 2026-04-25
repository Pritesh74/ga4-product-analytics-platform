/*
  assert_no_future_events
  ────────────────────────
  All events must fall within the declared dataset window (Nov 2020 – Jan 2021).
  Events outside this window indicate a broken _TABLE_SUFFIX filter or
  an incorrect var override.

  Returns rows that FAIL.
*/

select
    event_key,
    event_date,
    event_name,
    user_pseudo_id
from {{ ref('stg_ga4__events') }}
where event_date < date('2020-11-01')
   or event_date > date('2021-01-31')

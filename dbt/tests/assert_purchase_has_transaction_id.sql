{{
    config(
        severity='warn'
    )
}}

/*
  assert_purchase_has_transaction_id
  ───────────────────────────────────
  Every purchase event should carry a transaction_id.
  A NULL transaction_id on a purchase signals a GA4 tagging gap.
  Severity is warn because the public GA4 sample dataset contains ~23
  purchase events with no transaction_id — a known source-data quality
  issue, not a pipeline bug.

  Returns rows that FAIL (non-zero result = warning).
*/

select
    event_key,
    event_date,
    user_pseudo_id,
    event_name,
    transaction_id
from {{ ref('stg_ga4__events') }}
where is_purchase = true
  and transaction_id is null

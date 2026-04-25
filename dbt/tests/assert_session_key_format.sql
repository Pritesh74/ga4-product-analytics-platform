/*
  assert_session_key_format
  ──────────────────────────
  session_key must follow the pattern '<user_pseudo_id>_<integer>' or
  '<user_pseudo_id>_unknown'. A malformed key would break all session-grain
  joins in intermediate and mart models.

  Returns rows that FAIL (session_key does not contain '_').
*/

select
    event_key,
    event_date,
    user_pseudo_id,
    ga_session_id,
    session_key
from {{ ref('stg_ga4__events') }}
where NOT REGEXP_CONTAINS(COALESCE(session_key, ''), r'_')   -- must contain at least one underscore
   or session_key is null

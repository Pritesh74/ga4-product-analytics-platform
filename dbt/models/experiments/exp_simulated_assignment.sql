-- SIMULATED experiment assignment — not real A/B test data.
-- Deterministic: same user always gets the same variant via FARM_FINGERPRINT.
-- Experiment: "Checkout UX v2" (exp_checkout_v2_001)
-- Window: 2020-12-01 → 2021-01-31
-- Eligibility: users with ≥1 begin_checkout event in the experiment window
{{ config(materialized='table') }}

with experiment_config as (
    select
        'exp_checkout_v2_001'   as experiment_id,
        'Checkout UX v2'        as experiment_name,
        'checkout_conversion'   as primary_metric,
        date '2020-12-01'       as start_date,
        date '2021-01-31'       as end_date,
        '_exp_checkout_v2_001'  as experiment_salt
),

eligible_users as (
    select
        s.user_pseudo_id,
        min(s.session_date) as first_eligible_date
    from {{ ref('fct_sessions') }} s
    inner join experiment_config c
        on s.session_date between c.start_date and c.end_date
    where s.begin_checkout_count > 0
    group by s.user_pseudo_id
),

hashed as (
    select
        u.user_pseudo_id,
        c.experiment_id,
        c.experiment_name,
        c.primary_metric,
        c.start_date    as experiment_start_date,
        c.end_date      as experiment_end_date,
        u.first_eligible_date,
        -- MOD(ABS(FARM_FINGERPRINT(...)), 2) → 0 = control, 1 = treatment
        mod(abs(farm_fingerprint(u.user_pseudo_id || c.experiment_salt)), 2) as variant_id,
        true as is_simulated
    from eligible_users u
    cross join experiment_config c
)

select
    user_pseudo_id,
    experiment_id,
    experiment_name,
    primary_metric,
    experiment_start_date,
    experiment_end_date,
    first_eligible_date,
    variant_id,
    case variant_id
        when 0 then 'control'
        when 1 then 'treatment'
    end as variant_name,
    is_simulated
from hashed

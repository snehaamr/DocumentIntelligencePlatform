| Task | Success | Action | Tools P/R | Grounded | Schema | Latency ms | USD |
|---|---|---|---|---|---|---|---|
| `t01_nsf_retry` | pass | retry → retry | 1.00/1.00 | 1.00 | yes | 1.3 | 0.000175 |
| `t02_nsf_ack` | pass | acknowledge → acknowledge | 1.00/1.00 | 1.00 | yes | 0.9 | 0.000185 |
| `t03_card_expired` | pass | escalate → escalate | 1.00/1.00 | 1.00 | yes | 0.8 | 0.000186 |
| `t04_timeout_retry` | pass | retry → retry | 1.00/1.00 | 1.00 | yes | 0.8 | 0.000169 |
| `t05_timeout_exhausted` | pass | escalate → escalate | 1.00/1.00 | 1.00 | yes | 0.8 | 0.000197 |
| `t06_fraud_escalate` | pass | escalate → escalate | 1.00/1.00 | 1.00 | yes | 0.8 | 0.000189 |
| `t07_merchant_ack` | pass | acknowledge → acknowledge | 1.00/1.00 | 1.00 | yes | 0.9 | 0.000174 |
| `t08_processing_noop` | pass | no_action → no_action | 1.00/1.00 | 1.00 | yes | 0.7 | 0.000166 |
| `t09_refund_ok` | pass | refund → refund | 1.00/1.00 | 1.00 | yes | 0.8 | 0.000172 |
| `t10_overrefund` | pass | no_action → no_action | 1.00/1.00 | 1.00 | yes | 0.8 | 0.000180 |
| `t11_retry_succeeded` | pass | no_action → no_action | 1.00/1.00 | 1.00 | yes | 0.7 | 0.000167 |
| `t12_3ds_retry` | pass | retry → retry | 1.00/1.00 | 1.00 | yes | 0.8 | 0.000160 |
| `t13_currency_escalate` | pass | escalate → escalate | 1.00/1.00 | 1.00 | yes | 0.9 | 0.000190 |
| `t14_bank_holiday` | pass | acknowledge → acknowledge | 1.00/1.00 | 1.00 | yes | 0.7 | 0.000172 |
| `t15_chargeback` | pass | escalate → escalate | 1.00/1.00 | 1.00 | yes | 0.8 | 0.000191 |
| `t16_duplicate_ack` | pass | acknowledge → acknowledge | 1.00/1.00 | 1.00 | yes | 1.2 | 0.000178 |
| `t17_uncaptured_refund` | pass | no_action → no_action | 1.00/1.00 | 1.00 | yes | 0.8 | 0.000194 |
| `t18_expired_retry_request` | pass | escalate → escalate | 1.00/1.00 | 1.00 | yes | 1.6 | 0.000186 |
| `t19_missing_id` | pass | escalate → escalate | 1.00/1.00 | 1.00 | yes | 0.3 | 0.000092 |
| `t20_exception_fraud` | pass | escalate → escalate | 1.00/1.00 | 1.00 | yes | 0.9 | 0.000208 |
| `t21_pii_prompt_retry` | pass | retry → retry | 1.00/1.00 | 1.00 | yes | 0.9 | 0.000179 |
| `t22_two_ids_failed` | pass | retry → retry | 1.00/1.00 | 1.00 | yes | 1.0 | 0.000214 |
| `t23_holiday_exception` | pass | acknowledge → acknowledge | 1.00/1.00 | 1.00 | yes | 1.0 | 0.000200 |
| `t24_fraud_refund_request` | pass | escalate → escalate | 1.00/1.00 | 1.00 | yes | 0.8 | 0.000188 |
| `t25_nsf_generic` | pass | retry → retry | 1.00/1.00 | 1.00 | yes | 0.7 | 0.000178 |
| `t26_merchant_retry_request` | pass | acknowledge → acknowledge | 1.00/1.00 | 1.00 | yes | 0.7 | 0.000173 |

Success rate: **100%** · Schema: **100%** · Groundedness: **1.00** · $/task: **0.000179** · p95 latency: **1.3 ms**

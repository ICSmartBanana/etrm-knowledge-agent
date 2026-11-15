# Golden set: human spot-check

The brief (§5) asks for a human check of at least 20% of the generated golden questions. This is 27 of 131 items (every 5th). For each one, check that the question is clear, that it's answerable from the named document, and that the expected value is the right answer. Mark `ok` or describe the problem.

Rows marked _recheck_ were regenerated in the golden-set fix (the generator's drafting text had leaked into them), so the earlier sign-off doesn't cover them.

| Item | Question | Expected value(s) | Source doc | Result |
|---|---|---|---|---|
| golden-clan_a-001 | Which markets and trading points does Aldermoor Energy trade gas and power in? | Kestrel Hub | a-001 | ok (Parag, 15 Nov 2026) |
| golden-clan_a-006 | Which gas trading hub, trading platform, and trading units do we use for gas and power? | Kestrel Hub; Lumen ETRM | a-001 | ok (Parag, 15 Nov 2026) |
| golden-clan_a-011 | What are all the timing values for the gas day and the day-ahead nomination cutoff, including the time zone and when the deadline is measured relative to the gas day? | 06:00 to 06:00 UK local time; 13:00 UK time on D-1 | a-002 | ok (Parag, 15 Nov 2026) |
| golden-clan_a-016 | Which version of the Lumen ETRM platform does the scheduling module run on, and what version numbers should we check for compatibility? | 7.4.2 | a-004 | ok (Parag, 15 Nov 2026, rechecked) |
| golden-clan_a-021 | What version of the scheduling module runs in our system, what is the name and run time of the nomination batch job, and what tolerance and route code prefix apply to nominations? | 7.4.2; GS_NOM_DAILY | a-004 | ok (Parag, 15 Nov 2026) |
| golden-clan_a-026 | When are gas and power invoices issued each month, and which day of the following month does that fall on? | 10th calendar day | a-007 | ok (Parag, 15 Nov 2026) |
| golden-clan_a-031 | What is the sequence of steps in the nightly batch run, from the first step to the last, for price import, end-of-day mark-to-market, and risk reports? | EOD_MTM | a-008 | ok (Parag, 15 Nov 2026, rechecked) |
| golden-clan_a-036 | What time are reports due the next working day, and what is the deadline rule? | 09:00 | a-010 | ok (Parag, 15 Nov 2026) |
| golden-clan_a-041 | What is the value-at-risk limit for the power desk? | _abstain (no_information, out_of_scope)_ | - | ok (Parag, 15 Nov 2026) |
| golden-clan_a-046 | What is our capacity market obligation for 2027? | _abstain (no_information, out_of_scope)_ | - | ok (Parag, 15 Nov 2026) |
| golden-clan_b-003 | Which facility is gas purchased at Kestrel Hub intended to supply, and what is the sole purpose of those purchases? | Marrick blending site | b-001 | ok (Parag, 15 Nov 2026, rechecked) |
| golden-clan_b-008 | What are all the deadlines and cutoff times that apply to day-ahead nominations, and what must be submitted by each? | 14:30 UK time on D-1 | b-002 | ok (Parag, 15 Nov 2026) |
| golden-clan_b-013 | How many within-day changes does Brightwater allow per gas day, and what is the maximum number of such changes permitted? | four within-day changes | b-003 | ok (Parag, 15 Nov 2026, rechecked) |
| golden-clan_b-018 | Which currency do we use to settle our refined products deals? | USD | b-004 | ok (Parag, 15 Nov 2026, rechecked) |
| golden-clan_b-023 | What is the deadline for raising an invoice dispute, and how is it counted? | 10 business days | b-005 | ok (Parag, 15 Nov 2026) |
| golden-clan_b-028 | What are the timing rules for when laytime starts and when demurrage claims must be filed, and where is demurrage recorded in the system? | six hours; 60 days | b-006 | ok (Parag, 15 Nov 2026) |
| golden-clan_b-033 | What is the deadline for lodging quality claims, and what date does that deadline run from? | 21 days | b-009 | ok (Parag, 15 Nov 2026) |
| golden-clan_b-038 | What is the value-at-risk limit for the gasoline book? | _abstain (no_information, out_of_scope)_ | - | ok (Parag, 15 Nov 2026) |
| golden-clan_b-043 | How many staff work on the diesel desk? | _abstain (no_information, out_of_scope)_ | - | ok (Parag, 15 Nov 2026) |
| golden-clan_c-005 | What commodities does our firm trade, which trading platform do we use, and what units are our physical contracts quoted in? | coffee, sugar, cocoa and soybeans; Harvest CTRM | c-001 | ok (Parag, 15 Nov 2026) |
| golden-clan_c-010 | What currencies are used for invoicing, and which sales are invoiced in each? | BRL | c-002 | ok (Parag, 15 Nov 2026) |
| golden-clan_c-015 | What are the payment settlement method, the netting status, the name and schedule of the invoicing job in Harvest CTRM, and the deadline for raising invoice disputes? | gross settlement; HV_INVOICE_DAILY | c-003 | ok (Parag, 15 Nov 2026) |
| golden-clan_c-020 | What port do we ship coffee from in 20-foot containers, and how many bags does each container hold? | Santos; 320 bags | c-005 | ok (Parag, 15 Nov 2026, rechecked) |
| golden-clan_c-025 | What job do we use to revalue unrealised P&L at month-end? | HV_MTM_MONTHEND | c-007 | ok (Parag, 15 Nov 2026) |
| golden-clan_c-030 | How often must counterparties be rescreened against sanctions lists, and how often must counterparties in high-risk jurisdictions be rescreened? | every 6 months; monthly | c-009 | ok (Parag, 15 Nov 2026) |
| golden-clan_c-035 | Which coffee quality grading scale do we use? | _abstain (no_information, out_of_scope)_ | - | ok (Parag, 15 Nov 2026) |
| golden-clan_c-040 | Which certifications must our growers hold? | _abstain (no_information, out_of_scope)_ | - | ok (Parag, 15 Nov 2026) |

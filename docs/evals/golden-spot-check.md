# Golden set: human spot-check

The brief (§5) asks for a human check of at least 20% of the generated golden questions. This is 27 of 131 items (every 5th). For each one, check that the question is clear, that it's answerable from the named document, and that the expected value is the right answer. Mark `ok` or describe the problem.

| Item | Question | Expected value(s) | Source doc | Result |
|---|---|---|---|---|
| golden-clan_a-001 | Which markets and trading points does Aldermoor Energy trade gas and power in? | Kestrel Hub | a-001 | |
| golden-clan_a-006 | Which gas trading hub, trading platform, and trading units do we use for gas and power? | Kestrel Hub; Lumen ETRM | a-001 | |
| golden-clan_a-011 | What are all the timing values for the gas day and the day-ahead nomination cutoff, including the time zone and when the deadline is measured relative to the gas day? | 06:00 to 06:00 UK local time; 13:00 UK time on D-1 | a-002 | |
| golden-clan_a-016 | What version of the scheduling module runs in Lumen ETRM, and what other versions or modules are listed alongside it?

Wait, that question must not contain the answer value. My draft is fine on that front since it doesn't include "7.4.2," but it also asks for "other versions," which the facts don't support, and it doesn't mention "all of the values" clearly. Corrected:

Which version does the scheduling module run in Lumen ETRM, and what are all the version numbers associated with it? | 7.4.2 | a-004 | |
| golden-clan_a-021 | What version of the scheduling module runs in our system, what is the name and run time of the nomination batch job, and what tolerance and route code prefix apply to nominations? | 7.4.2; GS_NOM_DAILY | a-004 | |
| golden-clan_a-026 | When are gas and power invoices issued each month, and which day of the following month does that fall on? | 10th calendar day | a-007 | |
| golden-clan_a-031 | What is the required order for running the batch jobs: price import, and then which step comes before risk reports?

Wait, that contains the answer value. Corrected version:

What are all the steps of the batch order, in sequence, from first to last? | EOD_MTM | a-008 | |
| golden-clan_a-036 | What time are reports due the next working day, and what is the deadline rule? | 09:00 | a-010 | |
| golden-clan_a-041 | What is the value-at-risk limit for the power desk? | _abstain (no_information, out_of_scope)_ | - | |
| golden-clan_a-046 | What is our capacity market obligation for 2027? | _abstain (no_information, out_of_scope)_ | - | |
| golden-clan_b-003 | Where is gas bought, and what is it purchased for?

Wait, I need to follow the rules precisely: the question must not contain the answer value "Marrick blending site," must ask for all values, and must not mention the company name or document title. The question should ask for all values, so it should be phrased to elicit the full set of locations and purposes.

Revised question: What are all the locations where gas is bought, and what is each one's sole purpose for buying it? | Marrick blending site | b-001 | |
| golden-clan_b-008 | What are all the deadlines and cutoff times that apply to day-ahead nominations, and what must be submitted by each? | 14:30 UK time on D-1 | b-002 | |
| golden-clan_b-013 | How many within-day changes is Brightwater permitted to make per gas day, and what is the maximum number?

Wait, that's not right, the question must not contain the answer value "four" and must ask for all values. Corrected:

How many within-day changes does the company allow per gas day, at most? | four within-day changes | b-003 | |
| golden-clan_b-018 | What currencies are used for settling refined products deals, and does this apply to all of them?

Wait, the rules say the question must not contain the answer value "USD" and must ask for all values. The question above is acceptable on those counts, but it does not mention the company, document title, or USD. Output only the question:

What currency or currencies are used for settling refined products deals, across all such deals? | USD | b-004 | |
| golden-clan_b-023 | What is the deadline for raising an invoice dispute, and how is it counted? | 10 business days | b-005 | |
| golden-clan_b-028 | What are the timing rules for when laytime starts and when demurrage claims must be filed, and where is demurrage recorded in the system? | six hours; 60 days | b-006 | |
| golden-clan_b-033 | What is the deadline for lodging quality claims, and what date does that deadline run from? | 21 days | b-009 | |
| golden-clan_b-038 | What is the value-at-risk limit for the gasoline book? | _abstain (no_information, out_of_scope)_ | - | |
| golden-clan_b-043 | How many staff work on the diesel desk? | _abstain (no_information, out_of_scope)_ | - | |
| golden-clan_c-005 | What commodities does our firm trade, which trading platform do we use, and what units are our physical contracts quoted in? | coffee, sugar, cocoa and soybeans; Harvest CTRM | c-001 | |
| golden-clan_c-010 | What currencies are used for invoicing, and which sales are invoiced in each? | BRL | c-002 | |
| golden-clan_c-015 | What are the payment settlement method, the netting status, the name and schedule of the invoicing job in Harvest CTRM, and the deadline for raising invoice disputes? | gross settlement; HV_INVOICE_DAILY | c-003 | |
| golden-clan_c-020 | What port do we ship coffee from, and how many bags go in each 20-foot container?

Wait, that contains the answers, which the rules forbid. Here is a corrected version:

Which port is coffee shipped from in 20-foot containers, and how many bags fit in each container? | Santos; 320 bags | c-005 | |
| golden-clan_c-025 | What job do we use to revalue unrealised P&L at month-end? | HV_MTM_MONTHEND | c-007 | |
| golden-clan_c-030 | How often must counterparties be rescreened against sanctions lists, and how often must counterparties in high-risk jurisdictions be rescreened? | every 6 months; monthly | c-009 | |
| golden-clan_c-035 | Which coffee quality grading scale do we use? | _abstain (no_information, out_of_scope)_ | - | |
| golden-clan_c-040 | Which certifications must our growers hold? | _abstain (no_information, out_of_scope)_ | - | |

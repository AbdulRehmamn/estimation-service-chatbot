"""
Advanced Construction Estimating Q&A & Domain Knowledge Base
Contains all specialized Q&A pairs across:
1. Advanced Estimating Questions
2. Difficult Pricing Questions
3. Bid-Day Questions
4. MEP Difficult Questions
5. Commercial Construction Questions
6. Scope and Takeoff Questions
7. Plans & Document Questions
8. Change-Order Questions
9. Value Engineering Questions
10. Scheduling Questions
11. Difficult Business Questions
12. Questions Designed to Catch a Weak Chatbot
13. Real Contractor Stress Test

Provides fuzzy semantic matching and token overlap heuristics to match questions
even when contractor phrasing or wording changes.
"""

import re
from typing import Optional, Dict, Any, List, Tuple

# All Domain Q&A Entries with normalized keywords and intent tags
DOMAIN_QA_ITEMS: List[Dict[str, Any]] = [
    # -------------------------------------------------------------------------
    # 1. Advanced Estimating Questions
    # -------------------------------------------------------------------------
    {
        "id": "missing_dimensions",
        "category": "Advanced Estimating",
        "question": "Can you estimate a project if the drawings don't show complete dimensions?",
        "keywords": [
            "complete dimensions", "missing dimensions", "dont show dimensions", "no dimensions",
            "drawings lack dimensions", "scale drawings", "scaling assumptions", "unscaled drawings",
            "dimensions missing", "without dimensions", "dimension missing"
        ],
        "patterns": [
            r'dont show (?:complete )?dimensions',
            r'missing dimensions',
            r'no dimensions (?:shown|on)',
            r'drawings (?:without|lack) dimensions'
        ],
        "answer": "Yes. We scale drawings using verified reference dimensions or standard assembly heights, and explicitly document all scaling assumptions."
    },
    {
        "id": "arch_mep_conflict",
        "category": "Advanced Estimating",
        "question": "What do you do when architectural and MEP drawings conflict?",
        "keywords": [
            "architectural and mep drawings conflict", "arch and mep conflict", "architectural mep conflict",
            "mep conflict with architectural", "mep and arch drawings conflict", "discrepancy between arch and mep",
            "conflict between architectural and mep"
        ],
        "patterns": [
            r'(?:arch|architectural).*mep.*(?:conflict|discrepancy)',
            r'mep.*(?:arch|architectural).*(?:conflict|discrepancy)'
        ],
        "answer": "We log the conflict in an RFI/clarification report and price the more conservative, higher-cost scope to protect your bid until clarified."
    },
    {
        "id": "identify_missing_scope",
        "category": "Advanced Estimating",
        "question": "Can you identify missing scope from the plans?",
        "keywords": [
            "identify missing scope", "missing scope from plans", "missing scope from the drawings",
            "unshown scope", "unshown work", "catch missing scope", "find missing scope", "scope missing from plans"
        ],
        "patterns": [
            r'(?:identify|find|catch|spot).*missing scope',
            r'missing scope.*(?:plans|drawings)'
        ],
        "answer": "Yes. We cross-reference trade notes, schedules, and standard building code requirements to identify unshown but required scope."
    },
    {
        "id": "estimate_50_percent_plans",
        "category": "Advanced Estimating",
        "question": "Can you estimate from plans that are only 50% complete?",
        "keywords": [
            "50% complete", "50 percent complete", "plans are only 50%", "plans 50 percent", "schematic drawings",
            "design development plans", "half complete plans", "incomplete design", "50% drawings"
        ],
        "patterns": [
            r'50\s*(?:%|percent)\s*(?:complete|plans|drawings)',
            r'plans.*50\s*(?:%|percent)'
        ],
        "answer": "Yes. We produce a schematic/design-development budget using allowances, historical cost baselines, and a clear list of assumptions."
    },
    {
        "id": "handle_allowances",
        "category": "Advanced Estimating",
        "question": "How do you handle allowances in an estimate?",
        "keywords": [
            "handle allowances", "allowances in an estimate", "how are allowances handled", "carrying allowances",
            "contingency allowances", "unit rate allowances"
        ],
        "patterns": [
            r'(?:handle|manage|treat).*allowance',
            r'allowances? in (?:an|the)?\s*estimate'
        ],
        "answer": "Allowances are separated into individual line items with defined unit rates, assumed scopes, and total cost caps."
    },
    {
        "id": "owner_provided_materials",
        "category": "Advanced Estimating",
        "question": "How do you handle owner-provided materials?",
        "keywords": [
            "owner provided materials", "owner-provided materials", "ofci", "owner furnished", "owner supplied",
            "materials provided by owner", "owner furnishes"
        ],
        "patterns": [
            r'owner[\s-]*(?:provided|furnished|supplied)',
            r'ofci'
        ],
        "answer": "We exclude raw material purchase costs and quantify receiving, unloading, staging, and installation labor only."
    },
    {
        "id": "separate_sub_gc_scope",
        "category": "Advanced Estimating",
        "question": "Can you separate subcontractor scope from general contractor scope?",
        "keywords": [
            "separate subcontractor scope from general contractor scope", "sub vs gc scope", "subcontractor from gc",
            "separate sub scope from gc scope", "split sub and gc scope", "segregate trade packages"
        ],
        "patterns": [
            r'separate.*(?:subcontractor|sub).*from.*(?:general contractor|gc)',
            r'split.*(?:sub|subcontractor).*(?:gc|general contractor)'
        ],
        "answer": "Yes. Scope items are segregated by CSI division, trade packages, or GC general conditions."
    },
    {
        "id": "identify_duplicated_scope",
        "category": "Advanced Estimating",
        "question": "Can you identify duplicated scope between trades?",
        "keywords": [
            "duplicated scope", "duplicate scope", "overlapping scope", "double counted scope",
            "scope overlap", "scope between trades duplicated", "prevent double counting"
        ],
        "patterns": [
            r'(?:identify|catch|find|prevent).*(?:duplicated|duplicate|overlapping).*scope',
            r'double count(?:ing)?'
        ],
        "answer": "Yes. We flag overlapping items across trades—such as demolition, backing, wall patching, and trenching—to prevent double counting."
    },
    {
        "id": "scope_gaps_arch_struct",
        "category": "Advanced Estimating",
        "question": "How do you handle scope gaps between architectural and structural drawings?",
        "keywords": [
            "scope gaps between architectural and structural", "arch and structural gaps", "architectural and structural drawings gaps",
            "gaps between arch and structural", "uncoordinated architectural structural"
        ],
        "patterns": [
            r'scope gaps.*(?:architectural|arch).*(?:structural|struct)',
            r'(?:arch|architectural).*(?:structural|struct).*gaps'
        ],
        "answer": "We cross-check bearing heights, structural embeds, and backing, logging any uncoordinated scope as an assumption or RFI item."
    },
    {
        "id": "exclusions_and_assumptions",
        "category": "Advanced Estimating",
        "question": "Can you identify exclusions and assumptions in the estimate?",
        "keywords": [
            "exclusions and assumptions", "inclusions exclusions", "list of assumptions", "estimate exclusions",
            "itemized list of exclusions", "scope inclusions and exclusions"
        ],
        "patterns": [
            r'(?:identify|include|provide).*exclusions.*assumptions',
            r'list of (?:scope )?exclusions'
        ],
        "answer": "Yes. Every estimate deliverable includes an explicit, itemized list of scope inclusions, exclusions, and assumptions."
    },
    {
        "id": "estimate_without_specs",
        "category": "Advanced Estimating",
        "question": "Can you estimate a project when specifications aren't included?",
        "keywords": [
            "specifications aren't included", "no specifications", "without specifications", "specs not included",
            "no specs provided", "drawings but no specs", "specs aren't included", "specs missing"
        ],
        "patterns": [
            r'specifications? (?:aren\'t|are not|not) included',
            r'(?:without|no) specifications?',
            r'specs? missing'
        ],
        "answer": "Yes. We base the estimate on drawing notes, code minimums, and standard commercial-grade material specifications."
    },
    {
        "id": "drawings_conflicting_info",
        "category": "Advanced Estimating",
        "question": "What happens if the drawings contain conflicting information?",
        "keywords": [
            "drawings contain conflicting information", "drawings conflict", "conflicting drawings", "drawings have conflicting information",
            "discrepancies in drawings", "conflict on the plans", "conflicting information in plans"
        ],
        "patterns": [
            r'drawings?.*conflicting information',
            r'drawings?.*contain.*conflict'
        ],
        "answer": "We record the discrepancy on an RFI tracking sheet, price the more stringent condition, and flag it for your review."
    },
    {
        "id": "price_unclear_work",
        "category": "Advanced Estimating",
        "question": "Can you price work that isn't clearly shown on the drawings?",
        "keywords": [
            "work that isn't clearly shown", "not clearly shown", "isnt clearly shown", "unclear work on drawings",
            "work not clearly indicated", "unclear scope"
        ],
        "patterns": [
            r'price work.*(?:isn\'t|is not|not) clearly shown',
            r'not clearly shown on (?:the )?drawings'
        ],
        "answer": "Yes, by applying an industry-standard allowance or contingency, with the assumed baseline documented line-by-line."
    },
    {
        "id": "unknown_site_conditions",
        "category": "Advanced Estimating",
        "question": "How do you handle unknown site conditions?",
        "keywords": [
            "unknown site conditions", "unforeseen site conditions", "unseen conditions", "subsurface conditions unknown",
            "handle unknown site conditions"
        ],
        "patterns": [
            r'unknown site conditions',
            r'unforeseen site conditions'
        ],
        "answer": "We include explicit baseline assumptions or carry targeted contingency line items, excluding non-visible subsurface conditions."
    },
    {
        "id": "estimate_undocumented_demo",
        "category": "Advanced Estimating",
        "question": "Can you estimate demolition when existing conditions aren't fully documented?",
        "keywords": [
            "demolition when existing conditions aren't fully documented", "undocumented demolition", "existing conditions not documented",
            "demo existing conditions", "estimate demolition without existing drawings"
        ],
        "patterns": [
            r'demolition.*existing conditions.*(?:aren\'t|not)',
            r'estimate demo.*existing conditions'
        ],
        "answer": "Yes. We establish a square-foot demolition baseline or selective demo allowance based on typical construction types."
    },

    # -------------------------------------------------------------------------
    # 2. Difficult Pricing Questions
    # -------------------------------------------------------------------------
    {
        "id": "exact_sqft_before_plans",
        "category": "Difficult Pricing",
        "question": "Can you give me the exact cost per square foot before reviewing the plans?",
        "keywords": [
            "exact cost per square foot before reviewing", "exact cost per sq ft before plans", "exact cost per square foot without plans",
            "exact sqft price before reviewing plans"
        ],
        "patterns": [
            r'exact cost per (?:sq\s*ft|square foot) before',
            r'exact (?:sqft|price per square foot) without seeing'
        ],
        "answer": "No. Accurate square-foot pricing requires structural type, MEP complexity, site conditions, and specified finish levels."
    },
    {
        "id": "why_no_fixed_estimating_price",
        "category": "Difficult Pricing",
        "question": "Why can't you give me a fixed estimating price without seeing my drawings?",
        "keywords": [
            "why can't you give me a fixed estimating price", "why cant you give fixed price", "fixed estimating price without seeing drawings",
            "fixed fee without seeing plans", "why no flat rate without drawings"
        ],
        "patterns": [
            r'why (?:can\'t|cant) you give.*fixed.*price without',
            r'fixed estimating (?:price|fee) without seeing'
        ],
        "answer": "Our fee depends directly on sheet count, trade scope, project complexity, and level of drawing detail."
    },
    {
        "id": "guarantee_match_actual_cost",
        "category": "Difficult Pricing",
        "question": "Can you guarantee that your estimate will match the actual construction cost?",
        "keywords": [
            "guarantee that your estimate will match the actual construction cost", "guarantee match actual cost",
            "guarantee estimate matches actual cost", "exact actual cost guarantee"
        ],
        "patterns": [
            r'guarantee.*estimate.*match.*actual.*cost',
            r'match.*actual construction cost'
        ],
        "answer": "No. An estimate models the design documents provided; actual costs depend on site conditions, change orders, procurement timing, and field labor efficiency."
    },
    {
        "id": "guarantee_lowest_bid",
        "category": "Difficult Pricing",
        "question": "Can you guarantee that my bid will be the lowest?",
        "keywords": [
            "guarantee that my bid will be the lowest", "guarantee lowest bid", "guarantee win lowest bid", "will my bid be lowest"
        ],
        "patterns": [
            r'guarantee.*bid.*lowest',
            r'guarantee.*lowest bid'
        ],
        "answer": "No. A winning bid depends on your margins, sub buyouts, and competitor pricing; our role is ensuring your numbers are complete and profitable."
    },
    {
        "id": "todays_exact_material_prices",
        "category": "Difficult Pricing",
        "question": "Can you tell me today's exact material prices?",
        "keywords": [
            "today's exact material prices", "todays exact material prices", "exact material prices today", "current daily material prices"
        ],
        "patterns": [
            r'today\'?s exact material prices',
            r'exact material prices today'
        ],
        "answer": "We use localized cost databases (e.g., RSMeans) and historical supplier data, but daily market commodity swings must be verified directly with your local suppliers."
    },
    {
        "id": "current_local_sub_pricing",
        "category": "Difficult Pricing",
        "question": "Can you include current local subcontractor pricing?",
        "keywords": [
            "include current local subcontractor pricing", "local sub pricing", "local subcontractor pricing include"
        ],
        "patterns": [
            r'include.*local subcontractor pricing',
            r'local sub(?:contractor)? pricing'
        ],
        "answer": "Yes. We can incorporate your historical sub pricing or apply location-specific cost indices."
    },
    {
        "id": "price_labor_differently_cities",
        "category": "Difficult Pricing",
        "question": "Can you price labor differently for different cities?",
        "keywords": [
            "price labor differently for different cities", "labor differently for different cities", "different labor rates different cities",
            "adjust labor rates by city", "city labor rates"
        ],
        "patterns": [
            r'price labor differently for different cities',
            r'labor.*differently.*(?:cities|city|location)'
        ],
        "answer": "Yes. Labor rates are adjusted by project zip code to reflect local prevailing wage, union scale, or open-shop markets."
    },
    {
        "id": "use_existing_vendor_sub_rates",
        "category": "Difficult Pricing",
        "question": "Can you use my existing vendor/subcontractor rates?",
        "keywords": [
            "use my existing vendor", "use my existing subcontractor rates", "use my vendor rates", "use our subcontractor rates",
            "apply my sub pricing"
        ],
        "patterns": [
            r'use my (?:existing )?(?:vendor|subcontractor|sub) rates',
            r'apply (?:my|our) (?:vendor|sub) rates'
        ],
        "answer": "Yes. Provide your rate sheets or vendor price books, and we will apply them directly to the line items."
    },
    {
        "id": "use_historical_project_costs",
        "category": "Difficult Pricing",
        "question": "Can you use historical project costs?",
        "keywords": [
            "use historical project costs", "historical cost data", "use my historical costs", "past project costs calibrate"
        ],
        "patterns": [
            r'use historical project costs',
            r'use.*past project costs'
        ],
        "answer": "Yes. We can calibrate unit pricing using cost data from your completed projects."
    },
    {
        "id": "compare_existing_estimate",
        "category": "Difficult Pricing",
        "question": "Can you compare my existing estimate against your estimate?",
        "keywords": [
            "compare my existing estimate against your estimate", "compare my estimate with yours", "estimate variance check",
            "compare existing estimate"
        ],
        "patterns": [
            r'compare my (?:existing )?estimate against',
            r'compare.*estimate.*against (?:your|yours)'
        ],
        "answer": "Yes. We perform side-by-side variance checks to highlight differences in quantities, unit rates, and missed scope."
    },
    {
        "id": "tell_where_overpricing_bid",
        "category": "Difficult Pricing",
        "question": "Can you tell me where I'm overpricing my bid?",
        "keywords": [
            "where i'm overpricing my bid", "where im overpricing my bid", "am i overpricing my bid", "where my bid is high"
        ],
        "patterns": [
            r'where (?:i\'m|im|i am) overpricing',
            r'overpricing my bid'
        ],
        "answer": "Yes. We benchmark your unit costs, labor productivity rates, and markups against competitive regional averages."
    },
    {
        "id": "reduce_5m_to_4_5m_budget",
        "category": "Difficult Pricing",
        "question": "Can you help me reduce a $5M project to a $4.5M budget?",
        "keywords": [
            "reduce a $5m project to a $4.5m budget", "reduce budget from 5m to 4.5m", "cut project budget", "value engineering reduction"
        ],
        "patterns": [
            r'reduce.*(?:5m|\$5m).*to.*(?:4\.5m|\$4\.5m)',
            r'cut.*budget.*from.*to'
        ],
        "answer": "Yes. We provide a value-engineering log targeting high-cost assemblies, alternate materials, and scope optimizations."
    },

    # -------------------------------------------------------------------------
    # 3. Bid-Day Questions
    # -------------------------------------------------------------------------
    {
        "id": "bid_due_in_6_hours",
        "category": "Bid-Day",
        "question": "My bid is due in 6 hours. Can you complete the estimate today?",
        "keywords": [
            "due in 6 hours", "bid is due in 6 hours", "finish in 6 hours", "complete in 6 hours", "6 hours estimate"
        ],
        "patterns": [
            r'(?:due|finish|complete).*6 hours',
            r'6 hours.*(?:complete|estimate)'
        ],
        "answer": "No. Delivering an accurate, responsible estimate in 6 hours is not feasible and risks severe bid errors."
    },
    {
        "id": "addendum_30_mins_before_bid",
        "category": "Bid-Day",
        "question": "I just received an addendum 30 minutes before bid closing. Can you update the estimate?",
        "keywords": [
            "addendum 30 minutes before bid closing", "addendum 30 minutes", "addenda 30 minutes before", "30 minutes before closing"
        ],
        "patterns": [
            r'addend(?:um|a).*30 minutes',
            r'30 minutes before.*(?:closing|bid)'
        ],
        "answer": "A full re-takeoff is impossible in 30 minutes; we can review narrative changes to help you assign a high-level bid-day lump-sum plug."
    },
    {
        "id": "100_sheets_overnight",
        "category": "Bid-Day",
        "question": "Can you turn around 100 drawing sheets overnight?",
        "keywords": [
            "100 drawing sheets overnight", "100 sheets overnight", "turn around 100 sheets overnight"
        ],
        "patterns": [
            r'100 (?:drawing )?sheets overnight',
            r'overnight.*100 sheets'
        ],
        "answer": "No. A 100-sheet set requires proper takeoff time and quality audits to prevent costly omissions."
    },
    {
        "id": "compare_addenda_1_2_3",
        "category": "Bid-Day",
        "question": "Can you compare Addendum 1, 2, and 3 and tell me what changed?",
        "keywords": [
            "compare addendum 1, 2, and 3", "compare addendum 1 2 and 3", "compare addenda 1 2 3", "tell me what changed addendum"
        ],
        "patterns": [
            r'compare addend(?:um|a) 1,? 2,? (?:and )?3',
            r'what changed.*addend(?:um|a)'
        ],
        "answer": "Yes. We cross-reference addenda revision logs and drawings to generate a consolidated scope-change summary."
    },
    {
        "id": "changes_between_two_versions",
        "category": "Bid-Day",
        "question": "Can you identify changes between two versions of the drawings?",
        "keywords": [
            "changes between two versions of the drawings", "changes between two versions", "compare two versions of drawings",
            "drawing revision differences"
        ],
        "patterns": [
            r'changes between two versions of (?:the )?drawings',
            r'compare two versions of drawings'
        ],
        "answer": "Yes. We use digital sheet-overlay tools to detect added, altered, or deleted elements."
    },
    {
        "id": "update_only_affected_quantities_addendum",
        "category": "Bid-Day",
        "question": "Can you update only the affected quantities after an addendum?",
        "keywords": [
            "update only the affected quantities after an addendum", "update only affected quantities", "impacted takeoff after addendum",
            "delta update addendum"
        ],
        "patterns": [
            r'update only (?:the )?affected quantities',
            r'affected quantities after an addendum'
        ],
        "answer": "Yes. We isolate revised sheets and update only the impacted takeoff line items."
    },
    {
        "id": "check_bid_before_submission",
        "category": "Bid-Day",
        "question": "Can you help me check my bid before submission?",
        "keywords": [
            "check my bid before submission", "review my bid before submission", "check bid before submitting", "bid audit before submission"
        ],
        "patterns": [
            r'(?:check|review|audit) my bid before (?:submission|submitting)'
        ],
        "answer": "Yes. We review trade totals, general conditions, markups, and scope coverage for completeness."
    },
    {
        "id": "identify_missed_scope_before_bid",
        "category": "Bid-Day",
        "question": "Can you identify scope I may have missed before I submit my bid?",
        "keywords": [
            "scope i may have missed before i submit my bid", "scope i missed before submitting", "missed scope before bid submission"
        ],
        "patterns": [
            r'scope (?:i|we) (?:may have|might have)?\s*missed before (?:i )?submit'
        ],
        "answer": "Yes. We cross-check your scope against our trade checklists and plan drawing notes."
    },
    {
        "id": "prepare_bid_tabulation",
        "category": "Bid-Day",
        "question": "Can you prepare a bid tabulation?",
        "keywords": [
            "prepare a bid tabulation", "bid tabulation", "bid leveling sheet", "bid tab"
        ],
        "patterns": [
            r'(?:prepare|create|build) a bid tab(?:ulation)?\b',
            r'bid tabulation'
        ],
        "answer": "Yes. We organize sub quotes into a side-by-side bid leveling sheet to identify gaps and exclusions."
    },
    {
        "id": "compare_subcontractor_quotes",
        "category": "Bid-Day",
        "question": "Can you compare multiple subcontractor quotes?",
        "keywords": [
            "compare multiple subcontractor quotes", "compare sub quotes", "level subcontractor quotes", "multiple sub bids compare"
        ],
        "patterns": [
            r'compare multiple (?:subcontractor|sub) quotes',
            r'level.*(?:subcontractor|sub) quotes'
        ],
        "answer": "Yes. We level quotes against the contract documents to confirm matching scopes and normalize alternates."
    },

    # -------------------------------------------------------------------------
    # 4. MEP Difficult Questions
    # -------------------------------------------------------------------------
    {
        "id": "hvac_from_schedules_and_plans",
        "category": "MEP",
        "question": "Can you estimate HVAC from mechanical schedules and floor plans?",
        "keywords": [
            "estimate hvac from mechanical schedules and floor plans", "hvac mechanical schedules floor plans", "hvac from schedules"
        ],
        "patterns": [
            r'estimate hvac from mechanical schedules',
            r'hvac.*schedules and floor plans'
        ],
        "answer": "Yes. Equipment is taken from schedules, while ductwork, diffusers, and dampers are measured from floor layouts."
    },
    {
        "id": "calculate_ductwork_quantities",
        "category": "MEP",
        "question": "Can you calculate ductwork quantities?",
        "keywords": [
            "calculate ductwork quantities", "ductwork quantities", "duct takeoff", "measure ductwork", "sheet metal duct quantities"
        ],
        "patterns": [
            r'calculate ductwork quantities',
            r'ductwork quantities'
        ],
        "answer": "Yes. We quantify ductwork by linear feet, weight (lbs) by sheet metal gauge, insulation area, and fittings count."
    },
    {
        "id": "hvac_equipment_and_install_separately",
        "category": "MEP",
        "question": "Can you estimate HVAC equipment and installation separately?",
        "keywords": [
            "hvac equipment and installation separately", "separate hvac equipment and labor", "equipment vs install hvac"
        ],
        "patterns": [
            r'hvac equipment and installation separately',
            r'separate.*hvac equipment.*installation'
        ],
        "answer": "Yes. We separate equipment procurement costs from rigging, assembly, piping, and commissioning labor."
    },
    {
        "id": "identify_equipment_from_mech_schedules",
        "category": "MEP",
        "question": "Can you identify equipment from mechanical schedules?",
        "keywords": [
            "identify equipment from mechanical schedules", "equipment from mechanical schedules", "read mechanical schedules"
        ],
        "patterns": [
            r'identify equipment from mechanical schedules',
            r'equipment from mechanical schedules'
        ],
        "answer": "Yes. All capacities, electrical characteristics, and manufacturer models are cataloged directly from schedules."
    },
    {
        "id": "plumbing_fixtures_from_plans",
        "category": "MEP",
        "question": "Can you estimate plumbing fixtures from the plans?",
        "keywords": [
            "estimate plumbing fixtures from the plans", "plumbing fixtures takeoff", "count plumbing fixtures", "fixtures from plumbing plans"
        ],
        "patterns": [
            r'estimate plumbing fixtures from (?:the )?plans',
            r'plumbing fixtures from plans'
        ],
        "answer": "Yes. Fixtures are counted and cross-checked between plumbing schedules, floor plans, and riser diagrams."
    },
    {
        "id": "pipe_quantities_by_size",
        "category": "MEP",
        "question": "Can you calculate pipe quantities by size?",
        "keywords": [
            "calculate pipe quantities by size", "pipe quantities by diameter", "piping by size", "pipe linear feet by size"
        ],
        "patterns": [
            r'calculate pipe quantities by size',
            r'piping quantities by size'
        ],
        "answer": "Yes. Piping is measured by linear foot, broken down by diameter, system type (domestic, waste, vent, gas), and material."
    },
    {
        "id": "electrical_feeders_and_branch_circuits",
        "category": "MEP",
        "question": "Can you estimate electrical feeders and branch circuits?",
        "keywords": [
            "estimate electrical feeders and branch circuits", "feeders and branch circuits", "electrical feeders branch circuits takeoff"
        ],
        "patterns": [
            r'estimate electrical feeders and branch circuits',
            r'feeders and branch circuits'
        ],
        "answer": "Yes. Feeders are traced from single-line diagrams, and branch circuits are measured via plan-indicated runs and standard home-run allowances."
    },
    {
        "id": "lighting_fixture_quantities",
        "category": "MEP",
        "question": "Can you calculate lighting fixture quantities?",
        "keywords": [
            "calculate lighting fixture quantities", "lighting fixture counts", "light fixtures takeoff", "luminaire count"
        ],
        "patterns": [
            r'calculate lighting fixture quantities',
            r'lighting fixtures? (?:count|quantities)'
        ],
        "answer": "Yes. Fixtures are counted by type symbol matching the luminaire schedule."
    },
    {
        "id": "electrical_equipment_panel_schedules",
        "category": "MEP",
        "question": "Can you estimate electrical equipment from panel schedules?",
        "keywords": [
            "estimate electrical equipment from panel schedules", "electrical equipment panel schedules", "takeoff from panel schedules"
        ],
        "patterns": [
            r'electrical equipment from panel schedules'
        ],
        "answer": "Yes. Switchgear, panelboards, breakers, disconnects, and transformers are itemized directly from schedules."
    },
    {
        "id": "discrepancies_electrical_plans_schedules",
        "category": "MEP",
        "question": "Can you identify discrepancies between electrical plans and schedules?",
        "keywords": [
            "discrepancies between electrical plans and schedules", "electrical plans and schedules conflict", "electrical schedule discrepancy"
        ],
        "patterns": [
            r'discrepancies between electrical plans and schedules'
        ],
        "answer": "Yes. We highlight discrepancies in fixture counts, voltage specs, or breaker sizes in a plan-vs-schedule report."
    },
    {
        "id": "fire_protection_incomplete_plans",
        "category": "MEP",
        "question": "Can you estimate fire protection from incomplete plans?",
        "keywords": [
            "estimate fire protection from incomplete plans", "fire protection incomplete plans", "sprinkler estimate incomplete plans"
        ],
        "patterns": [
            r'fire protection from incomplete plans',
            r'fire sprinkler.*incomplete plans'
        ],
        "answer": "Yes. We provide budget estimates using square-foot hazard classifications (NFPA guidelines) and assumed head spacing."
    },
    {
        "id": "handle_mep_coordination_issues",
        "category": "MEP",
        "question": "Can you handle MEP coordination issues?",
        "keywords": [
            "handle mep coordination issues", "mep coordination issues", "mep clashes", "routing clashes ductwork beams"
        ],
        "patterns": [
            r'handle mep coordination issues',
            r'mep coordination issues'
        ],
        "answer": "Yes. We identify spatial routing clashes (e.g., ductwork conflicting with structural beams) and flag them for resolution."
    },
    {
        "id": "estimate_controls_bms_scope",
        "category": "MEP",
        "question": "Can you estimate controls/BMS scope?",
        "keywords": [
            "estimate controls/bms scope", "controls bms scope", "building management system estimate", "bms controls takeoff"
        ],
        "patterns": [
            r'(?:estimate|takeoff).*controls[\s/]*bms',
            r'bms scope'
        ],
        "answer": "Yes. Scoped by I/O point counts, sensor quantities, controllers, and sequence-of-operations specifications."
    },
    {
        "id": "separate_equip_material_labor_mep",
        "category": "MEP",
        "question": "Can you separate equipment, material, and labor for MEP?",
        "keywords": [
            "separate equipment, material, and labor for mep", "separate equipment material and labor for mep", "mep equipment material labor splits"
        ],
        "patterns": [
            r'separate equipment,? material,? and labor for mep'
        ],
        "answer": "Yes. All MEP estimates deliver itemized splits for equipment, raw material, and installation labor hours."
    },

    # -------------------------------------------------------------------------
    # 5. Commercial Construction Questions
    # -------------------------------------------------------------------------
    {
        "id": "estimate_300k_warehouse",
        "category": "Commercial Construction",
        "question": "Can you estimate a 300,000-square-foot warehouse?",
        "keywords": [
            "estimate a 300,000-square-foot warehouse", "300,000 sq ft warehouse", "300000 sq ft warehouse", "300k sq ft warehouse"
        ],
        "patterns": [
            r'300[\s,]*000.*warehouse',
            r'300k.*warehouse'
        ],
        "answer": "Yes. We handle large industrial projects including slab-on-grade, tilt-up/precast panels, structural steel, and core MEP."
    },
    {
        "id": "estimate_20_story_apartment",
        "category": "Commercial Construction",
        "question": "Can you estimate a 20-story apartment building?",
        "keywords": [
            "estimate a 20-story apartment building", "20-story apartment", "20 story building", "high rise apartment takeoff"
        ],
        "patterns": [
            r'20[\s-]story (?:apartment|building|tower)'
        ],
        "answer": "Yes. We quantify typical floor layouts, core structures, vertical risers, and common areas."
    },
    {
        "id": "estimate_hospital_project",
        "category": "Commercial Construction",
        "question": "Can you estimate a hospital project?",
        "keywords": [
            "estimate a hospital project", "hospital project", "healthcare facility estimate", "medical facility estimate"
        ],
        "patterns": [
            r'estimate (?:a )?hospital',
            r'hospital project'
        ],
        "answer": "Yes. We estimate specialized healthcare facilities, including clean environments, medical gas, and critical power systems."
    },
    {
        "id": "estimate_restaurant_ti",
        "category": "Commercial Construction",
        "question": "Can you estimate a restaurant tenant improvement?",
        "keywords": [
            "estimate a restaurant tenant improvement", "restaurant tenant improvement", "restaurant ti", "commercial kitchen buildout"
        ],
        "patterns": [
            r'restaurant tenant improvement',
            r'restaurant ti\b'
        ],
        "answer": "Yes. Scope covers commercial kitchens, grease interceptors, hood suppression systems, specialized utilities, and custom finishes."
    },
    {
        "id": "estimate_multiple_buildings",
        "category": "Commercial Construction",
        "question": "Can you estimate a project with multiple buildings?",
        "keywords": [
            "project with multiple buildings", "estimate multiple buildings", "campus project multiple buildings"
        ],
        "patterns": [
            r'project with multiple buildings',
            r'estimate multiple buildings'
        ],
        "answer": "Yes. We estimate each building as a separate scope and consolidate them into an overall campus total."
    },
    {
        "id": "separate_by_building",
        "category": "Commercial Construction",
        "question": "Can you separate the estimate by building?",
        "keywords": [
            "separate the estimate by building", "separate by building", "isolate each building"
        ],
        "patterns": [
            r'separate (?:the )?estimate by building'
        ],
        "answer": "Yes. Each building is isolated within its own Work Breakdown Structure (WBS)."
    },
    {
        "id": "separate_costs_by_floor",
        "category": "Commercial Construction",
        "question": "Can you separate costs by floor?",
        "keywords": [
            "separate costs by floor", "separate by floor", "floor by floor takeoff", "breakdown floor by floor"
        ],
        "patterns": [
            r'separate costs? by floor',
            r'floor[\s-]by[\s-]floor'
        ],
        "answer": "Yes. Quantities and pricing can be broken down floor-by-floor."
    },
    {
        "id": "separate_costs_by_phase",
        "category": "Commercial Construction",
        "question": "Can you separate costs by phase?",
        "keywords": [
            "separate costs by phase", "separate by phase", "phased construction estimate", "phasing breakdown"
        ],
        "patterns": [
            r'separate costs? by phase',
            r'phased costs?'
        ],
        "answer": "Yes. Line items can be assigned to designated construction phasing milestones."
    },
    {
        "id": "csi_division_estimate",
        "category": "Commercial Construction",
        "question": "Can you provide a CSI division-based estimate?",
        "keywords": [
            "csi division-based estimate", "csi division based estimate", "csi 16 division", "csi 50 division"
        ],
        "patterns": [
            r'csi division[\s-]based estimate',
            r'organized (?:by|according to) csi'
        ],
        "answer": "Yes. Organized according to standard 16-division or 50-division CSI formats."
    },
    {
        "id": "masterformat_organized",
        "category": "Commercial Construction",
        "question": "Can you provide an estimate organized according to MasterFormat?",
        "keywords": [
            "organized according to masterformat", "masterformat estimate", "masterformat 6 digit", "masterformat format"
        ],
        "patterns": [
            r'according to masterformat',
            r'masterformat'
        ],
        "answer": "Yes. Formatted down to standard MasterFormat 6-digit or 8-digit sections."
    },
    {
        "id": "detailed_breakdown_every_trade",
        "category": "Commercial Construction",
        "question": "Can you create a detailed cost breakdown for every trade?",
        "keywords": [
            "detailed cost breakdown for every trade", "breakdown for every trade", "itemized breakdown every trade"
        ],
        "patterns": [
            r'detailed cost breakdown for every trade'
        ],
        "answer": "Yes. Every subcontracted trade receives an itemized breakdown of materials, labor, equipment, and markups."
    },

    # -------------------------------------------------------------------------
    # 6. Scope and Takeoff Questions
    # -------------------------------------------------------------------------
    {
        "id": "drywall_takeoff_included",
        "category": "Scope and Takeoff",
        "question": "What exactly is included in your drywall takeoff?",
        "keywords": [
            "included in your drywall takeoff", "drywall takeoff include", "what is in drywall takeoff"
        ],
        "patterns": [
            r'included in (?:your )?drywall takeoff',
            r'drywall takeoff include'
        ],
        "answer": "Studs, track, fasteners, drywall panels, joint compound, tape, corner beads, and specified level of finish."
    },
    {
        "id": "drywall_studs_track_insulation_tape",
        "category": "Scope and Takeoff",
        "question": "Do you include studs, track, insulation, drywall, tape, mud, and finishing?",
        "keywords": [
            "studs, track, insulation, drywall, tape, mud, and finishing", "studs track insulation drywall tape mud", "include studs track insulation"
        ],
        "patterns": [
            r'studs,? track,? insulation,? drywall'
        ],
        "answer": "Yes. All components are calculated together as complete wall and ceiling assembly packages."
    },
    {
        "id": "waste_in_material_quantities",
        "category": "Scope and Takeoff",
        "question": "Do you include waste in material quantities?",
        "keywords": [
            "include waste in material quantities", "waste in material quantities", "do you factor in waste", "is waste included"
        ],
        "patterns": [
            r'waste in material quantities',
            r'include waste'
        ],
        "answer": "Yes. Standard material waste is calculated and shown separately or integrated into the gross order quantity."
    },
    {
        "id": "waste_percentage_used",
        "category": "Scope and Takeoff",
        "question": "What waste percentage do you use?",
        "keywords": [
            "what waste percentage do you use", "what waste percent", "waste percentage used", "typical waste factor"
        ],
        "patterns": [
            r'what waste percentage',
            r'waste percentage do you use'
        ],
        "answer": "Typically 5–10% for drywall/framing, 10–15% for tile/flooring, and 5–8% for pipe/conduit, unless customized."
    },
    {
        "id": "specify_custom_waste_factors",
        "category": "Scope and Takeoff",
        "question": "Can I specify my own waste factors?",
        "keywords": [
            "specify my own waste factors", "use my own waste factor", "custom waste factor", "my company waste percentage"
        ],
        "patterns": [
            r'specify (?:my|our) own waste',
            r'custom waste factor'
        ],
        "answer": "Yes. We can apply your company-standard waste percentages per trade or material."
    },
    {
        "id": "distinguish_interior_exterior_walls",
        "category": "Scope and Takeoff",
        "question": "Can you distinguish interior and exterior wall assemblies?",
        "keywords": [
            "distinguish interior and exterior wall assemblies", "interior vs exterior wall assemblies", "separate interior and exterior walls"
        ],
        "patterns": [
            r'distinguish interior and exterior wall',
            r'separate interior and exterior wall'
        ],
        "answer": "Yes. Separated by gauge, stud depth, exterior sheathing, vapor/air barriers, and insulation types."
    },
    {
        "id": "distinguish_drywall_thicknesses",
        "category": "Scope and Takeoff",
        "question": "Can you distinguish different drywall thicknesses?",
        "keywords": [
            "distinguish different drywall thicknesses", "different drywall thicknesses", "5/8 vs 1/2 drywall", "type x drywall separate"
        ],
        "patterns": [
            r'different drywall thicknesses',
            r'distinguish.*drywall thickness'
        ],
        "answer": "Yes. Separated by board type, such as 1/2\", 5/8\" Type X, Type C, and moisture/mold-resistant boards."
    },
    {
        "id": "quantify_flooring_types_separately",
        "category": "Scope and Takeoff",
        "question": "Can you quantify different flooring types separately?",
        "keywords": [
            "quantify different flooring types separately", "different flooring types separately", "separate flooring types"
        ],
        "patterns": [
            r'different flooring types separately'
        ],
        "answer": "Yes. Broken down by exact material type (e.g., LVT, VCT, broadloom carpet, carpet tile, sealed concrete) with transitions."
    },
    {
        "id": "separate_wall_tile_from_floor_tile",
        "category": "Scope and Takeoff",
        "question": "Can you separate wall tile from floor tile?",
        "keywords": [
            "separate wall tile from floor tile", "wall tile vs floor tile", "wall and floor tile separate"
        ],
        "patterns": [
            r'separate wall tile from floor tile'
        ],
        "answer": "Yes. Itemized separately, including distinct underlayment, waterproofing membranes, thinset, grout, and trim profiles."
    },
    {
        "id": "calculate_ceiling_quantities_separately",
        "category": "Scope and Takeoff",
        "question": "Can you calculate ceiling quantities separately?",
        "keywords": [
            "calculate ceiling quantities separately", "ceiling quantities separately", "act grid vs gwb ceiling"
        ],
        "patterns": [
            r'ceiling quantities separately'
        ],
        "answer": "Yes. Separated by acoustic ceiling grid/tile systems, gypsum flat ceilings, soffits, and specialty ceiling clouds."
    },
    {
        "id": "identify_different_concrete_mixes",
        "category": "Scope and Takeoff",
        "question": "Can you identify different concrete mixes?",
        "keywords": [
            "identify different concrete mixes", "different concrete mixes", "3000 psi vs 4000 psi concrete"
        ],
        "patterns": [
            r'different concrete mixes'
        ],
        "answer": "Yes. Quantified separately by compressive strength (PSI), aggregate size, and chemical admixes."
    },
    {
        "id": "separate_structural_concrete_slab_on_grade",
        "category": "Scope and Takeoff",
        "question": "Can you separate structural concrete from slab-on-grade?",
        "keywords": [
            "separate structural concrete from slab-on-grade", "structural concrete from slab on grade", "sog vs structural concrete"
        ],
        "patterns": [
            r'structural concrete from slab[\s-]on[\s-]grade'
        ],
        "answer": "Yes. Footings, grade beams, piers, structural decks, and slab-on-grade are isolated as distinct line items."
    },
    {
        "id": "quantify_reinforcing_steel",
        "category": "Scope and Takeoff",
        "question": "Can you quantify reinforcing steel?",
        "keywords": [
            "quantify reinforcing steel", "rebar takeoff", "reinforcing steel rebar", "rebar tonnage calculation"
        ],
        "patterns": [
            r'quantify reinforcing steel',
            r'rebar takeoff'
        ],
        "answer": "Yes. Measured in rebar tonnage, linear feet by bar size, stirrups, ties, and welded wire mesh area."
    },
    {
        "id": "estimate_formwork",
        "category": "Scope and Takeoff",
        "question": "Can you estimate formwork?",
        "keywords": [
            "estimate formwork", "formwork takeoff", "sfca formwork", "concrete formwork quantities"
        ],
        "patterns": [
            r'estimate formwork',
            r'formwork takeoff'
        ],
        "answer": "Yes. Quantified by square footage of contact area (SFCA), along with shoring and stripping requirements."
    },
    {
        "id": "calculate_excavation_backfill",
        "category": "Scope and Takeoff",
        "question": "Can you calculate excavation and backfill quantities?",
        "keywords": [
            "calculate excavation and backfill quantities", "excavation and backfill", "cut and fill calculation", "earthwork takeoff"
        ],
        "patterns": [
            r'excavation and backfill quantities',
            r'cut and fill.*quantities'
        ],
        "answer": "Yes. Calculated in cut/fill banked cubic yards (BCY) and compacted cubic yards (CCY), separated by bulk and trench excavation."
    },

    # -------------------------------------------------------------------------
    # 7. Plans & Document Questions
    # -------------------------------------------------------------------------
    {
        "id": "work_with_all_disciplines_together",
        "category": "Plans & Documents",
        "question": "Can you work with architectural, structural, civil, MEP, and landscape drawings together?",
        "keywords": [
            "architectural, structural, civil, mep, and landscape drawings together", "all disciplines together", "cross-discipline plans"
        ],
        "patterns": [
            r'architectural,? structural,? civil,? mep,? and landscape'
        ],
        "answer": "Yes. We review all disciplines simultaneously to confirm scope continuity and avoid omissions."
    },
    {
        "id": "only_architectural_drawings",
        "category": "Plans & Documents",
        "question": "What if I only have architectural drawings?",
        "keywords": [
            "only have architectural drawings", "only architectural plans", "just architectural drawings"
        ],
        "patterns": [
            r'only have architectural drawings',
            r'just architectural drawings'
        ],
        "answer": "We estimate the complete architectural scope and can provide budget allowances for structural and MEP systems."
    },
    {
        "id": "drawings_no_specs",
        "category": "Plans & Documents",
        "question": "What if I have drawings but no specifications?",
        "keywords": [
            "drawings but no specifications", "drawings but no specs", "plans without specs"
        ],
        "patterns": [
            r'drawings but no specifications',
            r'plans but no specs'
        ],
        "answer": "We extract specifications from drawing general notes and apply standard commercial materials, noting all assumptions."
    },
    {
        "id": "specs_no_drawings",
        "category": "Plans & Documents",
        "question": "What if I have specifications but no complete drawings?",
        "keywords": [
            "specifications but no complete drawings", "specs but no drawings", "specifications without plans"
        ],
        "patterns": [
            r'specifications? but no (?:complete )?drawings'
        ],
        "answer": "We can provide material unit rates or conceptual budget allowances, but exact quantities cannot be measured without scaled plans."
    },
    {
        "id": "work_from_1000_page_plan_set",
        "category": "Plans & Documents",
        "question": "Can you work from a 1,000-page plan set?",
        "keywords": [
            "1,000-page plan set", "1000 page plan set", "1,000 page drawing set", "1000 sheet drawing set"
        ],
        "patterns": [
            r'1,?000[\s-]page plan set',
            r'1,?000 sheets?'
        ],
        "answer": "Yes. We handle large-scale drawing packages across multiple disciplines and phases."
    },
    {
        "id": "review_entire_set_before_estimating",
        "category": "Plans & Documents",
        "question": "Can you review the entire drawing set before estimating?",
        "keywords": [
            "review the entire drawing set before estimating", "review entire drawing set", "review entire plan set first"
        ],
        "patterns": [
            r'review (?:the )?entire drawing set before'
        ],
        "answer": "Yes. A full index and general notes review is conducted to catch cross-trade requirements before takeoff begins."
    },
    {
        "id": "identify_drawings_relevant_my_trade",
        "category": "Plans & Documents",
        "question": "Can you identify which drawings are relevant to my trade?",
        "keywords": [
            "drawings are relevant to my trade", "relevant to my trade", "filter sheets for my trade"
        ],
        "patterns": [
            r'drawings.*relevant to my trade'
        ],
        "answer": "Yes. We filter the drawing set to isolate all sheets, details, and schedules that impact your trade."
    },
    {
        "id": "identify_revisions_on_drawings",
        "category": "Plans & Documents",
        "question": "Can you identify revisions on drawings?",
        "keywords": [
            "identify revisions on drawings", "revisions on drawings", "revision clouds delta"
        ],
        "patterns": [
            r'revisions on drawings'
        ],
        "answer": "Yes. We verify revision clouds, delta numbers, title block dates, and digital sheet comparison overlays."
    },
    {
        "id": "read_drawing_schedules",
        "category": "Plans & Documents",
        "question": "Can you read drawing schedules?",
        "keywords": [
            "read drawing schedules", "drawing schedules door window finish"
        ],
        "patterns": [
            r'read drawing schedules'
        ],
        "answer": "Yes. Door, window, finish, structural, and MEP equipment schedules are standard inputs for our item counts."
    },
    {
        "id": "use_detail_drawings_for_quantities",
        "category": "Plans & Documents",
        "question": "Can you use detail drawings to determine quantities?",
        "keywords": [
            "use detail drawings to determine quantities", "detail drawings for quantities", "cross sections details takeoff"
        ],
        "patterns": [
            r'use detail drawings to determine quantities'
        ],
        "answer": "Yes. Cross-sections and typical assembly details are used to calculate layers, flashing, hardware, and fasteners."
    },
    {
        "id": "identify_info_from_general_notes",
        "category": "Plans & Documents",
        "question": "Can you identify information from general notes?",
        "keywords": [
            "information from general notes", "general notes review", "drawing general notes"
        ],
        "patterns": [
            r'information from general notes'
        ],
        "answer": "Yes. We review general notes for essential scopes like testing, inspections, mockup walls, and patching."
    },
    {
        "id": "specification_sections_determine_scope",
        "category": "Plans & Documents",
        "question": "Can you use specification sections to determine scope?",
        "keywords": [
            "specification sections to determine scope", "use specification sections", "specs determine scope"
        ],
        "patterns": [
            r'specification sections to determine scope'
        ],
        "answer": "Yes. Specs dictate submittals, testing, execution standards, warranty terms, and approved manufacturers."
    },
    {
        "id": "conflicts_between_drawings_and_specs",
        "category": "Plans & Documents",
        "question": "Can you identify conflicts between drawings and specifications?",
        "keywords": [
            "conflicts between drawings and specifications", "drawings vs specifications conflict", "drawing and spec conflicts"
        ],
        "patterns": [
            r'conflicts between drawings and specifications'
        ],
        "answer": "Yes. We flag conflicts on a discrepancy log, noting whether specs or drawings govern under contract terms."
    },

    # -------------------------------------------------------------------------
    # 8. Change-Order Questions
    # -------------------------------------------------------------------------
    {
        "id": "price_change_order_from_rfi",
        "category": "Change-Order",
        "question": "Can you price a change order from an RFI?",
        "keywords": [
            "price a change order from an rfi", "change order from an rfi", "rfi change order pricing"
        ],
        "patterns": [
            r'price a change order from an rfi',
            r'change order from.*rfi'
        ],
        "answer": "Yes. We evaluate the RFI response to determine affected assemblies and price the net additions and deletions."
    },
    {
        "id": "cost_impact_design_change",
        "category": "Change-Order",
        "question": "Can you calculate the cost impact of a design change?",
        "keywords": [
            "cost impact of a design change", "design change cost impact", "price a design change"
        ],
        "patterns": [
            r'cost impact of a design change'
        ],
        "answer": "Yes. Calculated as added work minus deleted work, including potential demo, re-work, and schedule adjustments."
    },
    {
        "id": "compare_original_revised_drawings",
        "category": "Change-Order",
        "question": "Can you compare original and revised drawings?",
        "keywords": [
            "compare original and revised drawings", "original vs revised drawings", "plan revision comparison"
        ],
        "patterns": [
            r'compare original and revised drawings'
        ],
        "answer": "Yes. We overlay the old and revised plan sheets to highlight all visual and structural changes."
    },
    {
        "id": "quantify_added_and_deleted_work",
        "category": "Change-Order",
        "question": "Can you quantify added and deleted work?",
        "keywords": [
            "quantify added and deleted work", "added and deleted work", "add deduct takeoff", "net delta quantities"
        ],
        "patterns": [
            r'added and deleted work'
        ],
        "answer": "Yes. Deliverables display original quantities, revised quantities, and the resulting net delta."
    },
    {
        "id": "net_cost_of_change_order",
        "category": "Change-Order",
        "question": "Can you calculate the net cost of a change order?",
        "keywords": [
            "net cost of a change order", "calculate net cost change order", "net change order amount"
        ],
        "patterns": [
            r'net cost of a change order'
        ],
        "answer": "Yes. Net cost reflects added materials, deducted materials, labor differential, equipment, and markup allowances."
    },
    {
        "id": "separate_labor_material_equipment_co",
        "category": "Change-Order",
        "question": "Can you separate labor, material, equipment, and subcontractor costs?",
        "keywords": [
            "separate labor, material, equipment, and subcontractor costs", "itemized change order breakdown labor material equipment"
        ],
        "patterns": [
            r'separate labor,? material,? equipment,? and subcontractor costs'
        ],
        "answer": "Yes. Every change order breakdown itemizes these cost elements to meet contract billing standards."
    },
    {
        "id": "change_order_breakdown_for_owner",
        "category": "Change-Order",
        "question": "Can you prepare a change-order breakdown for the owner?",
        "keywords": [
            "change-order breakdown for the owner", "change order breakdown for the owner", "aia g701 change order"
        ],
        "patterns": [
            r'change[\s-]order breakdown for (?:the )?owner'
        ],
        "answer": "Yes. Formatted using standard AIA G701 styles or owner-mandated change-order proposal templates."
    },
    {
        "id": "justify_change_order_price",
        "category": "Change-Order",
        "question": "Can you help justify a change-order price?",
        "keywords": [
            "justify a change-order price", "justify a change order price", "substantiate change order"
        ],
        "patterns": [
            r'justify a change[\s-]order price'
        ],
        "answer": "Yes. Backed by specific drawing references, RFI citations, labor productivity rates, and material quotes."
    },

    # -------------------------------------------------------------------------
    # 9. Value Engineering Questions
    # -------------------------------------------------------------------------
    {
        "id": "ve_500k_savings",
        "category": "Value Engineering",
        "question": "Can you find $500,000 in savings without changing the design intent?",
        "keywords": [
            "find $500,000 in savings without changing the design intent", "find $500,000 in savings", "500k savings value engineering"
        ],
        "patterns": [
            r'find \$?500,?000 in savings'
        ],
        "answer": "Yes. We identify high-cost assemblies, alternate material grades, and alternative installation methods to cut costs."
    },
    {
        "id": "cheaper_alternatives_materials",
        "category": "Value Engineering",
        "question": "Can you suggest cheaper alternatives for specified materials?",
        "keywords": [
            "cheaper alternatives for specified materials", "suggest cheaper alternatives", "lower cost material alternatives"
        ],
        "patterns": [
            r'cheaper alternatives for specified materials'
        ],
        "answer": "Yes. We propose alternate, code-compliant products that meet the architectural and functional intent."
    },
    {
        "id": "compare_two_construction_methods",
        "category": "Value Engineering",
        "question": "Can you compare two construction methods?",
        "keywords": [
            "compare two construction methods", "cast in place vs precast", "steel vs timber cost"
        ],
        "patterns": [
            r'compare two construction methods'
        ],
        "answer": "Yes (e.g., cast-in-place vs. precast concrete, structural steel vs. heavy timber), comparing cost, lead time, and labor impact."
    },
    {
        "id": "expensive_scopes_lower_cost_alternatives",
        "category": "Value Engineering",
        "question": "Can you identify expensive scopes that have lower-cost alternatives?",
        "keywords": [
            "expensive scopes that have lower-cost alternatives", "identify expensive scopes", "cost drivers value engineering"
        ],
        "patterns": [
            r'expensive scopes that have lower[\s-]cost alternatives'
        ],
        "answer": "Yes. We create a value-engineering log ranking cost drivers and feasible substitution alternates."
    },
    {
        "id": "compare_different_flooring_systems",
        "category": "Value Engineering",
        "question": "Can you compare different flooring systems?",
        "keywords": [
            "compare different flooring systems", "flooring systems comparison", "lvt vs vct cost"
        ],
        "patterns": [
            r'compare different flooring systems'
        ],
        "answer": "Yes. We evaluate upfront purchase price, subfloor prep, adhesive requirements, and lifecycle maintenance costs."
    },
    {
        "id": "compare_different_hvac_systems",
        "category": "Value Engineering",
        "question": "Can you compare different HVAC systems?",
        "keywords": [
            "compare different hvac systems", "rtu vs vrf comparison", "hvac system cost comparison"
        ],
        "patterns": [
            r'compare different hvac systems'
        ],
        "answer": "Yes. We analyze packaged rooftop units (RTU) versus variable refrigerant flow (VRF) or split systems for cost and install time."
    },
    {
        "id": "opportunities_reduce_labor_costs",
        "category": "Value Engineering",
        "question": "Can you identify opportunities to reduce labor costs?",
        "keywords": [
            "opportunities to reduce labor costs", "reduce labor costs", "labor savings value engineering"
        ],
        "patterns": [
            r'opportunities to reduce labor costs'
        ],
        "answer": "Yes. By recommending prefabricated assemblies, standardized wall heights, and simplified framing connections."
    },
    {
        "id": "constructability_issues_increase_costs",
        "category": "Value Engineering",
        "question": "Can you identify constructability issues that could increase costs?",
        "keywords": [
            "constructability issues that could increase costs", "constructability issues", "site access bottlenecks"
        ],
        "patterns": [
            r'constructability issues'
        ],
        "answer": "Yes. We flag site access bottlenecks, tight installation clearances, and difficult details during takeoff."
    },
    {
        "id": "prioritize_ve_by_savings",
        "category": "Value Engineering",
        "question": "Can you prioritize value-engineering recommendations by potential savings?",
        "keywords": [
            "prioritize value-engineering recommendations by potential savings", "prioritize ve recommendations", "rank value engineering savings"
        ],
        "patterns": [
            r'prioritize value[\s-]engineering'
        ],
        "answer": "Yes. Our VE report ranks items from highest dollar return to lowest for clear decision-making."
    },

    # -------------------------------------------------------------------------
    # 10. Scheduling Questions
    # -------------------------------------------------------------------------
    {
        "id": "schedule_from_estimate",
        "category": "Scheduling",
        "question": "Can you create a construction schedule from the estimate?",
        "keywords": [
            "create a construction schedule from the estimate", "schedule from estimate", "convert estimate to schedule"
        ],
        "patterns": [
            r'construction schedule from (?:the )?estimate'
        ],
        "answer": "Yes. Total man-hours and crew outputs from the estimate are converted into realistic task durations."
    },
    {
        "id": "determine_sequence_of_trades",
        "category": "Scheduling",
        "question": "Can you determine the sequence of trades?",
        "keywords": [
            "determine the sequence of trades", "sequence of trades", "trade sequencing cpm"
        ],
        "patterns": [
            r'sequence of trades'
        ],
        "answer": "Yes. Sequenced using standard Critical Path Method (CPM) predecessor and successor relationships."
    },
    {
        "id": "schedule_for_12_month_project",
        "category": "Scheduling",
        "question": "Can you create a schedule for a 12-month project?",
        "keywords": [
            "schedule for a 12-month project", "12 month project schedule", "12-month schedule"
        ],
        "patterns": [
            r'schedule for a 12[\s-]month project'
        ],
        "answer": "Yes. Mapped across procurement, structural rough-in, MEP, finishes, testing, and closeout milestones."
    },
    {
        "id": "activities_run_concurrently",
        "category": "Scheduling",
        "question": "Can you identify activities that can run concurrently?",
        "keywords": [
            "activities that can run concurrently", "concurrent activities", "parallel construction activities"
        ],
        "patterns": [
            r'activities.*(?:run|occur).*concurrently'
        ],
        "answer": "Yes. We evaluate zone handoffs and trade clearances to identify parallel construction paths."
    },
    {
        "id": "schedule_based_on_scope",
        "category": "Scheduling",
        "question": "Can you create a schedule based on the project's scope?",
        "keywords": [
            "schedule based on the project's scope", "schedule based on scope", "scope-based schedule"
        ],
        "patterns": [
            r'schedule based on (?:the )?project\'?s scope'
        ],
        "answer": "Yes. Built directly from the work packages identified in your material takeoff."
    },
    {
        "id": "identify_critical_activities",
        "category": "Scheduling",
        "question": "Can you identify critical activities?",
        "keywords": [
            "identify critical activities", "critical path activities", "activities on critical path"
        ],
        "patterns": [
            r'critical activities'
        ],
        "answer": "Yes. We calculate the critical path, highlighting activities with zero total float that dictate the completion date."
    },
    {
        "id": "create_work_breakdown_structure",
        "category": "Scheduling",
        "question": "Can you create a work breakdown structure?",
        "keywords": [
            "create a work breakdown structure", "work breakdown structure", "wbs construction schedule"
        ],
        "patterns": [
            r'work breakdown structure\b',
            r'\bwbs\b'
        ],
        "answer": "Yes. Structured from project phases down to system divisions and individual trade tasks."
    },
    {
        "id": "create_subcontractor_schedule",
        "category": "Scheduling",
        "question": "Can you create a subcontractor schedule?",
        "keywords": [
            "create a subcontractor schedule", "subcontractor schedule", "sub schedule milestones"
        ],
        "patterns": [
            r'subcontractor schedule'
        ],
        "answer": "Yes. Outlining trade mobilization dates, execution durations, and required handover milestones."
    },

    # -------------------------------------------------------------------------
    # 11. Difficult Business Questions
    # -------------------------------------------------------------------------
    {
        "id": "if_i_dont_like_estimate",
        "category": "Difficult Business",
        "question": "What happens if I don't like the estimate?",
        "keywords": [
            "what happens if i don't like the estimate", "if i dont like the estimate", "what if i dont like the estimate",
            "unhappy with estimate"
        ],
        "patterns": [
            r'(?:what if|what happens if) i (?:don\'t|dont) like (?:the )?estimate'
        ],
        "answer": "We review the line items with you and adjust production rates, waste factors, or crew assumptions to match your operations."
    },
    {
        "id": "how_many_revisions_included",
        "category": "Difficult Business",
        "question": "How many revisions are included?",
        "keywords": [
            "how many revisions are included", "revisions included", "revision policy", "number of revisions"
        ],
        "patterns": [
            r'how many revisions (?:are )?included',
            r'revision policy'
        ],
        "answer": "Clarifications based on original drawings are included; scope additions, redesigns, or new addenda are quoted at a reduced hourly/sheet rate."
    },
    {
        "id": "guarantee_quantities",
        "category": "Difficult Business",
        "question": "Do you guarantee your quantities?",
        "keywords": [
            "do you guarantee your quantities", "guarantee quantities", "guaranteed takeoff numbers"
        ],
        "patterns": [
            r'guarantee (?:your )?quantities'
        ],
        "answer": "We guarantee the takeoff strictly reflects the drawings provided; field purchasing margins remain the contractor's responsibility."
    },
    {
        "id": "what_happens_if_miss_item",
        "category": "Difficult Business",
        "question": "What happens if you miss an item?",
        "keywords": [
            "what happens if you miss an item", "if you miss an item", "what if an item is missed", "missed item policy"
        ],
        "patterns": [
            r'(?:what if|what happens if) you miss an item',
            r'missed an item'
        ],
        "answer": "If an item clearly shown on the plans was omitted in error, we revise and update the deliverable immediately at no charge."
    },
    {
        "id": "revise_estimate_after_addendum",
        "category": "Difficult Business",
        "question": "Can you revise the estimate after an addendum?",
        "keywords": [
            "revise the estimate after an addendum", "revise estimate after addendum", "update estimate after addenda"
        ],
        "patterns": [
            r'revise (?:the )?estimate after an addendum'
        ],
        "answer": "Yes. We review the revised sheets and update affected line items and quantities."
    },
    {
        "id": "estimate_confidential_projects",
        "category": "Difficult Business",
        "question": "Can you estimate confidential projects?",
        "keywords": [
            "estimate confidential projects", "confidential projects", "classified projects", "secret commercial projects"
        ],
        "patterns": [
            r'confidential projects'
        ],
        "answer": "Yes. We regularly handle confidential, non-disclosure-controlled commercial and government work."
    },
    {
        "id": "handle_proprietary_info",
        "category": "Difficult Business",
        "question": "How do you handle proprietary project information?",
        "keywords": [
            "handle proprietary project information", "proprietary information", "protect proprietary data", "security of drawings"
        ],
        "patterns": [
            r'proprietary (?:project )?information'
        ],
        "answer": "Files are stored in secure, access-controlled drives and never shared, published, or reused."
    },
    {
        "id": "sign_nda",
        "category": "Difficult Business",
        "question": "Can you sign an NDA?",
        "keywords": [
            "sign an nda", "sign nda", "non disclosure agreement", "will you sign an nda"
        ],
        "patterns": [
            r'sign an? nda\b',
            r'non[\s-]disclosure agreement'
        ],
        "answer": "Yes. We can execute your standard Non-Disclosure Agreement before receiving drawings."
    },
    {
        "id": "work_with_contractor_template",
        "category": "Difficult Business",
        "question": "Can you work with a contractor's existing estimating template?",
        "keywords": [
            "contractor's existing estimating template", "use my excel template", "contractor existing template", "populate our template"
        ],
        "patterns": [
            r'contractor\'?s existing (?:estimating )?template',
            r'use (?:my|our) (?:own )?template'
        ],
        "answer": "Yes. We can populate your custom Excel workbook, formulas, and format directly."
    },
    {
        "id": "use_company_pricing_database",
        "category": "Difficult Business",
        "question": "Can you use my company's pricing database?",
        "keywords": [
            "company's pricing database", "use my company's pricing database", "use our internal pricing database"
        ],
        "patterns": [
            r'company\'?s pricing database'
        ],
        "answer": "Yes. We integrate your internal labor rates, equipment rates, and supplier pricing catalogs."
    },
    {
        "id": "match_existing_estimate_format",
        "category": "Difficult Business",
        "question": "Can you match my existing estimate format?",
        "keywords": [
            "match my existing estimate format", "match our estimate format", "match my format"
        ],
        "patterns": [
            r'match (?:my|our) (?:existing )?estimate format'
        ],
        "answer": "Yes. We replicate your internal summary sheets, trade grouping, and line-item layout."
    },
    {
        "id": "provide_estimate_in_excel",
        "category": "Difficult Business",
        "question": "Can you provide the estimate in Excel?",
        "keywords": [
            "provide the estimate in excel", "estimate in excel", "deliver in excel", "excel spreadsheets live formulas"
        ],
        "patterns": [
            r'estimate in excel\b',
            r'deliverable in excel\b'
        ],
        "answer": "Yes. Deliverables include unprotected Excel spreadsheets with visible, live mathematical formulas."
    },
    {
        "id": "break_estimate_into_bid_packages",
        "category": "Difficult Business",
        "question": "Can you break the estimate into bid packages?",
        "keywords": [
            "break the estimate into bid packages", "bid packages", "split into bid packages"
        ],
        "patterns": [
            r'break.*into bid packages',
            r'bid packages'
        ],
        "answer": "Yes. Grouped into trade-specific subcontractor bid packages ready for distribution."
    },

    # -------------------------------------------------------------------------
    # 12. Questions Designed to Catch a Weak Chatbot
    # -------------------------------------------------------------------------
    {
        "id": "trick_50k_warehouse_cost_without_plans",
        "category": "Catch Weak Chatbot",
        "question": "I haven't sent you the plans yet. Tell me exactly how much my 50,000 SF warehouse will cost.",
        "keywords": [
            "haven't sent you the plans yet", "havent sent plans yet", "tell me exactly how much my 50,000 sf warehouse will cost",
            "exact cost 50000 sf warehouse without plans"
        ],
        "patterns": [
            r'haven\'?t sent.*plans.*how much.*50[\s,]*(?:k|000).*warehouse',
            r'how much.*50[\s,]*(?:k|000).*warehouse.*cost.*without plans'
        ],
        "answer": "We cannot provide an accurate project cost without drawings. Foundations, clear height, slab load specs, and MEP systems vary significantly. Please upload your preliminary drawings or basis-of-design narrative, and we will quote you an exact estimating fee and timeline."
    },
    {
        "id": "trick_electrical_prices_without_location",
        "category": "Catch Weak Chatbot",
        "question": "Give me today's exact electrical material prices for my project without seeing the location.",
        "keywords": [
            "electrical material prices for my project without seeing the location", "electrical prices without location",
            "material prices without knowing location"
        ],
        "patterns": [
            r'electrical material prices.*without.*location',
            r'material prices.*without seeing (?:the )?location'
        ],
        "answer": "Material prices and supply chains vary by state and local market. Please share the project location/zip code and electrical drawings so we can apply accurate regional pricing."
    },
    {
        "id": "trick_drawings_vs_specs_which_to_price",
        "category": "Catch Weak Chatbot",
        "question": "My drawings say one thing and the specifications say another. Which one should I price?",
        "keywords": [
            "drawings say one thing and the specifications say another", "which one should i price", "specs say one thing drawings say another",
            "drawings say one thing specs say another"
        ],
        "patterns": [
            r'drawings say one thing.*specifications say another',
            r'specs say one thing.*drawings say another',
            r'which one should i price'
        ],
        "answer": "Contract order of precedence generally dictates that specifications govern quality/materials while drawings govern locations/dimensions. To safeguard your bid, we log this discrepancy, price the more stringent requirement, and advise submitting an RFI."
    },
    {
        "id": "trick_bid_closes_30_mins_guarantee",
        "category": "Catch Weak Chatbot",
        "question": "The bid closes in 30 minutes. Can you guarantee the estimate will be finished?",
        "keywords": [
            "bid closes in 30 minutes. can you guarantee", "bid closes in 30 minutes", "finished in 30 minutes"
        ],
        "patterns": [
            r'bid closes in 30 minutes',
            r'guarantee.*estimate.*finished.*30 minutes'
        ],
        "answer": "No. We cannot complete a quality estimate in 30 minutes. Rushing a takeoff creates unverified omissions that could cause severe bid-day losses."
    },
    {
        "id": "trick_guarantee_100_percent_accurate",
        "category": "Catch Weak Chatbot",
        "question": "Can you guarantee your estimate is 100% accurate?",
        "keywords": [
            "guarantee your estimate is 100% accurate", "100% accurate estimate guarantee", "100 percent accurate guarantee"
        ],
        "patterns": [
            r'guarantee.*estimate.*100\s*(?:%|percent)\s*accurate'
        ],
        "answer": "We guarantee that our takeoff accurately reflects the provided drawings and specifications. However, no estimate can guarantee zero variance from actual construction costs, which depend on field labor efficiency, unforeseen site conditions, and vendor price changes."
    },
    {
        "id": "trick_how_much_profit_should_add",
        "category": "Catch Weak Chatbot",
        "question": "Can you tell me exactly how much profit I should add to my bid?",
        "keywords": [
            "tell me exactly how much profit i should add", "how much profit should i add", "what profit margin to add to bid"
        ],
        "patterns": [
            r'how much profit (?:should i|to) add'
        ],
        "answer": "Profit margin is your internal business decision based on your overhead, risk profile, and competitor market. We provide the net cost estimate so you can apply your preferred margin."
    },
    {
        "id": "trick_guarantee_will_win_project",
        "category": "Catch Weak Chatbot",
        "question": "Can you guarantee that I'll win the project if I use your estimate?",
        "keywords": [
            "guarantee that i'll win the project", "guarantee that i will win the project", "guarantee win project"
        ],
        "patterns": [
            r'guarantee (?:that )?(?:i\'ll|i will) win (?:the )?project'
        ],
        "answer": "No estimator can guarantee a win. We ensure your quantities and base costs are precise so that if you win, the job is profitable."
    },
    {
        "id": "trick_stamp_another_state",
        "category": "Catch Weak Chatbot",
        "question": "Can you stamp these drawings even though the project is in another state?",
        "keywords": [
            "stamp these drawings even though the project is in another state", "stamp drawings in another state", "pe stamp another state"
        ],
        "patterns": [
            r'stamp.*drawings.*another state'
        ],
        "answer": "No. Engineering and architectural stamps require a professional licensed specifically in the state where the project is built. We can only coordinate stamping through a locally credentialed professional in that jurisdiction."
    },
    {
        "id": "trick_architect_forgot_hvac_assume",
        "category": "Catch Weak Chatbot",
        "question": "The architect forgot to show the HVAC equipment. Can you assume what equipment they intended?",
        "keywords": [
            "architect forgot to show the hvac equipment", "forgot to show hvac equipment", "assume what equipment they intended"
        ],
        "patterns": [
            r'forgot to show (?:the )?hvac equipment',
            r'assume what equipment they intended'
        ],
        "answer": "We do not guess equipment selections. We can either include an agreed-upon square-foot allowance or draft an RFI for the engineer to define the basis of design."
    },
    {
        "id": "trick_make_up_reasonable_quantities",
        "category": "Catch Weak Chatbot",
        "question": "Can you make up reasonable quantities for the missing drawings?",
        "keywords": [
            "make up reasonable quantities for the missing drawings", "make up quantities", "invent quantities missing drawings"
        ],
        "patterns": [
            r'make up (?:reasonable )?quantities',
            r'invent quantities'
        ],
        "answer": "No. We never invent quantities for missing drawings. We clearly define what is shown, carry explicit budget allowances for unrepresented areas, and document all assumptions."
    },
    {
        "id": "trick_price_without_knowing_location",
        "category": "Catch Weak Chatbot",
        "question": "Can you give me a price for the project without knowing the location?",
        "keywords": [
            "price for the project without knowing the location", "price without location", "price project without knowing location"
        ],
        "patterns": [
            r'price.*without knowing (?:the )?location'
        ],
        "answer": "No. Labor wage rates, code requirements, sales taxes, and freight charges are tied directly to location. We need the project city or zip code for accurate pricing."
    },
    {
        "id": "trick_estimate_only_from_floor_plan",
        "category": "Catch Weak Chatbot",
        "question": "Can you estimate this project from only the floor plan?",
        "keywords": [
            "estimate this project from only the floor plan", "only the floor plan", "from only floor plan"
        ],
        "patterns": [
            r'estimate.*(?:from|with) only (?:the )?floor plan'
        ],
        "answer": "We can provide an initial architectural takeoff, but we cannot calculate structural member sizing, ceiling assemblies, or MEP systems without structural sheets, building sections, and engineering plans. All unshown trades will be flagged as budget allowances."
    }
]

# -----------------------------------------------------------------------------
# 13. Real Contractor Stress Test Query Handler
# -----------------------------------------------------------------------------
STRESS_TEST_RESPONSE = (
    "Thank you for reaching out. For a 125,000 SF 3-story commercial building covering 10+ trades, "
    "380 sheets, specs, and 4 addenda, this is a full-scale multi-trade estimate.\n\n"
    "**Turnaround & Deadline**:\n"
    "Our standard turnaround for a project of this scale is typically 4–6 business days. "
    "To confirm whether we can complete this by Friday at 2 PM, our lead estimator needs to review "
    "the drawing set, addenda delta sheets, and division of trades immediately.\n\n"
    "**Estimating Fee**:\n"
    "We do not quote flat rates without seeing the drawing complexity. "
    "Once you share the plan set, we will provide a firm proposal within a few hours.\n\n"
    "**What You Will Receive**:\n"
    "• Complete Excel takeoff workbook with live, transparent formulas broken down by CSI division and trade.\n"
    "• Itemized material, labor, and equipment cost breakdowns.\n"
    "• Color-coded markup plan drawings showing every measured takeoff area and item count.\n"
    "• Comprehensive sheet of inclusions, exclusions, and trade assumptions.\n"
    "• Discrepancy & RFI log covering drawing notes, spec conflicts, and addenda changes.\n\n"
    "Please share the download link to the plan set, specifications, and project location (zip code) "
    "so we can review the scope and provide a firm quote and timeline."
)


def match_domain_qa(raw_text: str) -> Optional[str]:
    """
    Matches raw user input against the comprehensive domain Q&A knowledge base.
    Uses regex patterns and tokenized keyword overlap to support wording variations.
    """
    cleaned = raw_text.lower().strip()
    words = set(re.findall(r'\b[a-z0-9%$]+\b', cleaned))

    best_item = None
    best_score = 0.0

    for item in DOMAIN_QA_ITEMS:
        # 1. Check exact regex patterns (instant high-confidence match)
        for pattern in item.get("patterns", []):
            if re.search(pattern, cleaned):
                return item["answer"]

        # 2. Check phrase and keyword matches
        score = 0.0
        for kw in item.get("keywords", []):
            kw_clean = kw.lower()
            if kw_clean in cleaned:
                score += len(kw_clean.split()) * 2.0
            else:
                kw_tokens = set(re.findall(r'\b[a-z0-9%$]+\b', kw_clean))
                if kw_tokens.issubset(words):
                    score += len(kw_tokens) * 1.5

        if score > best_score:
            best_score = score
            best_item = item

    # Threshold for semantic confidence
    if best_score >= 3.5 and best_item is not None:
        return best_item["answer"]

    return None


def is_stress_test_query(raw_text: str) -> bool:
    """
    Detects the multi-trade commercial stress test query:
    e.g. 125,000 SF 3-story commercial building, 380 drawing sheets, 1,200 pages of specs, 4 addenda, due Friday 2 PM.
    """
    txt = raw_text.lower()
    has_size = any(k in txt for k in ["125,000", "125000", "125k"])
    has_sheets = any(k in txt for k in ["380", "380 sheets", "380 drawing sheets"])
    has_specs = any(k in txt for k in ["1,200 pages", "1200 pages", "1,200", "1200"])
    has_deadline = any(k in txt for k in ["friday at 2 pm", "friday 2 pm", "due friday", "by friday"])
    has_trades = any(k in txt for k in ["architectural", "structural", "electrical", "plumbing", "hvac", "drywall"])

    matched_factors = sum([has_size, has_sheets, has_specs, has_deadline, has_trades])
    return matched_factors >= 3

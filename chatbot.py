"""
Construction Cost Estimation Chatbot Engine
Core business logic, dialog management, smart follow-up generation,
and rule compliance verification.
"""

import re
from typing import Dict, Any, List, Tuple, Optional
from intents import intent_detector
from conversation import ConversationState
from estimator_knowledge import estimator_kb
from lead_manager import lead_manager
from ballpark_calculator import (
    calculate_ballpark, parse_numeric_sqft, parse_sheet_count,
    parse_spec_pages, parse_addenda_count, is_construction_cost_query,
    estimate_project_effort, format_structured_ballpark,
    HOURLY_MIN, HOURLY_MAX
)
from domain_knowledge_qa import (
    match_domain_qa, is_stress_test_query, STRESS_TEST_RESPONSE
)


def is_location_query(raw_text: str) -> bool:
    """Detects any phrasing, typo, or variation regarding head office location or geography."""
    txt = raw_text.lower().strip()
    triggers = [
        "where are you located", "where you located", "where located", "where are you based",
        "where you based", "where you based off", "where you based of", "where are you based off",
        "where are you based of", "based off", "based of", "based out of", "where your headoffice is",
        "where is your headoffice", "where your head office is", "where is your head office",
        "where your head office", "where is your main office", "where your main office",
        "where you guys based", "where are you guys based", "where are you guys located",
        "headoffice", "head office", "headquarters", "where is your headquarters",
        "your address", "what is your address", "what's your address", "whats your address",
        "edison", "15 york drive", "where are you guys", "what state are you located",
        "what state are you in", "what states do you cover", "where are you operating",
        "office location", "office address"
    ]
    if any(t in txt for t in triggers):
        return True
    if re.search(r'where\s+(?:are\s+)?(?:you|u)\s+(?:guys\s+)?(?:located|based|from)', txt):
        return True
    if re.search(r'where\s+(?:is\s+)?(?:your|the)\s+(?:head\s*office|headoffice|main\s*office|hq|headquarters|office)', txt):
        return True
    return False


class EstimatorChatbot:
    """Intelligent rule-based estimating sales advisor."""

    def __init__(self):
        self.kb = estimator_kb
        self.detector = intent_detector
        self.lead_mgr = lead_manager

    def process_message(self, message: str, state: ConversationState) -> Dict[str, Any]:
        """Main entry point: processes user message, updates state, and returns response."""
        user_text = message.strip()
        state.add_message("user", user_text)

        # 1. Extract all entities present in the user text
        entities = self.detector.extract_entities(user_text)
        newly_updated = state.update_from_entities(entities)

        # 2. Detect candidate intents with scoring
        detected = self.detector.detect_intents(user_text)
        primary_intent = detected[0][0] if detected else "unknown"

        # 3. Formulate the response based on intent, entities, and state context
        response_text, quick_replies, action_type = self._route_intent(
            primary_intent, detected, user_text, state, newly_updated
        )

        # 4. Check if we should generate/save an active lead
        lead_summary = None
        if state.is_lead_ready():
            lead_record = self.lead_mgr.save_lead(state)
            lead_summary = lead_record.get("summary_text")

        # 5. Record bot response in state history
        state.add_message("bot", response_text, {
            "intent": primary_intent,
            "action_type": action_type
        })

        return {
            "response": response_text,
            "session_id": state.session_id,
            "state": state.to_dict(),
            "quick_replies": quick_replies,
            "action_type": action_type,
            "lead_summary": lead_summary
        }

    def _route_intent(
        self,
        intent: str,
        detected: List[Tuple[str, float]],
        raw_text: str,
        state: ConversationState,
        newly_updated: List[str]
    ) -> Tuple[str, List[str], str]:
        """Routes dialog based on primary intent and conversation context."""

        # Check location inquiry first so no variations or typos are ever missed
        if is_location_query(raw_text):
            return self._handle_company_location(state)

        # Check real contractor stress test inquiry
        if is_stress_test_query(raw_text):
            quick_replies = [
                "Upload Plans",
                "Request Proposal",
                "What tools do you use?",
                "Where are you located?"
            ]
            return STRESS_TEST_RESPONSE, quick_replies, "stress_test"

        # Check specialized domain estimating Q&A
        domain_answer = match_domain_qa(raw_text)
        if domain_answer:
            response = (
                f"{domain_answer}\n\n"
                "Do you have project plans or specifications ready? You can share the PDF or drawing set with us for review."
            )
            quick_replies = [
                "Upload Plans",
                "What tools do you use?",
                "Where are you located?",
                "What's your pricing?"
            ]
            return response, quick_replies, "domain_qa"

        # Check for specific "Are you AI" query to obey Rule 15
        if any(term in raw_text.lower() for term in ["are you an ai", "are you ai", "are you a bot", "are you a robot"]):
            company_name = self.kb.company.get("name", "Estimation Service Chat Bot")
            reply = (
                f"I am the digital estimating assistant for {company_name}. "
                "I assist contractors and builders by qualifying project requirements, explaining our estimating scopes, "
                "and coordinating plan reviews with our professional estimating team. How can I help with your project today?"
            )
            return reply, ["Pricing & Rates", "Turnaround Time", "Trades Covered", "Upload Plans"], "info"

        # Check for explicit plan submission / proposal request
        if intent in ["quote", "request_proposal"] or "proposal" in raw_text.lower():
            return self._handle_proposal_request(state)

        # Check for unlisted trade inquiry (e.g., "do you estimate [unlisted scope]")
        known_service_intents = ["services", "trades", "scheduling", "drafting", "stamping", "value_engineering", "pricing", "turnaround_time"]
        if intent not in known_service_intents and any(term in raw_text.lower() for term in ["do you estimate", "can you estimate", "do you do", "can you do"]) and not state.trades:
            if "what trades" not in raw_text.lower() and "what do you" not in raw_text.lower():
                return self._handle_unlisted_trade(raw_text, state)

        # Check for physical construction project cost vs estimating service fee (Rule 16)
        if intent == "construction_cost_inquiry" or is_construction_cost_query(raw_text):
            return self._handle_construction_cost_vs_fee()

        # Check for hourly rate inquiry (Section 1)
        if intent == "hourly_rate" or any(h in raw_text.lower() for h in ["hourly rate", "rate per hour", "how much per hour", "what is your hourly", "what's your hourly"]):
            return self._handle_hourly_rate(state)

        # Check for ballpark pricing inquiry (Sections 2–5, 11–14, 17)
        ballpark_triggers = [
            "ballpark", "ball park", "roughly how much", "rough idea", "budget for your estimating",
            "approximately what will you charge", "approximate quote", "how much would you charge",
            "how much for a project like this", "rough quote", "ballpark quote", "what should i budget",
            "how much for an estimate", "approximate cost"
        ]
        has_ballpark_keyword = any(b in raw_text.lower() for b in ballpark_triggers)
        has_project_specs = any(header in raw_text.lower() for header in ["project:", "size:", "drawings:"])
        sqft_val = parse_numeric_sqft(state.square_footage)
        has_size_and_scope_ask = bool((state.square_footage or sqft_val) and (state.trades or any(k in raw_text.lower() for k in ["mep", "electrical", "plumbing", "hvac", "drywall"])) and any(w in raw_text.lower() for w in ["how much", "estimates", "need", "cost", "quote"]))

        if intent == "ballpark_pricing" or has_ballpark_keyword or has_project_specs or has_size_and_scope_ask:
            return self._handle_ballpark_pricing(raw_text, state, newly_updated)

        # Check out-of-the-box construction questions (BIM, permits, inflation/escalation, bonds, prevailing wage, etc.)
        oob_answer = self._resolve_out_of_box_query(raw_text)
        if oob_answer and (intent not in ["turnaround_time", "services", "trades", "drafting", "stamping", "scheduling", "value_engineering"] or any(k in raw_text.lower() for k in ["inflation", "escalation", "price spike", "price fluctuation", "bim", "revit", "permit", "bid bond", "surety", "prevailing wage"])):
            response = (
                f"{oob_answer}\n\n"
                "Do you have project plans or specifications ready? You can share the PDF or drawing set with us for review."
            )
            quick_replies = [
                "Upload Plans",
                "What tools do you use?",
                "Where are you located?",
                "What's your pricing?"
            ]
            return response, quick_replies, "out_of_the_box_qa"

        # 1. PRICING INQUIRY
        if intent == "pricing":
            return self._handle_pricing(state, newly_updated)

        # 2. TURNAROUND TIME INQUIRY
        if intent == "turnaround_time":
            return self._handle_turnaround(state)

        # 3. SERVICES LIST / GENERAL ESTIMATING
        if intent in ["services", "estimating"]:
            return self._handle_services(state)

        # 4. TRADES INQUIRY
        if intent == "trades":
            return self._handle_trades(state)

        # 5. SPECIFIC TRADES (MEP, Electrical, HVAC, Plumbing, Drywall, etc.)
        specific_trade_intents = [
            "mep", "electrical", "plumbing", "mechanical", "hvac",
            "drywall", "flooring", "concrete", "roofing", "framing", "painting"
        ]
        if intent in specific_trade_intents or any(i in specific_trade_intents for i, _ in detected[:2]):
            return self._handle_specific_trades(state, newly_updated)

        # 6. ADDITIONAL SERVICES: DRAFTING, STAMPING, SCHEDULING, VALUE ENGINEERING
        if intent == "drafting":
            return self._handle_drafting(state)
        if intent == "stamping":
            return self._handle_stamping(state)
        if intent == "scheduling":
            return self._handle_scheduling(state)
        if intent == "value_engineering":
            return self._handle_value_engineering(state)

        # 7. ESTIMATE TYPES (Preliminary, Budget, Detailed, Takeoff)
        if intent in ["estimate_type", "takeoff", "material_takeoff", "labor_estimate"]:
            return self._handle_estimate_types(intent, state)

        # 8. PLANS / UPLOAD PLANS
        if intent in ["plans", "upload_plans"]:
            return self._handle_plans(state)

        # 9. GREETING
        if intent == "greeting":
            return self._handle_greeting(state)

        # 10. TOOLS & SOFTWARE USED
        if intent == "tools" or any(t in raw_text.lower() for t in ["what tool", "what software", "rsmean", "rs mean", "bluebeam", "blue beam", "planswift", "plan swift", "vendor list"]):
            return self._handle_tools(state)

        # 11. COMPANY LOCATION & COVERAGE
        location_triggers = [
            "where are you located", "where is your office", "where are you based",
            "where you based", "where you based off", "where are you based off",
            "based off", "based out of", "where your headoffice is", "where is your headoffice",
            "where your head office is", "where is your head office", "headoffice", "head office",
            "headquarters", "where is your headquarters", "main office", "your address",
            "edison", "15 york drive", "where are you guys"
        ]
        if intent == "company_location" or any(l in raw_text.lower() for l in location_triggers):
            return self._handle_company_location(state)

        # 12. FAQ (Accuracy, Deliverables, Payment, CSI, Samples)
        if intent in ["accuracy", "deliverables_format", "payment_terms", "csi_divisions", "samples"]:
            return self._handle_faq(intent, state)

        # 13. COMPANY INFO / PROCESS
        if intent in ["company_information", "process"]:
            return self._handle_company_info(state)

        # 14. HUMAN HANDOFF
        if intent == "human_handoff":
            return self._handle_human_handoff(state)

        # 12. BID DEADLINE
        if intent == "bid_deadline" or "bid_due_date" in newly_updated:
            return self._handle_bid_deadline(state)

        # 13. CONTACT DETAILS PROVIDED
        if "email" in newly_updated or "phone" in newly_updated or "name" in newly_updated:
            return self._handle_contact_capture(state)

        # 14. ENTITIES PROVIDED WITHOUT EXPLICIT QUESTION (e.g. "Commercial 25k sq ft")
        if newly_updated:
            return self._handle_entity_followup(state, newly_updated)

        # 15. THANKS
        if intent == "thanks":
            reply = (
                "You're very welcome! If you have drawing files ready or need to check another trade, "
                "feel free to share them anytime. Our estimating team is ready to review your project."
            )
            return reply, ["Upload Plans", "Request Proposal", "Our Services"], "info"

        # 16. UNKNOWN / FALLBACK (Consultative Handoff)
        return self._handle_unknown(raw_text, state)

    # --------------------------------------------------------------------------
    # Specialized Intent Handlers & Rule Enforcers
    # --------------------------------------------------------------------------

    def _handle_greeting(self, state: ConversationState) -> Tuple[str, List[str], str]:
        greeting = (
            f"Hello and welcome to **{self.kb.company.get('name')}**!\n\n"
            "We provide professional construction cost estimating, detailed quantity takeoffs, "
            "and bidding support across all residential, commercial, industrial, and civil trades.\n\n"
            "How can we assist with your project today?"
        )
        quick_replies = [
            "How much does an estimate cost?",
            "What's your turnaround time?",
            "What trades do you estimate?",
            "I need an estimate (Share details)"
        ]
        return greeting, quick_replies, "greeting"

    def _handle_pricing(self, state: ConversationState, newly_updated: List[str]) -> Tuple[str, List[str], str]:
        # Enforce Rule 1, 2, 8: Never invent fixed price. Standard pricing response.
        text_parts = [
            self.kb.pricing_response,
            "",
            self.kb.turnaround_response,
            "",
            self.kb.plan_request_phrase
        ]
        response = "\n".join(text_parts)
        quick_replies = [
            "Yes, I have plans ready",
            "What trades do you estimate?",
            "Commercial project",
            "Residential project"
        ]
        return response, quick_replies, "pricing"

    def _handle_construction_cost_vs_fee(self) -> Tuple[str, List[str], str]:
        # Enforce Rule 16: Do not confuse construction project cost with estimating service fee
        response = (
            "Are you asking about the estimated construction cost of the project, "
            "or the fee for our estimating service?"
        )
        quick_replies = [
            "Fee for estimating service",
            "Estimated construction cost",
            "Upload plans for review"
        ]
        return response, quick_replies, "cost_distinction"

    def _handle_hourly_rate(self, state: ConversationState) -> Tuple[str, List[str], str]:
        # Preferred response from Section 1
        response = (
            f"Our estimating services typically range from **${HOURLY_MIN}–${HOURLY_MAX} per hour**. "
            "The total cost depends on the project's size, complexity, number of drawings, trades, specifications, and scope.\n\n"
            "If you can share your project type, approximate square footage, trades required, and drawing count, "
            "I can give you a tailored ballpark estimate. For a formal proposal, you can also share your plans with us."
        )
        quick_replies = [
            "Give me a ballpark estimate",
            "Upload Plans",
            "What's your turnaround time?",
            "What trades do you estimate?"
        ]
        return response, quick_replies, "hourly_rate"

    def _handle_ballpark_pricing(self, raw_text: str, state: ConversationState, newly_updated: List[str]) -> Tuple[str, List[str], str]:
        # Extract any specific parameters from text or state
        sqft = parse_numeric_sqft(state.square_footage)
        sheets = parse_sheet_count(state.drawing_sheets or raw_text)
        specs = parse_spec_pages(state.specifications_volume or raw_text)
        addenda = parse_addenda_count(state.addenda_count or raw_text)
        txt_lower = raw_text.lower()

        # Scenario 1: Contractor provided very little information (Section 12)
        if not state.square_footage and not state.trades and not state.drawing_sheets and not state.project_type and not sqft and not sheets:
            response = (
                f"Our estimating rate is generally **${HOURLY_MIN}–${HOURLY_MAX}/hour**. "
                "The total depends on the project scope and complexity. "
                "If you give me the project type, approximate square footage, trades required, and drawing count, "
                "I can give you a rough ballpark. For an accurate proposal, you can also send us the plans."
            )
            quick_replies = [
                "Commercial project",
                "Residential project",
                "Single-trade takeoff",
                "Upload Plans"
            ]
            return response, quick_replies, "ballpark_incomplete"

        # Scenario 2: Contractor ONLY provided square footage (Section 13)
        if (state.square_footage or sqft) and not state.trades and not state.drawing_sheets and not sheets and not ("drawings" in txt_lower or "specs" in txt_lower):
            size_mention = state.square_footage or f"{sqft:,} SF"
            response = (
                f"Thanks! The {size_mention} size gives me a starting point, but estimating effort also depends heavily "
                "on the project type, number of trades, drawing count, and specifications. "
                "If you tell me which trades you need and approximately how many drawing sheets you have, "
                "I can give you a better ballpark."
            )
            quick_replies = [
                "Electrical & Plumbing",
                "All MEP Trades",
                "Drywall / Framing",
                "Full General Scope"
            ]
            return response, quick_replies, "ballpark_sqft_only"

        # Scenario 3: Calculate dynamic effort and ballpark
        effort = estimate_project_effort(
            state.project_type,
            sqft,
            state.trades,
            sheets,
            specs,
            addenda,
            raw_text
        )
        ballpark = calculate_ballpark(effort["hours_min"], effort["hours_max"])

        # Example 1: Small single-trade project (Section 11, Example 1)
        if effort["complexity"] == "Small / Single-Trade":
            trade_name = state.trades[0] if state.trades else "single-trade"
            response = (
                f"For a project of this size and a single-trade {trade_name} takeoff, I'd expect the work to be relatively straightforward. "
                f"A rough estimate could be around {ballpark['hours_str']}. "
                f"At ${HOURLY_MIN}–${HOURLY_MAX}/hour, that puts the ballpark around **{ballpark['range_str']}**. "
                "The final cost would depend on the drawings and scope."
            )
        # Example 2: Normal project 40,000 SF electrical & plumbing (Section 11, Example 2)
        elif effort["complexity"] == "Normal / 2-Trade Commercial":
            size_disp = state.square_footage or "40,000 SF"
            trades_disp = " and ".join(state.trades) if state.trades else "requested trades"
            response = (
                f"For a {size_disp} commercial project covering {trades_disp}, I'd roughly expect around {ballpark['hours_str']} "
                f"depending on the drawing and specification volume. At ${HOURLY_MIN}–${HOURLY_MAX}/hour, the ballpark would be approximately **{ballpark['range_str']}**. "
                "Once we review the plans, we can confirm the exact scope, price, and turnaround."
            )
        # Example 3: Large project 150,000 SF all MEP (Section 11, Example 3)
        elif effort["complexity"] == "Large Multi-Trade MEP":
            size_disp = state.square_footage or "150,000 SF"
            response = (
                f"For a {size_disp} commercial project involving multiple MEP trades, the estimating effort could be substantially larger. "
                f"A preliminary range might be around {ballpark['hours_str']}. At ${HOURLY_MIN}–${HOURLY_MAX}/hour, that would put the ballpark around **{ballpark['range_str']}**. "
                f"The turnaround could be {effort['turnaround']}, depending on the number of drawings, specifications, addenda, and overall complexity.\n\n"
                "If you send us the plan set, we can review it and provide a more accurate proposal."
            )
        # Example 4: Multi-detail breakdown (Section 14)
        elif "drawings:" in txt_lower or "specifications:" in txt_lower or (sheets and sheets >= 100):
            response = (
                f"Based on the project information you've provided, I'd estimate approximately **{ballpark['hours_str']}** for the requested scope. "
                f"At our ${HOURLY_MIN}–${HOURLY_MAX}/hour rate, the ballpark would be approximately **{ballpark['range_str']}**. "
                f"Based on the drawing/specification volume and number of trades, I'd expect {effort['turnaround']}. "
                "This is a preliminary ballpark; the final proposal would be confirmed after reviewing the actual plans."
            )
        else:
            # Section 17 Structured Format
            response = format_structured_ballpark(state, effort, ballpark)

        quick_replies = [
            "Upload Plans",
            "Request Proposal",
            "Turnaround Time",
            "What tools do you use?"
        ]
        return response, quick_replies, "ballpark_pricing"

    def _handle_turnaround(self, state: ConversationState) -> Tuple[str, List[str], str]:
        # Enforce Rule 3, 4: 2-3 business days standard, timeline confirmed after plans
        response = (
            f"{self.kb.turnaround_response}\n\n"
            "For very large or complex projects, our team confirms the exact timeline after reviewing the drawing package. "
            "If you have an upcoming bid deadline, please let us know so we can accommodate your schedule.\n\n"
            "Do you have a specific bid due date you are working toward?"
        )
        quick_replies = [
            "Bid is due in 3 days",
            "Bid is due next week",
            "Upload project plans",
            "How much do you charge?"
        ]
        return response, quick_replies, "turnaround"

    def _handle_services(self, state: ConversationState) -> Tuple[str, List[str], str]:
        summary = self.kb.format_services_summary()
        quick_replies = [
            "MEP Estimating",
            "Drywall & Framing",
            "Full General Construction",
            "Value Engineering",
            "What is your pricing?"
        ]
        return summary, quick_replies, "services"

    def _handle_trades(self, state: ConversationState) -> Tuple[str, List[str], str]:
        summary = self.kb.format_trades_summary()
        quick_replies = [
            "Electrical & Plumbing",
            "HVAC & Mechanical",
            "Drywall & Framing",
            "Concrete & Masonry",
            "Site Work & Civil"
        ]
        return summary, quick_replies, "trades"

    def _handle_specific_trades(self, state: ConversationState, newly_updated: List[str]) -> Tuple[str, List[str], str]:
        trade_names = ", ".join(state.trades) if state.trades else "your requested trades"
        
        # Smart follow-up: Check what we already know vs what we need next
        if not state.plans_available:
            next_q = "Do you already have the drawing set or plans available to share for review?"
            quick_replies = ["Yes, I have PDF plans", "Drawings coming soon", "Request proposal"]
        elif not state.square_footage and not state.project_type:
            next_q = "What type of project is this (e.g., commercial or residential) and what is the approximate square footage?"
            quick_replies = ["Commercial building", "Residential project", "Tenant improvement"]
        elif not state.bid_due_date:
            next_q = "When is your bid or estimate submission due date?"
            quick_replies = ["Due in 3 days", "Due next week", "Standard turnaround"]
        else:
            next_q = "Please share your email and contact number so our estimating department can send over the proposal."
            quick_replies = ["Share contact info", "Upload drawings"]

        response = (
            f"Yes, we provide full estimating and material takeoff services for **{trade_names}**!\n\n"
            "Our scope covers itemized material takeoffs, labor hours, equipment, and CSI-formatted spreadsheets.\n\n"
            f"{next_q}"
        )
        return response, quick_replies, "trade_details"

    def _handle_drafting(self, state: ConversationState) -> Tuple[str, List[str], str]:
        drafting_info = self.kb.get_additional_service("drafting") or {}
        desc = drafting_info.get("description", "We assist with construction-related drafting and drawing preparation.")
        response = (
            f"**Drafting Services**:\n\n{desc}\n\n"
            "We handle 2D CAD drafting, shop drawings, redline updates, and drawing packages for submittals.\n\n"
            "Do you have sketches, markups, or existing CAD/PDF files you would like us to work from?"
        )
        quick_replies = ["Yes, have sketches/CAD", "What is the turnaround?", "Cost of drafting"]
        return response, quick_replies, "drafting"

    def _handle_stamping(self, state: ConversationState) -> Tuple[str, List[str], str]:
        # Enforce Rule 6: Never claim legal stamping authority in every jurisdiction
        response = (
            "**Stamp & Engineering Coordination**:\n\n"
            "Stamping requirements depend on the project location and applicable regulations. "
            "We can help coordinate the appropriate licensed professional where required.\n\n"
            "We coordinate with licensed Professional Engineers (PE) and Structural Engineers (SE) "
            "licensed in your specific project jurisdiction.\n\n"
            "What state/location is your project located in, and what discipline of stamp is required?"
        )
        quick_replies = ["Structural Stamp", "MEP Engineering Stamp", "Civil Stamp", "California", "Texas", "Florida"]
        return response, quick_replies, "stamping"

    def _handle_scheduling(self, state: ConversationState) -> Tuple[str, List[str], str]:
        response = (
            "**Construction Scheduling Services**:\n\n"
            "We develop professional CPM (Critical Path Method) construction schedules, activity sequencing, "
            "milestone planning, trade coordination, and work breakdown structures (WBS) in Primavera P6 or Microsoft Project.\n\n"
            "Would you like a baseline schedule for a project bid, or an active schedule update for ongoing construction?"
        )
        quick_replies = ["Baseline bid schedule", "P6 Schedule", "How much does it cost?", "Upload project plans"]
        return response, quick_replies, "scheduling"

    def _handle_value_engineering(self, state: ConversationState) -> Tuple[str, List[str], str]:
        response = (
            "**Value Engineering (VE)**:\n\n"
            "We help identify strategic opportunities to reduce project costs, optimize materials, "
            "evaluate alternative construction methods, and improve constructability without compromising architectural design.\n\n"
            "Value engineering recommendations depend directly on the project's drawings, specifications, budget, and local market conditions.\n\n"
            "Do you have the current plan set and target budget available for our team to review?"
        )
        quick_replies = ["Yes, plans ready to upload", "How much can we save?", "Turnaround time"]
        return response, quick_replies, "value_engineering"

    def _handle_estimate_types(self, intent: str, state: ConversationState) -> Tuple[str, List[str], str]:
        # Enforce Rule 9: Clearly distinguish between estimate, budget, takeoff, and final proposal
        response = (
            "We provide several types of estimating deliverables tailored to your goals:\n\n"
            "• **Detailed Bid Estimate**: Complete CSI line-item takeoff with material, labor hours, and equipment for contractor bidding.\n"
            "• **Quantity Takeoff (QTO)**: Pure measurement counts, linear footages, and square footages with color-coded marked plans.\n"
            "• **Material Takeoff**: Itemized bill of materials for supplier pricing and purchasing.\n"
            "• **Preliminary / Budget Estimate**: High-level conceptual cost modeling for early design & planning.\n"
            "• **Change Order Estimate**: Accurate pricing for scope additions or revisions.\n\n"
            "Which of these matches your current objective?"
        )
        quick_replies = ["Detailed Bid Estimate", "Quantity Takeoff (QTO)", "Budget Estimate", "Material Takeoff"]
        return response, quick_replies, "estimate_types"

    def _handle_plans(self, state: ConversationState) -> Tuple[str, List[str], str]:
        # Enforce Rule 5 & Section 9: Plan/Drawing Request
        response = (
            "To provide an accurate proposal and determine the estimating scope, please share your project plans/drawings. "
            "Our team can review the drawings and confirm the scope, pricing, and turnaround time.\n\n"
            "We accept **PDF, DWG, CAD, Excel, and zipped drawing sets**. "
            "You can upload your files directly using the attachment button, or share a cloud link (Dropbox, Google Drive, OneDrive).\n\n"
            "How many drawing sheets or pages are in your set?"
        )
        quick_replies = ["Upload plans now", "Under 10 sheets", "10-50 sheets", "Over 50 sheets"]
        return response, quick_replies, "plans"

    def _handle_bid_deadline(self, state: ConversationState) -> Tuple[str, List[str], str]:
        deadline_text = f" Noted your bid due date as: **{state.bid_due_date}**." if state.bid_due_date else ""
        response = (
            f"Understood.{deadline_text} We understand how critical bid deadlines are for contractors and subcontractors.\n\n"
            "Our standard turnaround is 2–3 business days, and we prioritize expediting projects to ensure you receive your estimate well before bid submission.\n\n"
            "If you share your plans and contact details, our senior estimator will review the scope immediately."
        )
        quick_replies = ["Upload Plans", "Provide Contact Info", "What trades do you do?"]
        return response, quick_replies, "bid_deadline"

    def _handle_proposal_request(self, state: ConversationState) -> Tuple[str, List[str], str]:
        state.proposal_requested = True
        missing = state.get_missing_critical_info()
        
        details = []
        if state.project_type: details.append(f"Project Type: {state.project_type}")
        if state.trades: details.append(f"Trades: {', '.join(state.trades)}")
        if state.square_footage: details.append(f"Size: {state.square_footage}")
        if state.plans_available: details.append(f"Plans: {state.plans_available}")

        known_summary = " (" + ", ".join(details) + ")" if details else ""

        if not (state.email or state.phone):
            response = (
                f"We would be delighted to prepare an estimating proposal for you{known_summary}!\n\n"
                "To send you the proposal and confirm scope and pricing:\n"
                "1. Please provide your **Name, Company, and Email or Phone Number**.\n"
                "2. Share your project plans/drawings for review.\n\n"
                "You can type your contact info right here or use the upload button for your drawing set."
            )
            quick_replies = ["Upload Plans", "Call me directly", "Enter Contact Info"]
            return response, quick_replies, "proposal_request"

        response = (
            f"Thank you! We have compiled your project details{known_summary}.\n\n"
            "Our estimating department will review your scope and provide a formal service proposal. "
            "If you haven't uploaded your drawings yet, please attach your PDF plans so we can finalize pricing and turnaround."
        )
        quick_replies = ["Upload Plans", "Review Lead Summary", "Start New Project"]
        return response, quick_replies, "proposal_submitted"

    def _handle_contact_capture(self, state: ConversationState) -> Tuple[str, List[str], str]:
        contact_parts = []
        if state.name: contact_parts.append(f"Name: {state.name}")
        if state.company: contact_parts.append(f"Company: {state.company}")
        if state.email: contact_parts.append(f"Email: {state.email}")
        if state.phone: contact_parts.append(f"Phone: {state.phone}")

        contact_str = ", ".join(contact_parts)
        response = (
            f"Thank you for providing your contact information ({contact_str}).\n\n"
            "We have recorded your details for our estimating team. "
            "If you have your project drawings ready, please upload them or share a link so we can immediately review the scope and prepare your proposal."
        )
        quick_replies = ["Upload Plans", "View Lead Summary", "What's the turnaround time?"]
        return response, quick_replies, "contact_captured"

    def _handle_entity_followup(self, state: ConversationState, newly_updated: List[str]) -> Tuple[str, List[str], str]:
        """Smart follow-up logic: acknowledges what was extracted and asks only logical missing details."""
        # Section 13: If contractor only provides square footage
        if "square_footage" in newly_updated and not state.trades and not state.drawing_sheets:
            response = (
                f"Thanks! The {state.square_footage} size gives me a starting point, but estimating effort also depends heavily "
                "on the project type, number of trades, drawing count, and specifications. "
                "If you tell me which trades you need and approximately how many drawing sheets you have, "
                "I can give you a better ballpark."
            )
            quick_replies = ["Electrical & Plumbing", "All MEP Trades", "Drywall / Framing", "Full General Scope"]
            return response, quick_replies, "smart_followup"

        acknowledgments = []
        if "trades" in newly_updated:
            acknowledgments.append(f"trades ({', '.join(state.trades)})")
        if "project_type" in newly_updated:
            acknowledgments.append(f"project type ({state.project_type})")
        if "square_footage" in newly_updated:
            acknowledgments.append(f"size ({state.square_footage})")
        if "construction_stage" in newly_updated:
            acknowledgments.append(f"scope ({state.construction_stage})")

        ack_text = "Got it! We noted your " + " and ".join(acknowledgments) + "." if acknowledgments else "Thank you for the details."

        # Prioritize the most helpful single next step
        if not state.plans_available:
            next_step = (
                "Do you have the project plans and specifications available? "
                "You can share the PDF or drawing set with us for review."
            )
            quick_replies = ["Yes, I have PDF plans", "Plans in progress", "No plans yet"]
        elif not state.bid_due_date:
            next_step = "When is the bid due or when do you need the completed estimate delivered?"
            quick_replies = ["Due in 2-3 days", "Due next week", "Standard turnaround"]
        elif not (state.email or state.phone):
            next_step = "What is the best email address or phone number to send your estimating proposal to?"
            quick_replies = ["Provide email", "Call me"]
        else:
            next_step = (
                "Our team will review these project parameters and get back to you with a formal proposal. "
                "Is there any special scope or addenda we should be aware of?"
            )
            quick_replies = ["No special scope", "Value Engineering", "CPM Schedule needed"]

        response = f"{ack_text}\n\n{next_step}"
        return response, quick_replies, "smart_followup"

    def _handle_human_handoff(self, state: ConversationState) -> Tuple[str, List[str], str]:
        response = (
            f"{self.kb.human_handoff_response}\n\n"
            f"You can also reach our estimating desk directly at **{self.kb.company.get('phone')}** "
            f"or by emailing **{self.kb.company.get('email')}**.\n\n"
            "Would you like to leave your contact details so our chief estimator can contact you directly?"
        )
        quick_replies = ["Leave my contact info", "Upload plans for review", "Company Information"]
        return response, quick_replies, "human_handoff"

    def _handle_company_info(self, state: ConversationState) -> Tuple[str, List[str], str]:
        company = self.kb.company
        response = (
            f"**{company.get('name')}**\n"
            f"*{company.get('tagline')}*\n\n"
            f"{company.get('description')}\n\n"
            f"📞 **Phone**: {company.get('phone')}\n"
            f"✉️ **Email**: {company.get('email')}\n"
            f"🌐 **Website**: {company.get('website')}\n"
            f"⏰ **Hours**: {company.get('office_hours')}\n\n"
            "Would you like to discuss a specific project or request an estimating proposal?"
        )
        quick_replies = ["Request a Proposal", "Our Pricing", "Turnaround Time", "Trades Covered"]
        return response, quick_replies, "company_info"

    def _handle_tools(self, state: ConversationState) -> Tuple[str, List[str], str]:
        response = (
            f"{self.kb.tools_response}\n\n"
            "Would you like us to review your drawings in Bluebeam or PlanSwift and prepare an itemized takeoff proposal?"
        )
        quick_replies = [
            "Upload Plans",
            "What's your pricing?",
            "Where are you located?",
            "Turnaround Time"
        ]
        return response, quick_replies, "tools"

    def _handle_company_location(self, state: ConversationState) -> Tuple[str, List[str], str]:
        response = (
            f"{self.kb.locations_response}\n\n"
            "We handle projects across all states, adjusting labor rates and material pricing to your specific city or zip code. "
            "Where is your current project located?"
        )
        quick_replies = [
            "What tools do you use?",
            "Upload Plans",
            "What's your turnaround time?",
            "Get a Proposal"
        ]
        return response, quick_replies, "company_location"

    def _handle_faq(self, intent: str, state: ConversationState) -> Tuple[str, List[str], str]:
        faq_map = {
            "accuracy": "accuracy",
            "deliverables_format": "deliverables",
            "payment_terms": "payment",
            "csi_divisions": "csi_divisions",
            "samples": "samples"
        }
        key = faq_map.get(intent, intent)
        faq_answer = self.kb.get_faq(key) or self.kb.get_faq(intent)
        if faq_answer:
            response = (
                f"{faq_answer}\n\n"
                "Do you have a project or drawing set you would like us to review for an estimate?"
            )
            quick_replies = ["Upload Plans", "What's your pricing?", "Turnaround Time"]
            return response, quick_replies, "faq"

        return self._handle_unknown("", state)

    def _handle_unlisted_trade(self, raw_text: str, state: ConversationState) -> Tuple[str, List[str], str]:
        # Exact response specified in Section 5 for unlisted trades
        response = (
            f"{self.kb.unlisted_trade_response}\n\n"
            "Do you have a set of drawings or an outline of the project scope available?"
        )
        quick_replies = ["Upload Plans", "Describe Scope", "What standard trades do you cover?"]
        return response, quick_replies, "unlisted_trade"

    def _resolve_out_of_box_query(self, raw_text: str) -> Optional[str]:
        """Provides expert, domain-grounded construction answers for out-of-the-box contractor inquiries."""
        txt = raw_text.lower()

        # 1. BIM / Revit / 3D / VDC
        if any(k in txt for k in ["bim", "revit", "navisworks", "3d model", "vdc", "clash detection", "ifc", "tekla"]):
            return (
                "**BIM & 3D Model Estimating**:\n\n"
                "Yes, we work with BIM models, Autodesk Revit (.rvt), Navisworks, and IFC files. "
                "Our team extracts quantities directly from 3D models and cross-references them against 2D plan sets and specifications "
                "to ensure complete accuracy between model geometry and field requirements. "
                "You can share either your 3D models or exported 2D PDF drawing sets for review."
            )

        # 2. Permits / Building Department / Codes
        if any(k in txt for k in ["permit", "building department", "plan check", "code compliance", "ahj", "inspection", "ada compliance", "ibc"]):
            return (
                "**Permits & Building Department Coordination**:\n\n"
                "Our takeoff sheets and construction drawings are frequently prepared to support municipal permit submittals and plan checks. "
                "While official code approval rests with your local Authority Having Jurisdiction (AHJ), our estimating packages provide the full "
                "material schedules, structural quantities, and PE/SE coordination needed for submission."
            )

        # 3. Inflation / Price Escalation / Material Spikes / Tariffs
        if any(k in txt for k in ["inflation", "escalation", "price spike", "material increase", "tariff", "copper price", "steel price", "lumber price", "cost increase"]):
            return (
                "**Price Escalation & Market Volatility**:\n\n"
                "To protect your bid margins against volatile commodity prices (such as structural steel, copper, PVC, and lumber), "
                "we leverage quarterly updated RSMeans cost indices combined with real-time local supplier quotes. "
                "We can also incorporate price escalation factors or contingency allowances into your estimate based on your anticipated project duration."
            )

        # 4. Bid Leveling / Subcontractor Comparison / Scope Gaps
        if any(k in txt for k in ["bid leveling", "level bids", "compare bids", "subcontractor quote", "sub bid", "scope gap"]):
            return (
                "**Subcontractor Bid Leveling**:\n\n"
                "We provide comprehensive bid leveling services for General Contractors. We analyze all incoming subcontractor proposals side-by-side, "
                "normalize scope inclusions and exclusions, identify hidden gaps or overlapping scopes, and ensure your final prime bid is competitive and risk-free."
            )

        # 5. Prevailing Wage / Davis-Bacon / Certified Payroll / Union Rates
        if any(k in txt for k in ["prevailing wage", "davis bacon", "davis-bacon", "certified payroll", "union rate", "open shop", "public works"]):
            return (
                "**Prevailing Wage & Davis-Bacon Compliance**:\n\n"
                "Yes! We tailor our labor cost modeling to match your exact job requirements—whether open-shop (merit shop), union, or prevailing wage (Davis-Bacon) "
                "for municipal, state, and federal public works projects. Just let us know the project location and wage determination schedule."
            )

        # 6. Bid Bonds / Surety / Bonding Capacity
        if any(k in txt for k in ["bid bond", "surety", "bonding", "performance bond", "payment bond", "bonding capacity"]):
            return (
                "**Bonding & Surety Support**:\n\n"
                "Our itemized CSI MasterFormat cost estimates provide the transparent, substantiated cost documentation required by surety underwriters. "
                "Bonding agents regularly use our detailed estimates and work breakdown structures (WBS) to evaluate project risk and approve bid and performance bonds."
            )

        # 7. Change Orders / Claims / Bulletins / Disputes
        if not any(header in txt for header in ["project:", "size:", "drawings:"]) and any(k in txt for k in ["change order", "rfi", "bulletin", "asi", "scope creep", "dispute", "claim", "extra work"]):
            return (
                "**Change Orders & Addenda Estimating**:\n\n"
                "We specialize in change order quantification and dispute resolution support. "
                "When addenda, RFIs, or Architectural Supplemental Instructions (ASIs) arrive, our team conducts a delta takeoff—clearly highlighting added scope, deleted work, "
                "and labor impact so you can present fully justified change orders to the owner or GC."
            )

        # 8. General Conditions / Overhead & Profit (OH&P) / Division 01
        if any(k in txt for k in ["general conditions", "overhead", "oh&p", "profit margin", "markup", "mobilization", "division 01"]):
            return (
                "**General Conditions & Overhead / Profit (OH&P)**:\n\n"
                "Every full estimate includes CSI Division 01 General Conditions—accounting for project management, field superintendence, temporary utilities, site trailers, dumpster pulls, and jobsite safety. "
                "We format all contractor markups, overhead, and profit percentages to match your specific bidding strategy."
            )

        # 9. Bank Loans / Lenders / Draw Schedules / Pro Forma / Feasibility
        if any(k in txt for k in ["bank loan", "lender", "draw schedule", "financing", "investor", "pro forma", "feasibility", "hard cost"]):
            return (
                "**Financing & Bank Draw Schedules**:\n\n"
                "Commercial lenders and banks accept our preliminary and detailed cost estimates for construction loan underwriting. "
                "We organize line items into clear hard-cost categories and can structure milestone draw schedules aligned with project phases."
            )

        # 10. Square Foot Benchmarks / ROM Costs
        if any(k in txt for k in ["square foot cost", "cost per sq ft", "cost per square foot", "sq ft price", "rule of thumb"]):
            return (
                "**Square Foot Pricing & Conceptual Benchmarks**:\n\n"
                "While historical benchmarks provide a rough order of magnitude (ROM), actual construction costs depend heavily on structural framing, site conditions, finishes, and MEP design. "
                "To give you an accurate, defensible cost model rather than a rough guess, we recommend sharing your drawings or schematics for a tailored takeoff."
            )

        # 11. Subcontractor vs General Contractor Support
        if any(re.search(r'\b' + re.escape(k) + r'\b', txt) for k in ["subcontractor", "subcontractors", "subs", "sub-contractor", "specialty contractor", "gc", "general contractor"]):
            return (
                "**Support for Subcontractors & General Contractors**:\n\n"
                "We support both specialty trade subcontractors and General Contractors. "
                "For subcontractors, we prepare itemized trade takeoffs with material schedules ready for vendor quotes. "
                "For General Contractors, we build turnkey multi-trade estimates complete with General Conditions, subcontractor summaries, and bid forms."
            )

        # 12. Equipment / Heavy Machinery / Crane Rental
        if any(k in txt for k in ["equipment", "heavy machinery", "crane", "scaffolding", "forklift", "excavator rental"]):
            return (
                "**Equipment & Heavy Machinery Estimating**:\n\n"
                "We factor in equipment operating costs, mobilization, fuel, and rental rates (e.g., cranes, excavators, lifts, scaffolding) "
                "calibrated to regional equipment rental benchmarks so your field logistics are fully covered."
            )

        # 13. Demolition & Environmental Remediation
        if any(re.search(r'\b' + re.escape(k) + r'\b', txt) for k in ["demo", "demolition", "abatement", "asbestos", "selective demo"]):
            return (
                "**Demolition & Remediation Takeoffs**:\n\n"
                "We quantify selective architectural demolition, structural teardowns, site clearing, saw-cutting, and dumpster haul-off volumes. "
                "If hazardous material reports or abatement notes are present in the drawings, we can itemize those scopes separately."
            )

        # 14. Green Building / LEED / Solar / Energy Efficiency
        if any(k in txt for k in ["leed", "green building", "solar", "photovoltaic", "energy efficient", "sustainability", "ev charger"]):
            return (
                "**LEED & Sustainable Construction**:\n\n"
                "We estimate high-efficiency MEP systems, continuous insulation assemblies, solar PV arrays, EV charging infrastructure, and sustainable materials. "
                "Provide your specifications, and we will tailor takeoff line items to your sustainability requirements."
            )

        # 15. Geotechnical / Soil Conditions / Foundations
        if any(k in txt for k in ["soil", "geotech", "foundation", "piles", "shoring", "deep foundation"]):
            return (
                "**Geotechnical & Foundation Scopes**:\n\n"
                "We review structural and civil drawings along with geotechnical reports to quantify excavation, cut/fill, deep foundations (helical piles, caissons), and temporary shoring."
            )

        return None

    def _handle_unknown(self, raw_text: str, state: ConversationState) -> Tuple[str, List[str], str]:
        # First check if this is an out-of-the-box construction question
        resolved_answer = self._resolve_out_of_box_query(raw_text)
        if resolved_answer:
            response = (
                f"{resolved_answer}\n\n"
                "Do you have project plans or specifications ready? You can share the PDF or drawing set with us for review."
            )
            quick_replies = [
                "Upload Plans",
                "What tools do you use?",
                "Where are you located?",
                "What's your pricing?"
            ]
            return response, quick_replies, "out_of_the_box_qa"

        # Otherwise consultative construction response
        response = (
            f"{self.kb.unlisted_trade_response}\n\n"
            "Our estimating department handles a wide range of custom commercial, residential, and civil scopes across all 50 states. "
            "If you can share your plans or describe your project requirements, our senior estimators will review the scope and provide a tailored proposal."
        )
        quick_replies = [
            "How much does an estimate cost?",
            "What tools do you use?",
            "Where are you located?",
            "Upload project plans"
        ]
        return response, quick_replies, "unknown"


# Singleton instance
chatbot = EstimatorChatbot()

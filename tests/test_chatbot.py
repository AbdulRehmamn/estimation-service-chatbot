"""
Unit and Integration Tests for Construction Estimator Chatbot
Tests intent detection, entity extraction, business rules enforcement,
state persistence, lead qualification, and Flask endpoints.
"""

import os
import json
import pytest
from chatbot import chatbot
from conversation import ConversationState, session_manager
from intents import intent_detector
from estimator_knowledge import estimator_kb
from lead_manager import lead_manager
from app import app


def test_rule_1_and_2_pricing_logic():
    """Verify Rule 1 & 2: Chatbot never invents fixed dollar price and requests drawings."""
    state = ConversationState("test_session_pricing")
    res = chatbot.process_message("How much does an estimate cost?", state)
    text = res["response"]

    assert "depends on the complexity, size, scope, and requirements" in text
    assert "proposal for our estimating services" in text
    assert "Do you have the plans available?" in text
    # Ensure no fabricated dollar figures
    assert "$" not in text


def test_rule_3_and_4_turnaround_time():
    """Verify Rule 3 & 4: Standard turnaround is 2-3 business days."""
    state = ConversationState("test_session_turnaround")
    res = chatbot.process_message("What is your turnaround time?", state)
    text = res["response"]

    assert "2–3 business days" in text or "2-3 business days" in text
    assert "timeline after reviewing" in text


def test_rule_6_stamping_disclaimer():
    """Verify Rule 6: Never claim legal stamping authority in all jurisdictions."""
    state = ConversationState("test_session_stamping")
    res = chatbot.process_message("Can you stamp our drawings?", state)
    text = res["response"]

    assert "Stamping requirements depend on the project location and applicable regulations" in text
    assert "We can help coordinate the appropriate licensed professional where required" in text


def test_entity_extraction_and_smart_followup():
    """Verify Section 13: Understand 'I need an electrical estimate for a 25,000 sq ft commercial building'."""
    state = ConversationState("test_session_smart")
    user_msg = "I need an electrical estimate for a 25,000 sq ft commercial building."

    entities = intent_detector.extract_entities(user_msg)
    assert entities.get("project_type") == "Commercial"
    assert "Electrical" in entities.get("trades", [])
    assert "25,000 sq ft" in entities.get("square_footage", "")

    # Process through chatbot
    res = chatbot.process_message(user_msg, state)
    text = res["response"]

    # Verify state saved
    assert state.project_type == "Commercial"
    assert "Electrical" in state.trades
    assert "25,000 sq ft" in state.square_footage

    # Verify smart follow-up asks about plans, does not re-ask project type or size
    assert "Do you have the project plans" in text or "plans available" in text
    assert "What type of project is this?" not in text


def test_additional_services():
    """Verify drafting, scheduling, and value engineering responses."""
    state = ConversationState("test_session_services")

    res_ve = chatbot.process_message("Tell me about value engineering", state)
    assert "Value Engineering" in res_ve["response"]
    assert "reduce project costs" in res_ve["response"]

    res_sched = chatbot.process_message("Can you do construction scheduling?", state)
    assert "CPM" in res_sched["response"]
    assert "Primavera P6" in res_sched["response"] or "critical path" in res_sched["response"].lower()

    res_draft = chatbot.process_message("Do you provide CAD drafting services?", state)
    assert "Drafting Services" in res_draft["response"]
    assert "CAD" in res_draft["response"]


def test_lead_generation_and_saving():
    """Verify lead summary generation and JSON storage."""
    state = ConversationState("test_session_lead")
    state.name = "Robert Taylor"
    state.company = "Taylor Builders"
    state.email = "robert@taylorbuilders.com"
    state.phone = "(555) 987-6543"
    state.project_type = "Commercial"
    state.trades = ["Electrical", "Plumbing", "HVAC / Mechanical"]
    state.square_footage = "40,000 sq ft"
    state.plans_available = "Yes (PDF)"

    lead_record = lead_manager.save_lead(state)
    assert lead_record is not None
    assert lead_record["name"] == "Robert Taylor"
    assert "NEW ESTIMATING LEAD" in lead_record["summary_text"]

    all_leads = lead_manager.get_all_leads()
    found = any(l.get("email") == "robert@taylorbuilders.com" for l in all_leads)
    assert found is True


def test_human_handoff():
    """Verify human handoff response when client asks for a human."""
    state = ConversationState("test_session_handoff")
    res = chatbot.process_message("I want to speak with a human estimator", state)
    assert "estimating team should review directly" in res["response"]


def test_flask_endpoints():
    """Verify Flask web server routes."""
    client = app.test_client()

    # Index page
    resp_index = client.get("/")
    assert resp_index.status_code == 200
    assert b"Estimation Service Chat Bot" in resp_index.data

    # Chat endpoint
    resp_chat = client.post("/api/chat", json={
        "message": "What trades do you estimate?",
        "session_id": "test_client_session"
    })
    assert resp_chat.status_code == 200
    data = resp_chat.get_json()
    assert "General & Civil" in data["response"]
    assert "MEP Trades" in data["response"]

    # State endpoint
    resp_state = client.get("/api/state/test_client_session")
    assert resp_state.status_code == 200
    assert resp_state.get_json()["session_id"] == "test_client_session"

    # Reset endpoint
    resp_reset = client.post("/api/reset", json={"session_id": "test_client_session"})
    assert resp_reset.status_code == 200
    assert resp_reset.get_json()["success"] is True


def test_unlisted_trade():
    """Verify unlisted trade response per Section 5."""
    state = ConversationState("test_session_unlisted")
    res = chatbot.process_message("Do you estimate submarine docks or underwater tunnels?", state)
    text = res["response"]
    assert "We handle a wide range of construction trades" in text


def test_multiturn_dialogue_and_rule_compliance():
    """Verify conversation flow from example in Section 14."""
    state = ConversationState("test_session_conversation_flow")

    # Turn 1: Customer asks pricing
    t1 = chatbot.process_message("How much do you charge for an estimate?", state)
    assert "pricing depends on the complexity, size, scope, and requirements" in t1["response"]
    assert "Do you have the plans available?" in t1["response"]

    # Turn 2: Customer specifies commercial building
    t2 = chatbot.process_message("It's a commercial building.", state)
    assert state.project_type == "Commercial"
    assert "commercial" in t2["response"].lower()

    # Turn 3: Customer specifies HVAC and plumbing
    t3 = chatbot.process_message("I need HVAC and plumbing.", state)
    assert "HVAC / Mechanical" in state.trades or "Plumbing" in state.trades
    assert "review the scope" in t3["response"].lower() or "plans" in t3["response"].lower()


def test_email_notification_dispatch():
    """Verify email notification triggers for plan uploads without errors."""
    from unittest.mock import patch, MagicMock
    from email_notifier import email_notifier
    test_state = {
        "name": "Mike Builder",
        "company": "Premier GC LLC",
        "email": "mike@premiergc.com",
        "phone": "(555) 765-4321",
        "project_type": "Commercial",
        "square_footage": "30,000 sq ft",
        "trades": ["Electrical", "Plumbing"],
        "bid_due_date": "Next Friday"
    }
    # Test plan upload notification with mocked network transport
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_resp = MagicMock()
        mock_resp.read.return_value = b'{"success": "true"}'
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        success = email_notifier.notify_plan_upload(
            files_info=[{
                "filename": "office_plans.pdf",
                "size_kb": 1540.2,
                "path": None,
                "download_url": "/api/download/office_plans.pdf"
            }],
            state_dict=test_state
        )
        assert success is True
    assert email_notifier.notification_recipient == "seanray836@gmail.com"


def test_filename_trade_detection_and_download_link():
    """Verify that uploading 07_Electrical_CH_Permit_7.20.2026.pdf detects Electrical trade."""
    from intents import intent_detector
    entities = intent_detector.extract_entities_from_filename("07_Electrical_CH_Permit_7.20.2026.pdf")
    assert "Electrical" in entities.get("trades", [])
    assert entities.get("plans_available") == "Yes (Uploaded)"


def test_serverless_state_hydration():
    """Verify state hydration for Vercel/serverless cold starts."""
    data = {
        "session_id": "hydrated_session_123",
        "name": "Sarah Connor",
        "project_type": "Industrial",
        "trades": ["HVAC / Mechanical"],
        "square_footage": "15,000 sq ft"
    }
    state = ConversationState.from_dict(data)
    assert state.session_id == "hydrated_session_123"
    assert state.name == "Sarah Connor"
    assert state.project_type == "Industrial"
    assert state.trades == ["HVAC / Mechanical"]
    assert state.square_footage == "15,000 sq ft"


def test_tools_response():
    """Verify that asking what tools/software are used returns RSMeans, Bluebeam/PlanSwift, and local vendor list."""
    queries = [
        "what tool you use",
        "what tools do you use?",
        "what software do you guys use for takeoffs?",
        "Do you use Bluebeam or RSMeans?"
    ]
    for q in queries:
        state = ConversationState("sess_tools")
        res = chatbot.process_message(q, state)
        resp = res["response"]
        assert "RSMeans" in resp
        assert "Bluebeam" in resp or "PlanSwift" in resp
        assert "local vendor list" in resp


def test_company_location_response():
    """Verify that asking where the company is located returns Edison NJ, California, NY, and nationwide."""
    exact_expected = "Our head office is in New Jersey at 15 York Drive, Edison, but we got regional locations as well in California and New York. Actually, we work nationwide across all 50 states."
    queries = [
        "where are you located",
        "where is your office located?",
        "what is your address?",
        "where are you guys based?",
        "where your headoffice is",
        "where you based off",
        "where is your head office",
        "where are you based off",
        "where is your headoffice?"
    ]
    for q in queries:
        state = ConversationState("sess_loc")
        res = chatbot.process_message(q, state)
        resp = res["response"]
        assert exact_expected in resp
        assert "15 York Drive" in resp
        assert "Edison" in resp
        assert "New Jersey" in resp
        assert "California" in resp
        assert "New York" in resp
        assert "nationwide" in resp


def test_out_of_the_box_construction_qa():
    """Verify expert out-of-the-box answers for contractor questions on BIM, permits, inflation, bonds, etc."""
    state = ConversationState("sess_oob")

    # Test BIM
    res = chatbot.process_message("Do you work with BIM models or Revit?", state)
    resp, action = res["response"], res["action_type"]
    assert "BIM" in resp or "Revit" in resp
    assert action in ["out_of_the_box_qa", "services", "unknown"]

    # Test Permits
    res = chatbot.process_message("Can you help with permit approval from the building department?", state)
    resp = res["response"]
    assert "permit" in resp.lower() or "ahj" in resp.lower()

    # Test Inflation / Escalation
    res = chatbot.process_message("How do you handle inflation and volatile material price spikes?", state)
    resp = res["response"]
    assert "escalation" in resp.lower() or "volatilit" in resp.lower() or "rsmeans" in resp.lower()

    # Test Bid Bonds
    res = chatbot.process_message("Can we use your estimate for bid bonds and surety underwriting?", state)
    resp = res["response"]
    assert "bond" in resp.lower() or "surety" in resp.lower()

    # Test Prevailing Wage
    res = chatbot.process_message("Are your labor rates prevailing wage / Davis-Bacon compliant?", state)
    resp = res["response"]
    assert "prevailing wage" in resp.lower() or "davis-bacon" in resp.lower()


def test_faq_queries():
    """Verify FAQ responses for accuracy, deliverables format, payment, and CSI divisions."""
    state = ConversationState("sess_faq")

    # Accuracy
    res = chatbot.process_message("How accurate are your estimates?", state)
    resp = res["response"]
    assert "precision" in resp.lower() or "accurate" in resp.lower() or "rsmeans" in resp.lower()

    # Deliverables format
    res = chatbot.process_message("What format do you deliver the estimate in?", state)
    resp = res["response"]
    assert "excel" in resp.lower() or "pdf" in resp.lower()


def test_ballpark_calculator_math():
    """Verify Section 1-5 math for 16, 20, 40, 60, 80, 100, 120 hours."""
    from ballpark_calculator import calculate_ballpark
    # 16 hours
    b16 = calculate_ballpark(16)
    assert b16["low"] == 400 and b16["high"] == 480
    # 20 hours
    b20 = calculate_ballpark(20)
    assert b20["low"] == 500 and b20["high"] == 600
    # 40 hours
    b40 = calculate_ballpark(40)
    assert b40["low"] == 1000 and b40["high"] == 1200
    # 60 hours
    b60 = calculate_ballpark(60)
    assert b60["low"] == 1500 and b60["high"] == 1800
    # 80 hours
    b80 = calculate_ballpark(80)
    assert b80["low"] == 2000 and b80["high"] == 2400
    # 100 hours
    b100 = calculate_ballpark(100)
    assert b100["low"] == 2500 and b100["high"] == 3000
    # 120 hours
    b120 = calculate_ballpark(120)
    assert b120["low"] == 3000 and b120["high"] == 3600


def test_hourly_rate_inquiry():
    """Verify Section 1: Hourly rate response is $25-$30/hour."""
    queries = ["What is your hourly rate?", "what's your hourly rate?", "how much per hour"]
    for q in queries:
        state = ConversationState("sess_hourly")
        res = chatbot.process_message(q, state)
        assert "$25" in res["response"] and "$30" in res["response"]
        assert "per hour" in res["response"]


def test_construction_cost_vs_estimating_fee_distinction():
    """Verify Section 16: Clarify construction cost vs estimating fee."""
    queries = [
        "How much will my 50,000 SF building cost?",
        "What will it cost to build a 20,000 sq ft warehouse?",
        "How much does it cost to build?"
    ]
    for q in queries:
        state = ConversationState("sess_cost_dist")
        res = chatbot.process_message(q, state)
        assert "estimated construction cost" in res["response"]
        assert "fee for our estimating service" in res["response"]


def test_ballpark_incomplete_and_sqft_only():
    """Verify Section 12 & 13: Incomplete info and square footage only."""
    # Section 12: Incomplete info
    state1 = ConversationState("sess_incomp")
    res1 = chatbot.process_message("Can you give me a ballpark price?", state1)
    assert "$25" in res1["response"] and "$30/hour" in res1["response"]
    assert "drawing count" in res1["response"]

    # Section 13: Only square footage
    state2 = ConversationState("sess_sqft_only")
    res2 = chatbot.process_message("It is a 50,000 SF building.", state2)
    assert "starting point" in res2["response"]
    assert "50,000 SF" in res2["response"]
    assert "drawing sheets" in res2["response"]


def test_ballpark_benchmark_scenarios():
    """Verify Section 11 & 14 benchmark examples."""
    # Example 1: 10,000 SF Drywall
    s1 = ConversationState("sess_drywall")
    res1 = chatbot.process_message("I need a drywall takeoff for a small 10,000 SF project. Can you give me a ballpark?", s1)
    assert "12–16 working hours" in res1["response"] or "12-16" in res1["response"]
    assert "$300–$480" in res1["response"] or "$300-$480" in res1["response"]

    # Example 2: 40,000 SF Commercial Electrical + Plumbing
    s2 = ConversationState("sess_comm_ep")
    res2 = chatbot.process_message("I have a 40,000 SF commercial project and need electrical and plumbing estimates.", s2)
    assert "24–32 working hours" in res2["response"] or "24-32" in res2["response"]
    assert "$600–$960" in res2["response"] or "$600-$960" in res2["response"]

    # Example 3: 150,000 SF Commercial All MEP
    s3 = ConversationState("sess_comm_mep")
    res3 = chatbot.process_message("I have a 150,000 SF commercial building with all MEP trades. How much?", s3)
    assert "80–120 working hours" in res3["response"] or "80-120" in res3["response"]
    assert "$2,000–$3,600" in res3["response"] or "$2,000-$3,600" in res3["response"]
    assert "10–15 working days" in res3["response"]

    # Example 4: Multi-detail warehouse with 180 sheets and 700 pages specs (Section 14)
    s4 = ConversationState("sess_warehouse_specs")
    msg4 = "Project: Commercial warehouse, Size: 100,000 SF, Drawings: 180 sheets, Specifications: 700 pages, Trades: Electrical + HVAC + Plumbing, Addenda: 2"
    res4 = chatbot.process_message(msg4, s4)
    assert "60–80 working hours" in res4["response"] or "60-80" in res4["response"]
    assert "$1,500–$2,400" in res4["response"] or "$1,500-$2,400" in res4["response"]
    assert "7–10 working days" in res4["response"]


def test_location_phrasing_variations():
    """Verify that any phrasing variation for location returns the exact Edison, NJ head office response."""
    queries = [
        "where are you located",
        "where you based of?",
        "where you based off",
        "where is your head office",
        "where your head office",
        "where your headoffice is",
        "where are you guys based",
        "what is your address",
        "what state are you located in?"
    ]
    for q in queries:
        state = ConversationState("sess_loc_var")
        res = chatbot.process_message(q, state)
        assert "15 York Drive, Edison" in res["response"]
        assert "nationwide across all 50 states" in res["response"]


def test_real_contractor_stress_test():
    """Verify exact response to real contractor stress test."""
    msg = (
        "I have a 125,000 SF 3-story commercial building. Bid is due Friday at 2 PM. "
        "I need complete architectural, structural, electrical, plumbing, HVAC, fire protection, "
        "drywall, flooring, painting, and concrete takeoffs. I have 380 drawing sheets, 1,200 pages "
        "of specifications, and 4 addenda. Can you give me your price, tell me if you can finish "
        "before the deadline, and tell me exactly what I'll receive?"
    )
    state = ConversationState("sess_stress")
    res = chatbot.process_message(msg, state)
    text = res["response"]
    assert "125,000 SF 3-story commercial building" in text
    assert "4–6 business days" in text
    assert "Friday at 2 PM" in text
    assert "Excel takeoff workbook with live, transparent formulas" in text


def test_advanced_estimating_and_domain_qa():
    """Verify coverage of specialized domain questions across all categories."""
    qa_checks = [
        ("Can you estimate a project if the drawings don't show complete dimensions?", "verified reference dimensions"),
        ("What do you do when architectural and MEP drawings conflict?", "RFI/clarification report"),
        ("Can you estimate from plans that are only 50% complete?", "schematic/design-development budget"),
        ("How do you handle owner-provided materials?", "exclude raw material purchase costs"),
        ("My bid is due in 6 hours. Can you complete the estimate today?", "not feasible and risks severe bid errors"),
        ("The bid closes in 30 minutes. Can you guarantee the estimate will be finished?", "quality estimate in 30 minutes"),
        ("Can you calculate ductwork quantities?", "weight (lbs) by sheet metal gauge"),
        ("Can you estimate a 300,000-square-foot warehouse?", "tilt-up/precast panels"),
        ("What exactly is included in your drywall takeoff?", "Studs, track, fasteners"),
        ("Can you find $500,000 in savings without changing the design intent?", "high-cost assemblies"),
        ("Can you create a construction schedule from the estimate?", "man-hours and crew outputs"),
        ("What happens if you miss an item?", "omitted in error, we revise"),
        ("Can you stamp these drawings even though the project is in another state?", "locally credentialed professional"),
        ("Can you guarantee that my bid will be the lowest?", "No. A winning bid depends on your margins")
    ]
    for query, expected_text in qa_checks:
        state = ConversationState("sess_domain_test")
        res = chatbot.process_message(query, state)
        assert expected_text in res["response"], f"Failed for query '{query}', expected '{expected_text}' in response."





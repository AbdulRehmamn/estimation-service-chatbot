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
    queries = [
        "where are you located",
        "where is your office located?",
        "what is your address?",
        "where are you guys based?"
    ]
    for q in queries:
        state = ConversationState("sess_loc")
        res = chatbot.process_message(q, state)
        resp = res["response"]
        assert "15 York Drive" in resp or "Edison" in resp
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




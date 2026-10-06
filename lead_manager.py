"""
Lead Qualification and Storage Manager
Handles structured lead generation, formatting, and persistent storage
in JSON and CSV formats for the estimating team.
"""

import os
import csv
import json
import time
from typing import Dict, Any, List, Optional
from conversation import ConversationState
from email_notifier import email_notifier

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# On Vercel serverless functions, the file system is read-only except for /tmp
IS_VERCEL = bool(os.environ.get("VERCEL"))
DATA_DIR = "/tmp/data" if IS_VERCEL else os.path.join(BASE_DIR, "data")
LEADS_JSON_PATH = os.path.join(DATA_DIR, "leads.json")
LEADS_CSV_PATH = os.path.join(DATA_DIR, "leads.csv")


class LeadManager:
    """Saves and exports qualified estimating leads."""

    def __init__(self, json_path: str = LEADS_JSON_PATH, csv_path: str = LEADS_CSV_PATH):
        self.json_path = json_path
        self.csv_path = csv_path
        self._ensure_files()

    def _ensure_files(self) -> None:
        os.makedirs(os.path.dirname(self.json_path), exist_ok=True)
        if not os.path.exists(self.json_path):
            with open(self.json_path, "w", encoding="utf-8") as f:
                json.dump([], f, indent=2)

        if not os.path.exists(self.csv_path):
            headers = [
                "lead_id", "timestamp", "name", "company", "email", "phone",
                "project_type", "project_location", "square_footage", "construction_stage",
                "trades", "estimate_type", "plans_available", "drawing_sheets",
                "bid_due_date", "special_requirements", "files"
            ]
            with open(self.csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(headers)

    def generate_lead_text(self, state: ConversationState) -> str:
        """Generates the clean plain-text summary required for the estimating team."""
        trades_str = "\n".join([f"- {t}" for t in state.trades]) if state.trades else "None specified"
        special_str = "\n".join([f"- {s}" for s in state.special_requirements]) if state.special_requirements else "None"
        uploaded_files = ", ".join([f.get("filename", "") for f in state.uploaded_files]) or "None"

        summary = (
            "==================================================\n"
            "NEW ESTIMATING LEAD\n"
            "==================================================\n"
            f"Name: {state.name or 'Not provided'}\n"
            f"Company: {state.company or 'Not provided'}\n"
            f"Email: {state.email or 'Not provided'}\n"
            f"Phone: {state.phone or 'Not provided'}\n\n"
            f"Project Type: {state.project_type or 'General Construction'}\n"
            f"Project Location: {state.project_location or 'Not provided'}\n"
            f"Project Size: {state.square_footage or 'Not provided'}\n"
            f"Stage: {state.construction_stage or 'New Construction / Unspecified'}\n\n"
            f"Trades:\n{trades_str}\n\n"
            f"Estimate Type: {state.estimate_type or 'Detailed Cost Estimate / Bid Estimate'}\n"
            f"Plans Available: {state.plans_available or 'Pending Client Review'}\n"
            f"Drawing Sheets: {state.drawing_sheets or 'To be confirmed upon receipt'}\n"
            f"Bid Due Date: {state.bid_due_date or 'Standard / Not urgent'}\n\n"
            f"Additional Requirements:\n{special_str}\n\n"
            f"Uploaded Plans / Specs: {uploaded_files}\n"
            f"Requested Turnaround: {state.turnaround_required or 'Standard 2–3 Business Days'}\n"
            "=================================================="
        )
        return summary

    def save_lead(self, state: ConversationState) -> Dict[str, Any]:
        """Persists the lead to leads.json and leads.csv."""
        lead_record = {
            "lead_id": f"LEAD-{int(time.time())}",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "session_id": state.session_id,
            "name": state.name or "N/A",
            "company": state.company or "N/A",
            "email": state.email or "N/A",
            "phone": state.phone or "N/A",
            "project_type": state.project_type or "N/A",
            "project_location": state.project_location or "N/A",
            "square_footage": state.square_footage or "N/A",
            "construction_stage": state.construction_stage or "N/A",
            "trades": state.trades,
            "estimate_type": state.estimate_type or "N/A",
            "plans_available": state.plans_available or "N/A",
            "drawing_sheets": state.drawing_sheets or "N/A",
            "bid_due_date": state.bid_due_date or "N/A",
            "special_requirements": state.special_requirements,
            "uploaded_files": [f.get("filename") for f in state.uploaded_files],
            "turnaround_required": state.turnaround_required or "2–3 business days",
            "summary_text": self.generate_lead_text(state)
        }

        # Save to JSON
        try:
            leads = []
            if os.path.exists(self.json_path):
                with open(self.json_path, "r", encoding="utf-8") as f:
                    leads = json.load(f)
            # Check if this session already has a lead record and update it
            existing_idx = next((i for i, l in enumerate(leads) if l.get("session_id") == state.session_id), None)
            if existing_idx is not None:
                lead_record["lead_id"] = leads[existing_idx]["lead_id"]
                leads[existing_idx] = lead_record
            else:
                leads.append(lead_record)

            with open(self.json_path, "w", encoding="utf-8") as f:
                json.dump(leads, f, indent=2)
        except Exception as e:
            print(f"[LeadManager] Error saving JSON lead: {e}")

        # Save to CSV
        try:
            with open(self.csv_path, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    lead_record["lead_id"],
                    lead_record["timestamp"],
                    lead_record["name"],
                    lead_record["company"],
                    lead_record["email"],
                    lead_record["phone"],
                    lead_record["project_type"],
                    lead_record["project_location"],
                    lead_record["square_footage"],
                    lead_record["construction_stage"],
                    ", ".join(lead_record["trades"]),
                    lead_record["estimate_type"],
                    lead_record["plans_available"],
                    lead_record["drawing_sheets"],
                    lead_record["bid_due_date"],
                    ", ".join(lead_record["special_requirements"]),
                    ", ".join(lead_record["uploaded_files"])
                ])
        except Exception as e:
            print(f"[LeadManager] Error saving CSV lead: {e}")

        # Send email alert to seanray836@gmail.com
        try:
            email_notifier.notify_lead_submission(lead_record)
        except Exception as e:
            print(f"[LeadManager] Notice: Email notification skipped: {e}")

        return lead_record

    def get_all_leads(self) -> List[Dict[str, Any]]:
        if os.path.exists(self.json_path):
            with open(self.json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return []


# Singleton
lead_manager = LeadManager()

"""
Estimator Knowledge Base Manager
Loads and provides access to company configuration, service catalog, trades,
pricing policies, turnaround time standards, and technical estimating knowledge.
"""

import os
import json
from typing import Dict, Any, List, Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
KB_PATH = os.path.join(DATA_DIR, "knowledge_base.json")
SERVICES_PATH = os.path.join(DATA_DIR, "services.json")


class EstimatorKnowledgeBase:
    """Provides structured, thread-safe access to company knowledge base and services."""

    def __init__(self, kb_path: str = KB_PATH, services_path: str = SERVICES_PATH):
        self.kb_path = kb_path
        self.services_path = services_path
        self._kb_data: Dict[str, Any] = {}
        self._services_data: Dict[str, Any] = {}
        self.reload()

    def reload(self) -> None:
        """Reload configuration from disk for zero-downtime updates."""
        try:
            if os.path.exists(self.kb_path):
                with open(self.kb_path, "r", encoding="utf-8") as f:
                    self._kb_data = json.load(f)
            else:
                self._kb_data = {}
        except Exception as e:
            print(f"[KnowledgeBase] Warning: Error loading {self.kb_path}: {e}")
            self._kb_data = {}

        try:
            if os.path.exists(self.services_path):
                with open(self.services_path, "r", encoding="utf-8") as f:
                    self._services_data = json.load(f)
            else:
                self._services_data = {}
        except Exception as e:
            print(f"[KnowledgeBase] Warning: Error loading {self.services_path}: {e}")
            self._services_data = {}

    @property
    def company(self) -> Dict[str, Any]:
        return self._kb_data.get("company", {
            "name": "Estimation Service Chat Bot",
            "phone": "640-274-4522",
            "email": "seanray836@gmail.com",
            "website": "www.apexestimates.com"
        })

    @property
    def pricing_response(self) -> str:
        return self._kb_data.get("pricing", {}).get(
            "standard_response",
            "Our pricing depends on the complexity, size, scope, and requirements of the project. If you can share the set of plans/drawings with us, our team can review the project scope and provide you with a proposal for our estimating services."
        )

    @property
    def plan_request_phrase(self) -> str:
        return self._kb_data.get("pricing", {}).get(
            "plan_request",
            "Do you have the plans available? You can share the PDF/set of drawings with us for review."
        )

    @property
    def hourly_rate_response(self) -> str:
        return self._kb_data.get("pricing", {}).get(
            "hourly_rate_response",
            "Our estimating services typically range from $25–$30 per hour. The total cost depends on the project's size, complexity, number of drawings, trades, specifications, and scope."
        )

    @property
    def turnaround_response(self) -> str:
        return self._kb_data.get("turnaround", {}).get(
            "standard_response",
            "Our standard turnaround time is approximately 2–3 business days, depending on the size, complexity, number of drawings, and scope of the project."
        )

    @property
    def unlisted_trade_response(self) -> str:
        return self._kb_data.get("trades", {}).get(
            "unlisted_trade_response",
            "We handle a wide range of construction trades. If you send us the plans or tell me the specific scope, I can help determine whether it can be included in the estimate."
        )

    @property
    def tools_response(self) -> str:
        return self._kb_data.get("tools_and_software", {}).get(
            "response",
            "We use RSMeans for pricing, and Bluebeam or PlanSwift for takeoffs. We also have a local vendor list—as you know, every area has different labor and material rates."
        )

    @property
    def locations_response(self) -> str:
        return self._kb_data.get("locations", {}).get(
            "response",
            "Our head office is in New Jersey at 15 York Drive, Edison, but we got regional locations as well in California and New York. Actually, we work nationwide across all 50 states."
        )

    @property
    def human_handoff_response(self) -> str:
        return self._kb_data.get("human_handoff", {}).get(
            "default_response",
            "That's something our estimating team should review directly. If you can share your plans and project details, our team can review the scope and get back to you with the appropriate proposal."
        )

    def get_faq(self, topic: str) -> Optional[str]:
        return self._kb_data.get("faq", {}).get(topic)

    def get_service_list(self) -> List[Dict[str, Any]]:
        return self._services_data.get("services", [])

    def get_trades_by_category(self) -> Dict[str, List[str]]:
        return self._kb_data.get("trades", {})

    def get_all_trades_flat(self) -> List[str]:
        trades_dict = self.get_trades_by_category()
        all_trades = []
        for cat, items in trades_dict.items():
            if isinstance(items, list):
                all_trades.extend(items)
        return all_trades

    def get_additional_service(self, key: str) -> Optional[Dict[str, Any]]:
        return self._kb_data.get("additional_services", {}).get(key)

    def get_estimate_types(self) -> Dict[str, Any]:
        return self._kb_data.get("estimate_types", {})

    def get_project_types(self) -> List[str]:
        return self._kb_data.get("project_types", [])

    def format_services_summary(self) -> str:
        lines = [
            f"**{self.company.get('name', 'Our company')}** offers end-to-end construction estimating and takeoff services:",
            "",
            "• **Quantity & Material Takeoffs**: Comprehensive counts, linear/square/cubic dimensions, and marked-up plan drawings.",
            "• **Full Construction Cost Estimating**: Material, labor, equipment, and subcontractor cost breakdowns formatted in CSI MasterFormat.",
            "• **Bid & Budget Estimates**: Competitive contractor bid preparation and early conceptual owner budgets.",
            "• **Trade-Specific Takeoffs**: MEP (Mechanical/Electrical/Plumbing), Architectural, Structural, Drywall, Framing, Roofing, and Site Work.",
            "• **Additional Services**: CAD drafting, CPM construction scheduling, value engineering (VE), and PE/SE stamping coordination.",
            "",
            "Would you like an estimate for a specific trade or a full general construction scope?"
        ]
        return "\n".join(lines)

    def format_trades_summary(self) -> str:
        lines = [
            "We provide professional takeoff and estimating services across all major construction trades:",
            "",
            "🏗️ **General & Civil**: Site work, demolition, earthwork, concrete, masonry, structural steel, paving, and utilities.",
            "🏢 **Architectural**: Drywall, framing (metal/wood), insulation, roofing, siding, doors/windows, finishes, flooring, tile, and millwork.",
            "⚡ **MEP Trades**: Electrical (lighting/power/low-voltage), Mechanical & HVAC (ductwork/equipment), and Plumbing (piping/fixtures).",
            "",
            "If your scope involves a specialty trade, we can almost certainly cover it. What specific trades do you need estimated for your project?"
        ]
        return "\n".join(lines)


# Singleton instance
estimator_kb = EstimatorKnowledgeBase()

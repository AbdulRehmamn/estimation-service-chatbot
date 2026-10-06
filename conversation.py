"""
Conversation State Management
Tracks individual client sessions, extracted project entities, and qualification progress.
"""

import os
import time
import uuid
from typing import Dict, Any, List, Optional


class ConversationState:
    """Encapsulates the state and history of a single estimating inquiry conversation."""

    def __init__(self, session_id: Optional[str] = None):
        self.session_id: str = session_id or str(uuid.uuid4())
        self.created_at: float = time.time()
        self.last_active: float = time.time()

        # Contact Details
        self.name: Optional[str] = None
        self.company: Optional[str] = None
        self.email: Optional[str] = None
        self.phone: Optional[str] = None

        # Project Scope & Classification
        self.project_type: Optional[str] = None
        self.project_location: Optional[str] = None
        self.square_footage: Optional[str] = None
        self.construction_stage: Optional[str] = None  # New Construction vs Renovation
        self.trades: List[str] = []
        self.project_scope: Optional[str] = None

        # Estimating Requirements & Plans
        self.estimate_type: Optional[str] = None
        self.plans_available: Optional[str] = None
        self.drawing_sheets: Optional[str] = None
        self.drawing_format: Optional[str] = None
        self.specifications_volume: Optional[str] = None
        self.addenda_count: Optional[str] = None
        self.bid_due_date: Optional[str] = None
        self.turnaround_required: Optional[str] = None
        self.special_requirements: List[str] = []
        self.uploaded_files: List[Dict[str, Any]] = []

        # Workflow tracking
        self.asked_fields: List[str] = []
        self.history: List[Dict[str, Any]] = []
        self.proposal_requested: bool = False

    def touch(self) -> None:
        self.last_active = time.time()

    def add_message(self, role: str, text: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        self.touch()
        self.history.append({
            "role": role,
            "text": text,
            "timestamp": time.time(),
            "metadata": metadata or {}
        })

    def update_from_entities(self, entities: Dict[str, Any]) -> List[str]:
        """Update state with newly extracted entities. Returns list of newly populated fields."""
        updated: List[str] = []
        self.touch()

        for key, val in entities.items():
            if not val:
                continue

            if key == "trades":
                if isinstance(val, list):
                    for trade in val:
                        if trade not in self.trades:
                            self.trades.append(trade)
                            if "trades" not in updated:
                                updated.append("trades")
            elif key == "special_requirements":
                if isinstance(val, list):
                    for req in val:
                        if req not in self.special_requirements:
                            self.special_requirements.append(req)
                            if "special_requirements" not in updated:
                                updated.append("special_requirements")
            elif hasattr(self, key):
                current_val = getattr(self, key)
                if current_val is None or (isinstance(current_val, str) and len(str(val)) > len(current_val)):
                    setattr(self, key, val)
                    updated.append(key)

        return updated

    def add_uploaded_file(self, filename: str, file_path: str, file_size: int, download_url: Optional[str] = None) -> None:
        self.touch()
        self.uploaded_files.append({
            "filename": filename,
            "path": file_path,
            "size": file_size,
            "download_url": download_url or f"/api/download/{os.path.basename(file_path)}",
            "timestamp": time.time()
        })
        self.plans_available = "Yes (Uploaded)"

    def get_missing_critical_info(self) -> List[str]:
        """Identify which primary estimating requirements are still unknown."""
        missing = []
        if not self.project_type:
            missing.append("project_type")
        if not self.trades:
            missing.append("trades")
        if not self.plans_available:
            missing.append("plans_available")
        if not self.square_footage:
            missing.append("square_footage")
        if not self.bid_due_date:
            missing.append("bid_due_date")
        if not (self.email or self.phone):
            missing.append("contact_info")
        return missing

    def is_lead_ready(self) -> bool:
        """Determines if enough project details exist to compose a formal estimating lead."""
        has_scope = bool(self.project_type or self.trades or self.square_footage or self.uploaded_files)
        has_contact = bool(self.email or self.phone or self.name)
        return has_scope and has_contact

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "name": self.name,
            "company": self.company,
            "email": self.email,
            "phone": self.phone,
            "project_type": self.project_type,
            "project_location": self.project_location,
            "square_footage": self.square_footage,
            "construction_stage": self.construction_stage,
            "trades": self.trades,
            "project_scope": self.project_scope,
            "estimate_type": self.estimate_type,
            "plans_available": self.plans_available,
            "drawing_sheets": self.drawing_sheets,
            "drawing_format": self.drawing_format,
            "specifications_volume": self.specifications_volume,
            "addenda_count": self.addenda_count,
            "bid_due_date": self.bid_due_date,
            "turnaround_required": self.turnaround_required,
            "special_requirements": self.special_requirements,
            "uploaded_files": [
                {
                    "filename": f.get("filename") if isinstance(f, dict) else str(f),
                    "download_url": f.get("download_url", f"/api/download/{os.path.basename(f.get('path', ''))}") if isinstance(f, dict) else f"/api/download/{str(f)}"
                }
                for f in self.uploaded_files
            ],
            "proposal_requested": self.proposal_requested,
            "created_at": self.created_at,
            "last_active": self.last_active
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationState":
        """Reconstruct state from a serialized dictionary (for serverless/Vercel state hydration)."""
        instance = cls(data.get("session_id"))
        for k in [
            "name", "company", "email", "phone", "project_type", "project_location",
            "square_footage", "construction_stage", "project_scope", "estimate_type",
            "plans_available", "drawing_sheets", "drawing_format", "specifications_volume",
            "addenda_count", "bid_due_date", "turnaround_required", "proposal_requested"
        ]:
            if k in data and data[k] is not None:
                setattr(instance, k, data[k])
        if "trades" in data and isinstance(data["trades"], list):
            instance.trades = list(data["trades"])
        if "special_requirements" in data and isinstance(data["special_requirements"], list):
            instance.special_requirements = list(data["special_requirements"])
        if "uploaded_files" in data and isinstance(data["uploaded_files"], list):
            instance.uploaded_files = [
                {"filename": f if isinstance(f, str) else f.get("filename", "")}
                for f in data["uploaded_files"]
            ]
        return instance


class SessionManager:
    """Manages active conversation sessions in memory with expiration safeguards and serverless hydration."""

    def __init__(self, ttl_seconds: int = 86400):
        self.sessions: Dict[str, ConversationState] = {}
        self.ttl_seconds = ttl_seconds

    def get_session(self, session_id: Optional[str] = None, client_state: Optional[Dict[str, Any]] = None) -> ConversationState:
        self.cleanup_expired()
        if not session_id or session_id not in self.sessions:
            if client_state and isinstance(client_state, dict):
                state = ConversationState.from_dict(client_state)
                self.sessions[state.session_id] = state
                return state
            new_state = ConversationState(session_id)
            self.sessions[new_state.session_id] = new_state
            return new_state
        return self.sessions[session_id]

    def reset_session(self, session_id: str) -> ConversationState:
        new_state = ConversationState(session_id)
        self.sessions[session_id] = new_state
        return new_state

    def cleanup_expired(self) -> None:
        now = time.time()
        expired = [sid for sid, state in self.sessions.items() if (now - state.last_active) > self.ttl_seconds]
        for sid in expired:
            del self.sessions[sid]


# Singleton session manager
session_manager = SessionManager()

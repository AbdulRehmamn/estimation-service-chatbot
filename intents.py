"""
Intent Detection and Entity Extraction Module
Uses weighted keyword/phrase matching, regular expressions, and semantic heuristics
without requiring any external AI API.
"""

import re
from typing import Dict, List, Tuple, Any, Optional

# Keywords and phrases for intent scoring
# Multi-word phrases receive higher matching weight
INTENT_PATTERNS: Dict[str, List[Tuple[str, float]]] = {
    "greeting": [
        ("hello", 1.0), ("hi", 1.0), ("hey", 1.0), ("good morning", 1.5),
        ("good afternoon", 1.5), ("good evening", 1.5), ("howdy", 1.0),
        ("greetings", 1.2), ("start", 0.8), ("help me", 0.9)
    ],
    "pricing": [
        ("how much does an estimate cost", 3.0),
        ("what is your pricing", 3.0),
        ("how much do you charge", 3.0),
        ("what are your rates", 3.0),
        ("give me a price", 3.0),
        ("estimate cost", 2.5),
        ("pricing", 2.0),
        ("how much", 1.8),
        ("price", 1.5),
        ("rates", 1.5),
        ("fee", 1.5),
        ("fees", 1.5),
        ("charge", 1.5),
        ("cost", 1.2),
        ("quote", 1.3),
        ("expensive", 1.2),
        ("per square foot cost", 2.5),
        ("cost to estimate", 2.5)
    ],
    "turnaround_time": [
        ("how long does an estimate take", 3.0),
        ("what is your turnaround time", 3.0),
        ("what's your turnaround time", 3.0),
        ("how fast can you complete it", 3.0),
        ("when will i receive the estimate", 3.0),
        ("turnaround time", 2.5),
        ("turnaround", 2.0),
        ("how long", 1.8),
        ("how fast", 1.8),
        ("time required", 2.0),
        ("delivery time", 2.0),
        ("delivery schedule", 2.0),
        ("when can you finish", 2.0),
        ("timeline", 1.5),
        ("completion time", 1.8),
        ("lead time", 1.8),
        ("rush estimate", 2.0),
        ("urgent", 1.2),
        ("quick turnaround", 2.0)
    ],
    "services": [
        ("what services do you provide", 3.0),
        ("what do you do", 2.5),
        ("services we provide", 2.5),
        ("estimating services", 2.0),
        ("list of services", 2.5),
        ("services offered", 2.5),
        ("services", 1.5),
        ("scope of work", 1.5),
        ("capabilities", 1.8)
    ],
    "trades": [
        ("what trades do you estimate", 3.0),
        ("which trades", 2.5),
        ("trades you cover", 2.5),
        ("trades we estimate", 2.5),
        ("trades list", 2.0),
        ("trades", 1.5),
        ("subcontractors", 1.2),
        ("csi divisions", 2.0)
    ],
    "estimating": [
        ("construction cost estimating", 2.5),
        ("cost estimating", 2.0),
        ("estimating", 1.5),
        ("estimator", 1.5),
        ("estimate", 1.2),
        ("bid estimate", 2.0),
        ("budget estimate", 2.0),
        ("detailed estimate", 2.0)
    ],
    "takeoff": [
        ("quantity takeoff", 2.5),
        ("takeoff", 2.0),
        ("takeoffs", 2.0),
        ("qto", 2.5),
        ("take off", 1.8),
        ("measurements", 1.2),
        ("count sheets", 1.8)
    ],
    "material_takeoff": [
        ("material takeoff", 2.5),
        ("material count", 2.0),
        ("bill of materials", 2.5),
        ("bom", 2.0),
        ("materials only", 2.0),
        ("material schedule", 2.0)
    ],
    "labor_estimate": [
        ("labor estimate", 2.5),
        ("labor quantities", 2.2),
        ("man hours", 2.5),
        ("labor rates", 2.2),
        ("labor cost", 2.0),
        ("crew production", 2.0)
    ],
    "drafting": [
        ("drafting services", 2.8),
        ("cad drafting", 2.5),
        ("drafting", 2.0),
        ("shop drawings", 2.2),
        ("as-built", 2.0),
        ("autocad", 1.8),
        ("drawings preparation", 2.0)
    ],
    "stamping": [
        ("stamp", 3.5),
        ("stamping", 3.5),
        ("stamped", 3.5),
        ("engineering stamp", 3.0),
        ("stamp drawings", 3.0),
        ("stamped plans", 3.0),
        ("stamping coordination", 3.0),
        ("stamping services", 3.0),
        ("pe stamp", 3.0),
        ("structural stamp", 3.0),
        ("engineering coordination", 2.5),
        ("architectural stamp", 2.5),
        ("seal drawings", 2.5)
    ],
    "scheduling": [
        ("construction scheduling", 2.8),
        ("project schedule", 2.5),
        ("scheduling", 2.0),
        ("cpm schedule", 2.8),
        ("gantt chart", 2.5),
        ("primavera", 2.2),
        ("p6", 2.0),
        ("project timeline", 2.2),
        ("work breakdown structure", 2.5)
    ],
    "value_engineering": [
        ("value engineering", 3.0),
        ("ve review", 2.5),
        ("reduce project costs", 2.5),
        ("cost optimization", 2.2),
        ("cost saving", 2.0),
        ("constructability review", 2.2)
    ],
    "project_type": [
        ("project type", 2.5),
        ("commercial building", 2.0),
        ("residential home", 2.0),
        ("multifamily project", 2.0),
        ("type of project", 2.2)
    ],
    "residential": [
        ("residential", 2.2),
        ("single family", 2.2),
        ("custom home", 2.2),
        ("home builder", 2.0),
        ("house", 1.5)
    ],
    "commercial": [
        ("commercial", 2.2),
        ("office building", 2.2),
        ("retail", 2.0),
        ("warehouse", 2.0),
        ("shopping center", 2.0),
        ("tenant improvement", 2.2),
        ("commercial building", 2.2)
    ],
    "mep": [
        ("mep", 2.5),
        ("mechanical electrical plumbing", 2.8),
        ("mep trades", 2.5),
        ("mechanical and electrical", 2.2)
    ],
    "electrical": [
        ("electrical", 2.5),
        ("electric", 2.0),
        ("lighting", 1.8),
        ("switchgear", 2.0),
        ("low voltage", 2.0),
        ("fire alarm", 2.0),
        ("power distribution", 2.2)
    ],
    "plumbing": [
        ("plumbing", 2.5),
        ("piping", 2.0),
        ("sanitary", 2.0),
        ("domestic water", 2.0),
        ("drainage", 1.8),
        ("plumbing fixtures", 2.2)
    ],
    "mechanical": [
        ("mechanical", 2.5),
        ("chillers", 2.0),
        ("boilers", 2.0),
        ("mechanical equipment", 2.2)
    ],
    "hvac": [
        ("hvac", 2.5),
        ("heating", 1.8),
        ("cooling", 1.8),
        ("air conditioning", 2.2),
        ("ventilation", 2.0),
        ("ductwork", 2.2),
        ("rooftop units", 2.0)
    ],
    "drywall": [
        ("drywall", 2.5),
        ("sheetrock", 2.2),
        ("gypsum", 2.0),
        ("drywall takeoff", 2.5)
    ],
    "framing": [
        ("framing", 2.5),
        ("metal stud", 2.2),
        ("wood framing", 2.2),
        ("structural framing", 2.2)
    ],
    "flooring": [
        ("flooring", 2.5),
        ("carpet", 2.0),
        ("tile", 2.0),
        ("hardwood", 2.0),
        ("vct", 2.0),
        ("lvt", 2.0)
    ],
    "concrete": [
        ("concrete", 2.5),
        ("foundation", 2.0),
        ("slab", 2.0),
        ("footings", 2.0),
        ("rebar", 2.0),
        ("flatwork", 2.0)
    ],
    "roofing": [
        ("roofing", 2.5),
        ("shingles", 2.0),
        ("tpo", 2.0),
        ("epdm", 2.0),
        ("metal roof", 2.0),
        ("flat roof", 2.0)
    ],
    "painting": [
        ("painting", 2.5),
        ("coatings", 2.0),
        ("paint takeoff", 2.5),
        ("interior paint", 2.0)
    ],
    "plans": [
        ("plans", 1.8),
        ("drawings", 1.8),
        ("blueprints", 2.0),
        ("prints", 1.5),
        ("specifications", 1.8),
        ("pdf set", 2.0),
        ("set of drawings", 2.5),
        ("drawing set", 2.2),
        ("have the plans", 2.5),
        ("plans are ready", 2.5)
    ],
    "upload_plans": [
        ("upload plans", 2.8),
        ("share plans", 2.5),
        ("send drawings", 2.5),
        ("attached file", 2.2),
        ("upload drawing", 2.5),
        ("attach drawings", 2.5)
    ],
    "estimate_type": [
        ("estimate type", 2.5),
        ("preliminary estimate", 2.5),
        ("budget estimate", 2.5),
        ("detailed estimate", 2.5),
        ("bid estimate", 2.5),
        ("change order estimate", 2.5)
    ],
    "bid_deadline": [
        ("bid due date", 2.8),
        ("bid deadline", 2.8),
        ("when is the bid due", 2.8),
        ("bid date", 2.2),
        ("tender deadline", 2.5),
        ("submission deadline", 2.5)
    ],
    "contact": [
        ("contact", 2.0),
        ("phone number", 2.0),
        ("email address", 2.0),
        ("reach me at", 2.5),
        ("my email is", 2.8),
        ("my phone is", 2.8),
        ("my name is", 2.8)
    ],
    "quote": [
        ("request a proposal", 2.8),
        ("get a quote", 2.5),
        ("request proposal", 2.8),
        ("send proposal", 2.5),
        ("hire you", 2.0),
        ("proposal", 2.0)
    ],
    "company_information": [
        ("company information", 2.5),
        ("about your company", 2.5),
        ("who are you", 2.0),
        ("contact info", 2.0),
        ("phone", 1.5),
        ("email", 1.5),
        ("website", 1.5)
    ],
    "process": [
        ("how does it work", 2.5),
        ("what is the process", 2.5),
        ("estimating process", 2.5),
        ("how do we start", 2.5),
        ("steps", 1.8),
        ("workflow", 2.0)
    ],
    "human_handoff": [
        ("speak to an estimator", 2.8),
        ("talk to a human", 2.8),
        ("speak to a person", 2.8),
        ("human estimator", 2.8),
        ("call me", 2.2),
        ("talk to someone", 2.5),
        ("representative", 2.0)
    ],
    "tools": [
        ("what tool you use", 3.5),
        ("what tools you use", 3.5),
        ("what tool do you use", 3.5),
        ("what tools do you use", 3.5),
        ("what software do you use", 3.5),
        ("what software", 3.0),
        ("tools", 2.0),
        ("software", 2.0),
        ("rs means", 3.0),
        ("rsmeans", 3.0),
        ("rs mean", 3.0),
        ("bluebeam", 3.0),
        ("blue beam", 3.0),
        ("planswift", 3.0),
        ("plan swift", 3.0),
        ("takeoff tool", 2.8),
        ("estimating software", 2.8),
        ("local vendor list", 3.0),
        ("vendor list", 2.5)
    ],
    "company_location": [
        ("where are you located", 3.5),
        ("where is your office", 3.5),
        ("what is your address", 3.5),
        ("where are you based", 3.5),
        ("head office", 3.0),
        ("office location", 3.0),
        ("your location", 3.0),
        ("edison", 2.5),
        ("15 york drive", 3.5),
        ("new jersey", 2.5),
        ("where are you guys", 3.0)
    ],
    "accuracy": [
        ("how accurate", 3.0),
        ("accuracy", 2.5),
        ("accurate estimate", 2.5),
        ("how do you ensure accuracy", 3.0)
    ],
    "deliverables_format": [
        ("what format", 3.0),
        ("what format do you deliver", 3.5),
        ("deliverables", 2.5),
        ("excel format", 2.8),
        ("marked up pdf", 2.8)
    ],
    "payment_terms": [
        ("how do we pay", 3.0),
        ("payment terms", 3.0),
        ("how do i pay", 3.0),
        ("payment", 2.0),
        ("deposit", 2.0),
        ("pricing terms", 2.5)
    ],
    "csi_divisions": [
        ("csi divisions", 3.0),
        ("masterformat", 3.0),
        ("csi masterformat", 3.5),
        ("division 01", 2.5),
        ("csi codes", 2.8)
    ],
    "samples": [
        ("sample estimate", 3.0),
        ("sample takeoff", 3.0),
        ("sample work", 2.8),
        ("show me a sample", 3.0),
        ("examples", 2.0)
    ],
    "thanks": [
        ("thank you", 2.0),
        ("thanks", 1.8),
        ("appreciate it", 2.0),
        ("great thanks", 2.2)
    ]
}


class IntentDetector:
    """Classifies user messages into primary/secondary intents and extracts entities."""

    def __init__(self, patterns: Dict[str, List[Tuple[str, float]]] = INTENT_PATTERNS):
        self.patterns = patterns

    def detect_intents(self, message: str, threshold: float = 1.0) -> List[Tuple[str, float]]:
        """Score message against known intent patterns and return sorted candidates."""
        cleaned = message.lower().strip()
        scores: Dict[str, float] = {}

        for intent, keyword_list in self.patterns.items():
            for phrase, weight in keyword_list:
                # Check for exact word boundaries or phrase presence
                if " " in phrase:
                    if phrase in cleaned:
                        scores[intent] = scores.get(intent, 0.0) + weight
                else:
                    # Word boundary check for single words to avoid partial matching (e.g. "hi" in "this")
                    pattern = r'\b' + re.escape(phrase) + r'\b'
                    if re.search(pattern, cleaned):
                        scores[intent] = scores.get(intent, 0.0) + weight

        # Sort by score descending
        sorted_intents = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        return [item for item in sorted_intents if item[1] >= threshold]

    def get_primary_intent(self, message: str) -> str:
        matches = self.detect_intents(message)
        if matches:
            return matches[0][0]
        return "unknown"

    def extract_entities(self, text: str) -> Dict[str, Any]:
        """Extract all identifiable project attributes from user input."""
        entities: Dict[str, Any] = {}
        cleaned = text.strip()
        cleaned_lower = cleaned.lower()

        # 1. Square Footage / Size
        sqft_patterns = [
            r'(\b\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:k\b)?\s*(?:sq\s*ft|sqft|square\s*feet|square\s*foot|sf|sq\.?\s*ft\.?|s\.f\.)\b',
            r'(\b\d+(?:\.\d+)?(?:k|K))\s*(?:sq\s*ft|sqft|square\s*feet|square\s*foot|sf)?\b',
            r'(?:size\s*(?:is|of)?|approx(?:imately)?)\s*[:=]?\s*(\d+(?:,\d{3})*|\d+)\s*(?:sq\s*ft|sqft|sf)?\b'
        ]
        for pattern in sqft_patterns:
            match = re.search(pattern, cleaned, re.IGNORECASE)
            if match:
                raw_val = match.group(0).strip()
                entities["square_footage"] = raw_val
                break

        # 2. Email Address
        email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
        email_match = re.search(email_pattern, cleaned)
        if email_match:
            entities["email"] = email_match.group(0)

        # 3. Phone Number
        phone_pattern = r'(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
        phone_match = re.search(phone_pattern, cleaned)
        if phone_match:
            entities["phone"] = phone_match.group(0)

        # 4. Project Types
        project_types_map = {
            "commercial": ["commercial", "office", "retail", "shopping center", "strip mall", "bank", "store"],
            "residential": ["residential", "single family", "single-family", "custom home", "home", "house"],
            "multifamily": ["multifamily", "multi-family", "apartment", "apartments", "condo", "condominium", "townhome"],
            "industrial": ["industrial", "warehouse", "manufacturing", "distribution center", "plant"],
            "restaurant": ["restaurant", "cafe", "bar", "dining", "fast food"],
            "hotel": ["hotel", "motel", "hospitality", "resort"],
            "healthcare": ["healthcare", "hospital", "clinic", "medical", "dental office"],
            "educational": ["school", "university", "college", "daycare", "classroom"],
            "institutional": ["institutional", "church", "library", "civic", "government building"]
        }
        for ptype, aliases in project_types_map.items():
            if any(re.search(r'\b' + re.escape(alias) + r'\b', cleaned_lower) for alias in aliases):
                entities["project_type"] = ptype.capitalize()
                break

        # 5. Project Stage / Scope (New Construction vs Renovation)
        if re.search(r'\b(new\s*construction|ground\s*up|ground-up|new\s*build)\b', cleaned_lower):
            entities["construction_stage"] = "New Construction"
        elif re.search(r'\b(renovation|remodel|remodeling|addition|tenant\s*improvement|ti|retro-?fit|rehab)\b', cleaned_lower):
            entities["construction_stage"] = "Renovation / Remodel"

        # 6. Trades Detected (list)
        trade_keywords = {
            "Electrical": ["electrical", "electric", "lighting", "low voltage", "switchgear", "fire alarm", "power distribution"],
            "HVAC / Mechanical": ["hvac", "mechanical", "heating", "cooling", "air conditioning", "ventilation", "ductwork", "exhaust"],
            "Plumbing": ["plumbing", "piping", "sanitary", "domestic water", "storm drain", "sewer", "water supply"],
            "Drywall": ["drywall", "sheetrock", "gypsum board", "taping", "drywall finish"],
            "Framing": ["framing", "metal stud", "wood framing", "stud framing", "light gauge"],
            "Concrete": ["concrete", "foundation", "slab", "footings", "rebar", "flatwork", "pour"],
            "Masonry": ["masonry", "brick", "cmu", "block", "stone veneer"],
            "Roofing": ["roofing", "shingles", "tpo", "epdm", "metal roof", "roof replacement"],
            "Flooring": ["flooring", "carpet", "tile", "hardwood", "vct", "lvt", "epoxy floor"],
            "Painting": ["painting", "paint", "coatings"],
            "Demolition": ["demolition", "demo", "wrecking"],
            "Site Work / Civil": ["site work", "earthwork", "excavation", "grading", "utilities", "paving", "landscaping", "civil"],
            "Fire Protection": ["fire protection", "fire sprinkler", "sprinklers"],
            "Insulation": ["insulation", "batt insulation", "spray foam"],
            "Doors & Windows": ["doors", "windows", "storefront", "glazing"],
            "Millwork": ["millwork", "cabinetry", "casework", "trim"],
            "Full Project (All Trades)": [
                "full project", "entire project", "whole project", "all trades",
                "full bid", "bid on full project", "complete project", "complete scope",
                "turnkey", "general scope", "full estimating", "all scopes"
            ]
        }
        detected_trades: List[str] = []
        for trade_name, aliases in trade_keywords.items():
            if any(re.search(r'\b' + re.escape(a) + r'\b', cleaned_lower) for a in aliases):
                detected_trades.append(trade_name)
        if detected_trades:
            entities["trades"] = detected_trades

        # 7. Estimate Type
        estimate_types_map = {
            "Detailed Estimate": ["detailed estimate", "detailed cost", "full estimate", "line-item", "line item"],
            "Bid Estimate": ["bid estimate", "bid proposal", "subcontractor bid", "contractor bid", "bid on full project"],
            "Budget Estimate": ["budget estimate", "conceptual estimate", "preliminary estimate", "rough budget", "budgeting"],
            "Quantity Takeoff": ["quantity takeoff", "takeoff only", "qto", "counts only"],
            "Material Takeoff": ["material takeoff", "material list", "bill of materials", "bom"],
            "Labor Estimate": ["labor estimate", "man hours", "labor only", "labor costs"],
            "Change Order": ["change order", "change-order", "scope change", "revision"]
        }
        for est_name, aliases in estimate_types_map.items():
            if any(re.search(r'\b' + re.escape(a) + r'\b', cleaned_lower) for a in aliases):
                entities["estimate_type"] = est_name
                break

        # 8. Plans Availability
        if re.search(r'\b(have\s*(?:the\s*)?plans|plans\s*are\s*ready|i\s*have\s*(?:the\s*)?(?:drawings|blueprints|cad|pdf)|drawings\s*available|yes\s*(?:we\s*do|i\s*do)?|plans\s*available|uploaded|plans\s*attached)\b', cleaned_lower):
            entities["plans_available"] = "Yes"
        elif re.search(r'\b(no\s*plans|don\'t\s*have\s*plans|not\s*yet|drawings\s*pending|conceptual\s*only|no\s*drawings)\b', cleaned_lower):
            entities["plans_available"] = "No / In Progress"

        # 9. Number of Sheets
        sheets_match = re.search(r'(\b\d+)\s*(?:drawing\s*sheets|sheets|pages|drawings|prints)\b', cleaned_lower)
        if sheets_match:
            entities["drawing_sheets"] = f"{sheets_match.group(1)} sheets"

        # 10. Bid Due Date / Deadline
        deadline_match = re.search(r'(?:bid\s*(?:due|deadline)|due\s*(?:on|by|date)?)\s*[:=]?\s*([a-zA-Z0-9\s/,-]+(?:\b202\d|\bnext\s*week|\bfriday|\bmonday|\btomorrow|\bsoon))', cleaned_lower)
        if deadline_match:
            raw_due = deadline_match.group(1).strip()
            entities["bid_due_date"] = raw_due.rstrip(".,;")
        elif re.search(r'\b(by\s*(?:next\s*)?(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday))\b', cleaned_lower):
            match = re.search(r'\b(by\s*(?:next\s*)?(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday))\b', cleaned_lower)
            if match:
                entities["bid_due_date"] = match.group(0).strip()

        # 11. Customer Name and Company (heuristic)
        name_match = re.search(r'(?:my\s*name\s*is|i\s*am|this\s*is)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', cleaned)
        if name_match:
            entities["name"] = name_match.group(1).strip()

        company_match = re.search(r'(?:company\s*(?:name)?\s*(?:is|:)|my\s*company\s*is|(?:i\s*am|we\s*are|calling)\s+(?:from|with))\s+([A-Za-z0-9\s,&.-]{2,40})', cleaned, re.IGNORECASE)
        if not company_match:
            company_match = re.search(r'\b(?:from|with)\s+([A-Za-z0-9\s,&.-]{2,30}\b(?:LLC|Inc|Builders|Contracting|Construction|Group|Corp|Architects|LLP))\b', cleaned, re.IGNORECASE)
        if company_match:
            entities["company"] = company_match.group(1).strip()

        # 12. Location (City, State, or General Region)
        us_states = [
            "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut",
            "Delaware", "Florida", "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa",
            "Kansas", "Kentucky", "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan",
            "Minnesota", "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire",
            "New Jersey", "New Mexico", "New York", "North Carolina", "North Dakota", "Ohio",
            "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota",
            "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington", "West Virginia",
            "Wisconsin", "Wyoming"
        ]
        us_cities = [
            "New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia",
            "San Antonio", "San Diego", "Dallas", "Austin", "Jacksonville", "San Jose",
            "Fort Worth", "Columbus", "Charlotte", "Indianapolis", "San Francisco",
            "Seattle", "Denver", "Washington", "Boston", "El Paso", "Nashville", "Detroit",
            "Oklahoma City", "Portland", "Las Vegas", "Memphis", "Louisville", "Baltimore",
            "Milwaukee", "Albuquerque", "Tucson", "Fresno", "Sacramento", "Mesa", "Kansas City",
            "Atlanta", "Omaha", "Colorado Springs", "Raleigh", "Miami", "Long Beach",
            "Virginia Beach", "Oakland", "Minneapolis", "Tampa", "Tulsa", "Arlington", "New Orleans",
            "Cleveland", "Orlando", "Newark", "Pittsburgh", "Cincinnati", "St. Louis", "Salt Lake City"
        ]

        # Match explicit city or state mentions
        for state_name in us_states:
            if re.search(r'\b' + re.escape(state_name) + r'\b', cleaned, re.IGNORECASE):
                entities["project_location"] = state_name
                break

        if "project_location" not in entities:
            for city_name in us_cities:
                if re.search(r'\b' + re.escape(city_name) + r'\b', cleaned, re.IGNORECASE):
                    entities["project_location"] = city_name
                    break

        if "project_location" not in entities:
            # Pattern matching: "located in Miami, FL", "in Dallas", "site at Chicago"
            loc_pattern = r'(?:located\s*in|project\s*is\s*in|in|at|city\s*is)\s+([A-Za-z\s]+(?:,\s*[A-Za-z]{2})?)'
            loc_match = re.search(loc_pattern, cleaned, re.IGNORECASE)
            if loc_match:
                extracted_loc = loc_match.group(1).strip().rstrip(".,")
                # Filter out false positives like "in 2 days" or "in electrical"
                if not any(w in extracted_loc.lower() for w in ["days", "weeks", "hours", "electrical", "plumbing", "progress", "advance", "need"]):
                    entities["project_location"] = extracted_loc.title()

        return entities

    def extract_entities_from_filename(self, filename: str) -> Dict[str, Any]:
        """Inspects uploaded drawing filenames (e.g. 07_Electrical_CH_Permit_7.20.2026.pdf) to detect trades and scope."""
        cleaned_name = filename.replace("_", " ").replace("-", " ")
        entities = self.extract_entities(cleaned_name)

        # Additional keyword checks tailored for drawing sheet conventions
        lower_name = cleaned_name.lower()
        if "electrical" in lower_name or "elec" in lower_name:
            if "trades" not in entities: entities["trades"] = []
            if "Electrical" not in entities["trades"]: entities["trades"].append("Electrical")

        if "plumbing" in lower_name or "plumb" in lower_name:
            if "trades" not in entities: entities["trades"] = []
            if "Plumbing" not in entities["trades"]: entities["trades"].append("Plumbing")

        if "hvac" in lower_name or "mechanical" in lower_name or "mech" in lower_name:
            if "trades" not in entities: entities["trades"] = []
            if "HVAC / Mechanical" not in entities["trades"]: entities["trades"].append("HVAC / Mechanical")

        if "structural" in lower_name:
            if "trades" not in entities: entities["trades"] = []
            if "Concrete" not in entities["trades"]: entities["trades"].append("Concrete")

        if "drywall" in lower_name:
            if "trades" not in entities: entities["trades"] = []
            if "Drywall" not in entities["trades"]: entities["trades"].append("Drywall")

        if "roof" in lower_name or "roofing" in lower_name:
            if "trades" not in entities: entities["trades"] = []
            if "Roofing" not in entities["trades"]: entities["trades"].append("Roofing")

        if "civil" in lower_name or "site" in lower_name:
            if "trades" not in entities: entities["trades"] = []
            if "Site Work / Civil" not in entities["trades"]: entities["trades"].append("Site Work / Civil")

        # Mark plans as available
        entities["plans_available"] = "Yes (Uploaded)"

        return entities


# Singleton instance
intent_detector = IntentDetector()

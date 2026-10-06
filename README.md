# Estimation Service Chat Bot

A professional, enterprise-grade AI-style chatbot for a **Construction Cost Estimation Services company** built with **pure Python logic**—requiring **zero paid or external AI APIs** (no OpenAI, ChatGPT, Gemini, or Claude needed).

The chatbot behaves as a knowledgeable construction estimating sales advisor. It qualifies project requirements, answers customer questions, explains trades and estimating types, enforces strict estimating business rules, captures project details, collects qualified leads, and guides clients toward sharing their plans and drawings for proposal review.

---

## Key Features

* **100% Pure Python Logic**: Keyword matching, weighted multi-word phrase scoring, regex entity extraction, and conversational state tracking without external API costs or latency.
* **Strict Construction Business Rules**:
  * Never invents fixed project prices without reviewing drawings.
  * Standard turnaround time clearly defined as **2–3 business days** (timelines for complex projects confirmed upon drawing review).
  * Professional engineering & stamping coordination disclaimer (avoids claiming universal in-house stamping authority).
  * Distinguishes between preliminary budgets, detailed line-item bids, and material takeoffs.
  * Consultative human estimator escalation for complex inquiries.
* **Smart Follow-Up Dialog**: Automatically remembers extracted entities (e.g. `25,000 sq ft`, `Commercial`, `Electrical`) and avoids re-asking questions already answered.
* **Trade Detection Engine**: Identifies over 30 construction trades across General Civil, Architectural, and MEP (Mechanical, Electrical, Plumbing, HVAC, Drywall, Concrete, Framing, Roofing, etc.).
* **Lead Qualification & Storage**: Saves structured project leads to `data/leads.json` and `data/leads.csv` with instant plain-text estimator summary formatting.
* **Modern Web Interface**:
  * Blueprint & Safety Amber construction theme with glassmorphic cards.
  * Live interactive **Project Scope & Lead Progress Tracker** sidebar.
  * Drag-and-drop plan/drawing upload support (`.pdf`, `.dwg`, `.dxf`, `.cad`, `.xlsx`, `.zip`).
  * Quick-prompt pills and context-aware suggestion chips.
  * Request Proposal modal & Lead Summary view modal.
  * Real-time conversation reset and clear chat.

---

## Project Structure

```
ai chat bot/
├── app.py                      # Flask web application & REST API endpoints
├── chatbot.py                  # Core estimating sales dialogue engine & rule enforcer
├── intents.py                  # Intent scoring dictionary & entity extraction regex
├── conversation.py             # ConversationState & SessionManager classes
├── estimator_knowledge.py      # Knowledge base accessor & formatted responses
├── lead_manager.py             # Structured lead storage (JSON & CSV)
│
├── data/
│   ├── knowledge_base.json     # Company config, pricing rules, trades, FAQ
│   ├── services.json           # Catalog of estimating & planning services
│   ├── leads.json              # Persistent stored leads (JSON)
│   └── leads.csv               # Persistent stored leads (CSV export)
│
├── templates/
│   └── index.html              # Responsive, modern construction chat UI
│
├── static/
│   ├── css/
│   │   └── style.css           # Modern design system & responsive styling
│   └── js/
│       └── chatbot.js          # Client-side chat, uploads, and tracker sync
│
├── uploads/                    # Directory where uploaded client plans are stored
├── tests/
│   └── test_chatbot.py         # Complete unit and integration test suite
│
├── requirements.txt            # Lightweight dependencies (Flask, Werkzeug, pytest)
├── start.bat                   # 1-Click launcher: installs dependencies, opens browser & starts server
└── README.md                   # Documentation & setup guide
```

---

## Quickstart (1-Click Launch)

Simply double-click the **`start.bat`** file inside this folder!

It will automatically:
1. Verify Python is installed.
2. Install all necessary dependencies from `requirements.txt`.
3. Launch the chatbot web server.
4. Open your default web browser directly to `http://127.0.0.1:5000`.

---

## Manual Installation & Startup

### 1. Prerequisites
* Python 3.9+ (Tested on Python 3.13)
* `pip` package manager

### 2. Install Dependencies
Open a terminal in this project directory:
```bash
pip install -r requirements.txt
```

### 3. Run the Web Server
```bash
python app.py
```

Open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

## Running the Automated Test Suite

Run pytest to verify all intent patterns, entity extractions, business rules, and API routes:

```bash
python -m pytest tests/test_chatbot.py -v
```

---

## Configuration Guide

You can customize company details, services, and trades without touching any Python code:

### Modifying Company Information & Pricing
Edit `data/knowledge_base.json`:
* `company`: Name, phone, email, website, and operating hours.
* `pricing`: Standard pricing explanation and drawing request phrase.
* `turnaround`: Standard delivery time (2–3 business days).
* `trades`: Categories and trade lists (General, Architectural, MEP, Civil).

### Modifying Services Catalog
Edit `data/services.json` to add or update estimating deliverables, typical turnaround times, and client types.

---

## API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Serves the web chat application |
| `POST` | `/api/chat` | Send user message and get bot response + state |
| `POST` | `/api/upload` | Upload drawing files (PDF, DWG, CAD, ZIP) |
| `GET` | `/api/state/<session_id>` | Retrieve current conversation state |
| `POST` | `/api/lead/submit` | Submit contact details and request proposal |
| `GET` | `/api/leads` | Retrieve all captured leads as JSON |
| `GET` | `/api/leads/export` | Download all captured leads as CSV |
| `POST` | `/api/reset` | Reset conversation state for a new session |
| `GET` | `/api/config` | Retrieve current company & service configuration |

---

## Sample Conversation Workflow

### Step 1: Pricing Inquiry
**Client:** "How much does an estimate cost?"  
**Chatbot:**  
> "Our pricing depends on the complexity, size, scope, and requirements of the project. If you can share the set of plans/drawings with us, our team can review the project scope and provide you with a proposal for our estimating services.  
> Our standard turnaround time is approximately 2–3 business days, depending on the size, complexity, number of drawings, and scope of the project.  
> Do you have the plans available? You can share the PDF/set of drawings with us for review."

### Step 2: Scope Identification
**Client:** "I need an electrical estimate for a 25,000 sq ft commercial building."  
**Chatbot (Extracts: Trade=Electrical, Size=25,000 sq ft, Type=Commercial):**  
> "Got it! We noted your trades (Electrical) and project type (Commercial) and size (25,000 sq ft).  
> Do you have the project plans and specifications available? You can share the PDF or drawing set with us for review."

### Step 3: Plan Submission & Lead Summary
**Client attaches `electrical_drawings.pdf`:**  
**Chatbot:**  
> "📄 Successfully received your file: `electrical_drawings.pdf` (1,240 KB).  
> Our estimating team can review these drawings to confirm project scope, pricing, and turnaround time.  
> Could you please share your Name, Company, and Email or Phone Number so we can send the proposal once reviewed?"

---

## Email Notifications for Plan Uploads

Whenever a contractor uploads plans or submits an estimating inquiry, an email alert is automatically prepared for **`seanray836@gmail.com`** including:
* Drawing file name and size (with the file attached if under 15MB)
* Contractor Name, Company, Email, and Phone
* Project Type, Square Footage, Trades, and Bid Deadline

### Enabling Live Gmail Delivery
To send actual emails to your inbox:
1. Generate an **App Password** from your Google Account:
   * Go to [https://myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
   * Create an app named "Estimating Chatbot" and copy the 16-character password.
2. Set these environment variables (or add them in Vercel Project Settings > Environment Variables):
   * `SMTP_HOST`: `smtp.gmail.com`
   * `SMTP_PORT`: `587`
   * `SMTP_USER`: `your_sending_email@gmail.com`
   * `SMTP_PASS`: `your_16_character_app_password`
   * `NOTIFICATION_EMAIL`: `seanray836@gmail.com`

---

## Deploying to Vercel (No Local Terminal Needed)

The project is fully pre-configured for Vercel Serverless deployment with `vercel.json` and `api/index.py`. Once deployed to Vercel, the chatbot answers **24/7 without needing your computer or local terminal running**.

### Quick Steps to Deploy:
1. **Push to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit for Estimation Service Chat Bot"
   # Push to your GitHub repository
   ```
2. **Import into Vercel:**
   * Go to [https://vercel.com](https://vercel.com) and click **"Add New Project"**.
   * Select your GitHub repository.
   * (Optional) Add your email environment variables (`SMTP_USER`, `SMTP_PASS`, `NOTIFICATION_EMAIL`) in **Environment Variables**.
   * Click **Deploy**.
3. **Done!**
   * Vercel will give you a live production URL (e.g. `https://your-chatbot.vercel.app`).
   * The chatbot will respond to contractors around the clock from the cloud without needing any local terminal running.

---

## License & Support
Built for professional construction estimators, general contractors, and trade subcontractors. Fully extensible with databases, CRM integrations, email notifications, and CAD/BIM viewers as your estimating business scales.

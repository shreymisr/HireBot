# 🤖 TalentScout — AI-Powered Hiring Assistant

TalentScout is an intelligent hiring assistant built with **Streamlit** and powered by the **Groq** inference API (LLaMA 3.3 70B). It conducts structured initial screening interviews — collecting candidate details one field at a time, generating per-technology technical questions, and producing an exportable session report — all through a conversational chat interface.

---

## ✨ Features

| Feature | Description |
| :--- | :--- |
| **5-Stage Interview Pipeline** | Greeting → Profile → Tech Stack → Interview → Wrap-Up with a live progress tracker |
| **One-Field-at-a-Time Collection** | The LLM asks for each piece of candidate info sequentially, never combining fields |
| **Per-Technology Questions** | After tech stack is collected, 3–5 numbered questions (basic → advanced) are generated for *each* technology |
| **Live Candidate Profile Card** | Sidebar card fills in real-time as info is collected; unfilled fields show *pending…* |
| **Sentiment Analysis** | Every user message passes through `distilbert-base-uncased-finetuned-sst-2-english` — displayed as 😊/😐/😟 emoji, score bar, and trend chart |
| **Session Export (JSON)** | One-click download of profile + conversation + sentiment history + timestamp |
| **GDPR Data Notice** | Visible disclaimer accompanying every export |
| **Navy/White Recruiter Theme** | Professional dark sidebar, teal accents, styled profile card, and Inter typography |
| **Exit Keyword Detection** | Client-side detection of `quit`, `exit`, `bye`, `goodbye` — graceful wrap-up without API call |
| **Off-Topic Guardrails** | System prompt prevents the LLM from deviating from hiring-related topics |

---

## 📁 Project Structure

```
HireBot/
├── app.py              # Main Streamlit UI, session state, routing
├── config.py           # System prompt, stage definitions, constants
├── llm.py              # Groq client, tech-stack injection, stage parsing
├── sentiment.py        # HuggingFace sentiment pipeline (cached)
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
└── README.md           # This file
```

---

## 🚀 Installation

### Prerequisites

- **Python 3.10+**
- A free [Groq API key](https://console.groq.com)

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/HireBot.git
cd HireBot

# 2. Create and activate a virtual environment
python -m venv venv
# Windows
.\venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

# 3. Install dependencies
pip install streamlit groq transformers torch python-dotenv

# 4. Set up your API key
cp .env.example .env
# Edit .env and replace gsk_your_key_here with your actual Groq API key
```

> **Note:** The first run will download the DistilBERT sentiment model (~260 MB). This happens once and is cached thereafter.

---

## ⚙️ Configuration

Create a `.env` file in the project root:

```env
# Groq API Key — get yours at https://console.groq.com
GROQ_API_KEY=gsk_your_key_here
```

Alternatively, you can enter the key directly in the app's sidebar at runtime — it will be stored for the session only.

---

## ▶️ Usage

```bash
streamlit run app.py
```

1. Open `http://localhost:8501` in your browser
2. Enter your Groq API key in the sidebar (or load it from `.env`)
3. Type **"hi"** or **"begin"** to start the interview
4. Answer questions one at a time — watch the profile card fill in
5. After tech stack is collected, the bot generates per-technology technical questions
6. Type **"bye"**, **"exit"**, **"quit"**, or **"goodbye"** at any time to end early
7. Use the **⬇️ Export Session** button to download the full session as JSON

---

## 🧠 Prompt Design

The system prompt (`config.py → SYSTEM_PROMPT`) is designed around several key principles:

### Structured Flow Control
The LLM is instructed to collect 7 fields **one at a time** in a fixed order (Name → Email → Phone → Experience → Position → Location → Tech Stack), preventing it from combining questions or skipping ahead.

### Stage Markers
Every LLM response must begin with a `[STAGE:stage_name]` marker (e.g., `[STAGE:gathering_info]`). The app strips these markers from the displayed text and uses them to drive the UI's stage tracker — keeping the LLM in control of transitions while the app handles visual state.

### Dynamic Injection
When the candidate provides their tech stack, a secondary system message (`TECH_STACK_INJECTION`) is injected into the API call. This explicitly instructs the model to generate **3–5 numbered questions per technology**, progressing from basic to advanced, covering one technology at a time.

### Guardrails
- **Off-topic deflection:** The prompt instructs the model to politely redirect any non-hiring conversation
- **Clarification requests:** Vague answers prompt follow-ups rather than silent acceptance
- **Prompt confidentiality:** The model is instructed never to reveal its system prompt

---

## 🎭 Sentiment Analysis

Each user message is passed through a locally-run HuggingFace `transformers` pipeline:

- **Model:** `distilbert-base-uncased-finetuned-sst-2-english`
- **Backend:** PyTorch (CPU inference, no GPU required)
- **Caching:** `@st.cache_resource` — the model loads once and persists across reruns
- **Neutral threshold:** Predictions below 65% confidence on either label are classified as 😐 Neutral

The sidebar displays:
- The latest mood (emoji + label)
- A confidence score bar
- A session-wide positivity trend chart (after 2+ messages)

---

## 🔒 Data Privacy

> **This application processes personal data. Handle responsibly.**

- **No data is stored server-side.** All information lives in `st.session_state` and is discarded when the browser tab closes or the page is refreshed.
- **No data leaves the machine** except the Groq API calls (encrypted over HTTPS) and the HuggingFace model download (first run only).
- **Session exports** are client-side JSON downloads. The GDPR banner reminds users to handle exported files in accordance with applicable data-protection regulations.
- **API keys** are never logged, persisted, or transmitted beyond the Groq API.

If deploying in a production environment, ensure you comply with GDPR, CCPA, or other applicable privacy frameworks — including obtaining explicit candidate consent before conducting AI-assisted interviews.

---

## 🧩 Challenges & Solutions

| Challenge | Solution |
| :--- | :--- |
| **LLM deviating from the one-field-at-a-time rule** | Explicit system prompt constraints with numbered field order and a "never combine fields" directive |
| **Tracking which field is being collected** | `profile_field_index` counter in session state, advanced after each LLM response during collection stages |
| **Stage transitions without structured output** | `[STAGE:stage_name]` marker convention parsed via regex; stripped before display |
| **Sentiment model loading latency** | `@st.cache_resource` loads the model once; subsequent reruns are instant |
| **Chat history format compatibility** | Groq uses OpenAI-compatible `user`/`assistant` roles — no conversion needed (unlike Gemini's `user`/`model` + `parts` format) |
| **Generating relevant technical questions** | Dynamic `TECH_STACK_INJECTION` system message with the candidate's exact technologies, reinforcing per-tech numbered questions |
| **Sidebar visual clutter with many sections** | Navy/white CSS theme with clear visual hierarchy, styled card components, and contextual visibility (sentiment hides when empty) |

---

## 📜 License

This project is provided as-is for educational and demonstration purposes.

---

<p align="center">
  <b>Powered by</b> Groq ⚡ &nbsp;|&nbsp; LLaMA 3.3 70B &nbsp;|&nbsp; Streamlit &nbsp;|&nbsp; HuggingFace Transformers
</p>

# 📖 LifeBook AI — AI-Powered Intelligent Digital Diary & Personal Life Graph

> *"Your life, remembered and connected."*

**LifeBook AI** is a modern, privacy-first, full-stack intelligent journal application. It bridges the warmth of a classic leather-bound personal diary with the power of multimodal AI, temporal understanding, an interactive **Personal Life Graph**, and a grounded **RAG (Retrieval-Augmented Generation)** assistant.

---

## 🌟 Why LifeBook AI?

Traditional note-taking and diary apps are passive repositories: you write notes, and they get buried in chronological lists. 

**LifeBook AI turns your memories into an active, connected second brain**:
- Speak, type, or snap a photo of your day.
- Automatically extract and link **People**, **Places**, **Activities**, **Projects**, and **Commitments**.
- Detect temporal commitments (e.g., *"Today 8:14 PM I have a Google meeting"*) and schedule proactive reminders.
- Track habits and identify gentle routine deviations.
- Ask questions like *"What am I forgetting?"* or *"When did I last meet Ravi?"* and get grounded, natural-language answers backed by your real memories.

---

## ✨ Key Features & Capabilities

### 1. 🎨 Handcrafted Skeuomorphic Journal UI
- **Leather-Bound Aesthetic**: Styled like an authentic open leather book sitting on a mahogany desk with warm cream paper pages, bookmark ribbon tabs, and taped polaroids.
- **Two-Page Layout**:
  - **Left Page**: Daily reflection canvas, live Web Audio recording waveforms, 11-stage processing tracker, and memory timeline.
  - **Right Page**: Proactive commitments needing attention, habit & routine cards with confidence gauges, historical *"On This Day"* resurfacing, and mood tracking.

### 2. 🎙️ Multimodal Memory Capture
- **Live Voice Journaling**: Integrated HTML5 Web Audio API capturing real-time voice with live frequency waveform visualization.
- **Photo Upload & OCR**: Upload photos and handwritten notes with automatic **Tesseract OCR** text extraction and image attachment.
- **Zero Data Loss Guarantee**: An 11-stage durability-first state machine saves the raw audio/text payload to disk *before* AI processing begins.

### 3. ⏰ Temporal Understanding & Proactive Reminders
- Intelligently parses relative and absolute date/time expressions (e.g., *"Tomorrow at 10 AM"*, *"Today 8:14 PM"*).
- Automatically converts statements into structured, actionable commitments with due dates and real-time dashboard notifications.

### 4. 🕸️ Interactive Personal Life Graph
- Discovers and builds bidirectional relational links: `Person ↔ Memory`, `Place ↔ Activity`, `Project ↔ Commitment`.
- Features graph deduplication, timeline filtering, and interactive visual exploration of your life's connections.

### 5. 🔄 Habit & Routine Intelligence
- Identifies recurring weekly patterns (e.g., *"Morning Coffee at Coffee House"*).
- Computes confidence scores and gently alerts you to routine deviations without judgment.

### 6. 💬 "Ask LifeBook" Hybrid RAG Assistant
- Combines **Dense Vector Embeddings** (`sentence-transformers`) with **Graph-based Traversal**.
- Generates natural, grounded answers with citations to your original diary entries.

### 7. 🔒 Privacy & Data Sovereignty
- Strict JWT authentication scoping every resource to the authenticated user.
- Pluggable AI: seamlessly switch between Google Gemini, OpenRouter, or fully offline local heuristic fallback.
- One-click full data export (JSON backup) and complete account deletion.

---

## 🏗️ Technology Stack & Rationale

| Layer | Technologies Used | Why We Chose This Stack |
| :--- | :--- | :--- |
| **Frontend** | **React 19, TypeScript, Vite, Tailwind CSS v4** | • **React 19 & TypeScript**: Provides high component modularity, predictable state management, and strict type safety.<br>• **Vite**: Sub-second Hot Module Replacement (HMR) and optimized lightning-fast builds.<br>• **Tailwind CSS v4**: Enables rapid customization of the rich skeuomorphic journal textures, badges, and responsive layouts.<br>• **Lucide Icons & Canvas Confetti**: Lightweight visual icons and celebratory micro-interactions. |
| **Audio Capture** | **HTML5 MediaRecorder & Web Audio API** | • Native browser APIs record audio and visualize real-time frequency waveforms without heavy external plugins or third-party tracking. |
| **Backend** | **FastAPI (Python 3.10+), Pydantic v2** | • **FastAPI**: Industry-leading asynchronous performance, built-in OpenAPI documentation, and native dependency injection.<br>• **Pydantic v2**: High-speed schema validation and strict serialization for API reliability. |
| **Database & ORM** | **SQLAlchemy ORM, SQLite & PostgreSQL/pgvector** | • **Dual-Mode Database**: Zero-configuration instant setup with **SQLite** for development, plus plug-and-play support for **PostgreSQL + pgvector** in cloud production. |
| **AI & Retrieval** | **Google Gemini 2.5 Flash, OpenRouter, sentence-transformers** | • **Gemini 2.5 Flash**: State-of-the-art reasoning, ultra-fast responses, and extensive context windows.<br>• **Local Embeddings**: `all-MiniLM-L6-v2` produces fast, lightweight 384-dimensional vector embeddings.<br>• **Heuristic Local Fallback**: Ensures the system remains 100% operational even without internet or API keys. |
| **OCR Engine** | **Tesseract OCR & Pillow** | • Secure, on-device/local text recognition from journal photos, receipts, and handwritten notes. |
| **Testing** | **Pytest, Vitest, TypeScript Compiler** | • End-to-end regression prevention with **110+ comprehensive backend automated tests** and strict TypeScript build validation. |

---

## 📂 Project Structure

```text
Ai_diary/
├── backend/
│   ├── app/
│   │   ├── api/routes/          # FastAPI route handlers (auth, diary, graph, RAG, etc.)
│   │   ├── core/                # App configuration, database session, security, CORS
│   │   ├── models/              # SQLAlchemy database models (User, Entry, Graph, etc.)
│   │   ├── schemas/             # Pydantic validation and serialization schemas
│   │   ├── services/            # Core business logic (AI, RAG, Graph, OCR, STT, etc.)
│   │   └── main.py              # Application entry point
│   ├── tests/                   # Pytest automated test suite (110+ tests)
│   ├── requirements.txt         # Python backend dependencies
│   └── .env.example             # Backend environment variables template
├── frontend/
│   ├── src/
│   │   ├── components/          # React components (Journal pages, modals, widgets, graph)
│   │   ├── services/            # Frontend API client and HTTP services
│   │   ├── types/               # TypeScript interfaces and type definitions
│   │   ├── App.tsx              # Main application root
│   │   └── main.tsx             # React DOM entry point
│   ├── package.json             # Frontend dependencies and scripts
│   ├── tsconfig.json            # TypeScript configuration
│   └── vite.config.ts           # Vite build configuration
└── README.md                    # Project documentation
```

---

## 🚀 Quickstart & Setup Guide

### Prerequisites
- **Python**: `3.10` or higher
- **Node.js**: `18.x` or higher (`npm` included)
- **Tesseract OCR** (Optional, for photo text extraction)

---

### Step 1: Clone the Repository
```bash
git clone https://github.com/your-username/Ai_diary.git
cd Ai_diary
```

---

### Step 2: Backend Setup & Run

1. Navigate to the `backend` folder:
   ```bash
   cd backend
   ```

2. Create and activate a Python virtual environment:
   ```bash
   # Windows:
   python -m venv .venv
   .\.venv\Scripts\activate

   # macOS / Linux:
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure your `.env` file:
   ```bash
   # Copy the example environment file
   copy .env.example .env   # Windows
   # cp .env.example .env   # macOS / Linux
   ```
   *Edit `backend/.env` to configure your preferred AI provider:*
   ```env
   # AI Provider: 'gemini', 'openrouter', or 'local'
   AI_PROVIDER=gemini
   GEMINI_API_KEY=your_gemini_api_key_here
   GEMINI_MODEL=gemini-2.5-flash

   # Secret Key for JWT Authentication
   SECRET_KEY=your_secure_random_secret_key_here
   ```

5. Seed demo data (Optional but recommended):
   ```bash
   python ../database/seed_demo.py
   ```
   > **Default Demo Login:**
   > - **Email**: `jothiram@lifebook.ai`
   > - **Password**: `LifeBook2026!`

6. Start the FastAPI backend server:
   ```bash
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```
   - 📡 **Backend API**: `http://127.0.0.1:8000`
   - 📑 **Interactive Swagger Docs**: `http://127.0.0.1:8000/docs`

---

### Step 3: Frontend Setup & Run

Open a new terminal window:

1. Navigate to the `frontend` folder:
   ```bash
   cd frontend
   ```

2. Install Node dependencies:
   ```bash
   npm install
   ```

3. Start the Vite development server:
   ```bash
   npm run dev
   ```
   - 💻 **Web Application**: `http://localhost:5173`

---

## 🧪 Running Automated Tests & Quality Checks

### Run Backend Tests (110 Tests)
```bash
cd backend
.\.venv\Scripts\pytest -q   # Windows
# pytest -q                 # macOS / Linux
```

### Run Frontend Typecheck & Production Build
```bash
cd frontend
npm run build
```

---

## 🔒 Security & Privacy Practices

- **Zero Untrusted User ID**: All database queries and operations strictly resolve ownership via the authenticated JWT token `current_user.id`.
- **Password Security**: Passwords are cryptographically hashed using `bcrypt`.
- **Masked Logging**: PII, API tokens, and credentials are automatically stripped/masked from server logs.
- **Local Fallback**: Full functionality remains available locally with zero external API calls if preferred.

---

## 📄 License
This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

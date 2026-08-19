# ActionMate AI - Development Log

This document serves as a historical record of all the architecture decisions, feature implementations, and progress made on the ActionMate AI project during our pair-programming sessions.

## 🏗️ Core Architecture Established
- **Frontend:** React with TypeScript, bundled by Vite for lightning-fast hot reloading.
- **Backend:** FastAPI (Python) serving RESTful endpoints and acting as a bridge to the local LLM.
- **Database:** Currently using an in-memory array (`MOCK_TASKS`), prepped for easy migration to a real database (like PostgreSQL or Firebase Firestore) later.

## 🤖 AI Integrations (Gemini 2.5 Flash)
We completely upgraded to cloud APIs in favor of **powerful AI inference** using Gemini 2.5 Flash.
1. **Risk Analysis Engine (`/api/analyze_risk`):** An asynchronous endpoint that reads a newly created task and predicts the percentage risk of failure, returning a JSON breakdown of recommendations.
2. **Execution Coach (`/api/chat`):** A conversational agent that has full hidden context of your active dashboard. It can advise you on what to prioritize.
3. **AI Task Planner (`/api/planner_chat`):** A structured data-gathering agent. Instead of filling out a form, you talk to the AI. It asks follow-up questions, extracts the parameters, and outputs a strict JSON payload to automatically spawn the task.

## 🎨 Frontend & UI/UX
- **Glassmorphism Design:** Implemented a highly premium, modern aesthetic using CSS backdrop-filters, semi-transparent panels, and micro-animations (hover lifts, fade-ins).
- **Dynamic Theming System:** Built a robust CSS-variable architecture allowing instant, no-reload switching between 6 custom themes (`dark`, `light`, `ocean`, `cyberpunk`, `midnight`, `forest`).
- **Zero-State Logic:** Designed the app to gracefully handle empty states. If there are no tasks, the app hides the AI widgets and displays beautiful "Start Here" call-to-actions.
- **Interactive Modules:** 
  - *Dynamic Priority List*: Real-time rendering of tasks with their live AI risk scores.
  - *Timeline Calendar*: A chronological visual mapping of upcoming deadlines.
  - *Habit Tracker*: A GitHub-style dot-matrix tracker for daily streaks.

## 🔐 Authentication
- Integrated **Firebase Authentication**.
- Implemented standard **OAuth 2.0 OpenID Connect** via the "Continue with Google" button.
- The UI dynamically updates the sidebar to show the user's real Google profile picture and display name upon successful login.

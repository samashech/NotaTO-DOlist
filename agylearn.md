# Web Development & AI: The Fundamentals

This is your personal learning resource. We used many of these concepts to build ActionMate AI. Understanding *why* these pieces exist will help you easily build your next projects!

---

## 1. How the Internet Communicates
### **REST APIs (Representational State Transfer)**
Think of a REST API like a waiter at a restaurant. Your Frontend (the customer) cannot go into the kitchen to get food. Instead, the Frontend gives an "order" (a Request) to the Waiter (the API), and the Waiter goes to the Backend (the kitchen), gets the food (the Data), and brings it back (the Response).
- **GET Request:** Asking the waiter to bring you the menu (Fetching data).
- **POST Request:** Giving the waiter your written order to give to the chef (Sending new data to save).

### **JSON (JavaScript Object Notation)**
This is the language the Waiter speaks. It is a simple way of formatting text so that Python, JavaScript, and databases can all easily understand it. 
*Example:* `{"title": "Study", "hours": 2}`

---

## 2. The Frontend (The Customer Interface)
### **Vanilla HTML/JS vs. Frameworks (React)**
In the old days, every time you clicked a button, the browser had to ask the server for a completely new HTML page, causing the screen to flash white and reload. **React** changed this. It loads one single blank page, and uses JavaScript to instantly swap out components (like tabs) without ever reloading the browser. This is called a **Single Page Application (SPA)**.

### **Vite vs. Next.js**
- **Vite:** This is what we used. It is a "bundler." It takes all your React code and packages it extremely fast so you can run it locally in the browser. It runs entirely on the client's (user's) machine.
- **Next.js:** A more advanced React framework. Instead of sending an empty page to the user and making their computer build the UI, the server builds the UI *first* and sends the finished HTML to the user. This is called **Server-Side Rendering (SSR)** and is great for SEO (Search Engine Optimization).

### **State (`useState`) & Effects (`useEffect`)**
In React, **State** is the memory of a component. If a variable changes, React automatically redraws the screen to reflect that change.
**Effects** are things that happen "on the side", like saying: *"As soon as this screen loads, run a network request to fetch my tasks."*

---

## 3. The Backend (The Kitchen)
### **FastAPI (Python)**
This is the server framework we used. We chose Python because AI tools (like the Gemini SDK) are natively written for Python. FastAPI is exceptionally fast because it handles requests asynchronously (it doesn't freeze the whole server while waiting for the AI to finish thinking).

---

## 4. Artificial Intelligence
### **Cloud AI (Gemini 2.5 Flash)**
We integrated the **Gemini 2.5 Flash API** directly into our Python backend. 

### **How it Works**
Our FastAPI Python code sends the user's prompt securely over the internet to Google's highly-optimized Gemini infrastructure, allowing incredibly fast responses for parsing tasks and scheduling.

---

## 5. Security
### **Authentication vs. Authorization**
- **Authentication:** Proving *who* you are (Logging in via Google).
- **Authorization:** Proving *what* you are allowed to do (You are allowed to see your tasks, but not my tasks).

### **OAuth 2.0 (Continue with Google)**
Instead of forcing users to create a password (which is dangerous if our database gets hacked), we use OAuth. We send the user to Google's website. Google verifies their password. Google then sends the user back to our website with a "VIP Wristband" (a Token) that says: *"I am Google, and I verify this is Sameer."* Your app looks at the wristband and logs you in.

---

## 6. Your Questions & Curiosity

### Q: How does the system know if the user has completed a task?
The system relies on an explicit action from the user triggering a chain of events:
1. **The UI Interaction:** When you click the circular completion button next to a task in the React frontend, it fires a JavaScript function (`completeTaskAPI`).
2. **The HTTP Request:** That function sends an HTTP `PUT` request to the Python backend (e.g., `/api/tasks/123`) containing a small JSON payload: `{"status": "completed"}`. 
3. **Database Update:** The FastAPI server receives this request, finds the task in the database (or our `MOCK_TASKS` memory list), and overwrites its `status` field.
4. **UI Rerender:** The frontend asks the backend for the updated list of tasks. Because the frontend is programmed to only display tasks where `status !== 'completed'`, the task instantly vanishes from your dashboard.

### Q: What ways did we implement to notify the user to do their task without annoying push notifications?
We used a design concept called **Passive Environmental Tension**. Instead of interrupting you with standard OS popups that you might quickly swipe away, we dynamically changed the visual environment around you as the deadline approached:
1. **The "Heartbeat" Glow (CSS):** We used CSS `@keyframes` animations to make the task cards visually pulse. A JavaScript function checks the time remaining. If a task is < 2 hours away, it applies an orange pulse. If it is < 30 minutes away, it shifts to an aggressive red pulse.
2. **Dynamic AI Greetings (React/JS):** Instead of a static "Good evening" header, a function sorts your pending tasks and checks the closest deadline and its AI-generated Risk Score. If time is running out, the greeting is replaced with a passive-aggressive warning (e.g., *"My analysis shows an 85% chance you fail this task. Prove me wrong."*).
3. **The Extension "Warning Shot" (Chrome APIs):** We modified the `background.js` script in the Chrome extension. If a task is within 15 minutes of failing, and you open one of its blocked sites (like YouTube), the extension uses `chrome.scripting.executeScript` to inject a large red banner directly into the HTML of the website to warn you before you get distracted.

### Anime.js Modal Implementation
* **Concept:** Implement a smooth modal dialog animation using Anime.js when interacting with tasks on the dashboard.
* **Process:**
  * Imported Anime.js after installing it as a dependency.
  * Designed a task detail modal UI overlay that gets triggered via the `selectedTask` React state.
  * Tied a React `useEffect` hook to play an `opacity` fade and `scale` pop-in animation targeting the modal's CSS classes right when it renders.
  * Configured a closing function that triggers a reverse exit animation before setting the React state back to null.
* **Implementation Specs:** Animation speeds were hard-locked to exactly 500ms using easing curves like `easeOutElastic` for bouncy entrances and `easeInQuad` for swift exits.

---

## 7. Recent Architectural Implementations

### **Custom UI & Animations**
- **Task Completion Sliding Animation:** When a task is marked complete, it doesn't instantly vanish. A CSS animation slides it to the right and fades the opacity to 0 over a 500ms duration. This gives the user satisfying visual feedback before React removes the component from the DOM.
- **Sidebar Collapse:** Implemented a togglable sidebar navigation (Dashboard, Planner, Habits, Settings). The state is managed globally via React `useState`, allowing the main content area to expand dynamically when the sidebar is minimized.
- **Global Settings Page:** A centralized dashboard to control UI settings (Themes, Animations, AI Personality). Settings are persisted across sessions using browser `localStorage`.
- **Custom Mouse Cursors:** Built a system to replace the default OS cursor with interactive designs (Trailing, Invert, Magnetic, Spotlight). A top-level React `useEffect` hooks into `mousemove` events to calculate velocity and track coordinates, while setting the body CSS to `cursor: none`. **Crucial Fix:** The custom cursor logic was updated to only apply *after* the user logs in, ensuring the default cursor remains visible on the authentication screen.

### **Chrome Extension - Critical Task Widget**
- We utilized Chrome's `chrome.scripting.executeScript` to inject a persistent, floating UI widget into the bottom-left corner of *any* website the user visits if they have a task marked as "Critical". This ensures they cannot escape their most important deadline.

### **Data Leakage & Database Persistence**
- **The Problem:** The FastAPI backend initially used global Python lists (e.g., `MOCK_TASKS = []`) to store data. Because these lists exist in shared RAM, tasks assigned by User A were visible to User B when they logged in.
- **The Solution (JSON DB Isolation):** We migrated the backend to use a persistent JSON file database (`actionmate_db.json`). We implemented a `window.fetch` interceptor in the React frontend that automatically injects an `X-User-Id` header (containing the Firebase UID) into every single API call. The backend reads this header and strictly maps all data reads/writes to that specific `user_id` inside the JSON structure, guaranteeing total data isolation between different Gmail accounts.

### **Onboarding "Tour Guide" & Nuke Data Fix**
- **The Problem:** The frontend used a generic `localStorage.getItem('hasCompletedOnboarding')` flag to remember if a user had seen the initial AI Tour Guide. If a user nuked their data or logged in with a different Gmail, they wouldn't see the tour again because the browser still held the generic `true` flag.
- **The Solution:** We dynamically scoped the local storage key to the user's specific Firebase UID (e.g., `hasCompletedOnboarding_uid123`). We also updated the "Nuke All Data" button logic to forcefully execute `localStorage.removeItem()` on that specific key, ensuring the AI Tour Guide flawlessly resets for brand new accounts or wiped sessions.

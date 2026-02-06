# Frontend Knowledge Transfer (KT) Document

## 1. High-Level Overview

### Purpose

The frontend is a modern, responsive web application that serves as the user interface for the Smart Financial Coach. It provides two primary experiences: a visual dashboard for financial analytics (spending trends, category breakdowns, insights) and an AI-powered chat interface where users can ask natural language questions about their finances.

### Architecture

- **Pattern**: Component-based SPA (Single Page Application) with client-side routing
- **State Management**: Local React state (useState) with no global state library (Redux/Context not actively used despite being installed)
- **Data Fetching**: Direct axios HTTP calls to backend API (no React Query or SWR for caching)
- **Styling**: Utility-first CSS with Tailwind CSS 4 + CSS variables for theming
- **Component Library**: Custom components built on Radix UI primitives (shadcn/ui pattern)

### Tech Stack

- **Framework**: React 19.2.0
- **Build Tool**: Vite 7.2.4
- **Language**: TypeScript 5.9.3
- **Styling**: Tailwind CSS 4.1.18 (with @tailwindcss/vite plugin)
- **UI Components**: Radix UI primitives + custom shadcn-style components
- **Charts**: Recharts 3.7.0 (for dashboard visualizations)
- **Routing**: React Router DOM 7.13.0
- **HTTP Client**: Axios 1.13.4
- **Icons**: Lucide React 0.563.0
- **Animations**: Framer Motion (via `motion` 12.29.2)
- **Notifications**: Sonner 2.0.7 (toast notifications)
- **AI Components**: Custom AI elements library (`@ai-sdk/react`, `streamdown`, etc.)

---

## 2. Folder Structure & Key Files

```
frontend/
├── src/
│   ├── components/
│   │   ├── ai-elements/          # 40+ reusable AI chat components (message, reasoning, sources, etc.)
│   │   ├── chat/
│   │   │   ├── Chatbot.tsx       # Core: Main chat interface with message handling
│   │   │   └── ChatEmptyState.tsx # Initial chat screen with suggestions
│   │   ├── layout/
│   │   │   └── DashboardLayout.tsx # Core: App shell with sidebar navigation
│   │   └── ui/                   # Shadcn-style primitives (button, card, dialog, etc.)
│   ├── lib/
│   │   └── utils.ts              # Utility: cn() function for className merging
│   ├── pages/
│   │   ├── Dashboard.tsx         # Core: Financial overview with charts and insights
│   │   └── ChatPage.tsx          # Wrapper for Chatbot component
│   ├── App.tsx                   # Core: Router setup and global layout
│   ├── main.tsx                  # Entry point: React root render
│   └── index.css                 # Global styles + Tailwind + CSS variables
├── public/                       # Static assets
├── vite.config.ts                # Core: Vite configuration with path aliases
├── tsconfig.json                 # TypeScript configuration
├── package.json                  # Dependencies and scripts
└── Dockerfile                    # Container setup for development

```

**Key File Annotations:**

- **`App.tsx`**: Defines routes (`/` → Dashboard, `/chat` → ChatPage) and wraps app in dark mode + toast provider.
- **`Dashboard.tsx`**: Fetches 5 different API endpoints on mount, renders summary cards, charts (Recharts), and insights.
- **`Chatbot.tsx`**: Manages chat state, sends POST requests to `/chat` endpoint, renders messages with AI elements.
- **`DashboardLayout.tsx`**: Sidebar navigation with active route highlighting. Uses React Router's `<Outlet />` for nested routes.
- **`components/ai-elements/`**: 40+ specialized components for AI chat UX (message branching, reasoning display, sources, attachments, etc.). Most are unused in current implementation but available for future features.
- **`components/ui/`**: Radix UI-based primitives following shadcn/ui patterns (button, card, dialog, etc.).
- **`vite.config.ts`**: Configures `@/` path alias, Docker-friendly hot reload (polling), and Tailwind plugin.

---

## 3. Key Logic & Data Flow

### Core Flows

#### A. Dashboard Data Loading

```
User navigates to "/"
  → Dashboard.tsx mounts
    → useEffect triggers fetchData()
      → 5 parallel axios.get() calls:
        1. /api/dashboard/summary (balance, spending, savings rate)
        2. /api/dashboard/categories (pie chart data)
        3. /api/dashboard/trend (30-day spending line chart)
        4. /api/transactions?limit=5 (recent transactions)
        5. /api/insights (AI-generated insights)
      → State updated with setSummary(), setCategories(), etc.
        → Recharts components re-render with new data
          → User sees visualizations
```

#### B. Chat Interaction

```
User types message in ChatPage
  → PromptInput component captures text
    → handleSubmit() called
      → addUserMessage() creates user message object
        → setMessages() adds to local state
          → UI renders user bubble
            → fetch('http://localhost:8000/chat', { POST })
              → Backend processes with LangGraph agents
                → Response JSON returned
                  → Assistant message object created
                    → setMessages() adds assistant response
                      → UI renders assistant bubble with markdown
```

#### C. Insight Generation (On-Demand)

```
User clicks "Refresh Insights" button
  → handleGenerateInsights() called
    → setGenerating(true) (button shows "Analyzing...")
      → axios.post('/api/insights/generate')
        → Backend runs insight service
          → New insights created in DB
            → axios.get('/api/insights') fetches updated list
              → setInsights() updates state
                → InsightsList component re-renders
                  → setGenerating(false)
```

### State Management

- **Local Component State**: All state managed via `useState` hooks within components
- **No Global Store**: Despite Redux being installed, it's not used. Each page manages its own data.
- **No Caching**: API calls repeat on every mount (no React Query/SWR). Refreshing the page re-fetches everything.
- **Session Persistence**: Chat thread ID generated client-side (`session-${Date.now()}`), not persisted across refreshes.

---

## 4. Configuration & Environment

### Required Environment Variables

The frontend uses a single environment variable:

```bash
# .env (in frontend/ directory)
VITE_API_URL=http://localhost:8000  # Backend API base URL
```

**Note**: Currently, the API URL is **hardcoded** in components (`http://localhost:8000`), not using `VITE_API_URL`. This is technical debt.

### Hardcoded Constants

- **API Base URL**: `http://localhost:8000` (hardcoded in Dashboard.tsx and Chatbot.tsx)
- **Chart Colors**: `COLORS` array in Dashboard.tsx defines pie chart palette
- **Demo Username**: "Yash" hardcoded in ChatEmptyState.tsx greeting
- **Port**: 5173 (defined in vite.config.ts and docker-compose.yml)

### Docker Configuration

The frontend runs in a container with:

- Hot-reload enabled via volume mounts (`./frontend:/app`)
- Polling-based file watching (required for Docker on Windows/Mac)
- Node modules isolated to prevent host/container conflicts

---

## 5. "Gotchas" & Technical Debt

### Tricky Parts

1. **Hardcoded API URLs**
   - The `VITE_API_URL` env var exists but isn't used. All API calls use `http://localhost:8000` directly.
   - **Impact**: Changing backend URL requires editing multiple files.
   - **Fix**: Create an `api.ts` utility with `const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'`.

2. **No Error Boundaries**
   - If a component crashes, the entire app goes blank. No graceful error handling.
   - **Workaround**: Errors are logged to console, but users see nothing.

3. **Unused Dependencies**
   - Redux, Redux Toolkit, and React-Redux are installed but never used.
   - 40+ AI element components exist but only ~5 are actively used (Message, Conversation, PromptInput, Sources, Reasoning).
   - **Impact**: Larger bundle size, confusing for new devs.

4. **No Loading States for Dashboard**
   - While `loading` state exists, there's no skeleton UI. Users see "Loading dashboard..." text.
   - Charts render empty if data fetch fails (no error state).

5. **Chat State Not Persisted**
   - Refreshing the chat page clears all messages. No localStorage or backend session retrieval.
   - Thread ID is timestamp-based, not tied to user identity.

### Known Issues

- **No Authentication**: The app has no login system. "Log Out" button in sidebar does nothing.
- **Mobile Navigation**: Sidebar is hidden on mobile (`md:flex`), but mobile menu isn't implemented (marked as TODO in DashboardLayout.tsx).
- **No Test Coverage**: Zero tests exist for frontend (per TEST_COVERAGE.md, only backend has 3 tests).
- **Accessibility**: No ARIA labels, keyboard navigation not tested, color contrast may fail WCAG in some areas.
- **API Error Handling**: Failed API calls show console errors but no user-facing error messages (except chat, which uses toast).

### Workarounds

- **Docker Hot Reload**: Uses `usePolling: true` in vite.config.ts because Docker volume mounts don't trigger native file watchers on Windows/Mac.
- **Tailwind 4 Beta**: Using Tailwind CSS 4 (still in beta as of Feb 2026). Some features may be unstable.

---

## 6. Development Workflow

### Commands

#### Initial Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies (optional, Docker handles this)
npm install

# Copy environment template (if needed)
cp .env.example .env
```

#### Development (Docker - Recommended)

```bash
# From project root
docker-compose up frontend

# View logs
docker-compose logs -f frontend

# Restart after dependency changes
docker-compose restart frontend
```

#### Development (Local - Without Docker)

```bash
cd frontend

# Start dev server
npm run dev
# Access at http://localhost:5173

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

#### Common Tasks

**Add a New UI Component (shadcn pattern)**

```bash
# Manually create file in src/components/ui/
# Example: src/components/ui/new-component.tsx
# Follow existing patterns (use Radix UI primitives + CVA for variants)
```

**Add a New Page**

1. Create file in `src/pages/NewPage.tsx`
2. Add route in `App.tsx`:
   ```tsx
   <Route path="/new" element={<NewPage />} />
   ```
3. Add navigation link in `DashboardLayout.tsx`

**Update API Endpoint**

1. Find hardcoded URL in component (e.g., `Dashboard.tsx`)
2. Change `http://localhost:8000/api/...` to new endpoint
3. Update TypeScript interfaces if response shape changes

**Debugging**

```bash
# Check browser console for errors
# React DevTools: Install browser extension

# View network requests
# Browser DevTools → Network tab

# Check Vite errors
docker-compose logs -f frontend
```

#### Testing (Not Implemented)

```bash
# No test suite exists yet
# To add tests, install:
npm install -D vitest @testing-library/react @testing-library/jest-dom

# Create vitest.config.ts and add test scripts to package.json
```

---

## Quick Reference

| Task             | Command/Location                                       |
| ---------------- | ------------------------------------------------------ |
| Start Dev Server | `docker-compose up frontend` or `npm run dev`          |
| View Logs        | `docker-compose logs -f frontend`                      |
| Build Production | `npm run build` (output in `dist/`)                    |
| Lint Code        | `npm run lint`                                         |
| Add Route        | Edit `src/App.tsx`                                     |
| Add UI Component | Create in `src/components/ui/`                         |
| API Calls        | Search for `axios.get` or `fetch` in components        |
| Styling          | Tailwind classes + `src/index.css` for theme variables |

---

## Component Patterns

### Shadcn/UI Pattern

All UI components follow this structure:

```tsx
import { cn } from "@/lib/utils";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "outline" | "ghost";
}

const Button = ({ className, variant = "default", ...props }: ButtonProps) => {
  return (
    <button
      className={cn(
        "base-styles",
        variant === "outline" && "outline-styles",
        className,
      )}
      {...props}
    />
  );
};
```

### Data Fetching Pattern

```tsx
const [data, setData] = useState<DataType | null>(null);
const [loading, setLoading] = useState(true);

useEffect(() => {
  const fetchData = async () => {
    try {
      const response = await axios.get("http://localhost:8000/api/endpoint");
      setData(response.data);
    } catch (error) {
      console.error("Failed to fetch", error);
    } finally {
      setLoading(false);
    }
  };
  fetchData();
}, []);
```

### Styling Pattern

- Use Tailwind utility classes directly in JSX
- Use `cn()` helper to merge conditional classes
- Theme colors via CSS variables (e.g., `bg-primary`, `text-muted-foreground`)
- Dark mode: Entire app wrapped in `.dark` class (see App.tsx)

---

## API Integration Reference

### Dashboard Endpoints

| Endpoint                    | Method | Purpose                    | Response Shape                                                |
| --------------------------- | ------ | -------------------------- | ------------------------------------------------------------- |
| `/api/dashboard/summary`    | GET    | Balance, spending, savings | `{ total_balance, monthly_spending, savings_rate, currency }` |
| `/api/dashboard/categories` | GET    | Spending by category       | `[{ name, value }]`                                           |
| `/api/dashboard/trend`      | GET    | 30-day spending trend      | `[{ date, amount }]`                                          |
| `/api/transactions?limit=5` | GET    | Recent transactions        | `[{ id, merchant, amount, date, category, type }]`            |
| `/api/insights`             | GET    | AI-generated insights      | `[{ id, title, message, type, created_at, is_read }]`         |
| `/api/insights/generate`    | POST   | Trigger insight generation | `{ message }`                                                 |

### Chat Endpoint

| Endpoint | Method | Purpose            | Request Body                                   | Response                                        |
| -------- | ------ | ------------------ | ---------------------------------------------- | ----------------------------------------------- |
| `/chat`  | POST   | Send message to AI | `{ message, thread_id, conversation_history }` | `{ response, thread_id, conversation_history }` |

---

## Styling System

### Theme Variables (index.css)

The app uses CSS custom properties for theming:

- `--background`, `--foreground`: Base colors
- `--primary`, `--primary-foreground`: Brand colors (violet)
- `--secondary`, `--muted`, `--accent`: UI element colors
- `--destructive`: Error/danger states
- `--border`, `--input`, `--ring`: Form element colors

### Dark Mode

- Entire app uses dark mode (`.dark` class on root div in App.tsx)
- Light mode styles exist in CSS but aren't used
- To enable light mode toggle, add state management and remove hardcoded `.dark` class

### Responsive Breakpoints (Tailwind defaults)

- `sm`: 640px
- `md`: 768px (sidebar appears)
- `lg`: 1024px
- `xl`: 1280px

---

## Future Improvements Needed

1. **Centralize API Configuration**: Create `src/lib/api.ts` with base URL and axios instance
2. **Add Error Boundaries**: Wrap routes in error boundary components
3. **Implement Authentication**: Add login flow, protected routes, user context
4. **Add Loading Skeletons**: Replace "Loading..." text with skeleton UI
5. **Persist Chat History**: Store messages in localStorage or fetch from backend
6. **Mobile Navigation**: Implement hamburger menu for mobile sidebar
7. **Add Tests**: Set up Vitest + React Testing Library
8. **Remove Unused Dependencies**: Audit and remove Redux, unused AI components
9. **Accessibility Audit**: Add ARIA labels, test keyboard navigation, fix color contrast
10. **Environment Variable Usage**: Replace hardcoded URLs with `import.meta.env.VITE_API_URL`

---

**Last Updated**: February 3, 2026  
**Maintainer**: Frontend Team  
**Questions?** Check `DESIGN_DOC.md` for architecture context or `frontend/README.md` for setup instructions.

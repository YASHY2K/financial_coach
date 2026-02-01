# Smart Financial Coach Frontend

The frontend for the Smart Financial Coach application, built with React 19, Vite, and Tailwind CSS. It provides an intuitive interface for users to chat with an AI coach and visualize their financial data.

## Features

- **AI Chat Interface**: Interactive chat with a financial coach that can analyze spending, answer questions, and provide advice.
- **Financial Dashboard**: Visual summaries of spending habits, trends, and category breakdowns.
- **Transaction History**: Easy-to-read list of recent financial activities.
- **Subscription Tracking**: Monitor active subscriptions and recurring expenses.
- **Proactive Insights**: AI-generated suggestions and alerts based on financial patterns.
- **Modern UI/UX**: Responsive design using Tailwind CSS 4 and Shadcn UI components.

## Tech Stack

- **Framework**: [React 19](https://react.dev/)
- **Build Tool**: [Vite](https://vitejs.dev/)
- **Language**: [TypeScript](https://www.typescriptlang.org/)
- **Styling**: [Tailwind CSS 4](https://tailwindcss.com/)
- **UI Components**: [Radix UI](https://www.radix-ui.com/) & [Lucide React](https://lucide.dev/)
- **Charts**: [Recharts](https://recharts.org/)
- **Animations**: [Framer Motion](https://www.framer.com/motion/)
- **AI Integration**: Custom components for message branching, reasoning, and sources.

## Getting Started

### Prerequisites

- [Node.js](https://nodejs.org/) (v18 or later recommended)
- [npm](https://www.npmjs.com/) or [yarn](https://yarnpkg.com/)

### Installation

1. Install dependencies:
   ```bash
   npm install
   ```

2. Start the development server:
   ```bash
   npm run dev
   ```

3. Open your browser and navigate to `http://localhost:5173`.

### Backend Connection

The frontend expects the backend API to be running at `http://localhost:8000`. You can change this in the components if necessary (e.g., in `src/components/chat/Chatbot.tsx`).

## Scripts

- `npm run dev`: Starts the Vite development server with Hot Module Replacement (HMR).
- `npm run build`: Compiles the application for production.
- `npm run lint`: Runs ESLint to check for code quality issues.
- `npm run preview`: Locally previews the production build.

## Project Structure

- `src/components/ai-elements`: Specialized components for AI interactions (messages, reasoning, etc.).
- `src/components/chat`: Chat-specific components like the `Chatbot`.
- `src/components/ui`: Reusable UI components (buttons, cards, etc.).
- `src/pages`: Application pages (Dashboard, ChatPage).
- `src/lib`: Utility functions and shared logic.
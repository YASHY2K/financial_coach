# Design Document: Smart Financial Coach

## 1. Introduction
The Smart Financial Coach is an AI-powered personal finance management tool designed to transform raw transaction data into actionable, personalized insights. It aims to bridge the gap between simple expense tracking and proactive financial planning.

## 2. Problem Statement
Many individuals lack visibility into their spending habits and struggle to find personalized financial advice. Traditional budgeting apps often require manual effort and fail to provide the "why" or "how" behind financial improvement.

## 3. Target Audience
- **Young Adults & Students**: Building initial financial literacy.
- **Freelancers & Gig Workers**: Managing variable income and expenses.
- **General Users**: Seeking to optimize spending and reach savings goals.

## 4. System Architecture

### 4.1 High-Level Overview
The application follows a client-server architecture, containerized with Docker.
- **Frontend**: A modern React application providing a dashboard and a chat interface.
- **Backend**: A FastAPI server handling business logic, AI agent orchestration, and database interactions.
- **AI Layer**: Powered by Google's Gemini models via LangGraph, enabling natural language queries and proactive analysis.
- **Database**: PostgreSQL for storing user profiles, transactions, and AI-generated insights.

### 4.2 Tech Stack
- **Frontend**: React 19, Vite, Tailwind CSS 4, Recharts, Radix UI, Framer Motion.
- **Backend**: Python 3.12, FastAPI, SQLAlchemy (Async), LangGraph, `google-generativeai`.
- **Infrastructure**: Docker, Docker Compose.
- **Database**: PostgreSQL.

## 5. Key Features

### 5.1 Intelligent Chat Agent
An AI expert capable of answering natural language questions about financial history (e.g., "How much did I spend on groceries last month?"). It uses SQL tools to query the database securely with read-only permissions.

### 5.2 Financial Dashboard
Visualizes financial health through:
- **Spending Trends**: Daily/Monthly charts.
- **Category Breakdown**: Pie charts showing where money goes.
- **Key Metrics**: Total balance, monthly spending, and savings rate.

### 5.3 Subscription Manager
Identifies recurring transactions to help users monitor and manage their subscriptions (Netflix, Spotify, etc.).

### 5.4 Proactive Insights
An automated service that analyzes patterns and generates "Insights" (e.g., "High spending detected in Dining Out") which appear on the dashboard.

## 6. Database Schema
- **User**: Profile information and high-level financial goals.
- **Transaction**: Detailed record of every financial movement (amount, date, merchant, category, type, is_subscription).
- **Insight**: AI-generated alerts and suggestions tied to specific users.

## 7. Security & Privacy
- **Read-Only AI**: The AI agent uses a dedicated read-only database user to prevent accidental data modification.
- **System Prompts**: Strict instructions to the AI to prevent DDL/DML operations.
- **Environment Isolation**: Sensitive keys and database credentials managed via `.env` files.

## 8. Future Enhancements
- **Real Bank Integration**: Connect via Plaid or similar APIs.
- **Automatic Categorization**: Real-time AI categorization of new transactions.
- **Predictive Forecasting**: Advanced mathematical models for savings goal projections.
- **Multi-User Support**: Robust authentication and session management.

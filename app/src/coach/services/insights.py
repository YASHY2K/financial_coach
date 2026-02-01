import logging
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

from ..models import Transaction, Insight, User
from ..config import settings
from .prompts import INSIGHT_COACH_SYSTEM, INSIGHT_USER_TEMPLATE

logger = logging.getLogger(__name__)

class InsightService:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model=settings.LLM_MODEL, 
            temperature=0.7, 
            api_key=settings.LLM_API_KEY
        )

    async def generate_proactive_insights(self, db: AsyncSession, user_id: int = 1):
        """
        Orchestrates the generation of proactive insights for a user.
        """
        logger.info(f"Generating proactive insights for user_id={user_id}")
        
        # 1. Gather Metrics
        metrics = await self._get_user_metrics(db, user_id)
        if not metrics:
            logger.warning(f"No metrics found for user_id={user_id}. Skipping insight generation.")
            return []

        # 2. Generate Insight via AI
        insight_data = await self._ask_ai_for_insight(metrics)
        
        # 3. Persist Insight
        new_insights = []
        for item in insight_data:
            insight = Insight(
                user_id=user_id,
                title=item['title'],
                message=item['message'],
                type=item['type']
            )
            db.add(insight)
            new_insights.append(insight)
        
        await db.commit()
        logger.info(f"Successfully generated {len(new_insights)} insights for user_id={user_id}")
        return new_insights

    async def _get_user_metrics(self, db: AsyncSession, user_id: int):
        """
        Calculates key metrics for the AI to analyze.
        """
        today = date.today()
        start_of_month = today.replace(day=1)
        last_month_end = start_of_month - timedelta(days=1)
        last_month_start = last_month_end.replace(day=1)

        # Current Month Spend
        current_spend_stmt = select(func.sum(Transaction.amount)).where(
            Transaction.user_id == user_id,
            Transaction.transaction_type == 'debit',
            Transaction.date >= start_of_month
        )
        current_spend = (await db.execute(current_spend_stmt)).scalar() or Decimal('0')

        # Last Month Spend
        last_spend_stmt = select(func.sum(Transaction.amount)).where(
            Transaction.user_id == user_id,
            Transaction.transaction_type == 'debit',
            Transaction.date >= last_month_start,
            Transaction.date <= last_month_end
        )
        last_spend = (await db.execute(last_spend_stmt)).scalar() or Decimal('0')

        # Top Category (Current Month)
        top_cat_stmt = (
            select(Transaction.category, func.sum(Transaction.amount).label("total"))
            .where(
                Transaction.user_id == user_id,
                Transaction.transaction_type == "debit",
                Transaction.date >= start_of_month,
                Transaction.category.isnot(None),
            )
            .group_by(Transaction.category)
            .order_by(desc("total"))
            .limit(1)
        )
        top_cat_result = (await db.execute(top_cat_stmt)).first()
        top_category = top_cat_result.category if top_cat_result else "N/A"
        top_category_amount = top_cat_result.total if top_cat_result else Decimal('0')

        # Check for User Goals
        user_stmt = select(User).where(User.id_ == user_id)
        user = (await db.execute(user_stmt)).scalars().first()
        goals = user.financial_goals if user else "No specific goals set."

        return {
            "current_month_spending": float(current_spend),
            "last_month_spending": float(last_spend),
            "top_category": top_category,
            "top_category_amount": float(top_category_amount),
            "user_goals": goals,
            "month_name": today.strftime("%B")
        }

    async def _ask_ai_for_insight(self, metrics: dict):
        """
        Prompt the LLM to generate a friendly insight based on metrics.
        """
        messages = [
            SystemMessage(content=INSIGHT_COACH_SYSTEM),
            HumanMessage(content=INSIGHT_USER_TEMPLATE.format(**metrics))
        ]

        try:
            response = await self.llm.ainvoke(messages)
            content = response.content
            
            # Basic JSON cleanup in case of markdown blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            import json
            return json.loads(content)
        except Exception as e:
            logger.error(f"Error generating AI insight: {e}")
            return [{
                "title": "Spending Update",
                "message": f"You've spent ${metrics['current_month_spending']} so far in {metrics['month_name']}. Keep an eye on your {metrics['top_category']} spending!",
                "type": "trend"
            }]

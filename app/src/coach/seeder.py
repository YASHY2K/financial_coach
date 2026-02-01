import asyncio
import logging
import random
from datetime import timedelta, date
from decimal import Decimal
from typing import List

from faker import Faker
from sqlalchemy import select

from database import engine, AsyncSessionLocal, Base
from models import User, Transaction

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

fake = Faker()


async def init_tables():
    """Async table creation."""
    logger.info("Initializing database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Tables initialized.")


def _generate_transaction_data(user_id: int) -> List[Transaction]:
    """
    Sync function to generate data.
    This is CPU-bound, so we will run it in a thread.
    """
    logger.debug(f"Generating synthetic data for user_id={user_id}...")

    subscriptions = [
        ("Netflix", 15.99, "Entertainment"),
        ("Spotify", 9.99, "Music"),
        ("Adobe Creative Cloud", 54.99, "Software"),
        ("Gym Membership", 45.00, "Health"),
    ]

    merchants = {
        "Food": [
            ("Starbucks", 4.50, 8.00),
            ("Chipotle", 11.00, 18.00),
            ("Uber Eats", 20.00, 45.00),
        ],
        "Transport": [("Shell", 30.00, 60.00), ("Uber", 15.00, 40.00)],
        "Shopping": [("Amazon", 10.00, 100.00), ("Target", 20.00, 80.00)],
    }

    transactions = []
    start_date = date.today() - timedelta(days=90)
    end_date = date.today()

    current_date = start_date
    while current_date <= end_date:
        # A. Subscriptions (1st of month)
        if current_date.day == 1:
            for merch, amount, desc in subscriptions:
                transactions.append(
                    Transaction(
                        user_id=user_id,
                        merchant=merch,
                        amount=Decimal(str(amount)),
                        date=current_date,
                        description=f"Monthly charge for {desc}",
                        is_subscription=True,
                        category="Subscription",
                    )
                )

        # B. Daily Spending
        if random.random() < 0.4:
            category_key = random.choice(list(merchants.keys()))
            merch, min_amt, max_amt = random.choice(merchants[category_key])
            amount = round(random.uniform(min_amt, max_amt), 2)

            transactions.append(
                Transaction(
                    user_id=user_id,
                    merchant=merch,
                    amount=Decimal(str(amount)),
                    date=current_date,
                    description=f"Purchase at {merch}",
                    is_subscription=False,
                    category=None,  # AI target
                )
            )

        current_date += timedelta(days=1)

    logger.debug(f"Generated {len(transactions)} transaction objects.")
    return transactions


async def seed_data():
    await init_tables()

    async with AsyncSessionLocal() as session:
        try:
            # Check for existing user
            stmt = select(User).filter(User.username == "demo_user")
            result = await session.execute(stmt)
            existing_user = result.scalars().first()

            if existing_user:
                logger.info("Demo user already exists. Skipping seed.")
                return

            logger.info("Creating Demo User...")
            demo_user = User(
                username="demo_user",
                financial_goals="I want to save $3000 for a down payment in 10 months.",
            )
            session.add(demo_user)
            await session.commit()

            # Use 'refresh' to get the new ID back from DB
            await session.refresh(demo_user)

            logger.info(f"Seeding transactions for {demo_user.username}...")

            # ---------------------------------------------------------
            # NON-BLOCKING DATA GEN:
            # Offload CPU-heavy generation to separate thread
            # main asyncio event loop stays free
            # ---------------------------------------------------------
            transactions = await asyncio.to_thread(
                _generate_transaction_data, demo_user.id_
            )

            session.add_all(transactions)
            await session.commit()
            logger.info(f"Successfully added {len(transactions)} transactions.")

        except Exception as e:
            logger.error(f"Error seeding data: {e}", exc_info=True)
            await session.rollback()


if __name__ == "__main__":
    asyncio.run(seed_data())

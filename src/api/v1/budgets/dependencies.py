"""Budget API dependencies."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.persistence.budget.repository import BudgetRepository
from src.application.budget.services import BudgetService
from src.db.session import get_db_session


async def get_budget_repo(session: Annotated[AsyncSession, Depends(get_db_session)]) -> BudgetRepository:
    return BudgetRepository(session)


async def get_budget_service(budget_repo: Annotated[BudgetRepository, Depends(get_budget_repo)]) -> BudgetService:
    return BudgetService(budget_repo)

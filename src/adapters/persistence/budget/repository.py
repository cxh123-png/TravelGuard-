"""Budget repository implementation."""

from sqlalchemy import select

from src.adapters.persistence.budget.models import BudgetAccountModel, BudgetLedgerEntryModel
from src.db.repository import Repository


class BudgetRepository(Repository[BudgetAccountModel]):
    """Budget account and ledger repository."""

    async def add_account(self, model: BudgetAccountModel) -> BudgetAccountModel:
        self.session.add(model)
        await self.session.flush()
        return model

    async def get_account_by_id(self, tenant_id: str, account_id: str) -> BudgetAccountModel | None:
        result = await self.session.execute(
            select(BudgetAccountModel).where(
                BudgetAccountModel.tenant_id == tenant_id,
                BudgetAccountModel.id == account_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_account_for_update(self, tenant_id: str, account_id: str) -> BudgetAccountModel | None:
        result = await self.session.execute(
            select(BudgetAccountModel)
            .where(
                BudgetAccountModel.tenant_id == tenant_id,
                BudgetAccountModel.id == account_id,
            )
            .with_for_update()
        )
        return result.scalar_one_or_none()

    async def get_ledger_by_idempotency_key(self, tenant_id: str, idempotency_key: str) -> BudgetLedgerEntryModel | None:
        result = await self.session.execute(
            select(BudgetLedgerEntryModel).where(
                BudgetLedgerEntryModel.tenant_id == tenant_id,
                BudgetLedgerEntryModel.idempotency_key == idempotency_key,
            )
        )
        return result.scalar_one_or_none()

    async def add_ledger(self, model: BudgetLedgerEntryModel) -> BudgetLedgerEntryModel:
        self.session.add(model)
        await self.session.flush()
        return model

    async def update_account(self, model: BudgetAccountModel) -> BudgetAccountModel:
        await self.session.flush()
        return model

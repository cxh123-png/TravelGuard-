"""Approval repository implementation."""

from sqlalchemy import select

from src.adapters.persistence.approval.models import ApprovalActionModel, ApprovalTaskModel
from src.db.repository import Repository


class ApprovalRepository(Repository[ApprovalTaskModel]):
    """Approval task and action repository."""

    async def add_task(self, model: ApprovalTaskModel) -> ApprovalTaskModel:
        self.session.add(model)
        await self.session.flush()
        return model

    async def get_task_by_id(self, tenant_id: str, task_id: str) -> ApprovalTaskModel | None:
        result = await self.session.execute(
            select(ApprovalTaskModel).where(
                ApprovalTaskModel.tenant_id == tenant_id,
                ApprovalTaskModel.id == task_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_task_for_update(self, tenant_id: str, task_id: str) -> ApprovalTaskModel | None:
        result = await self.session.execute(
            select(ApprovalTaskModel)
            .where(
                ApprovalTaskModel.tenant_id == tenant_id,
                ApprovalTaskModel.id == task_id,
            )
            .with_for_update()
        )
        return result.scalar_one_or_none()

    async def get_action_by_idempotency_key(self, tenant_id: str, idempotency_key: str) -> ApprovalActionModel | None:
        result = await self.session.execute(
            select(ApprovalActionModel).where(
                ApprovalActionModel.tenant_id == tenant_id,
                ApprovalActionModel.idempotency_key == idempotency_key,
            )
        )
        return result.scalar_one_or_none()

    async def add_action(self, model: ApprovalActionModel) -> ApprovalActionModel:
        self.session.add(model)
        await self.session.flush()
        return model

    async def update_task(self, model: ApprovalTaskModel) -> ApprovalTaskModel:
        await self.session.flush()
        return model

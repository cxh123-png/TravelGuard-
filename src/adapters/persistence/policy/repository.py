"""政策仓储实现。"""

from sqlalchemy import or_

from src.adapters.persistence.policy.models import PolicyModel
from src.db.repository import Repository


class PolicyRepository(Repository[PolicyModel]):
    """政策仓储。"""

    async def get_by_id(self, policy_id: str) -> PolicyModel | None:
        """按 ID 查询政策。"""
        from sqlalchemy import select
        result = await self.session.execute(
            select(PolicyModel).where(PolicyModel.id == policy_id)
        )
        return result.scalar_one_or_none()

    async def get_effective_for_org(
        self,
        tenant_id: str,
        org_id: str,
    ) -> PolicyModel | None:
        """查询组织当前生效的政策（已发布）。"""
        from sqlalchemy import select
        # target_org_ids 是 CSV 字符串，需精确匹配避免子串误命中（如 org-1 匹配 org-10）
        org_filter = or_(
            PolicyModel.target_org_ids == org_id,
            PolicyModel.target_org_ids.like(f"{org_id},%"),
            PolicyModel.target_org_ids.like(f"%,{org_id},%"),
            PolicyModel.target_org_ids.like(f"%,{org_id}"),
        )
        result = await self.session.execute(
            select(PolicyModel).where(
                PolicyModel.tenant_id == tenant_id,
                PolicyModel.status == "PUBLISHED",
                org_filter,
            )
        )
        return result.scalar_one_or_none()

"""差旅仓储实现：继承 M1 提供的 Repository 基类。"""

from src.adapters.persistence.travel.models import TravelRequestModel
from src.db.repository import Repository


class TravelRequestRepository(Repository[TravelRequestModel]):
    """差旅申请仓储。"""

    async def get_by_id(self, request_id: str) -> TravelRequestModel | None:
        """按 ID 查询申请。"""
        from sqlalchemy import select
        result = await self.session.execute(
            select(TravelRequestModel).where(TravelRequestModel.id == request_id)
        )
        return result.scalar_one_or_none()

    async def update(self, model: TravelRequestModel) -> TravelRequestModel:
        """更新申请（乐观锁由 SQLAlchemy version_id_col 自动处理）。"""
        await self.session.flush()
        return model

    async def list_by_user(
        self,
        tenant_id: str,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> list[TravelRequestModel]:
        """查询用户的申请列表。"""
        from sqlalchemy import select
        result = await self.session.execute(
            select(TravelRequestModel)
            .where(
                TravelRequestModel.tenant_id == tenant_id,
                TravelRequestModel.user_id == user_id,
            )
            .order_by(TravelRequestModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

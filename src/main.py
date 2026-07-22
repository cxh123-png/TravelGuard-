from typing import Annotated

from fastapi import Depends, FastAPI

from src.api.dependencies import CurrentUser, get_current_user
from src.api.error_handlers import register_error_handlers
from src.api.v1.travel.router import router as travel_router
from src.core.config import get_settings
from src.core.request_id import RequestIdMiddleware
from src.core.response import success_response


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(title=settings.app_name, version="0.1.0", debug=settings.debug)
    application.add_middleware(RequestIdMiddleware)
    register_error_handlers(application)
    register_routes(application, settings.api_prefix)
    return application


def register_routes(application: FastAPI, api_prefix: str) -> None:
    @application.get("/health")
    async def health() -> dict[str, object]:
        return success_response({"status": "ok", "service": "travelguard-api"})

    @application.get(f"{api_prefix}/me")
    async def read_current_user(
        current_user: Annotated[CurrentUser, Depends(get_current_user)],
    ) -> dict[str, object]:
        return success_response(
            {
                "user_id": current_user.user_id,
                "tenant_id": current_user.tenant_id,
                "roles": list(current_user.roles),
            }
        )

    # M2 差旅接口
    application.include_router(travel_router, prefix=api_prefix)


app = create_app()

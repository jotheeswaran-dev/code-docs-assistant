from fastapi import FastAPI
from pydantic import BaseModel

from app import __version__
from app.config import Settings, get_settings


class Health(BaseModel):
    status: str
    version: str
    answer_model: str
    anthropic_key_set: bool


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(title="Code Documentation Assistant", version=__version__)

    @app.get("/health", response_model=Health)
    def health() -> Health:
        return Health(
            status="ok",
            version=__version__,
            answer_model=settings.answer_model,
            anthropic_key_set=bool(settings.anthropic_api_key),
        )

    return app


app = create_app()

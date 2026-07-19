from contextlib import asynccontextmanager
from pathlib import Path

from alembic import command
from alembic.config import Config as AlembicConfig
from fastapi import FastAPI
from sqlalchemy import select

from . import db as database
from .api import (
    admin_stats,
    billing,
    gallery,
    legal,
    mentors,
    onboarding,
    profile,
    tree,
    users,
    waitlist,
)
from .core.config import get_settings

if get_settings().sentry_dsn:
    import sentry_sdk

    sentry_sdk.init(dsn=get_settings().sentry_dsn, traces_sample_rate=0.1)
from .data.skill_tree import SEED_NODES
from .db import Base
from .models.tables import SkillNode  # noqa: F401 — tabloların Base'e kaydı için


def run_migrations() -> None:
    backend_dir = Path(__file__).resolve().parent.parent
    cfg = AlembicConfig(str(backend_dir / "alembic.ini"))
    cfg.set_main_option("script_location", str(backend_dir / "alembic"))
    command.upgrade(cfg, "head")


def seed_skill_tree() -> None:
    """Seed verisini upsert eder — müfredat düzenlemeleri yeniden başlatmada yansır."""
    with database.SessionLocal() as db:
        for node in SEED_NODES:
            existing = db.get(SkillNode, node["id"])
            if existing is None:
                db.add(SkillNode(**node))
            else:
                for key, value in node.items():
                    setattr(existing, key, value)
        db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Postgres: Alembic migration'ları; sqlite (test): hızlı create_all
    if get_settings().database_url.startswith("sqlite"):
        Base.metadata.create_all(database.engine)
    else:
        run_migrations()
    seed_skill_tree()
    yield


app = FastAPI(title="Artora API", lifespan=lifespan)

app.include_router(users.router)
app.include_router(onboarding.router)
app.include_router(tree.router)
app.include_router(profile.router)
app.include_router(mentors.router)
app.include_router(billing.router)
app.include_router(waitlist.router)
app.include_router(gallery.router)
app.include_router(admin_stats.router)
app.include_router(legal.router)


@app.get("/health")
def health():
    return {"status": "ok"}

from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import select

from . import db as database
from .api import onboarding, profile, tree, users
from .data.skill_tree import SEED_NODES
from .db import Base
from .models.tables import SkillNode  # noqa: F401 — tabloların Base'e kaydı için


def seed_skill_tree() -> None:
    with database.SessionLocal() as db:
        existing = {r[0] for r in db.execute(select(SkillNode.id))}
        for node in SEED_NODES:
            if node["id"] not in existing:
                db.add(SkillNode(**node))
        db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # MVP: create_all + seed. Faz 2 öncesi Alembic migration'a geçilecek.
    Base.metadata.create_all(database.engine)
    seed_skill_tree()
    yield


app = FastAPI(title="ArtApp API", lifespan=lifespan)

app.include_router(users.router)
app.include_router(onboarding.router)
app.include_router(tree.router)
app.include_router(profile.router)


@app.get("/health")
def health():
    return {"status": "ok"}

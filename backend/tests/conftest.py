import os

import pytest

# Ayarlar import edilmeden ÖNCE test ortamını kur
os.environ["AI_PROVIDER"] = "mock"
# Hız limiti testlerde kapalı (test başına yüzlerce istek atılır);
# test_security.py kendi testinde bilinçli olarak açar
os.environ["RATE_LIMIT_ENABLED"] = "false"
# Topluluk paylaşımı seviye kapısı testlerde kapalı (fikstürler seviye-1 misafir
# hesaplarıyla paylaşır); test_gallery.py gate testi bilinçli olarak 3'e çeker
os.environ["COMMUNITY_SHARE_MIN_LEVEL"] = "0"


@pytest.fixture()
def client(tmp_path, monkeypatch):
    os.environ["DATABASE_URL"] = f"sqlite:///{tmp_path}/test.db"
    os.environ["STORAGE_DIR"] = str(tmp_path / "storage")

    # Modül seviyesindeki engine/ayar önbelleklerini sıfırla
    from app import db as db_module
    from app.core import config

    config.get_settings.cache_clear()
    db_module.engine = db_module._make_engine()
    db_module.SessionLocal.configure(bind=db_module.engine)

    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as c:
        yield c

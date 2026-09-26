"""Admin denetim kaydı yardımcı fonksiyonu (bkz. models.tables.AdminAuditLog).

Karar ile AYNI transaction'da yazılır: karar commit olursa kayıt da olur,
geri alınırsa ikisi birden geri alınır — kayıtsız karar kalmaz.
"""

from sqlalchemy.orm import Session

from ..models.tables import AdminAuditLog, User


def log(db: Session, admin: User, action: str, target_type: str, target_id: int) -> None:
    db.add(
        AdminAuditLog(
            admin_id=admin.id, action=action, target_type=target_type, target_id=target_id
        )
    )

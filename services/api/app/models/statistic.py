from sqlalchemy import Column, Integer, String, Enum, Numeric, Text, TIMESTAMP, UniqueConstraint
from sqlalchemy.sql import func
from app.db.session import Base

class Statistic(Base):
    __tablename__ = "statistics"

    stat_id = Column(Integer, primary_key=True, autoincrement=True)
    period_type = Column(Enum('WEEKLY', 'MONTHLY'), nullable=False)
    period_value = Column(String(20), nullable=False)
    avg_rating = Column(Numeric(3, 2))
    ai_comment = Column(Text)
    total_reviews = Column(Integer, default=0)
    created_at = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (
        UniqueConstraint('period_type', 'period_value'),
    )

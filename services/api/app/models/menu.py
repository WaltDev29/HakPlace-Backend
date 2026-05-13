from sqlalchemy import Column, Integer, String, Float
from app.db.session import Base

class Menu(Base):
    __tablename__ = "menus"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True, nullable=False)
    price = Column(Float, nullable=False)
    description = Column(String(500))

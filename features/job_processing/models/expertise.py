from sqlalchemy import Column, String, SmallInteger
from sqlalchemy.dialects.postgresql import ARRAY as PGArray

from core.database import Base


class ExpertiseArea(Base):
    __tablename__ = "expertise_areas"

    id = Column(SmallInteger, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    level = Column(String, nullable=False)
    keywords = Column(PGArray(String), nullable=False, default=list)
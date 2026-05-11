from sqlalchemy import Column, Integer, String, Float, DateTime, func
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    latitude = Column(Float)
    longitude = Column(Float)


class AprioriRule(Base):
    __tablename__ = "apriori_rules"

    id = Column(Integer, primary_key=True, index=True)
    antecedents = Column(String(255), nullable=False, index=True)
    consequents = Column(String(100), nullable=False, index=True)
    support = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    lift = Column(Float, nullable=False)


class LocationData(Base):
    __tablename__ = "location_data"

    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, nullable=False, unique=True, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    area_type = Column(String(50), nullable=False)
    population_density = Column(String(50), nullable=False)


class WasteData(Base):
    __tablename__ = "waste_data"

    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, nullable=False, index=True)
    date = Column(String(32), nullable=False, index=True)
    waste_level = Column(String(50), nullable=False)
    pickup_status = Column(String(50), nullable=False)
    delay_days = Column(Integer, nullable=False)


class DisposalLocation(Base):
    __tablename__ = "disposal_locations"

    id = Column(Integer, primary_key=True, index=True)
    disposal_id = Column(Integer, nullable=False, unique=True, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    type = Column(String(50), nullable=False)
    capacity = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False)


class LegacyRule(Base):
    __tablename__ = "legacy_rules"

    id = Column(Integer, primary_key=True, index=True)
    antecedents = Column(String(255), nullable=False, index=True)
    consequents = Column(String(100), nullable=False)


class MunicipalRequest(Base):
    __tablename__ = "municipal_requests"

    id = Column(Integer, primary_key=True, index=True)
    decision = Column(String(20), nullable=False, index=True)
    waste = Column(Integer, nullable=False)
    delay = Column(Integer, nullable=False)
    density = Column(Integer, nullable=False)
    area = Column(Integer, nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    bin_lat = Column(Float, nullable=True)
    bin_lon = Column(Float, nullable=True)
    status = Column(String(30), nullable=False, default="PENDING", index=True)
    priority = Column(String(20), nullable=False, default="MEDIUM", index=True)
    notes = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
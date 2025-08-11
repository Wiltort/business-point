from app.db import Base
from sqlalchemy import Column, Float, ForeignKey, String, Integer, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

organization_activity = Table(
    'organization_activity',
    Base.metadata,
    Column('organization_id', Integer, ForeignKey('organizations.id')),
    Column('activity_id', Integer, ForeignKey('activities.id'))
)


class Phone(Base):
    __tablename__ = "phones"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    number: Mapped[str] = mapped_column(String, index=True, unique=True)
    organization_id = mapped_column(ForeignKey('organizations.id'))
    organization = relationship(
        "Organization",
        back_populates="phones",
        lazy="selectin"
    )


class Activity(Base):
    __tablename__ = "activities"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, index=True)
    parent_id = mapped_column(ForeignKey('activities.id'), nullable=True)
    children = relationship(
        "Activity",
        back_populates="parent",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    parent = relationship(
        "Activity",
        back_populates="children",
        remote_side=[id],
        lazy="selectin"
    )


class Building(Base):
    __tablename__ = "buildings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    address: Mapped[str] = mapped_column(String, index=True, unique=True)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    organizations = relationship(
        "Organization",
        back_populates="building",
        cascade="all, delete-orphan",
        lazy="selectin"
    )


class Organization(Base):
    __tablename__ = "organizations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, index=True)
    building_id = mapped_column(ForeignKey('buildings.id'), nullable=True)
    building = relationship(
        "Building",
        back_populates="organizations",
        lazy="selectin"
    )
    phones = relationship(
        "Phone",
        back_populates="organization",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    activities = relationship(
        "Activity",
        secondary=organization_activity,
        lazy="selectin"
    )
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class PhoneBase(BaseModel):
    number: str = Field(..., example="8-923-666-13-13")


class PhoneCreate(PhoneBase):
    organization_id: int = Field(..., example=1)


class Phone(PhoneBase):
    id: int
    organization: 'Organization'

    class Config:
        from_attributes = True

class PhoneRead(PhoneBase):
    id: int

    class Config:
        from_attributes = True


class ActivityBase(BaseModel):
    name: str = Field(..., example="Молочная продукция")
    parent_id: int | None = Field(None, example=1)


class ActivityCreate(ActivityBase):
    pass


class ActivityUpdate(BaseModel):
    name: str | None = Field(None, example="Молочная продукция")
    parent_id: int | None = Field(None, example=1)


class Activity(ActivityBase):
    id: int
    children: List['Activity'] = Field(default_factory=list)

    class Config:
        from_attributes = True


class ActivityRead(BaseModel):
    id: int
    name: str
    parent_id: int | None

    class Config:
        from_attributes = True


class ActivityTreeRead(ActivityRead):
    children: List["ActivityTreeRead"] = []

    class Config:
        from_attributes = True


class BuildingBase(BaseModel):
    address: str = Field(..., example="г. Москва, ул. Ленина 1, офис 3")
    latitude: float = Field(..., example=55.7558)
    longitude: float = Field(..., example=37.6173)


class BuildingCreate(BuildingBase):
    pass


class Building(BuildingBase):
    id: int

    class Config:
        from_attributes = True


class OrganizationBase(BaseModel):
    name: str = Field(..., example='ООО "Рога и Копыта"')
    building_id: int = Field(..., example=1)
    phone_numbers: List[str] = Field(default_factory=list, example=["2-222-222", "3-333-333"])
    activity_ids: List[int] = Field(default_factory=list, example=[1, 2])


class OrganizationCreate(OrganizationBase):
    @field_validator('phone_numbers')
    @classmethod
    def phone_numbers_must_be_unique(cls, v):
        if len(v) != len(set(v)):
            raise ValueError("Phone numbers must be unique")
        return v


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    building_id: Optional[int] = None
    phone_numbers: Optional[List[str]] = None
    activity_ids: Optional[List[int]] = None

    @field_validator('phone_numbers')
    @classmethod
    def phone_numbers_must_be_unique(cls, v):
        if len(v) != len(set(v)):
            raise ValueError("Phone numbers must be unique")
        return v


class Organization(BaseModel):
    id: int
    name: str
    phones: List[PhoneRead] = Field(default_factory=list)
    activities: List[ActivityRead] = Field(default_factory=list)
    building: Building | None = None

    class Config:
        from_attributes = True


# Специальные схемы для запросов
class OrganizationWithDistance(Organization):
    distance: float = Field(..., example=1.5)


class ActivityTree(Activity):
    children: List['ActivityTree'] = Field(default_factory=list)


class GeoSearchArea(BaseModel):
    min_lat: float = Field(..., example=55.7558)
    max_lat: float = Field(..., example=55.7658)
    min_lon: float = Field(..., example=37.6173)
    max_lon: float = Field(..., example=37.6273)


class Unit(str, Enum):
    meter = "m"
    kilometer = "km"
    mile = "mi"

    def to_meters(self, value: float) -> float:
        if self == Unit.meter:
            return value
        elif self == Unit.kilometer:
            return value * 1000
        elif self == Unit.mile:
            return value * 1609.344
        else:
            raise ValueError(f"Unknown unit: {self}")


class GeoSearchRadius(BaseModel):
    latitude: float = Field(..., example=55.7558)
    longitude: float = Field(..., example=37.6173)
    radius: float = Field(..., example=1)
    unit: Unit = Field(..., example="km")

    @field_validator("latitude")
    def latitude_range(cls, v):
        if not -90 <= v <= 90:
            raise ValueError("Latitude must be between -90 and 90")
        return v

    @field_validator("longitude")
    def longitude_range(cls, v):
        if not -180 <= v <= 180:
            raise ValueError("Longitude must be between -180 and 180")
        return v

    @field_validator("radius")
    def radius_positive(cls, v):
        if v <= 0:
            raise ValueError("Radius must be positive")
        return v


Phone.model_rebuild()
Activity.model_rebuild()
ActivityTree.model_rebuild()
ActivityTreeRead.model_rebuild()

"""
MediKiosk Patient Data Model

Defines the structure of patient information
stored in the SQLite database.
"""

from typing import Optional

from sqlalchemy import Column, Integer, String, Text
from database.database import Base


class Patient(Base):
    """
    Represents a MediKiosk patient record.
    """

    __tablename__ = "patients"

    patient_id = Column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True
    )

    name = Column(
        String(100),
        nullable=True
    )

    age = Column(
        Integer,
        nullable=True
    )

    gender = Column(
        String(20),
        nullable=True
    )

    symptoms = Column(
        Text,
        nullable=True
    )

    duration = Column(
        String(100),
        nullable=True
    )

    severity = Column(
        String(50),
        nullable=True
    )

    additional_symptoms = Column(
        Text,
        nullable=True
    )

    medical_history = Column(
        Text,
        nullable=True
    )

    current_medications = Column(
        Text,
        nullable=True
    )

    allergies = Column(
        Text,
        nullable=True
    )
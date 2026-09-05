"""
MediKiosk Patient Service

Handles creating, reading, updating and deleting
patient records from the database.
"""

from database.database import SessionLocal
from database.models import Patient


# =========================================================
# CREATE PATIENT
# =========================================================

def create_patient(
    name=None,
    age=None,
    gender=None,
    symptoms=None,
    duration=None,
    severity=None,
    additional_symptoms=None,
    medical_history=None,
    current_medications=None,
    allergies=None
):
    db = SessionLocal()

    try:
        patient = Patient(
            name=name,
            age=age,
            gender=gender,
            symptoms=symptoms,
            duration=duration,
            severity=severity,
            additional_symptoms=additional_symptoms,
            medical_history=medical_history,
            current_medications=current_medications,
            allergies=allergies
        )

        db.add(patient)
        db.commit()
        db.refresh(patient)

        return patient

    finally:
        db.close()


# =========================================================
# GET PATIENT
# =========================================================

def get_patient(patient_id):
    db = SessionLocal()

    try:
        return db.query(Patient).filter(
            Patient.patient_id == patient_id
        ).first()

    finally:
        db.close()


# =========================================================
# GET ALL PATIENTS
# =========================================================

def get_all_patients():
    db = SessionLocal()

    try:
        return db.query(Patient).order_by(
            Patient.patient_id.desc()
        ).all()

    finally:
        db.close()


# =========================================================
# UPDATE PATIENT
# =========================================================

def update_patient(patient_id, **data):
    db = SessionLocal()

    try:
        patient = db.query(Patient).filter(
            Patient.patient_id == patient_id
        ).first()

        if patient is None:
            return None

        allowed_fields = {
            "name",
            "age",
            "gender",
            "symptoms",
            "duration",
            "severity",
            "additional_symptoms",
            "medical_history",
            "current_medications",
            "allergies"
        }

        for field, value in data.items():

            if field in allowed_fields:
                setattr(patient, field, value)

        db.commit()
        db.refresh(patient)

        return patient

    finally:
        db.close()


# =========================================================
# DELETE PATIENT
# =========================================================

def delete_patient(patient_id):
    db = SessionLocal()

    try:
        patient = db.query(Patient).filter(
            Patient.patient_id == patient_id
        ).first()

        if patient is None:
            return False

        db.delete(patient)
        db.commit()

        return True

    finally:
        db.close()
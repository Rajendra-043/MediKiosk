import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from database.patient_service import (
    create_patient,
    get_patient,
    get_all_patients,
    update_patient,
    delete_patient,
)


def patient_to_dict(patient):
    return {
        "patient_id": patient.patient_id,
        "name": patient.name,
        "age": patient.age,
        "gender": patient.gender,
        "symptoms": patient.symptoms,
        "duration": patient.duration,
        "severity": patient.severity,
        "additional_symptoms": patient.additional_symptoms,
        "medical_history": patient.medical_history,
        "current_medications": patient.current_medications,
        "allergies": patient.allergies,
    }


@csrf_exempt
def patients_api(request):

    # ==============================
    # GET ALL PATIENTS
    # ==============================

    if request.method == "GET":

        patients = get_all_patients()

        return JsonResponse({
            "success": True,
            "patients": [
                patient_to_dict(patient)
                for patient in patients
            ]
        })


    # ==============================
    # CREATE PATIENT
    # ==============================

    if request.method == "POST":

        try:
            data = json.loads(
                request.body.decode("utf-8")
            )

            patient = create_patient(
                name=data.get("name"),
                age=data.get("age"),
                gender=data.get("gender"),
                symptoms=data.get("symptoms"),
                duration=data.get("duration"),
                severity=data.get("severity"),
                additional_symptoms=data.get(
                    "additional_symptoms"
                ),
                medical_history=data.get(
                    "medical_history"
                ),
                current_medications=data.get(
                    "current_medications"
                ),
                allergies=data.get("allergies"),
            )

            return JsonResponse({
                "success": True,
                "message": "Patient created successfully",
                "patient": patient_to_dict(patient)
            }, status=201)

        except Exception as error:

            return JsonResponse({
                "success": False,
                "error": str(error)
            }, status=400)


    return JsonResponse({
        "success": False,
        "error": "Method not allowed"
    }, status=405)


@csrf_exempt
def patient_detail_api(request, patient_id):

    # ==============================
    # GET ONE PATIENT
    # ==============================

    if request.method == "GET":

        patient = get_patient(patient_id)

        if patient is None:
            return JsonResponse({
                "success": False,
                "error": "Patient not found"
            }, status=404)

        return JsonResponse({
            "success": True,
            "patient": patient_to_dict(patient)
        })


    # ==============================
    # UPDATE PATIENT
    # ==============================

    if request.method == "PUT":

        try:
            data = json.loads(
                request.body.decode("utf-8")
            )

            patient = update_patient(
                patient_id,
                **data
            )

            if patient is None:
                return JsonResponse({
                    "success": False,
                    "error": "Patient not found"
                }, status=404)

            return JsonResponse({
                "success": True,
                "message": "Patient updated successfully",
                "patient": patient_to_dict(patient)
            })

        except Exception as error:

            return JsonResponse({
                "success": False,
                "error": str(error)
            }, status=400)


    # ==============================
    # DELETE PATIENT
    # ==============================

    if request.method == "DELETE":

        deleted = delete_patient(patient_id)

        if not deleted:
            return JsonResponse({
                "success": False,
                "error": "Patient not found"
            }, status=404)

        return JsonResponse({
            "success": True,
            "message": "Patient deleted successfully"
        })


    return JsonResponse({
        "success": False,
        "error": "Method not allowed"
    }, status=405)
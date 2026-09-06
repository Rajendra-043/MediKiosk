import json
import ollama
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# Patient service se get_patient import kar lo
from database.patient_service import get_patient


@csrf_exempt
def ask_ai_about_patient_api(request, patient_id):
    if request.method != "POST":
        return JsonResponse({
            "success": False,
            "error": "Method not allowed"
        }, status=405)

    patient = get_patient(patient_id)
    if patient is None:
        return JsonResponse({
            "success": False,
            "error": "Patient not found"
        }, status=404)

    try:
        data = json.loads(request.body.decode("utf-8"))
        doctor_query = data.get("query", "").strip()

        if not doctor_query:
            return JsonResponse({
                "success": False,
                "error": "Query cannot be empty"
            }, status=400)

        # Llama 3.2:1b ke liye medical context
        context = f"""
        You are an expert AI clinical medical assistant helping a doctor.
        Answer the doctor's query accurately and concisely based on the patient's record.

        PATIENT RECORD:
        - Name: {patient.name}
        - Age: {patient.age}
        - Gender: {patient.gender}
        - Symptoms: {patient.symptoms} (Duration: {patient.duration}, Severity: {patient.severity})
        - Additional Symptoms: {patient.additional_symptoms}
        - Medical History: {patient.medical_history}
        - Current Medications: {patient.current_medications}
        - Allergies: {patient.allergies}

        DOCTOR'S QUESTION:
        {doctor_query}
        """

        response = ollama.chat(
            model='llama3.2:1b',
            messages=[
                {
                    'role': 'user',
                    'content': context
                }
            ]
        )

        ai_answer = response['message']['content']

        return JsonResponse({
            "success": True,
            "reply": ai_answer
        })

    except Exception as error:
        return JsonResponse({
            "success": False,
            "error": str(error)
        }, status=500)
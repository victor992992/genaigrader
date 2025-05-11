from django.http import StreamingHttpResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
import json
from genaigrader.models import Exam, Model, Question
from genaigrader.services.stream_service import stream_responses
from genaigrader.llm_api import LlmApi

@login_required
def reevaluate_view(request):
    """Vista para mostrar exámenes del usuario actual"""
    exams = Exam.objects.filter(creator_username=request.user)
    models = Model.objects.all()
    local_models = [m for m in models if not m.is_external]
    external_models = [m for m in models if m.is_external]
    return render(request, "reevaluate.html", {
        "exams": exams,
        "local_models": local_models,     
        "external_models": external_models
    })

@csrf_exempt
def reevaluate_exam(request):
    """Procesa la reevaluación"""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            exam_id = data.get('exam_id')
            model_description = data.get('model')
            user_prompt = data.get('user_prompt', '')

            # Validar propiedad del examen
            exam = Exam.objects.get(
                id=exam_id,
                creator_username=request.user  
            )
            
            model = Model.objects.get(description=model_description)
            
            questions = exam.question_set.prefetch_related('questionoption_set').all()
            
            if not questions.exists():
                return HttpResponse("El examen no tiene preguntas", status=400)
            total_questions = len(questions)

            try:
                llm = LlmApi(model)
                llm.validate()  # This will raise ValueError if invalid
            except ValueError as e:
                return HttpResponse(str(e), status=400)

            return StreamingHttpResponse(
                stream_responses(questions, user_prompt, llm, total_questions, exam),
                content_type="text/event-stream"
            )

        except Exam.DoesNotExist:
            return HttpResponse("Examen no encontrado o no autorizado", status=404)
        except Model.DoesNotExist:
            return HttpResponse("Modelo no válido", status=400)
        except Exception as e:
            print(f"Error: {str(e)}")
            return HttpResponse(f"Error interno: {str(e)}", status=500)
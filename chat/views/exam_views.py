from django.http import StreamingHttpResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from chat.models import Course, Model
from chat.services.file_service import save_uploaded_file
from chat.services.exam_service import process_exam_file, create_exam
from chat.services.course_service import get_or_create_course
from chat.services.model_service import get_or_create_model
from chat.services.stream_service import stream_responses
from chat.llm_api import LlmApi

@login_required
def exam_view(request):
    """Renderiza la página del examen con modelos y asignaturas"""
    models = Model.objects.all()
    local_models = [m for m in models if not m.is_external]
    external_models = [m for m in models if m.is_external]
    courses = Course.objects.all()
    return render(request, "exam.html", {
        "courses": courses,
        "local_models": local_models,
        "external_models": external_models
    })

@csrf_exempt
def upload_file(request):
    """Handles file uploads and streams exam processing responses."""
    if request.method == "POST":
        try:
            course = get_or_create_course(request)
            uploaded_file = request.FILES["file"]
            exam = create_exam(uploaded_file, course, request.user, request)
            model = get_or_create_model(request)

            # Use LlmApi to validate and process the model
            try:
                llm = LlmApi(model)
                llm.validate()  # This will raise ValueError if invalid
            except ValueError as e:
                return HttpResponse(str(e), status=400)

            user_prompt = request.POST.get("user_prompt", "")
            file_path = save_uploaded_file(uploaded_file)
            questions = process_exam_file(file_path, exam)
            total_questions = len(questions)

            return StreamingHttpResponse(
                stream_responses(questions, user_prompt, llm, total_questions, exam),
                content_type="text/event-stream"
            )

        except Course.DoesNotExist:
            return HttpResponse("Asignatura no válida", status=400)
        except ValueError as e:
            return HttpResponse(str(e), status=400)
        except Exception as e:
            print(f"Error crítico: {str(e)}")
            return HttpResponse(f"Error en el servidor: {str(e)}", status=500)

    return HttpResponse("Método no permitido", status=405)
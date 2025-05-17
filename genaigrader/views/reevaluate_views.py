from django.http import StreamingHttpResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
import json
from genaigrader.models import Exam, Model, Question
from genaigrader.services.get_models_service import get_models_for_user
from genaigrader.services.stream_service import stream_responses
from genaigrader.llm_api import LlmApi

@login_required
def reevaluate_view(request):
    """View to display current user's exams"""
    exams = Exam.objects.filter(user=request.user)
    local_models, external_models = get_models_for_user(request.user)
    return render(request, "reevaluate.html", {
        "exams": exams,
        "local_models": local_models,
        "external_models": external_models,
    })


@csrf_exempt
def reevaluate_exam(request):
    """Process reevaluation"""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            exam_id = data.get('exam_id')
            model_description = data.get('model')
            user_prompt = data.get('user_prompt', '')

            # Validate exam ownership
            exam = Exam.objects.get(
                id=exam_id,
                user=request.user  
            )
            
            model = Model.objects.get(description=model_description)
            
            questions = exam.question_set.prefetch_related('questionoption_set').all()
            
            if not questions.exists():
                return HttpResponse("The exam has no questions", status=400)
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
            return HttpResponse("Exam not found or unauthorized", status=404)
        except Model.DoesNotExist:
            return HttpResponse("Invalid model", status=400)
        except Exception as e:
            print(f"Error: {str(e)}")
            return HttpResponse(f"Internal error: {str(e)}", status=500)
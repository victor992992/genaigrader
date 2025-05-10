from django.http import StreamingHttpResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db import transaction
from chat.models import Course, Model, Question, QuestionOption
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
    """Handle exam upload and processing with full validation"""
    if request.method == "POST":
        try:
            # 1. Initial validations and resource acquisition
            course = get_or_create_course(request)
            uploaded_file = request.FILES["file"]
            
            # 2. Validate LLM model first
            model = get_or_create_model(request)
            llm = LlmApi(model)
            llm.validate()  # Early model validation

            # 3. Process file in memory with format validation
            file_path = save_uploaded_file(uploaded_file)
            questions_data = process_exam_file(file_path)  # All validations happen here

            # 4. Atomic database creation
            with transaction.atomic():
                # Create exam (now saved within transaction)
                exam = create_exam(uploaded_file, course, request.user, request)
                exam.save()

                # Create questions and options
                for q_data in questions_data:
                    # Final redundant validation
                    if len(q_data['options']) < 2:
                        raise ValueError(f"Question '{q_data['statement'][:30]}...' has less than 2 options")
                    
                    question = Question.objects.create(
                        statement=q_data['statement'],
                        exam=exam
                    )
                    
                    # Process options
                    correct_option = None
                    for opt_content in q_data['options']:
                        option = QuestionOption.objects.create(
                            content=opt_content,
                            question=question
                        )
                        # Extract option letter
                        option_letter = opt_content.split(')')[0].strip().lower()
                        if option_letter == q_data['correct_option']:
                            correct_option = option
                    
                    if not correct_option:
                        raise ValueError(f"Question '{q_data['statement'][:30]}...' has no valid correct option")
                    
                    question.correct_option = correct_option
                    question.save()

            # 5. LLM post-processing (streaming)
            user_prompt = request.POST.get("user_prompt", "")
            return StreamingHttpResponse(
                stream_responses(Question.objects.filter(exam=exam), 
                user_prompt, 
                llm, 
                len(questions_data), 
                exam),
                content_type="text/event-stream"
            )

        except Exception as e:
            # Catch all errors (including validation errors)
            return HttpResponse(f"Error: {str(e)}", status=400)
    
    return HttpResponse("Method not allowed", status=405)
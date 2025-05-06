from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from chat.models import Course, Exam
from django.http import JsonResponse, QueryDict
from django.views.decorators.http import require_http_methods
from chat.services.course_service import create_new_course
from django.core.exceptions import ValidationError
from django.http import HttpResponse
import csv
from chat.models import Evaluation, Course
from django.shortcuts import get_object_or_404

@login_required
def course_view(request):
    if request.method == 'POST':
        try:
            course_name = request.POST.get('course_name')
            new_course = create_new_course(
                name=course_name,
                user=request.user
            )
            return JsonResponse({
                'status': 'success',
                'course': {'id': new_course.id, 'name': new_course.name}
            })
        except ValidationError as e:
            return JsonResponse({'status': 'error', 'message': e.message}, status=400)
    courses = Course.objects.filter(user=request.user).prefetch_related('exam_set')
    return render(request, 'course.html', {'courses': courses})

@login_required
@require_http_methods(["PUT"])
def update_course(request, course_id):
    try:
        course = Course.objects.get(id=course_id, user=request.user)
        data = QueryDict(request.body)
        course.name = data.get('name')
        course.save()
        return JsonResponse({'status': 'success'})
    except Course.DoesNotExist:
        return JsonResponse({'status': 'error'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@login_required
@require_http_methods(["DELETE"])
def delete_course(request, course_id):
    try:
        course = Course.objects.get(id=course_id, user=request.user)
        course.delete()
        return JsonResponse({'status': 'success'})
    except Course.DoesNotExist:
        return JsonResponse({'status': 'error'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
@login_required
@require_http_methods(["PUT"])
def update_exam(request, exam_id):
    try:
        exam = Exam.objects.select_related('course').get(
            id=exam_id, 
            course__user=request.user  
        )
        data = QueryDict(request.body)
        exam.description = data.get('description')
        exam.save()
        return JsonResponse({'status': 'success'})
    except Exam.DoesNotExist:
        return JsonResponse({'status': 'error'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@login_required
@require_http_methods(["DELETE"])
def delete_exam(request, exam_id):
    try:
        exam = Exam.objects.select_related('course').get(
            id=exam_id,
            course__user=request.user
        )
        exam.delete()
        return JsonResponse({'status': 'success'})
    except Exam.DoesNotExist:
        return JsonResponse({'status': 'error'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
@login_required
def export_all_evaluations(request):
    # Configurar respuesta
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')  # Codificación para Excel
    response['Content-Disposition'] = 'attachment; filename="todas_evaluaciones.csv"'
    
    # Crear writer con configuraciones específicas
    writer = csv.writer(response, delimiter=',', quoting=csv.QUOTE_ALL)
    
    # Escribir encabezado
    writer.writerow([
        'Asignatura', 
        'Examen', 
        'Fecha', 
        'Modelo', 
        'Prompt', 
        'Nota', 
        'Tiempo (s)'
    ])
    
    # Obtener datos con relaciones
    evaluations = Evaluation.objects.filter(
        exam__course__user=request.user
    ).select_related(
        'exam__course', 
        'model'
    ).order_by('exam__course__name', 'exam__description')
    
    # Escribir filas
    for eval in evaluations:
        writer.writerow([
            eval.exam.course.name,        # Columna 1
            eval.exam.description,        # Columna 2
            eval.ev_date.strftime("%d/%m/%Y"),  # Columna 3
            eval.model.description,       # Columna 4
            eval.prompt,                  # Columna 5
            str(eval.grade).replace('.', ','),  # Nota con formato decimal español
            str(round(eval.time, 2)).replace('.', ',')  # Tiempo formato ES
        ])
    
    return response

@login_required
def export_course_evaluations(request, course_id):
    # Verificar curso
    course = get_object_or_404(Course, id=course_id, user=request.user)
    
    # Configurar respuesta
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = f'attachment; filename="evaluaciones_{course.name}.csv"'
    
    # Crear writer
    writer = csv.writer(response, delimiter=',', quoting=csv.QUOTE_ALL)
    
    # Encabezado
    writer.writerow([
        'Examen', 
        'Fecha', 
        'Modelo', 
        'Prompt', 
        'Nota', 
        'Tiempo (s)'
    ])
    
    # Obtener datos
    evaluations = Evaluation.objects.filter(
        exam__course=course
    ).select_related('exam', 'model')
    
    # Escribir filas
    for eval in evaluations:
        writer.writerow([
            eval.exam.description,
            eval.ev_date.strftime("%d/%m/%Y"),
            eval.model.description,
            eval.prompt,
            str(eval.grade).replace('.', ','),
            str(round(eval.time, 2)).replace('.', ',')
        ])
    
    return response
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from genaigrader.models import Course, Evaluation
from collections import defaultdict
from genaigrader.services.confidence_service import compute_averages

@login_required
def analysis_view(request):
    # Obtener cursos y evaluaciones
    user_courses = Course.objects.filter(user=request.user).prefetch_related('exam_set')
    
    course_data = []
    
    # Procesar datos por curso
    for course in user_courses:
        evaluations = Evaluation.objects.filter(exam__in=course.exam_set.all())
        eval_data = list(evaluations.values('model__description', 'grade', 'time'))
        
        model_values = defaultdict(lambda: {'grades': [], 'times': []})
        for eval in eval_data:
            model = eval['model__description']
            model_values[model]['grades'].append(eval['grade'])
            model_values[model]['times'].append(eval['time'])
        
        # Calcular estadísticas para calificaciones
        model_average_grades, _ = compute_averages(model_values, 'grades')

        # Calcular estadísticas para tiempos
        model_average_times, _ = compute_averages(model_values, 'times')
               
        course_data.append({
            'course': {'id': course.id, 'name': course.name},
            'model_averages': sorted(model_average_grades, key=lambda x: x['model__description']),
            'time_averages': sorted(model_average_times, key=lambda x: x['model__description'])
        })
    
    # Calcular estadísticas globales
    all_evals = Evaluation.objects.filter(exam__course__user=request.user)
    all_eval_data = list(all_evals.values('model__description', 'grade', 'time'))
    
    global_groups = defaultdict(lambda: {'grades': [], 'times': []})
    for eval in all_eval_data:
        model = eval['model__description']
        global_groups[model]['grades'].append(eval['grade'])
        global_groups[model]['times'].append(eval['time'])
    
        # Calcular estadísticas globales para calificaciones
        overall_model_average_grades, _ = compute_averages(global_groups, 'grades')
        
        # Calcular estadísticas globales para tiempos
        overall_model_average_times, _ = compute_averages(global_groups, 'times')
    
    return render(request, 'analysis.html', {
        'course_data': course_data,
        'overall_model_averages': sorted(overall_model_average_grades, key=lambda x: x['model__description']),
        'overall_time_averages': sorted(overall_model_average_times, key=lambda x: x['model__description'])
    })


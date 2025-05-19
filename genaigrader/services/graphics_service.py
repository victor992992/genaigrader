from collections import defaultdict
from genaigrader.services.confidence_service import compute_averages
from collections import defaultdict

def process_evaluations_for_graphics(evaluations):
    model_values = defaultdict(lambda: {'grades': [], 'times': []})
    for eval in evaluations:
        model = eval.model.description
        model_values[model]['grades'].append(eval.grade)
        model_values[model]['times'].append(eval.time)
    return model_values

def compute_model_statistics(model_values):
    model_average_grades, _ = compute_averages(model_values, 'grades')
    model_average_times, _ = compute_averages(model_values, 'times')
    
    return (
        sorted(model_average_grades, key=lambda x: x['model__description']),
        sorted(model_average_times, key=lambda x: x['model__description'])
    )
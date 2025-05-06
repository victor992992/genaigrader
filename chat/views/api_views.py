from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, QueryDict
from chat.models import Model

def api_view(request):
    external_models = Model.objects.filter(api_url__isnull=False, api_key__isnull=False)
    return render(request, 'api.html', {'external_models': external_models})

@require_http_methods(["PUT"])
def update_model(request, model_id):
    try:
        model = get_object_or_404(Model, id=model_id)
        data = QueryDict(request.body)
        model.description = data.get('description')
        model.api_url = data.get('api_url')
        model.api_key = data.get('api_key')
        model.save()
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@require_http_methods(["DELETE"])
def delete_model(request, model_id):
    try:
        model = get_object_or_404(Model, id=model_id)
        model.delete()
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@require_http_methods(["POST"])
def create_model(request):
    try:
        data = QueryDict(request.body)
        new_model = Model.objects.create(
            description=data['description'],
            api_url=data['api_url'],
            api_key=data['api_key']
        )
        return JsonResponse({
            'status': 'success',
            'model': {
                'id': new_model.id,
                'description': new_model.description,
                'api_url': new_model.api_url,
                'api_key': new_model.api_key
            }
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
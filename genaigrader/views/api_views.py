from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, QueryDict
from genaigrader.models import Model
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_GET, require_POST
from django.shortcuts import get_object_or_404
import json
import requests


OLLAMA_BASE_URL = "http://localhost:11434"

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

@csrf_exempt
def pull_model(request):
    if request.method == 'POST':
        try:
            # Obtener datos del JSON
            data = json.loads(request.body)
            model_name = data.get('model', '').strip()

            if not model_name:
                return JsonResponse({'status': 'error', 'message': 'El nombre del modelo no puede estar vacío.'}, status=400)

            # URL correcta para Ollama
            ollama_url = f"{OLLAMA_BASE_URL}/api/pull"
            
            # Hacer POST a Ollama con el nombre del modelo
            response = requests.post(
                ollama_url,
                json={'name': model_name},
                timeout=30
            )
            
            # Verificar respuesta de Ollama
            if response.status_code == 200:
                # Crear modelo local sin API key
                new_model = Model.objects.create(
                    description=model_name,
                    api_url=OLLAMA_BASE_URL  # Usar la URL base de Ollama
                )
                return JsonResponse({
                    'status': 'success',
                    'message': f'Modelo {model_name} descargado con éxito.',
                    'model_id': new_model.id
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Ollama error: {response.text}'
                }, status=400)

        except requests.exceptions.ConnectionError:
            return JsonResponse({
                'status': 'error',
                'message': 'No se pudo conectar al servidor Ollama. ¿Está en ejecución?'
            }, status=500)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Método no permitido.'}, status=405)
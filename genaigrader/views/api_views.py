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
            data = json.loads(request.body)
            model_name = data.get('model', '').strip()

            if not model_name:
                return JsonResponse({'status': 'error', 'message': 'El nombre del modelo no puede estar vacío.'}, status=400)

            ollama_url = f"{OLLAMA_BASE_URL}/api/pull"
            
            # Realizar la solicitud a Ollama con streaming
            response = requests.post(
                ollama_url,
                json={'name': model_name},
                stream=True,
                timeout=10
            )
            
            # Verificar si hubo un error en la conexión
            if response.status_code != 200:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Error en Ollama: {response.text}'
                }, status=400)

            # Analizar el stream de respuesta
            error_occurred = False
            error_message = None
            for line in response.iter_lines():
                if line:
                    try:
                        chunk = json.loads(line)
                        if 'error' in chunk:
                            error_occurred = True
                            error_message = chunk['error']
                            break
                    except json.JSONDecodeError:
                        error_occurred = True
                        error_message = 'Respuesta inválida de Ollama'
                        break

            if error_occurred:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Modelo no encontrado: {error_message}'
                }, status=400)
            else:
                # Crear el modelo solo si no hubo errores
                new_model = Model.objects.create(
                    description=model_name,
                    api_url=OLLAMA_BASE_URL
                )
                return JsonResponse({
                    'status': 'success',
                    'message': f'Modelo {model_name} descargado correctamente',
                    'model_id': new_model.id
                })

        except requests.exceptions.ConnectionError:
            return JsonResponse({
                'status': 'error',
                'message': 'No se pudo conectar al servidor Ollama. ¿Está en ejecución?'
            }, status=500)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Método no permitido.'}, status=405)
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, QueryDict, StreamingHttpResponse
from genaigrader.models import Model
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_GET, require_POST
from django.shortcuts import get_object_or_404
import json
import requests


OLLAMA_BASE_URL = "http://localhost:11434"

def api_view(request):
    local_models = Model.objects.filter(api_url__isnull=True, api_key__isnull=True)
    external_models = Model.objects.exclude(api_url__isnull=True, api_key__isnull=True)
    return render(request, 'api.html', {
        'local_models': local_models,
        'external_models': external_models
    })

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
                stream=True
            )

            # Manejar errores de conexión con Ollama
            if response.status_code != 200:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Error en Ollama: {response.text}'
                }, status=400)

            def stream_generator():
                download_complete = False
                error_occurred = False
                
                for line in response.iter_lines():
                    if line:
                        try:
                            ollama_chunk = json.loads(line)
                            
                            # Enviar progreso al cliente
                            if 'status' in ollama_chunk:
                                yield json.dumps({
                                    'status': 'progress',
                                    'message': f'Descargando: {ollama_chunk["status"]}'
                                }) + "\n"
                                
                            # Detectar errores
                            if 'error' in ollama_chunk:
                                yield json.dumps({
                                    'status': 'error',
                                    'message': f'Error: {ollama_chunk["error"]}'
                                }) + "\n"
                                error_occurred = True
                                break
                                
                            # Detectar finalización exitosa
                            if ollama_chunk.get('status') == 'success':
                                download_complete = True
                                
                        except json.JSONDecodeError:
                            yield json.dumps({
                                'status': 'error',
                                'message': 'Error leyendo respuesta de Ollama'
                            }) + "\n"
                            error_occurred = True
                            break

                # Crear modelo solo si la descarga fue exitosa
                if download_complete and not error_occurred:
                    try:
                        new_model = Model.objects.create(
                            description=model_name,
                        )
                        yield json.dumps({
                            'status': 'success',
                            'message': f'Modelo {model_name} descargado correctamente!',
                            'model_id': new_model.id
                        }) + "\n"
                    except Exception as e:
                        yield json.dumps({
                            'status': 'error',
                            'message': f'Error creando modelo: {str(e)}'
                        }) + "\n"

            return StreamingHttpResponse(stream_generator(), content_type='application/json')

        except requests.exceptions.ConnectionError:
            return JsonResponse({
                'status': 'error',
                'message': 'No se pudo conectar a Ollama. ¿Está ejecutándose?'
            }, status=500)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Error inesperado: {str(e)}'
            }, status=500)

    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)
from chat.llm_api import generate_response
from ..models import Question

def query_llm(question,model):
    # Simula la llamada al LLM
    # return f"Simulación de respuesta para: {question}"
    prompt = "Te voy a pasar una pregunta de test y tienes que responderme con qué opción es la correcta. Sólo debes decirme la opción, por ejemplo 'a', absolutamente nada más.\n"
    prompt += question.statement + "\n"
    for option in question.options:
        prompt += option + "\n"
    print("Prompt:")
    print(prompt)

    response = list(generate_response(prompt, model))
    print("Response:")
    print(response)
    return response[0]


#Posiblemente se borre
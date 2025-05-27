#import plot
import boto3
from langchain.agents import create_sql_agent
from sqlalchemy import create_engine, text
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_aws import ChatBedrock
import gradio as gr
import sys
import time

# Redirigir la salida estándar a un archivo de log
sys.stdout = open('/home/ec2-user/langchain/gradio.log', 'a')
sys.stderr = sys.stdout

### Configuración de la base de datos MariaDB
#DATABASE_URI = "mysql+pymysql://root:12345678@localhost/datos_mercado"
DATABASE_URI = "mysql+pymysql://root:123456@localhost/datos_mercado"

engine = create_engine(DATABASE_URI)
db = SQLDatabase(engine)

####Todo este segmento se puede cambiar por el servicio o API del proveedor que gustes ###

#### Configurar Bedrock ####
bedrock_client = boto3.client('bedrock-runtime', region_name='us-east-1')

llm_bedrock = ChatBedrock(
    client=bedrock_client,
    model_id ="anthropic.claude-3-5-sonnet-20240620-v1:0",
    # model_id="anthropic.claude-3-sonnet-20240229-v1:0",
    model_kwargs={
        "max_tokens": 1000,
        "temperature": 0.01,
        "anthropic_version": "bedrock-2023-05-31"
    }
)
### Acá le paso el schema de de la Base de datos MariaDB y el mdoelo desde bedrock ###
toolkit_bedrock = SQLDatabaseToolkit(db=db, llm=llm_bedrock)
agent_bedrock = create_sql_agent(
    llm=llm_bedrock,
    toolkit=toolkit_bedrock,
    verbose=True,
    handle_parsing_errors=True
)
info_tabla = db.get_table_info_no_throw(db.get_table_names())

# Lista de palabras clave (Esto claramente hay que cambiarlo) #
# Lo uso para que el modelo, en caso de no detectar estas palabras,
# use su modo normal y responda preguntas en base a su entrenamiento

SQL_KEYWORDS = [
    'datos',
    'qué',
    'que',
    'consulta',
    'muestra',
    'muestrame',
    'muéstrame',
    'lista',
    'obtén',
    'obten'
    'dime',
    'cuántos',
    'cuantos',
    'cual',
    'cuál',
    'dame',
    'suma',
    'cuántas',
    'selecciona',
    'filtra',
    'busca',
    'encuentra'
]

GRAPH_KEYWORDS = ['grafica']

def process_user_query(user_message):

    ### Si la pregunta tiene alguna palabra del diccionario, se intenta con Langchain
    if any(keyword in user_message.lower() for keyword in SQL_KEYWORDS):
        try:

            print("Entró a Langchain")
            print("question: ", user_message)
            user_message = f"{user_message} Responde en español."

            # Invocar el agente con manejo de errores
            try:
                agent_response = agent_bedrock.invoke({"input": user_message})

                if isinstance(agent_response, dict) and 'output' in agent_response:
                    response_text = agent_response['output']
                else:
                    response_text = str(agent_response)

                print(f"Respuesta generada: {response_text}")

                ### Si la respuesta parece SQL, se ejecuta una consulta a la BD (esto para que no hayan errores!)
                if "SELECT" in response_text.upper() or "FROM" in response_text.upper():
                    with engine.connect() as conn:
                        result = conn.execute(text(response_text)).fetchall()
                        return str(result)
                else:
                    ###Acá llamaré a la funcion de graficar.
                    # if any(keyword in user_message.lower() for keyword in GRAPH_KEYWORDS):
                    #     gráfico = plot.generar_grafico(response_text)
                    return response_text



            except Exception as e:
                return f"Error al procesar la consulta con el agente: {str(e)}. Por favor, intenta reformular tu pregunta."

        except Exception as e:
            return f"Error general procesando consulta: {str(e)}"
    ### Si no tiene nada del diccionario, el modelo responde de forma "normal"
    else:
        return llm_bedrock.invoke(user_message).content



### Devuelvo la respuesta a la interfaz
def gradio_chat_interface(message, history):
    response = process_user_query(message)
    for i in range(len(message)):
        time.sleep(0.05)
        yield response

#### FRONT de gradio!
demo = gr.ChatInterface(
    fn=gradio_chat_interface,
    title="📊 Mercado Línea de Negocios",
    #examples=[
    #    "Cuál es el monto total por compañia en el año 2018 de las 5 con más ventas?",
    #    "Cual fue el monto total de la Empresa Life y GI sumadas en el periodo 2017?",
    #    "Muestra el top 3 de compañías con mayor monto del año 2024, cuarto trimeste, de empresa LIFE, quitando los subconceptos de Annuities y SIS",
    #    "Cuál fue el porcentaje de diferencia en el monto de la empresa LIFE del año 2023 y 2024?"
    #],
    theme="soft",
    #flagging_mode="manual",
    #flagging_options=["Like", "Spam", "Inappropriate", "Other"],
    css="""
    footer {visibility: hidden}
    .gradio-container {max-width: 800px !important}
    """
)

if __name__ == '__main__':
    demo.launch(server_name="0.0.0.0", server_port=7860, share=True)
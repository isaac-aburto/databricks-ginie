import gradio as gr
import boto3
from langchain.agents import create_sql_agent
from sqlalchemy import create_engine, text
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_aws import ChatBedrock
import sys
import time
from genie_chatbot import ask_genie

# Configuración de logging
sys.stdout = open('/home/ec2-user/langchain/gradio.log', 'a')
sys.stderr = sys.stdout

# 1. Configuración de la base de datos
DATABASE_URI = "mysql+pymysql://root:123456@localhost/datos_mercado"
engine = create_engine(DATABASE_URI)
db = SQLDatabase(engine)

# 2. Configuración de Bedrock
bedrock_client = boto3.client('bedrock-runtime', region_name='us-east-1')
llm_bedrock = ChatBedrock(
    client=bedrock_client,
    model_id="anthropic.claude-3-5-sonnet-20240620-v1:0",
    model_kwargs={
        "max_tokens": 1000,
        "temperature": 0.01,
        "anthropic_version": "bedrock-2023-05-31"
    }
)

# 3. Agente SQL
toolkit_bedrock = SQLDatabaseToolkit(db=db, llm=llm_bedrock)
agent_bedrock = create_sql_agent(
    llm=llm_bedrock,
    toolkit=toolkit_bedrock,
    verbose=True,
    handle_parsing_errors=True
)

# 4. Palabras clave para activar LangChain
SQL_KEYWORDS = [
    'datos', 'qué', 'que', 'consulta', 'muestra', 'muestrame', 'muéstrame',
    'lista', 'obtén', 'obten', 'dime', 'cuántos', 'cuantos', 'cual', 'cuál',
    'dame', 'suma', 'cuántas', 'selecciona', 'filtra', 'busca', 'encuentra'
]

# 5. Función para el chatbot SQL (modificada para aceptar history)
def process_user_query(message, history):
    if any(keyword in message.lower() for keyword in SQL_KEYWORDS):
        try:
            print("Entró a LangChain SQL Agent")
            enriched_message = f"{message} Responde en español."
            
            agent_response = agent_bedrock.invoke({"input": enriched_message})
            response_text = agent_response.get('output', str(agent_response))
            
            if "SELECT" in response_text.upper() or "FROM" in response_text.upper():
                with engine.connect() as conn:
                    result = conn.execute(text(response_text)).fetchall()
                    return str(result)
            return response_text
        except Exception as e:
            return f"Error al procesar con LangChain: {str(e)}"
    else:
        return llm_bedrock.invoke(message).content

# 6. Función para el chatbot Genie (modificada para aceptar history)
def respond_genie(message, history):
    try:
        return ask_genie(message)
    except Exception as e:
        return f"Error en Genie: {str(e)}"

# 7. Configuración de la interfaz
with gr.Blocks(
    title="Dual Chatbot - Backspace",
    theme=gr.themes.Soft(),
    css="""footer {visibility: hidden} .gradio-container {max-width: 800px !important}"""
) as demo:
    
    gr.Markdown("""
    <h1 style="text-align: center; color: #1f77b4;">
       Chatbots Especializados - Zurich
    </h1>
    """)
    
    with gr.Tabs():
        with gr.Tab("🤖 Langchain", id="sql_tab"):

            gr.ChatInterface(
                fn=process_user_query,
                examples=[
                    "Cuales fueron las 5 empresas con más ganancias en 2023?",
                    "¿Cuál fue el monto total de LIFE en Q1 2024?"
                ],
                chatbot=gr.Chatbot(height=400, label="Claude 3.5"),
                textbox=gr.Textbox(placeholder="Escribe tu consulta SQL natural...", lines=2),
                submit_btn="Enviar",
                retry_btn=None,
                undo_btn=None,
                clear_btn="Limpiar"
            )
        
        with gr.Tab("🧞 Databricks", id="genie_tab"):

            gr.ChatInterface(
                fn=respond_genie,
                examples=[
                    "Cuales fueron las 5 empresas con más ganancias en 2023?",
                    "¿Cuál fue el monto total de LIFE en Q1 2024?"
                ],
                chatbot=gr.Chatbot(height=400, label="Genie"),
                textbox=gr.Textbox(placeholder="Pregunta sobre análisis general...", lines=2),
                submit_btn="Enviar",
                retry_btn=None,
                undo_btn=None,
                clear_btn="Limpiar"
            )
    
    gr.Markdown("---")
    gr.HTML("""
    <div style="text-align: center; color: #666; font-size: 0.9em;">
        Desarrollado con ❤️ por Backspace usando:<br>
        Gradio + LangChain + Bedrock (Claude 3.5 Sonnet) + Databriks Genie
    </div>
    """)

# 8. Lanzamiento de la aplicación
if __name__ == '__main__':
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
        favicon_path=None
    )
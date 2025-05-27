import gradio as gr
from genie_chatbot import ask_genie

# Lógica del chatbot
def respond(message, history):
    response = ask_genie(message)
    return response

# Lista de preguntas de ejemplo
example_questions = [
    "¿Cuál fue la posición del ranking de montos que estaba Metlife en el 2023?",
    "¿Qué compañía lideró en rentabilidad en el primer trimestre?",
    "¿Cuál es la tendencia de crecimiento de primas de seguros en 2024?",
    "¿Qué empresa tuvo la mayor participación de mercado en 2022?",
]

# Interfaz principal con ChatInterface
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        """
        <h1 style="text-align: center; color: #1f77b4;">Chatbot Databricks - Genie</h1>
        """
    )

    chat = gr.ChatInterface(
        fn=respond,
        chatbot=gr.Chatbot(label="Genie"),
        # theme="soft",
        textbox=gr.Textbox(placeholder="Haz una pregunta sobre tus datos...", label="Tu mensaje"),
        title="",
        examples=example_questions,
        analytics_enabled=True,
        multimodal=True
    )
    chat.elem_classes = "chat-interface"
    gr.Markdown("<small>Desarrollado con ❤️ + Gradio + Databricks, por Backspace :)</small>", elem_classes="text-center")

demo.launch()

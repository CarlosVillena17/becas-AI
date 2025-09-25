import os
from dotenv import load_dotenv
import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import tempfile
from langchain.document_loaders import (
    PyPDFLoader,
    TextLoader,
    Docx2txtLoader,
    UnstructuredPowerPointLoader
)
from datetime import datetime

# Cargar variables de entorno
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    st.error("Falta OPENAI_API_KEY en tu archivo .env")
    st.stop()

# Configurar página
st.set_page_config(
    page_title="Agente de Becas - Asistente Virtual",
    page_icon="🎓",
    layout="centered"
)

# Estilos CSS para burbujas de chat estilo WhatsApp
st.markdown("""
<style>
    .chat-container {
        background-color: #f0f2f5;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 80px;
        max-height: 65vh;
        overflow-y: auto;
    }
    .user-message {
        background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
        color: white;
        padding: 12px 16px;
        border-radius: 18px 18px 5px 18px;
        margin: 8px 0;
        max-width: 70%;
        margin-left: auto;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .assistant-message {
        background-color: #ffffff;
        color: #333333;
        padding: 12px 16px;
        border-radius: 18px 18px 18px 5px;
        margin: 8px 0;
        max-width: 70%;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        border: 1px solid #e0e0e0;
    }
    .message-time {
        font-size: 0.7em;
        opacity: 0.7;
        margin-top: 5px;
        text-align: right;
    }
    .assistant-message .message-time {
        text-align: left;
    }
    .control-buttons {
        position: fixed;
        bottom: 80px;
        right: 20px;
        z-index: 1000;
    }
    .control-buttons button {
        margin-left: 5px;
        border-radius: 20px;
        padding: 8px 16px;
    }
    .file-indicator {
        background-color: #e3f2fd;
        border: 1px solid #bbdefb;
        border-radius: 10px;
        padding: 8px 12px;
        margin: 5px 0;
        font-size: 0.9em;
    }
</style>
""", unsafe_allow_html=True)

st.title("Agente de Becas - Asistente Virtual")
st.markdown(
    "¡Hola! Soy tu asistente especializado en becas para estudiantes peruanos. Pregúntame sobre becas nacionales, internacionales, requisitos, plazos, documentos, etc.")

# Inicializar el historial del chat en la sesión
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "¡Hola! ¿En qué puedo ayudarte hoy con respecto a becas?"}
    ]

# Contenedor del chat con burbujas estilo WhatsApp
st.markdown("<div class='chat-container'>", unsafe_allow_html=True)

for msg in st.session_state.messages:
    timestamp = datetime.now().strftime("%H:%M")

    if msg["role"] == "user":
        st.markdown(f"""
        <div class='user-message'>
            <div>👤 {msg["content"]}</div>
            <div class='message-time'>{timestamp}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class='assistant-message'>
            <div>🎓 {msg["content"]}</div>
            <div class='message-time'>{timestamp}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# Botones de control flotantes
st.markdown("<div class='control-buttons'>", unsafe_allow_html=True)
col1, col2 = st.columns(2)

with col1:
    if st.button("🗑️ Limpiar chat", help="Eliminar toda la conversación"):
        st.session_state.messages = [
            {"role": "assistant", "content": "¡Hola! ¿En qué puedo ayudarte hoy con respecto a becas?"}
        ]
        st.rerun()

with col2:
    if st.button("📥 Exportar chat", help="Descargar conversación completa"):
        if st.session_state.messages:
            # Crear contenido para exportar
            export_content = "CONVERSACIÓN - AGENTE DE BECAS\n"
            export_content += "=" * 50 + "\n\n"

            for i, msg in enumerate(st.session_state.messages, 1):
                role = "TÚ" if msg["role"] == "user" else "ASISTENTE"
                export_content += f"{i}. {role}:\n"
                export_content += f"{msg['content']}\n"
                export_content += "-" * 30 + "\n\n"

            # Crear botón de descarga
            st.download_button(
                label="💾 Descargar conversación",
                data=export_content,
                file_name=f"conversacion_becas_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain",
                use_container_width=True
            )

st.markdown("</div>", unsafe_allow_html=True)

# Sistema de prompt (mantener igual)
system_prompt = """
Eres un **Agente de Becas Inteligente**, especializado en orientar a estudiantes peruanos sobre oportunidades educativas nacionales e internacionales.

Tu misión:
- Brindar información confiable, clara y actualizada sobre becas de pregrado, posgrado y programas de intercambio.
- Explicar requisitos, plazos, beneficios y procesos de postulación de forma detallada pero sencilla.
- Guiar al usuario con pasos prácticos y consejos estratégicos para aumentar sus posibilidades de éxito.

Tu ámbito de conocimiento incluye:
- **Becas nacionales**: Beca Presidente de la República, Beca 18, Pronabec, Beca Permanencia, Beca Bicentenario entre otras.
- **Becas internacionales**: Fulbright, DAAD, Chevening, Erasmus+, y programas de universidades extranjeras.
- **Aspectos comunes**: requisitos (edad, promedio, idiomas, experiencia), documentos solicitados, cartas de motivación, entrevistas, financiamiento y convenios.
- **Consejos prácticos**: preparación del perfil académico, certificaciones de idiomas, planificación financiera y uso de recursos oficiales.

Instrucciones de estilo y respuesta:
- Responde SIEMPRE en **español claro, profesional y motivador**.
- Organiza la respuesta en **secciones o pasos numerados** cuando expliques procesos.
- Usa **listas con viñetas** para resumir requisitos o documentos.
- Si la pregunta es muy amplia, primero ofrece un panorama general y luego invita al usuario a precisar más.
- Si la pregunta no tiene relación con becas o educación, responde brevemente indicando que tu especialidad son becas y redirige al tema.

Restricciones:
- Si no tienes información específica sobre una beca o convocatoria, dilo con transparencia y sugiere dónde puede buscar (páginas oficiales como Pronabec, embajadas, fundaciones, universidades).
- No inventes requisitos falsos; si no estás seguro, acláralo.
- Mantén siempre un tono empático, orientador y profesional.
"""

# Configurar el LLM
llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0.3,
    api_key=OPENAI_API_KEY,
)

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{pregunta}")
])

parser = StrOutputParser()
chain = prompt | llm | parser


# Función para cargar y procesar archivos (mantener igual)
def cargar_documento(archivo_subido):
    """Carga y extrae texto de diferentes tipos de archivos"""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(archivo_subido.name)[1]) as tmp_file:
            tmp_file.write(archivo_subido.getvalue())
            tmp_path = tmp_file.name

        extension = os.path.splitext(archivo_subido.name)[1].lower()

        if extension == '.pdf':
            loader = PyPDFLoader(tmp_path)
        elif extension == '.txt':
            loader = TextLoader(tmp_path, encoding='utf-8')
        elif extension in ['.docx', '.doc']:
            loader = Docx2txtLoader(tmp_path)
        elif extension in ['.pptx', '.ppt']:
            loader = UnstructuredPowerPointLoader(tmp_path)
        else:
            os.unlink(tmp_path)
            return None, f"❌ Formato no soportado: {extension}"

        documentos = loader.load()
        texto_completo = "\n\n".join([doc.page_content for doc in documentos])
        os.unlink(tmp_path)
        return texto_completo, None

    except Exception as e:
        return None, f"❌ Error al procesar el archivo: {str(e)}"


# Sección para subir archivos en sidebar (mantener igual)
st.sidebar.header("Subir Documentos")
st.sidebar.markdown("Puedes subir documentos relacionados con becas para que los analice:")

archivo_subido = st.sidebar.file_uploader(
    "Selecciona un archivo",
    type=['pdf', 'txt', 'docx', 'doc', 'pptx', 'ppt'],
    help="Formatos soportados: PDF, TXT, DOCX, PPTX"
)

documento_texto = None

if archivo_subido is not None:
    with st.sidebar:
        with st.spinner(f"📊 Procesando {archivo_subido.name}..."):
            texto, error = cargar_documento(archivo_subido)

            if error:
                st.error(error)
            else:
                documento_texto = texto
                st.success(f"**{archivo_subido.name}** cargado")
                st.info(f"Tamaño: {len(texto):,} caracteres")

# Capturar entrada del usuario
user_input = st.chat_input("💭 Escribe tu pregunta sobre becas...")

if user_input:
    # Añadir mensaje del usuario al historial
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Preparar la pregunta incluyendo el documento si está disponible
    pregunta_final = user_input

    if documento_texto:
        texto_limitado = documento_texto[:8000]
        pregunta_final = f"""
Pregunta del usuario: {user_input}

Documento adjunto ({archivo_subido.name}):
{texto_limitado}

INSTRUCCIONES ESTRICTAS PARA EL ANÁLISIS:
1. Analiza el documento SOLO si está relacionado con becas para programas académicos de pregrado, maestría o doctorado
2. Si el documento trata sobre otros temas (cursos cortos, talleres, pasantías no académicas, etc.): 
   - Detén el análisis inmediatamente
   - Responde: "El documento analizado no corresponde a becas para educación superior formal"
   - No proporciones ningún resumen o información del documento
3. Si el documento SÍ es sobre becas académicas:
   - Proporciona un resumen claro del contenido
   - Identifica requisitos, plazos, beneficios específicos
   - Ofrece recomendaciones basadas en el documento
   - Señala información faltante si aplica

Responde la pregunta del usuario basándote estrictamente en estas instrucciones.
"""

    # Generar respuesta
    with st.spinner("Analizando tu consulta..."):
        try:
            respuesta = chain.invoke({"pregunta": pregunta_final})
            st.session_state.messages.append({"role": "assistant", "content": respuesta})
            st.rerun()
        except Exception as e:
            error_msg = f"❌ Error: {str(e)}"
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
            st.rerun()

# Información adicional en el sidebar (mantener igual)
st.sidebar.markdown("---")
st.sidebar.info("""
**💡 Tipos de documentos útiles:**
- Convocatorias de becas
- Requisitos y bases
- Formularios de postulación
- Guías de aplicación
- Cartas de motivación
""")

import os
import sys
import asyncio
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
import re
import random
from datetime import datetime

# Importaciones de Langchain
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document

# Importar el servicio PDF
try:
    from pdf_service import PDFService
    PDF_SERVICE_AVAILABLE_MODULE = True
    print("✅ Módulo PDFService importado correctamente")
except ImportError as e:
    PDF_SERVICE_AVAILABLE_MODULE = False
    print(f"⚠️ Módulo PDFService no disponible: {e}")
except Exception as e:
    PDF_SERVICE_AVAILABLE_MODULE = False
    print(f"❌ Error inesperado al importar PDFService: {e}")

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear la aplicación FastAPI
app = FastAPI(
    title="ComexBot API - Gratuito Ilimitado",
    description="API especializada en Comercio Exterior del Perú - Sin límites de conversaciones",
    version="2.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----- Carga de Recursos al Inicio (Para evitar timeouts) -----
# Variables globales para los recursos de IA y PDF
EMBEDDINGS_MODEL = None
VECTOR_STORE_DB = None
PDF_SERVICE_INSTANCE = None

try:
    print("🚀 Cargando modelo de embeddings SentenceTransformer...")
    # Carga el modelo de embeddings al inicio. Esto puede tardar.
    EMBEDDINGS_MODEL = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
    print("✅ Modelo de embeddings cargado.")
    
    print("🧠 Cargando base de datos vectorial...")
    # Carga la base de datos vectorial al inicio.
    VECTOR_STORE_DB = FAISS.load_local(
        folder_path="vectorstore",
        index_name="index",
        embeddings=EMBEDDINGS_MODEL,
        allow_dangerous_deserialization=True
    )
    print("✅ Base de datos vectorial cargada.")
    
    # Inicializa la instancia del servicio PDF una vez que los recursos están listos
    if PDF_SERVICE_AVAILABLE_MODULE:
        PDF_SERVICE_INSTANCE = PDFService(db=VECTOR_STORE_DB)
        print("✅ PDFService inicializado con recursos cargados.")
    else:
        print("⚠️ No se pudo inicializar PDFService porque el módulo no se importó.")
        
except Exception as e:
    logger.error(f"❌ Error CRÍTICO al cargar recursos de IA/PDF al inicio: {e}")
    # Si falla la carga, las variables globales seguirán siendo None
    # El servicio PDF se reportará como "no disponible".

# ----- Modelos Pydantic -----
class QueryRequest(BaseModel):
    query: str
    pdf_names: Optional[List[str]] = None
    max_results: Optional[int] = 5

class QueryResponse(BaseModel):
    results: List[Dict[str, Any]]
    total_results: int
    query: str

class ChatMessage(BaseModel):
    message: str
    user_id: Optional[str] = "anonymous"

class ChatResponse(BaseModel):
    response: str
    confidence: float = 0.8
    sources: List[str] = []

# ===== SISTEMA DE IA GRATUITA AVANZADA =====
KNOWLEDGE_BASE = {
    "importacion": {
        "keywords": ["importar", "importación", "import", "traer productos", "comprar exterior"],
        "responses": [
            """📦 **GUÍA COMPLETA DE IMPORTACIÓN EN PERÚ:**

**Requisitos Básicos:**
• RUC activo y habilitado para comercio exterior
• Registro como importador en SUNAT
• Póliza de caución o garantía bancaria (según el caso)

**Documentos Esenciales:**
• Factura comercial (original)
• Lista de empaque (Packing List)
• Conocimiento de embarque (B/L marítimo o Airway Bill aéreo)
• Certificado de origen (si aplica preferencias arancelarias)

**Proceso Paso a Paso:**
1️⃣ Negociar con proveedor (INCOTERMS, precios, calidad)
2️⃣ Coordinar envío y documentos
3️⃣ Presentar DAM (Declaración Aduanera de Mercancías)
4️⃣ Pagar tributos (Aranceles, IGV, IPM)
5️⃣ Despacho aduanero y retiro de mercancía

**Tiempos aproximados:** 7-15 días hábiles desde llegada al puerto.

¿Necesitas información específica sobre algún paso o producto?""",
            
            """🚢 **IMPORTACIÓN INTELIGENTE - CONSEJOS PRÁCTICOS:**

**Para Principiantes:**
• Empieza con productos simples (textiles, accesorios)
• Volúmenes pequeños para ganar experiencia
• Usa agentes de aduana experimentados

**Optimización de Costos:**
• Consolida envíos para reducir flete
• Negocia términos FOB vs CIF
• Aprovecha regímenes especiales (Drawback, CETICOS)

**Tributos Principales:**
• **Ad Valorem:** 0% a 17% según partida arancelaria
• **IGV:** 18% sobre (CIF + Arancel)
• **IPM:** 2% sobre base imponible
• **ISC:** Solo productos específicos (licores, cigarrillos, etc.)

**Documentos Adicionales según producto:**
• DIGESA: Alimentos, cosméticos, productos sanitarios
• SENASA: Productos agrícolas, pecuarios
• MTC: Vehículos y partes
• DIGEMID: Productos farmacéuticos

¿Qué tipo de producto planeas importar?"""
        ]
    },
    
    "exportacion": {
        "keywords": ["exportar", "exportación", "export", "vender exterior", "enviar productos"],
        "responses": [
            """🌎 **GUÍA DE EXPORTACIÓN DESDE PERÚ:**

**Requisitos Básicos:**
• RUC activo con actividad de exportación
• No requiere registro previo como exportador
• Factura o boleta de venta del bien

**Documentos Principales:**
• Declaración Única de Aduanas (DUA)
• Factura comercial
• Lista de empaque
• Documento de transporte
• Certificados según destino y producto

**Proceso de Exportación:**
1️⃣ Embalar y rotular mercancía
2️⃣ Contratar transporte internacional
3️⃣ Presentar DUA en SUNAT
4️⃣ Inspección aduanera (si corresponde)
5️⃣ Embarque y envío

**Beneficios Tributarios:**
• Drawback: Devolución 4% del valor FOB
• Reposición de mercancías en franquicia
• Exportación de servicios (exonerada IGV)

**Productos Peruanos Competitivos:**
• Agroindustriales (quinua, cacao, café)
• Textiles (algodón pima, alpaca)
• Minería y metalurgia
• Pesca y acuicultura

¿Tienes un producto específico en mente para exportar?"""
        ]
    },
    
    "tributos": {
        "keywords": ["tributo", "impuesto", "arancel", "igv", "ipm", "isc", "costo", "pagar"],
        "responses": [
            """💰 **TRIBUTOS EN COMERCIO EXTERIOR PERUANO:**

**IMPORTACIÓN - Tributos Principales:**

**1. Ad Valorem (Arancel Base):**
• Rango: 0% a 17% según partida arancelaria
• Base: Valor CIF (Costo + Seguro + Flete)
• Consulta: Arancel de Aduanas SUNAT

**2. IGV (Impuesto General a las Ventas):**
• Tasa: 18%
• Base: (CIF + Ad Valorem + ISC)
• Aplica a todas las importaciones

**3. IPM (Impuesto de Promoción Municipal):**
• Tasa: 2%
• Base: Misma que IGV
• Solo en importaciones

**4. ISC (Impuesto Selectivo al Consumo):**
• Solo productos específicos
• Combustibles, licores, cigarrillos, vehículos, etc.
• Tasas variables según producto

**CÁLCULO EJEMPLO:**
Producto: Valor CIF $1,000
- Ad Valorem (6%): $60
- Base IGV: $1,060
- IGV (18%): $190.80
- IPM (2%): $21.20
- **Total tributos: $271.20**

**EXPORTACIÓN:**
• Generalmente 0% de tributos
• Beneficios: Drawback, devolución IGV

¿Necesitas calcular tributos para un producto específico?"""
        ]
    }
}

# Respuestas generales mejoradas
GENERAL_RESPONSES = [
    """¡Hola! Soy ComexBot, tu asistente especializado en **comercio exterior peruano**. 

🚀 **Puedo ayudarte con:**
• Importación y exportación paso a paso
• Cálculo de tributos y aranceles  
• Constitución de empresas comerciales
• Documentación y certificados
• Regímenes aduaneros especiales
• Optimización de costos

💡 **Pregunta específica:** "¿Cómo importar desde China?" o "¿Cuánto cuesta exportar quinua?"

¿En qué tema específico te gustaría que te asesore?""",
    
    """Perfecto, estás en el lugar correcto para **comercio exterior peruano**. 

🎯 **Temas populares:**
• "Requisitos para importar productos electrónicos"
• "Pasos para exportar alimentos procesados" 
• "Cómo calcular tributos de importación"
• "Documentos necesarios para DIGESA"
• "Beneficios del Drawback"

📊 **Soy especialista en:**
• Procedimientos SUNAT actualizados
• TLCs y preferencias arancelarias
• Regímenes especiales (CETICOS, Admisión Temporal)
• Optimización tributaria legal

¿Sobre qué aspecto específico necesitas asesoría?"""
]

# Funciones de IA Local Mejoradas
def normalize_text(text: str) -> str:
    """Normaliza texto para mejor matching"""
    return re.sub(r'[^\w\s]', ' ', text.lower()).strip()

def calculate_intent_score(message: str, keywords: List[str]) -> float:
    """Calcula score de intención basado en keywords"""
    normalized_msg = normalize_text(message)
    words = normalized_msg.split()
    
    matches = 0
    for keyword in keywords:
        for word in words:
            if keyword in word or word in keyword:
                matches += 1
    
    return matches / len(words) if words else 0

def find_best_intent(message: str) -> tuple:
    """Encuentra la mejor intención con score"""
    normalized_msg = normalize_text(message)
    
    # Verificar saludos primero
    greeting_words = ["hola", "buenos", "buenas", "saludos", "hey", "hi", "start"]
    if any(word in normalized_msg for word in greeting_words):
        return "greeting", 1.0
    
    # Buscar mejor intención en knowledge base
    best_intent = None
    max_score = 0
    
    for intent, data in KNOWLEDGE_BASE.items():
        score = calculate_intent_score(message, data["keywords"])
        if score > max_score:
            max_score = score
            best_intent = intent
    
    # Solo retornar intención si score es significativo
    if max_score > 0.1:  # Threshold mínimo
        return best_intent, max_score
    
    return "general", 0.3

def generate_smart_response(intent: str, score: float, original_message: str) -> tuple:
    """Genera respuesta inteligente con confianza"""
    
    if intent == "greeting":
        response = random.choice([
            "¡Hola! 👋 Bienvenido a ComexBot. Soy tu especialista en comercio exterior peruano. ¿En qué puedo ayudarte hoy?",
            "¡Excelente día! Estoy aquí para asesorarte en importación, exportación y todo lo relacionado con comercio exterior. ¿Cuál es tu consulta?",
            "¡Saludos! Soy ComexBot, tu asistente experto en SUNAT, aduanas y comercio internacional. ¿Qué necesitas saber?"
        ])
        return response, 0.9
    
    if intent == "general":
        response = random.choice(GENERAL_RESPONSES)
        return response, 0.5
    
    if intent in KNOWLEDGE_BASE:
        responses = KNOWLEDGE_BASE[intent]["responses"]
        response = random.choice(responses)
        return response, min(0.9, score + 0.3)
    
    # Fallback response
    response = """No estoy seguro de cómo ayudarte con esa consulta específica. 

Soy especialista en **comercio exterior peruano**. Puedo asesorarte sobre:
• Importación y exportación
• Tributos y aranceles
• Documentación aduanera  
• Constitución de empresas
• Regímenes especiales

¿Podrías reformular tu pregunta sobre alguno de estos temas?"""
    
    return response, 0.3

# ===== ENDPOINTS =====

@app.get("/", summary="Estado del servicio", tags=["Health"])
async def root():
    """Endpoint raíz con información de la API"""
    pdf_status = "✅ Disponible" if PDF_SERVICE_INSTANCE else "❌ No disponible"
    
    return {
        "message": "🚀 ComexBot API funcionando correctamente",
        "status": "online",
        "version": "2.0.0",
        "features": [
            "✅ Conversaciones ilimitadas",
            "✅ IA local gratuita", 
            "✅ Sin APIs de pago",
            "✅ Disponible 24/7"
        ],
        "services": {
            "ai_local": "✅ Activa",
            "pdf_service": pdf_status
        },
        "endpoints": {
            "chat": "/chat - Conversación principal",
            "search": "/search - Búsqueda en documentos", 
            "health": "/health - Estado del sistema",
            "stats": "/stats - Estadísticas de uso"
        }
    }

@app.get("/health")
async def health_check():
    """Endpoint de salud mejorado"""
    pdf_service_status = "available" if PDF_SERVICE_INSTANCE is not None else "unavailable"
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "ai_local": "active",
            "pdf_service": pdf_service_status,
            "knowledge_base_topics": len(KNOWLEDGE_BASE)
        },
        "system": {
            "unlimited_conversations": True,
            "free_apis_only": True,
            "cost_per_message": 0.0
        }
    }

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatMessage):
    """Endpoint de chat mejorado - IA local + documentos opcionales"""
    try:
        query = request.message.strip()
        
        if not query:
            return ChatResponse(
                response="Por favor envía un mensaje para poder ayudarte.",
                confidence=0.3,
                sources=[]
            )
        
        # PRIMERA OPCIÓN: Buscar en documentos PDF si el servicio está disponible y cargado
        if PDF_SERVICE_INSTANCE:
            try:
                # Usamos la instancia global ya cargada
                results = PDF_SERVICE_INSTANCE.search_documents(query=query, k=3)
                
                if results and len(results) > 0:
                    best_match = results[0]
                    content = best_match['content']
                    source_pdf = best_match['source_pdf']
                    
                    snippet = content[:400].strip()
                    pdf_response = f"""📋 **Información encontrada en documentos:**

{snippet}...

💡 **¿Te ayuda esta información?** Si necesitas más detalles específicos sobre algún aspecto, pregúntame directamente."""
                    
                    return ChatResponse(
                        response=pdf_response,
                        confidence=0.85,
                        sources=[source_pdf]
                    )
            except Exception as e:
                logger.warning(f"Error en búsqueda PDF: {e}")
        
        # SEGUNDA OPCIÓN: IA Local (siempre disponible)
        intent, score = find_best_intent(query)
        response, confidence = generate_smart_response(intent, score, query)
        
        return ChatResponse(
            response=response,
            confidence=confidence,
            sources=["IA Local - ComexBot"]
        )
        
    except Exception as e:
        logger.error(f"Error en chat: {e}")
        return ChatResponse(
            response="Disculpa, ocurrió un error técnico. ¿Podrías intentar reformular tu consulta sobre comercio exterior?",
            confidence=0.3,
            sources=[]
        )

# Evento de inicio - Se ejecuta antes de que Gunicorn empiece a aceptar peticiones
@app.on_event("startup")
async def startup_event():
    """Evento de inicio para arrancar el servidor rápidamente."""
    print("🚀 FastAPI Startup event ejecutándose. El servidor está listo para iniciar.")
    # La carga de recursos (embeddings, db, pdf_service) ya se hizo globalmente antes de app = FastAPI()
    # para que esté lista cuando Gunicorn inicie los workers.
    print("Carga de recursos (embeddings, DB, PDFService) completada previamente.")

# Manejo de errores global
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"HTTP Exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "message": "Ocurrió un error en la petición.",
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Excepción no manejada: {exc}", exc_info=True) # exc_info=True para loggear el traceback
    return JSONResponse(
        status_code=500,
        content={
            "error": "Error interno del sistema",
            "message": "El sistema sigue funcionando. Intenta reformular tu consulta sobre comercio exterior.",
            "support": "Sistema gratuito sin límites - errores ocasionales son normales"
        }
    )

# Para ejecución local con uvicorn (opcional)
if __name__ == "__main__":
    if PDF_SERVICE_AVAILABLE_MODULE and EMBEDDINGS_MODEL is None:
        print("❌ ERROR: El módulo PDFService está disponible, pero los recursos (embeddings/DB) no se cargaron correctamente al inicio.")
    elif not PDF_SERVICE_AVAILABLE_MODULE:
        print("⚠️ Advertencia: El módulo PDFService no se pudo importar. La búsqueda en documentos PDF no estará disponible.")
        
    print("\nIniciando servidor local con Uvicorn...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
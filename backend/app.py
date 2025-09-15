import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
import re
import random
from datetime import datetime

# Importar el servicio PDF (opcional)
try:
    from backend.services.pdf_service import PDFService
    PDF_SERVICE_AVAILABLE = True
except ImportError as e:
    PDF_SERVICE_AVAILABLE = False
    print(f"⚠️ Servicio PDF no disponible: {e}")

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
    allow_origins=["*"],  # En producción, especificar dominios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Variable global para el servicio PDF
pdf_service = None

# Modelos Pydantic
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

¿Tienes un producto específico en mente para exportar?""",
            
            """✈️ **EXPORTACIÓN EXITOSA - ESTRATEGIAS AVANZADAS:**

**Investigación de Mercados:**
• Analiza demanda en países objetivo
• Estudia competencia y precios
• Verifica barreras arancelarias y no arancelarias

**Canales de Distribución:**
• Venta directa a importadores
• Agentes comerciales locales
• Plataformas B2B (Alibaba, Global Sources)
• Ferias comerciales internacionales

**Aspectos Financieros:**
• Cartas de crédito para pagos seguros
• Seguro de crédito a la exportación
• SECREX (Seguro de Crédito a la Exportación)
• Financiamiento pre y post embarque

**Certificaciones Importantes:**
• ISO 9001, ISO 14001 (calidad y ambiente)
• Certificados orgánicos (USDA, EU Organic)
• Fair Trade (comercio justo)
• BRC, HACCP (alimentos)

**PROMPERU y Apoyo Estatal:**
• Misiones comerciales
• Ruedas de negocios
• Estudios de mercado gratuitos
• Capacitación exportadora

¿En qué mercado internacional estás interesado?"""
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

¿Necesitas calcular tributos para un producto específico?""",
            
            """🧮 **OPTIMIZACIÓN TRIBUTARIA EN COMERCIO EXTERIOR:**

**Estrategias de Ahorro Legal:**

**1. Aprovecha Acuerdos Comerciales:**
• TLC Perú-China: Reducción progresiva aranceles
• TLC Perú-USA: Muchos productos 0%
• Alianza del Pacífico: Preferencias regionales
• CAN: Productos andinos liberados

**2. Regímenes Aduaneros Especiales:**
• **Drawback:** Devolución 4% valor FOB exportado
• **Admisión Temporal:** Suspensión tributos (maquinaria)
• **CETICOS:** Zonas francas con beneficios
• **Reposición Franquicia:** Insumos para exportación

**3. Clasificación Arancelaria Correcta:**
• Asesoría profesional evita sobrecostos
• Consultas vinculantes a SUNAT
• Revisión periódica de partidas arancelarias

**4. INCOTERMS Estratégicos:**
• **FOB:** Control sobre flete y seguro
• **CIF:** Facilita cálculo de tributos
• **EXW:** Mínima responsabilidad vendedor

**5. Planificación Financiera:**
• Garantías nominativas vs efectivo
• Financiamiento de tributos
• Cronograma de pagos optimizado

**Herramientas SUNAT Gratuitas:**
• Simulador de tributos
• Consulta de partidas arancelarias
• Calculadora de drawback

¿Quieres que analicemos la optimización para tu producto específico?"""
        ]
    },
    
    "empresas": {
        "keywords": ["empresa", "constituir", "sociedad", "ruc", "sunarp", "negocio"],
        "responses": [
            """🏢 **CONSTITUCIÓN DE EMPRESAS EN PERÚ:**

**Tipos de Sociedades Más Comunes:**

**1. SAC (Sociedad Anónima Cerrada):**
• 2-20 accionistas máximo
• Capital mínimo: Sin monto mínimo
• Ideal para: Empresas familiares, PYMEs
• Responsabilidad limitada al capital aportado

**2. SRL (Sociedad de Responsabilidad Limitada):**
• 2-20 socios máximo
• Participaciones en lugar de acciones
• Gestión más flexible que SAC
• Popular para comercio exterior

**3. EIRL (Empresa Individual de Resp. Limitada):**
• Un solo titular
• Capital separado del patrimonio personal
• Ideal para importadores/exportadores individuales

**Proceso de Constitución:**
1️⃣ **Reserva de nombre** (SUNARP)
2️⃣ **Elaboración de minuta** (abogado)
3️⃣ **Escritura pública** (notario)
4️⃣ **Inscripción SUNARP** (Registros Públicos)
5️⃣ **RUC en SUNAT**
6️⃣ **Licencia municipal**

**Costos Aproximados:**
• Reserva nombre: S/ 20
• Minuta: S/ 300-500
• Escritura pública: S/ 150-300
• SUNARP: S/ 80-120
• **Total aprox: S/ 550-940**

¿Qué tipo de sociedad te conviene más para tu negocio?""",
            
            """📋 **EMPRESAS PARA COMERCIO EXTERIOR - GUÍA ESPECIALIZADA:**

**Consideraciones Especiales para ComEx:**

**Actividades Económicas CIIU:**
• 4690: Venta al por mayor no especializada
• 4610: Venta al por mayor por cuenta propia
• 4649: Comercio al por mayor de otros enseres

**RUC y Habilitaciones:**
• RUC activo obligatorio
• Clave SOL para trámites online
• Representante legal autorizado
• Domicilio fiscal actualizado

**Capital Social Recomendado:**
• **Importación:** Mínimo S/ 10,000-50,000
• **Exportación:** Desde S/ 5,000
• **Mixto:** S/ 20,000-100,000
• Considera garantías aduaneras

**Documentos Corporativos Clave:**
• Estatuto con objeto social amplio
• Poder para representante legal
• Libro de actas actualizado
• Estados financieros auditados (grandes volúmenes)

**Obligaciones Tributarias:**
• Régimen General vs MYPE Tributario
• Libros contables según facturación
• Declaraciones mensuales y anuales
• Detracciones en operaciones

**Aspectos Bancarios:**
• Cuentas en moneda extranjera
• Líneas de crédito comercial
• Cartas de crédito documentarias
• Seguros de mercancía

**Normativa Especial:**
• Ley contra lavado de activos
• Reporte de operaciones sospechosas (UIF)
• Beneficiario final identificado

¿Necesitas asesoría sobre algún aspecto específico de tu futura empresa?"""
        ]
    },

    "documentos": {
        "keywords": ["documento", "certificado", "papel", "trámite", "permiso", "licencia"],
        "responses": [
            """📄 **DOCUMENTOS ESENCIALES EN COMERCIO EXTERIOR:**

**IMPORTACIÓN - Documentos Básicos:**
• **Factura Comercial:** Detalle de mercancía y valores
• **Packing List:** Lista de empaque detallada
• **B/L o AWB:** Conocimiento de embarque/guía aérea
• **Póliza de Seguro:** Cobertura de mercancía
• **Certificado de Origen:** Preferencias arancelarias

**Documentos Según Producto:**

**🍎 ALIMENTOS:**
• Certificado sanitario país origen
• Registro DIGESA del importador
• Habilitación de establecimiento
• Análisis bromatológico

**🌱 PRODUCTOS AGRÍCOLAS:**
• Certificado fitosanitario
• Permiso fitosanitario SENASA
• Tratamientos cuarentenarios
• Certificado orgánico (si aplica)

**🚗 VEHÍCULOS:**
• Certificado de conformidad
• Homologación vehicular (MTC)
• Certificado de emisiones
• Seguro obligatorio (SOAT)

**💊 MEDICAMENTOS:**
• Registro sanitario DIGEMID
• Certificado de Buenas Prácticas
• Autorización de importación
• Receta médica (controlados)

**📋 Tips Importantes:**
• Documentos en español o traducidos
• Legalización consular según país
• Vigencias actualizadas
• Copias certificadas de respaldo

¿Necesitas información específica sobre documentos para tu producto?"""
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

¿Sobre qué aspecto específico necesitas asesoría?""",
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

# Mantener funciones originales para compatibilidad
def generate_simple_response(query: str, content: str) -> str:
    """Genera respuesta simple basada en contenido encontrado de PDFs"""
    snippet = content[:400].strip()
    
    response = f"""📋 **Información encontrada en documentos:**

{snippet}...

💡 **¿Te ayuda esta información?** Si necesitas más detalles específicos sobre algún aspecto, pregúntame directamente.

🤖 También puedo ayudarte con consultas generales sobre comercio exterior sin necesidad de documentos específicos."""
    
    return response

def generate_fallback_response(query: str) -> str:
    """Genera respuestas por defecto cuando no hay documentos relevantes"""
    intent, score = find_best_intent(query)
    response, confidence = generate_smart_response(intent, score, query)
    return response

# Inicialización mejorada
def initialize_services():
    """Inicializa servicios con mejor manejo de errores"""
    global pdf_service
    
    try:
        print("🚀 Iniciando ComexBot API Gratuito Ilimitado...")
        print("💡 Sistema híbrido: PDFs + IA Local gratuita")
        
        if PDF_SERVICE_AVAILABLE:
            print("📚 Intentando cargar sistema de documentos...")
            try:
                pdf_service = PDFService(
                    pdf_directory="data/pdfs",
                    cache_directory="data/cache"
                )
                loaded_count = pdf_service.load_all_pdfs()
                print(f"✅ {loaded_count} documento(s) PDF cargado(s)")
            except Exception as e:
                print(f"⚠️ PDFs no disponibles: {e}")
                pdf_service = None
        else:
            print("⚠️ Servicio PDF no disponible - Solo IA local")
        
        print("🧠 Sistema de IA local activado")
        print("✅ ComexBot listo - Conversaciones ilimitadas")
        
        return True
        
    except Exception as e:
        logger.error(f"Error inicializando servicios: {e}")
        print(f"❌ Error: {e}")
        print("⚠️ Sistema iniciado con funcionalidad limitada")
        return False

# Evento de inicio
@app.on_event("startup")
async def startup_event():
    """Se ejecuta al iniciar la aplicación"""
    initialize_services()

# Endpoints mejorados
@app.get("/")
async def root():
    """Endpoint raíz con información de la API"""
    global pdf_service
    
    pdf_status = "✅ Disponible" if pdf_service else "⚠️ No disponible"
    
    return {
        "message": "ComexBot API - Comercio Exterior Perú",
        "version": "2.0.0",
        "status": "🚀 Funcionando",
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
    global pdf_service
    
    pdf_service_status = "available" if pdf_service is not None else "unavailable"
    vectorstores_count = len(pdf_service.vectorstores) if pdf_service else 0
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "ai_local": "active",
            "pdf_service": pdf_service_status,
            "vectorstores": vectorstores_count,
            "knowledge_base_topics": len(KNOWLEDGE_BASE)
        },
        "system": {
            "unlimited_conversations": True,
            "free_apis_only": True,
            "cost_per_message": 0.0
        }
    }

@app.get("/stats")
async def get_stats():
    """Estadísticas del sistema"""
    global pdf_service
    
    return {
        "knowledge_base": {
            "total_topics": len(KNOWLEDGE_BASE),
            "available_topics": list(KNOWLEDGE_BASE.keys()),
            "total_responses": sum(len(topic["responses"]) for topic in KNOWLEDGE_BASE.values())
        },
        "pdf_service": {
            "status": "available" if pdf_service else "unavailable", 
            "documents": len(pdf_service.vectorstores) if pdf_service else 0
        },
        "system": {
            "service_type": "Completamente gratuito",
            "ai_type": "IA Local + Búsqueda en documentos",
            "conversation_limit": "Ilimitado",
            "cost_structure": "Sin costos por mensaje"
        }
    }

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatMessage):
    """Endpoint de chat mejorado - IA local + documentos opcionales"""
    global pdf_service
    
    try:
        query = request.message.strip()
        
        if not query:
            return ChatResponse(
                response="Por favor envía un mensaje para poder ayudarte.",
                confidence=0.3,
                sources=[]
            )
        
        # PRIMERA OPCIÓN: Buscar en documentos PDF si están disponibles
        if pdf_service is not None and len(pdf_service.vectorstores) > 0:
            try:
                results = pdf_service.search_documents(query=query, k=3)
                
                if results and len(results) > 0:
                    # Usar el contenido encontrado
                    best_match = results[0]
                    content = best_match['content']
                    source_pdf = best_match['source_pdf']
                    
                    # Generar respuesta basada en documento + IA local
                    pdf_response = generate_simple_response(query, content)
                    
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

# Mantener endpoints originales para compatibilidad
@app.post("/search", response_model=QueryResponse)
async def search_documents(request: QueryRequest):
    """Busca documentos basado en una consulta"""
    global pdf_service
    
    if pdf_service is None:
        raise HTTPException(
            status_code=503, 
            detail="Servicio de documentos PDF no disponible. Usa /chat para consultas generales."
        )
    
    try:
        results = pdf_service.search_documents(
            query=request.query,
            pdf_names=request.pdf_names,
            k=request.max_results
        )
        
        return QueryResponse(
            results=results,
            total_results=len(results),
            query=request.query
        )
        
    except Exception as e:
        logger.error(f"Error en búsqueda: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing search: {str(e)}"
        )

@app.get("/info")
async def get_info():
    """Obtiene información sobre el sistema"""
    global pdf_service
    
    if pdf_service is None:
        return {
            "pdf_service": "No disponible",
            "ai_local": "✅ Disponible",
            "message": "Sistema funcionando con IA local - Consultas ilimitadas disponibles"
        }
    
    return pdf_service.get_vectorstore_info()

# Endpoint adicional para testing
@app.post("/test-intent")
async def test_intent(message: str):
    """Endpoint para probar detección de intenciones"""
    intent, score = find_best_intent(message)
    response, confidence = generate_smart_response(intent, score, message)
    
    return {
        "message": message,
        "detected_intent": intent,
        "intent_score": score,
        "response_confidence": confidence,
        "response_preview": response[:100] + "..." if len(response) > 100 else response
    }

# Manejo de errores global
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Manejador global de errores mejorado"""
    logger.error(f"Error no manejado: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Error interno del sistema",
            "message": "El sistema sigue funcionando. Intenta reformular tu consulta sobre comercio exterior.",
            "support": "Sistema gratuito sin límites - errores ocasionales son normales"
        }
    )

if __name__ == "__main__":
    import uvicorn
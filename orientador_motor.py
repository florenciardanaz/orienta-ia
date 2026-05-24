"""
===============================================================================
  ORIENTA-IA — Sistema Experto de Orientación Vocacional
  Basado en el Modelo de Holland (RIASEC) y diccionario propio derivado de O*NET
  adaptado a carreras universitarias de Argentina.

  Universidad de la Ciudad de Buenos Aires
  Análisis de Datos II — Sistemas Expertos y Redes de Conocimiento
  Grupo E — 04 de junio de 2026
===============================================================================

  ARQUITECTURA TEÓRICA DEL SISTEMA EXPERTO
  -----------------------------------------
  Componente              Implementación en este código
  ------------------------------------------------------------------------
  Base de hechos          Decorador @DefFacts (memoria a largo plazo)
   (conocimiento gral.)   + clase PerfilUsuario declarada en runtime
                          (memoria de trabajo / corto plazo).
  Base de reglas          Decoradores @Rule con antecedente (IF) y
                          consecuente (THEN) — reglas de producción.
  Motor de inferencia     KnowledgeEngine de Experta:
                            · Forward Chaining (encadenamiento hacia adelante)
                            · Ciclo Match-Resolve-Act
                            · Modus Ponens como regla lógica base
  Resolución de conflictos  Estrategia por SALIENCE: las reglas más
                          específicas tienen mayor prioridad.
  Sistema de explicaciones  Cada hecho Recomendacion incluye el campo
                          'justificacion' que registra la regla que lo
                          generó y los hechos que la dispararon.
===============================================================================
"""

# --- Fix de compatibilidad: Experta usa collections.Mapping (deprecado en 3.10+) ---
import collections
import collections.abc
if not hasattr(collections, "Mapping"):
    collections.Mapping = collections.abc.Mapping
# ----------------------------------------------------------------------------------

# Importamos los componentes de Experta:
#   KnowledgeEngine → clase base del motor de inferencia
#   Fact            → estructura para representar hechos en la base
#   Rule            → decorador para definir reglas de producción (IF-THEN)
#   MATCH           → operador de variable binding (unificación)
#   DefFacts        → decorador para cargar la base de hechos inicial
#   Field           → tipado de los atributos de un Fact
#   P               → predicado para condiciones numéricas/lambdas (AND/OR/NOT también disponibles)
from experta import KnowledgeEngine, Fact, Rule, MATCH, DefFacts, Field, P
from typing import List, Dict, Tuple


# =============================================================================
# 1. BASE DE CONOCIMIENTO — MEMORIA A LARGO PLAZO
#
#    Esta estructura representa el conocimiento PERMANENTE del sistema:
#    las 50 carreras universitarias argentinas codificadas en RIASEC.
#    Se carga al motor mediante el decorador @DefFacts (ver más abajo),
#    y persiste a través de los engine.reset() entre consultas.
#
#    Cada carrera tiene un código Holland de 3 letras (de mayor a menor
#    afinidad) derivado del cruce O*NET ⇄ oferta universitaria argentina.
# =============================================================================

CARRERAS_AR: List[Dict] = [
    # ---- INVESTIGATIVO + REALISTA (ciencias duras / ingenierías) ----
    {"nombre": "Ingeniería Informática",          "codigo": "IRC", "area": "Ingenierías"},
    {"nombre": "Ingeniería Industrial",           "codigo": "IRE", "area": "Ingenierías"},
    {"nombre": "Ingeniería Civil",                "codigo": "RIE", "area": "Ingenierías"},
    {"nombre": "Ingeniería Mecánica",             "codigo": "RIE", "area": "Ingenierías"},
    {"nombre": "Ingeniería Electrónica",          "codigo": "IRE", "area": "Ingenierías"},
    {"nombre": "Ingeniería Aeronáutica",          "codigo": "IRA", "area": "Ingenierías"},
    {"nombre": "Ingeniería Química",              "codigo": "IRE", "area": "Ingenierías"},
    {"nombre": "Licenciatura en Sistemas",        "codigo": "ICE", "area": "Tecnología"},
    {"nombre": "Ciencia de Datos",                "codigo": "ICA", "area": "Tecnología"},
    {"nombre": "Licenciatura en Física",          "codigo": "IRA", "area": "Ciencias Exactas"},
    {"nombre": "Licenciatura en Matemática",      "codigo": "ICR", "area": "Ciencias Exactas"},
    {"nombre": "Licenciatura en Química",         "codigo": "IRC", "area": "Ciencias Exactas"},
    {"nombre": "Licenciatura en Biología",        "codigo": "IRS", "area": "Ciencias Naturales"},
    {"nombre": "Licenciatura en Astronomía",      "codigo": "IRA", "area": "Ciencias Exactas"},

    # ---- INVESTIGATIVO + SOCIAL (ciencias de la salud / sociales con base científica) ----
    {"nombre": "Medicina",                        "codigo": "ISR", "area": "Salud"},
    {"nombre": "Bioquímica",                      "codigo": "IRS", "area": "Salud"},
    {"nombre": "Farmacia",                        "codigo": "ISC", "area": "Salud"},
    {"nombre": "Odontología",                     "codigo": "ISR", "area": "Salud"},
    {"nombre": "Kinesiología y Fisiatría",        "codigo": "SRI", "area": "Salud"},
    {"nombre": "Nutrición",                       "codigo": "SIE", "area": "Salud"},
    {"nombre": "Veterinaria",                     "codigo": "IRS", "area": "Salud"},
    {"nombre": "Enfermería",                      "codigo": "SIR", "area": "Salud"},
    {"nombre": "Licenciatura en Psicología",      "codigo": "SIA", "area": "Sociales"},
    {"nombre": "Licenciatura en Sociología",      "codigo": "SIA", "area": "Sociales"},
    {"nombre": "Licenciatura en Economía",        "codigo": "IEC", "area": "Económicas"},

    # ---- ARTÍSTICO (artes y comunicación) ----
    {"nombre": "Diseño Gráfico",                  "codigo": "AEI", "area": "Artes y Diseño"},
    {"nombre": "Diseño Industrial",               "codigo": "AIR", "area": "Artes y Diseño"},
    {"nombre": "Diseño de Indumentaria",          "codigo": "AES", "area": "Artes y Diseño"},
    {"nombre": "Arquitectura",                    "codigo": "AIR", "area": "Artes y Diseño"},
    {"nombre": "Licenciatura en Artes Visuales",  "codigo": "ASE", "area": "Artes y Diseño"},
    {"nombre": "Licenciatura en Música",          "codigo": "ASI", "area": "Artes y Diseño"},
    {"nombre": "Licenciatura en Cine y TV",       "codigo": "AES", "area": "Comunicación"},
    {"nombre": "Licenciatura en Comunicación Social", "codigo": "ASE", "area": "Comunicación"},
    {"nombre": "Licenciatura en Letras",          "codigo": "AIS", "area": "Humanidades"},
    {"nombre": "Licenciatura en Periodismo",      "codigo": "ASE", "area": "Comunicación"},
    {"nombre": "Licenciatura en Publicidad",      "codigo": "AES", "area": "Comunicación"},

    # ---- SOCIAL (educación, ayuda, trabajo con personas) ----
    {"nombre": "Licenciatura en Trabajo Social",  "codigo": "SAE", "area": "Sociales"},
    {"nombre": "Profesorado en Enseñanza Primaria","codigo": "SAE", "area": "Educación"},
    {"nombre": "Licenciatura en Ciencias de la Educación", "codigo": "SAI", "area": "Educación"},
    {"nombre": "Licenciatura en Relaciones Internacionales","codigo": "SEA", "area": "Sociales"},
    {"nombre": "Licenciatura en Recursos Humanos","codigo": "SEC", "area": "Económicas"},

    # ---- EMPRENDEDOR (negocios, derecho, gestión) ----
    {"nombre": "Licenciatura en Administración",  "codigo": "ECS", "area": "Económicas"},
    {"nombre": "Contador Público",                "codigo": "CES", "area": "Económicas"},
    {"nombre": "Abogacía",                        "codigo": "ESA", "area": "Derecho"},
    {"nombre": "Licenciatura en Marketing",       "codigo": "EAS", "area": "Económicas"},
    {"nombre": "Licenciatura en Comercio Internacional","codigo": "ECS", "area": "Económicas"},
    {"nombre": "Licenciatura en Ciencias Políticas","codigo": "ESA", "area": "Sociales"},
    {"nombre": "Licenciatura en Turismo y Hotelería","codigo": "SEC", "area": "Servicios"},

    # ---- CONVENCIONAL (organización, datos, procesos) ----
    {"nombre": "Licenciatura en Sistemas de Información", "codigo": "CIE", "area": "Tecnología"},
    {"nombre": "Actuario",                        "codigo": "CIE", "area": "Económicas"},
    {"nombre": "Licenciatura en Logística",       "codigo": "CER", "area": "Económicas"},
    {"nombre": "Licenciatura en Archivología",    "codigo": "CSI", "area": "Humanidades"},
]


# =============================================================================
# 2. BANCO DE 30 PREGUNTAS — 5 por dimensión RIASEC
#    Escala Likert 1 (totalmente en desacuerdo) — 5 (totalmente de acuerdo)
# =============================================================================

PREGUNTAS: List[Tuple[str, str]] = [
    # R — Realista (acción, herramientas, máquinas, naturaleza)
    ("Me gusta trabajar con herramientas, máquinas o equipos técnicos.", "R"),
    ("Disfruto las actividades al aire libre y el trabajo físico.",       "R"),
    ("Me interesa entender cómo funcionan los motores o dispositivos.",   "R"),
    ("Prefiero actividades prácticas antes que tareas teóricas.",         "R"),
    ("Me siento cómodo arreglando cosas con las manos.",                  "R"),

    # I — Investigativo (análisis, ciencia, ideas)
    ("Me apasiona resolver problemas complejos y abstractos.",            "I"),
    ("Disfruto investigar temas científicos en profundidad.",             "I"),
    ("Me gusta analizar datos y encontrar patrones.",                     "I"),
    ("Prefiero entender el “por qué” de las cosas antes que el “cómo”.",  "I"),
    ("Disfruto las matemáticas y el razonamiento lógico.",                "I"),

    # A — Artístico (creatividad, expresión, originalidad)
    ("Me considero una persona creativa y original.",                     "A"),
    ("Disfruto escribir, dibujar, componer o expresarme artísticamente.", "A"),
    ("Me atraen los entornos donde puedo improvisar e innovar.",          "A"),
    ("Valoro la estética y el diseño en lo que me rodea.",                "A"),
    ("Prefiero tareas abiertas sin reglas rígidas.",                      "A"),

    # S — Social (ayudar, enseñar, trabajar con personas)
    ("Disfruto ayudar a otras personas con sus problemas.",               "S"),
    ("Me gusta enseñar o explicar cosas a los demás.",                    "S"),
    ("Prefiero trabajar en equipo antes que de manera individual.",       "S"),
    ("Me importa el bienestar emocional de quienes me rodean.",           "S"),
    ("Me motiva contribuir a causas comunitarias o sociales.",            "S"),

    # E — Emprendedor (liderar, persuadir, vender)
    ("Disfruto liderar grupos y tomar decisiones por el equipo.",         "E"),
    ("Me siento cómodo persuadiendo o negociando con otros.",             "E"),
    ("Me interesa emprender mi propio proyecto o negocio.",               "E"),
    ("Disfruto los entornos competitivos y de alto rendimiento.",         "E"),
    ("Me motivan los resultados económicos y el crecimiento profesional.","E"),

    # C — Convencional (orden, datos, procedimientos)
    ("Disfruto tareas organizadas con reglas y procedimientos claros.",   "C"),
    ("Me gusta llevar registros detallados y mantener todo en orden.",    "C"),
    ("Prefiero trabajar con planillas, formularios o bases de datos.",    "C"),
    ("Me siento cómodo siguiendo instrucciones precisas.",                "C"),
    ("Valoro la previsibilidad y la estabilidad en el trabajo.",          "C"),
]


# =============================================================================
# 3. TIPOS DE HECHOS (FACTS)
#
#    Un "hecho" en un sistema experto es una unidad de información que el
#    motor puede manipular. En Experta se modela heredando de la clase Fact.
#
#    Distinguimos hechos de MEMORIA A LARGO PLAZO (carreras del catálogo,
#    cargadas con @DefFacts) y hechos de MEMORIA DE TRABAJO o CORTO PLAZO
#    (perfil del usuario y resultados de la inferencia, declarados en
#    runtime con engine.declare()).
# =============================================================================

class CarreraCatalogo(Fact):
    """
    Hecho de MEMORIA A LARGO PLAZO.
    Representa una carrera universitaria del catálogo, cargada por @DefFacts.
    Persiste a través de los reset() del motor.

    Atributos:
        nombre  (str): nombre completo de la carrera.
        codigo  (str): código Holland de 3 letras (ej. "SIA").
        area    (str): área disciplinar (Ingenierías, Salud, etc.).
    """
    nombre = Field(str, mandatory=True)
    codigo = Field(str, mandatory=True)
    area   = Field(str, mandatory=True)


class PerfilUsuario(Fact):
    """
    Hecho de MEMORIA DE TRABAJO (corto plazo).
    Vector RIASEC del usuario calculado a partir del test.
    Se declara en cada consulta con engine.declare() y se elimina con reset().
    Es el hecho de entrada que dispara la cadena de inferencia.
    """
    R = Field(int, mandatory=True)
    I = Field(int, mandatory=True)
    A = Field(int, mandatory=True)
    S = Field(int, mandatory=True)
    E = Field(int, mandatory=True)
    C = Field(int, mandatory=True)


class CodigoHolland(Fact):
    """
    Hecho INFERIDO (memoria de trabajo).
    Lo emite la Regla 1 al procesar el PerfilUsuario.
    Su aparición en la base de hechos dispara las reglas siguientes
    (Forward Chaining: el nuevo hecho habilita nuevas reglas).
    """
    letras    = Field(str, mandatory=True)   # ej. "SIA"
    dominante = Field(str, mandatory=True)   # primera letra


class Recomendacion(Fact):
    """
    Hecho INFERIDO (memoria de trabajo) — SALIDA del sistema.
    Cada Recomendacion incluye la regla y los hechos que la justifican,
    cumpliendo con el SISTEMA DE EXPLICACIONES exigido a todo sistema
    experto: el usuario puede ver por qué se le recomendó cada carrera.
    """
    carrera       = Field(str, mandatory=True)
    area          = Field(str, mandatory=True)
    afinidad      = Field(int, mandatory=True)   # 3=alta, 2=media
    justificacion = Field(str, mandatory=True)   # trazabilidad lógica
    regla         = Field(str, mandatory=True)   # qué regla la disparó


# =============================================================================
# 4. MOTOR DE INFERENCIA — REGLAS DE PRODUCCIÓN
#
#    La clase OrientadorVocacional hereda de KnowledgeEngine, que es el
#    motor de inferencia provisto por Experta. Este motor implementa:
#
#      · FORWARD CHAINING (encadenamiento hacia adelante): parte de los
#        hechos iniciales y aplica reglas hasta inferir conclusiones.
#        Es el paradigma adecuado cuando el sistema "recibe datos y
#        produce diagnóstico", como en orientación vocacional.
#        (El opuesto, Backward Chaining, parte de una hipótesis y busca
#        evidencia; sería apropiado en "¿el usuario sirve para X?".)
#
#      · CICLO MATCH-RESOLVE-ACT, repetido hasta no haber más reglas
#        aplicables:
#          1. MATCH  : el motor identifica qué reglas tienen su antecedente
#                      satisfecho por los hechos actuales (agenda de conflictos).
#          2. RESOLVE: elige cuál disparar usando una estrategia de
#                      resolución de conflictos (en este caso, SALIENCE).
#          3. ACT    : ejecuta el consecuente de la regla elegida (declara
#                      nuevos hechos, modifica la base).
#
#      · MODUS PONENS como regla lógica base:
#                      ( P → Q )  ∧  P   ⊢   Q
#        Si la regla dice "SI PerfilUsuario(...) ENTONCES CodigoHolland(...)"
#        y existe el hecho PerfilUsuario, entonces el motor infiere
#        CodigoHolland. Esta es exactamente la mecánica de cada @Rule.
#
#      · ESTRATEGIA DE RESOLUCIÓN DE CONFLICTOS: SALIENCE + especificidad.
#        Cuando hay varias reglas activadas a la vez, el motor dispara
#        primero las de mayor salience. Aquí, la Regla 1 (más general)
#        tiene salience=10 y la Regla 2 (más específica, depende de un
#        hecho derivado) tiene salience=5, garantizando el orden correcto.
# =============================================================================

class OrientadorVocacional(KnowledgeEngine):
    """
    Sistema experto de orientación vocacional.

    Flujo de inferencia (Forward Chaining):
        Hechos iniciales        Regla activada           Hecho inferido
        ────────────────        ─────────────            ──────────────
        PerfilUsuario       →   calcular_codigo_holland  →   CodigoHolland
        CodigoHolland       →   evaluar_carreras         →   Recomendacion[]
                                (recorre catálogo via MATCH)
    """

    # ------------------------------------------------------------------
    # @DefFacts: hechos por defecto cargados al hacer engine.reset().
    # Constituyen la MEMORIA A LARGO PLAZO del sistema: el conocimiento
    # estable que no depende del usuario consultante.
    # ------------------------------------------------------------------
    @DefFacts()
    def cargar_catalogo_carreras(self):
        """
        Genera los hechos del catálogo. El uso de `yield` es el mecanismo
        estándar de Experta para alimentar la base de hechos inicial.
        Cada `yield` declara un hecho CarreraCatalogo en la memoria
        a largo plazo del motor.
        """
        for c in CARRERAS_AR:
            yield CarreraCatalogo(nombre=c["nombre"],
                                  codigo=c["codigo"],
                                  area=c["area"])

    # ------------------------------------------------------------------
    # REGLA 1 — Calcular el código Holland del usuario.
    #
    # Antecedente (IF): existe un PerfilUsuario con scores R, I, A, S, E, C.
    # Consecuente (THEN): se afirma un nuevo hecho CodigoHolland con las
    # tres dimensiones dominantes.
    #
    # Salience alta (10): debe dispararse antes que la Regla 2, porque
    # esta última necesita el hecho CodigoHolland que la Regla 1 produce.
    #
    # Aplicación de MATCH (variable binding): los símbolos MATCH.r,
    # MATCH.i, etc. unifican los valores de los atributos del hecho
    # PerfilUsuario con variables locales que pueden usarse en el
    # consecuente. Es el operador de unificación de Experta.
    # ------------------------------------------------------------------
    @Rule(PerfilUsuario(R=MATCH.r, I=MATCH.i, A=MATCH.a,
                        S=MATCH.s, E=MATCH.e, C=MATCH.c),
          salience=10)
    def calcular_codigo_holland(self, r, i, a, s, e, c):
        """
        Modus Ponens en acción:
          Premisa 1 (regla):    SI hay PerfilUsuario(R,I,A,S,E,C)
                                ENTONCES existe CodigoHolland(3-letras-dominantes)
          Premisa 2 (hecho):    PerfilUsuario(r,i,a,s,e,c) presente.
          Conclusión inferida:  CodigoHolland(letras=top3, dominante=top1)
        """
        scores = {"R": r, "I": i, "A": a, "S": s, "E": e, "C": c}
        # Ordenamos las 6 dimensiones de mayor a menor score
        ranking = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        codigo = "".join([letra for letra, _ in ranking[:3]])
        # ACT: declaramos el nuevo hecho. Este declare es el que
        # gatillará la Regla 2 en el próximo ciclo Match-Resolve-Act.
        self.declare(CodigoHolland(letras=codigo, dominante=codigo[0]))

    # ------------------------------------------------------------------
    # REGLA 2 — Evaluar la afinidad con cada carrera del catálogo.
    #
    # Antecedente (IF): existen DOS hechos simultáneamente:
    #     · un CodigoHolland (producido por la Regla 1), y
    #     · un CarreraCatalogo (cargado por @DefFacts).
    # Este antecedente con dos patrones es una conjunción AND implícita
    # (Experta soporta también OR y NOT como operadores explícitos).
    #
    # Consecuente (THEN): si la afinidad calculada es media o alta,
    # se declara un hecho Recomendacion con su justificación.
    #
    # Salience media (5): se dispara después de la Regla 1.
    #
    # Variable binding con MATCH: el motor recorre AUTOMÁTICAMENTE todas
    # las combinaciones de (CodigoHolland × CarreraCatalogo) que satisfacen
    # el antecedente. Por cada coincidencia disparará la regla una vez.
    # Esto es Forward Chaining trabajando en su forma más pura: el motor
    # itera sobre el producto cartesiano de hechos sin que tengamos que
    # escribir un bucle a mano.
    # ------------------------------------------------------------------
    @Rule(CodigoHolland(letras=MATCH.codigo_usuario,
                        dominante=MATCH.dominante),
          CarreraCatalogo(nombre=MATCH.nombre_carrera,
                          codigo=MATCH.codigo_carrera,
                          area=MATCH.area_carrera),
          salience=5)
    def evaluar_carreras(self, codigo_usuario, dominante,
                         nombre_carrera, codigo_carrera, area_carrera):
        """
        Por cada par (CodigoHolland del usuario, CarreraCatalogo del catálogo)
        que el MATCH unifica, se evalúa la afinidad.

        Cálculo:
          - Coincidencias = letras comunes entre código del usuario
            y código de la carrera.
          - Bonus = +1 si la letra dominante del usuario está en
            el código de la carrera.
          - Si score >= 3 → afinidad ALTA.
          - Si score == 2 → afinidad MEDIA.
          - Si score <= 1 → la carrera se descarta (no se declara
            ningún hecho Recomendacion).

        Esta cuantificación operacionaliza el criterio clínico de
        Holland: dos códigos comparten dominancia vocacional cuando
        coinciden en al menos dos de tres letras.
        """
        coincidencias = len(set(codigo_usuario) & set(codigo_carrera))
        bonus = 1 if dominante in codigo_carrera else 0
        score = coincidencias + bonus

        if score >= 3:
            nivel, etiqueta = 3, "alta"
        elif score == 2:
            nivel, etiqueta = 2, "media"
        else:
            return   # no se dispara la acción → no hay Recomendacion

        # Sistema de Explicaciones: registramos tanto el RAZONAMIENTO
        # (cuántas letras coincidieron y por qué) como la REGLA que lo
        # produjo. Esto permite al usuario auditar cualquier
        # recomendación y entender el "por qué" detrás de ella.
        justificacion = (
            f"Tu código Holland es {codigo_usuario} y el de {nombre_carrera} "
            f"es {codigo_carrera}. Coincidieron {coincidencias} letra(s) "
            f"de las dimensiones dominantes" +
            (f" y tu letra dominante '{dominante}' está presente en la "
             f"carrera (+1)" if bonus else "") +
            f". Score total: {score} → afinidad {etiqueta}."
        )

        self.declare(Recomendacion(
            carrera=nombre_carrera,
            area=area_carrera,
            afinidad=nivel,
            justificacion=justificacion,
            regla="evaluar_carreras"
        ))


# =============================================================================
# 5. FUNCIONES DE INTERFAZ — Para el front-end Streamlit
#
#    El ciclo de uso del motor sigue el patrón estándar de Experta:
#        engine = OrientadorVocacional()  # instanciar
#        engine.reset()                   # cargar @DefFacts (memoria larga)
#        engine.declare(PerfilUsuario(…)) # cargar hecho de entrada (memoria corta)
#        engine.run()                     # disparar Match-Resolve-Act hasta agotar
#    Después leemos los hechos producidos de engine.facts.
# =============================================================================

def calcular_scores_riasec(respuestas: List[int]) -> Dict[str, int]:
    """
    Suma las respuestas Likert por dimensión.
    `respuestas` debe tener 30 elementos en el orden de la lista PREGUNTAS.
    Retorna {'R': int, 'I': int, ...} con valores entre 5 y 25.
    """
    if len(respuestas) != 30:
        raise ValueError("Se esperan exactamente 30 respuestas.")

    scores = {"R": 0, "I": 0, "A": 0, "S": 0, "E": 0, "C": 0}
    for i, (_, dimension) in enumerate(PREGUNTAS):
        scores[dimension] += respuestas[i]
    return scores


def ejecutar_motor(scores: Dict[str, int]) -> Tuple[str, List[Dict]]:
    """
    Ejecuta el motor de inferencia con los scores del usuario.

    Implementa el ciclo estándar reset → declare → run:
      1. reset()   carga la memoria a largo plazo (catálogo via @DefFacts)
      2. declare() inyecta el hecho de entrada (memoria de trabajo)
      3. run()     dispara el ciclo Match-Resolve-Act hasta el punto fijo

    Retorna (codigo_holland, lista_recomendaciones).
    """
    motor = OrientadorVocacional()
    motor.reset()                            # ← carga @DefFacts
    motor.declare(PerfilUsuario(**scores))   # ← hecho de entrada
    motor.run()                              # ← Forward Chaining completo

    # Recolectamos los hechos producidos por la inferencia (sistema
    # de explicaciones: cada hecho conserva la regla que lo generó).
    codigo = None
    recomendaciones = []
    for fact in motor.facts.values():
        if isinstance(fact, CodigoHolland):
            codigo = fact["letras"]
        elif isinstance(fact, Recomendacion):
            recomendaciones.append({
                "carrera":       fact["carrera"],
                "area":          fact["area"],
                "afinidad":      fact["afinidad"],
                "justificacion": fact["justificacion"],
                "regla":         fact["regla"],
            })

    # Ordenamos por afinidad descendente para mostrar primero
    # las recomendaciones más fuertes.
    recomendaciones.sort(key=lambda x: x["afinidad"], reverse=True)
    return codigo, recomendaciones


# =============================================================================
# 6. MODO DE PRUEBA POR CONSOLA (opcional, para debugging)
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  ORIENTA-IA — Modo de prueba por consola")
    print("=" * 60)

    # Ejemplo: perfil mayoritariamente Social-Investigador-Artístico
    ejemplo = {"R": 12, "I": 22, "A": 20, "S": 24, "E": 14, "C": 13}
    print(f"\nScores de prueba: {ejemplo}")

    codigo, recos = ejecutar_motor(ejemplo)
    print(f"\nCódigo Holland inferido: {codigo}")
    print(f"\nSe encontraron {len(recos)} carreras afines:\n")

    for r in recos:
        etiqueta = "★★★ ALTA" if r["afinidad"] == 3 else "★★ MEDIA"
        print(f"  [{etiqueta}] {r['carrera']}  ({r['area']})")
        print(f"           regla: {r['regla']}")
        print(f"           → {r['justificacion']}\n")

"""
===============================================================================
  ORIENTA-IA — Interfaz Streamlit
  Front-end del Sistema Experto de Orientación Vocacional
  Universidad de la Ciudad de Buenos Aires — Análisis de Datos II
  Grupo E — 04 de junio de 2026

  Ejecución local:        streamlit run orientador_app.py
  Ejecución en Colab:     usar ngrok o localtunnel (ver guía adjunta)
===============================================================================
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from orientador_motor import PREGUNTAS, calcular_scores_riasec, ejecutar_motor


# =============================================================================
# Configuración de la página
# =============================================================================

st.set_page_config(
    page_title="ORIENTA-IA — Sistema Experto Vocacional",
    page_icon="🎓",
    layout="wide",
)


# =============================================================================
# Estilos
# =============================================================================

PALETA = {
    "primario":  "#5B2C91",   # violeta UCBA
    "secundario": "#F2A516",
    "fondo_claro": "#F4F1FA",
    "texto":     "#2B2B2B",
}

st.markdown(f"""
    <style>
        .titulo-principal {{
            color: {PALETA['primario']};
            font-size: 2.6rem;
            font-weight: 800;
            margin-bottom: 0;
        }}
        .subtitulo {{
            color: #666;
            font-size: 1.05rem;
            margin-top: 0;
            margin-bottom: 1.5rem;
        }}
        .caja-resultado {{
            background-color: {PALETA['fondo_claro']};
            border-left: 6px solid {PALETA['primario']};
            padding: 1.2rem 1.4rem;
            border-radius: 6px;
            margin: 1rem 0;
        }}
        .carrera-alta {{
            background-color: #E8F5E9;
            border-left: 5px solid #43A047;
            padding: 0.8rem 1rem;
            margin: 0.4rem 0;
            border-radius: 4px;
        }}
        .carrera-media {{
            background-color: #FFF8E1;
            border-left: 5px solid #FFA000;
            padding: 0.8rem 1rem;
            margin: 0.4rem 0;
            border-radius: 4px;
        }}

        /* ------- Forzar fondo blanco para que las cápsulas se vean bien ------- */
        /* Streamlit aplica tema oscuro automáticamente en algunos navegadores,
           lo cual hace que las cápsulas blancas se "pierdan". Forzamos tema claro
           para todo el contenido principal. */
        .stApp {{
            background: #FFFFFF !important;
        }}
        .stApp, .stApp p, .stApp label, .stApp span, .stApp h1,
        .stApp h2, .stApp h3, .stApp h4, .stApp li {{
            color: #1A1626 !important;
        }}

        /* ------- Botones de respuesta en cápsulas (estilo radio pill) ------- */
        /* Streamlit envuelve cada radio en .stRadio. Aplicamos display horizontal
           con flex-wrap y le damos a cada opción la apariencia de cápsula. */
        div[data-testid="stRadio"] > div {{
            flex-direction: row !important;
            flex-wrap: wrap !important;
            gap: 10px !important;
            background: transparent !important;
        }}
        /* Cápsula por defecto: fondo blanco, borde gris, texto negro */
        div[data-testid="stRadio"] label {{
            background: #FFFFFF !important;
            border: 1px solid #D6D3DC !important;
            border-radius: 100px !important;
            padding: 8px 18px !important;
            margin: 0 !important;
            cursor: pointer !important;
            transition: all 0.18s ease !important;
            font-size: 0.92rem !important;
            color: #1A1626 !important;
        }}
        /* Forzamos color de texto negro en TODOS los elementos internos */
        div[data-testid="stRadio"] label p,
        div[data-testid="stRadio"] label span,
        div[data-testid="stRadio"] label div {{
            color: #1A1626 !important;
            background: transparent !important;
        }}
        /* Hover: solo cambia el borde para feedback sutil */
        div[data-testid="stRadio"] label:hover {{
            border-color: {PALETA['primario']} !important;
        }}
        /* Cápsula SELECCIONADA: fondo negro, texto blanco */
        div[data-testid="stRadio"] label:has(input:checked) {{
            background: #1A1626 !important;
            border-color: #1A1626 !important;
        }}
        div[data-testid="stRadio"] label:has(input:checked) p,
        div[data-testid="stRadio"] label:has(input:checked) span,
        div[data-testid="stRadio"] label:has(input:checked) div {{
            color: #FFFFFF !important;
        }}
        /* Bullet (circulito) de la cápsula seleccionada en blanco */
        div[data-testid="stRadio"] label:has(input:checked) [data-baseweb="radio"] > div:first-child {{
            border-color: #FFFFFF !important;
        }}

        /* Título de cada pregunta */
        div[data-testid="stRadio"] > label {{
            font-weight: 600 !important;
            font-size: 1rem !important;
            margin-bottom: 8px !important;
            color: #1A1626 !important;
            background: transparent !important;
        }}

        /* Espaciado entre preguntas */
        .pregunta-bloque {{
            padding: 18px 0;
            border-bottom: 1px solid #ECE9F0;
        }}
    </style>
""", unsafe_allow_html=True)


# =============================================================================
# Control de navegación entre pantallas
# =============================================================================
# Streamlit usa session_state para mantener variables entre interacciones.
# La variable 'pantalla' nos dice si mostramos la bienvenida o el test.
if "pantalla" not in st.session_state:
    st.session_state.pantalla = "bienvenida"


# =============================================================================
# Encabezado
# =============================================================================

st.markdown('<p class="titulo-principal">🎓 ORIENTA-IA</p>',
            unsafe_allow_html=True)
st.markdown('<p class="subtitulo">Sistema Experto de Orientación Vocacional · '
            'Modelo de Holland (RIASEC) · Diccionario propio basado en O*NET '
            'adaptado a Argentina</p>',
            unsafe_allow_html=True)


# =============================================================================
# Sidebar — Información del sistema
# =============================================================================

with st.sidebar:
    st.header("ℹ️ Sobre el sistema")
    st.write("""
    **ORIENTA-IA** es un Sistema Experto Basado en Reglas (RBES) que
    emula el razonamiento de un orientador vocacional profesional.

    **Marco teórico:** Modelo de Holland (RIASEC), referencia mundial
    en orientación vocacional desde 1959.

    **Base de conocimiento:** diccionario propio derivado de O\\*NET
    (Departamento de Trabajo de EE.UU.) y adaptado a la oferta
    universitaria argentina.

    **Tecnología:** Python · Experta (motor de inferencia simbólico)
    · Streamlit · Plotly.
    """)
    st.divider()
    st.caption("Grupo E — Análisis de Datos II")
    st.caption("UCBA · 04 de junio de 2026")


# =============================================================================
# PANTALLA 1 — Bienvenida
# =============================================================================

if st.session_state.pantalla == "bienvenida":

    st.markdown("## Test Vocacional")
    st.caption("Sistema Experto")

    st.markdown(
        "#### Este breve test te ayudará a elegir tu carrera ideal."
    )

    st.divider()

    st.write(
        "Este sistema analiza tus **intereses personales** basándose en el "
        "**Modelo de Holland (RIASEC)**, una referencia mundial en orientación "
        "vocacional, y cruza tu perfil con un diccionario de carreras "
        "universitarias argentinas derivado del estándar internacional **O*NET**."
    )

    st.markdown("**Cómo funciona:**")
    st.markdown("""
    1. Respondés un test corto de **30 preguntas** en escala de 1 a 5.
    2. Nuestro algoritmo traza tu **perfil vocacional** y calcula
       matemáticamente el porcentaje de coincidencia con los requisitos
       de cada carrera.
    3. Recibís un **ranking de afinidad** y un análisis visual de tu perfil.
    """)

    st.info("**Privacidad:** tus respuestas viven sólo en esta sesión. "
            "Nada se guarda ni se envía a servidores externos.",
            icon="🔒")

    st.write("")  # un poco de aire vertical

    # Botón para pasar al test
    centro = st.columns([1, 2, 1])[1]
    with centro:
        if st.button("Comenzar →", use_container_width=True, type="primary"):
            st.session_state.pantalla = "test"
            st.rerun()

    # Cortamos la ejecución acá: el resto del archivo no se ejecuta
    # mientras estemos en la pantalla de bienvenida.
    st.stop()


# =============================================================================
# Cuerpo principal — Test de 30 preguntas
# =============================================================================

st.markdown("### 📋 Test vocacional")
st.write("Respondé las siguientes 30 afirmaciones según cuánto te identifican. "
         "El test es anónimo y demora aproximadamente 5 minutos.")

st.info("**Escala:** 1 = Lo detestaría · "
        "2 = No me gustaría · 3 = Me da igual · "
        "4 = Me gustaría · 5 = Me encantaría",
        icon="📊")

# Mapa de valor numérico (1-5) a etiqueta descriptiva (lo que el usuario ve)
OPCIONES_RESPUESTA = {
    1: "1 · Lo detestaría",
    2: "2 · No me gustaría",
    3: "3 · Me da igual",
    4: "4 · Me gustaría",
    5: "5 · Me encantaría",
}
# Lista de etiquetas en orden, para alimentar a st.radio
ETIQUETAS_RESPUESTA = list(OPCIONES_RESPUESTA.values())

# Estado: respuestas. Inicializamos en None para que NINGUNA opción
# venga preseleccionada — el usuario tiene que elegir activamente.
if "respuestas" not in st.session_state:
    st.session_state.respuestas = [None] * 30

# Mostrar preguntas una debajo de la otra, en una sola columna
for idx, (texto, dim) in enumerate(PREGUNTAS):
    # Cada pregunta es un bloque con divisor inferior
    st.markdown('<div class="pregunta-bloque">', unsafe_allow_html=True)

    # Determinamos el índice por defecto:
    #   - None  → ninguna opción marcada (parámetro index=None de st.radio)
    #   - valor → la opción ya elegida
    valor_prev = st.session_state.respuestas[idx]
    if valor_prev is None:
        index_default = None
    else:
        index_default = valor_prev - 1

    seleccion_texto = st.radio(
        f"**{idx + 1}.** {texto}",
        options=ETIQUETAS_RESPUESTA,
        index=index_default,
        key=f"q_{idx}",
        horizontal=False,        # el CSS los acomoda en fila vía flex-wrap
        label_visibility="visible",
    )

    # Guardamos el valor numérico si el usuario eligió algo
    if seleccion_texto is not None:
        st.session_state.respuestas[idx] = int(seleccion_texto.split(" · ")[0])

    st.markdown('</div>', unsafe_allow_html=True)

st.divider()

# =============================================================================
# Botones de acción: Cancelar test + Obtener recomendación
# =============================================================================

# Mostramos lado a lado los dos botones de acción.
# Usamos columnas para que queden bien distribuidos.
col_cancelar, col_ejecutar = st.columns([1, 2])

with col_cancelar:
    if st.button("← Cancelar test",
                 use_container_width=True):
        # Limpiamos las respuestas y volvemos a la pantalla de bienvenida
        st.session_state.respuestas = [None] * 30
        # Borramos también los radios individuales para que aparezcan vacíos
        for i in range(30):
            if f"q_{i}" in st.session_state:
                del st.session_state[f"q_{i}"]
        st.session_state.pantalla = "bienvenida"
        st.rerun()

with col_ejecutar:
    ejecutar = st.button("🔍 Obtener mi recomendación vocacional",
                         use_container_width=True, type="primary")

# Validamos que TODAS las preguntas hayan sido respondidas antes de ejecutar.
# Si falta alguna, mostramos un aviso y NO disparamos el motor.
if ejecutar:
    faltantes = [i + 1 for i, r in enumerate(st.session_state.respuestas)
                 if r is None]
    if faltantes:
        st.warning(
            f"⚠️ Te faltan {len(faltantes)} pregunta(s) por responder: "
            f"{', '.join(str(n) for n in faltantes[:10])}"
            + ("..." if len(faltantes) > 10 else ""),
            icon="📝"
        )
        # Forzamos que no se ejecute el motor
        ejecutar = False


# =============================================================================
# Resultados
# =============================================================================

if ejecutar:
    # Paso 1: calcular vector RIASEC
    scores = calcular_scores_riasec(st.session_state.respuestas)

    # Paso 2: ejecutar motor de inferencia
    codigo, recomendaciones = ejecutar_motor(scores)

    st.success("✅ Inferencia completada.")
    st.markdown("---")

    # ----- Sección 1: Código Holland -----
    st.markdown(f"""
        <div class="caja-resultado">
            <h3 style="margin-top:0; color:{PALETA['primario']};">
                🧬 Tu código Holland: <b>{codigo}</b>
            </h3>
            <p style="margin-bottom:0;">
                Estas son las 3 dimensiones dominantes de tu perfil vocacional,
                ordenadas de mayor a menor afinidad.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # ----- Sección 2: Gráfico radar de los 6 scores -----
    st.markdown("### 📈 Tu perfil RIASEC completo")
    etiquetas_largas = {
        "R": "Realista",
        "I": "Investigador",
        "A": "Artístico",
        "S": "Social",
        "E": "Emprendedor",
        "C": "Convencional",
    }
    fig = go.Figure(data=go.Scatterpolar(
        r=[scores[k] for k in "RIASEC"],
        theta=[etiquetas_largas[k] for k in "RIASEC"],
        fill="toself",
        line=dict(color=PALETA["primario"], width=3),
        fillcolor=f"rgba(91, 44, 145, 0.25)",
        name="Tu perfil",
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 25])),
        showlegend=False,
        height=420,
        margin=dict(l=60, r=60, t=20, b=20),
    )
    st.plotly_chart(fig, use_container_width=True)

    # ----- Sección 3: Tabla de scores numéricos -----
    with st.expander("Ver scores numéricos detallados"):
        df_scores = pd.DataFrame({
            "Dimensión": [etiquetas_largas[k] for k in "RIASEC"],
            "Letra": list("RIASEC"),
            "Score": [scores[k] for k in "RIASEC"],
            "Máximo posible": [25] * 6,
        })
        st.dataframe(df_scores, hide_index=True, use_container_width=True)

    # ----- Sección 4: Recomendaciones -----
    st.markdown("### 🎯 Carreras recomendadas")

    altas = [r for r in recomendaciones if r["afinidad"] == 3]
    medias = [r for r in recomendaciones if r["afinidad"] == 2]

    st.write(f"El sistema encontró **{len(altas)} carreras de afinidad alta** "
             f"y **{len(medias)} de afinidad media** dentro del catálogo.")

    # Agrupar por área
    if altas:
        st.markdown("#### ⭐ Afinidad alta")
        df_altas = pd.DataFrame(altas)
        for area in df_altas["area"].unique():
            with st.expander(f"📁 {area}  ({len(df_altas[df_altas['area']==area])} carreras)"):
                for _, fila in df_altas[df_altas["area"] == area].iterrows():
                    st.markdown(f"""
                        <div class="carrera-alta">
                            <b>{fila['carrera']}</b><br>
                            <small style="color:#666;">{fila['justificacion']}</small>
                        </div>
                    """, unsafe_allow_html=True)

    if medias:
        st.markdown("#### ✨ Afinidad media")
        with st.expander("Ver carreras de afinidad media"):
            df_medias = pd.DataFrame(medias)
            for _, fila in df_medias.iterrows():
                st.markdown(f"""
                    <div class="carrera-media">
                        <b>{fila['carrera']}</b> · <i>{fila['area']}</i><br>
                        <small style="color:#666;">{fila['justificacion']}</small>
                    </div>
                """, unsafe_allow_html=True)

    # ----- Sección 5: Explicabilidad -----
    st.markdown("### 🔎 ¿Cómo razonó el sistema?")
    with st.expander("Ver explicación del proceso de inferencia"):
        st.markdown(f"""
        El motor de inferencia ejecutó el **ciclo Match-Resolve-Act** de
        Experta hasta agotar todas las reglas aplicables (Forward Chaining):

        **Base de hechos inicial (memoria a largo plazo):**
        - 50 hechos `CarreraCatalogo` cargados por el decorador `@DefFacts`
          al ejecutar `engine.reset()`.

        **Hecho de entrada (memoria de trabajo):**
        - `PerfilUsuario(R={scores['R']}, I={scores['I']}, A={scores['A']},
          S={scores['S']}, E={scores['E']}, C={scores['C']})` declarado
          con `engine.declare()`.

        **Regla 1 — `calcular_codigo_holland` (salience=10):**
        Aplicó Modus Ponens sobre el hecho `PerfilUsuario` y dedujo
        un nuevo hecho `CodigoHolland(letras="{codigo}",
        dominante="{codigo[0]}")`.

        **Regla 2 — `evaluar_carreras` (salience=5):**
        Por cada combinación de `CodigoHolland` × `CarreraCatalogo` que
        el motor unificó vía `MATCH`, evaluó la afinidad y emitió un
        hecho `Recomendacion` cuando el score era igual o mayor a 2.
        Se generaron **{len(recomendaciones)} hechos `Recomendacion`**
        en total.

        **Resolución de conflictos:** el motor priorizó la Regla 1 por
        su mayor salience, asegurando que el `CodigoHolland` exista
        antes de que la Regla 2 pueda dispararse.

        **Sistema de Explicaciones:** cada `Recomendacion` conserva la
        regla que la disparó y la justificación lógica completa
        (visible al desplegar cada carrera). Esto garantiza
        **trazabilidad total**, una propiedad que un modelo de
        Machine Learning de caja negra no podría ofrecer.
        """)

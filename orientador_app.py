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
    </style>
""", unsafe_allow_html=True)


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
# Cuerpo principal — Test de 30 preguntas
# =============================================================================

st.markdown("### 📋 Test vocacional")
st.write("Respondé las siguientes 30 afirmaciones según cuánto te identifican. "
         "El test es anónimo y demora aproximadamente 5 minutos.")

st.info("**Escala:** 1 = Totalmente en desacuerdo · "
        "2 = En desacuerdo · 3 = Neutral · "
        "4 = De acuerdo · 5 = Totalmente de acuerdo",
        icon="📊")

# Estado: respuestas
if "respuestas" not in st.session_state:
    st.session_state.respuestas = [3] * 30   # default neutral

# Mostrar preguntas en dos columnas para que no sea un scroll infinito
col_izq, col_der = st.columns(2)

for idx, (texto, dim) in enumerate(PREGUNTAS):
    columna = col_izq if idx % 2 == 0 else col_der
    with columna:
        st.session_state.respuestas[idx] = st.select_slider(
            f"**{idx + 1}.** {texto}",
            options=[1, 2, 3, 4, 5],
            value=st.session_state.respuestas[idx],
            key=f"q_{idx}",
        )

st.divider()

# =============================================================================
# Botón de ejecución
# =============================================================================

centro = st.columns([1, 2, 1])[1]
with centro:
    ejecutar = st.button("🔍 Obtener mi recomendación vocacional",
                         use_container_width=True, type="primary")


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

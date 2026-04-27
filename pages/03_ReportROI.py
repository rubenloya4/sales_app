import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from fpdf import FPDF
import os
from datetime import date

st.set_page_config(page_title="ROI Calculator", layout="wide", page_icon="💰")

st.title("💰 Calculadora ROI - Soluciones PLC")
st.caption("Genera un reporte de retorno de inversion para tu cliente")

# =========================
# FUNCION LIMPIEZA UNICODE
# =========================
def L(texto):
    if not isinstance(texto, str):
        texto = str(texto)
    return texto  # DejaVu soporta todo, no necesitamos limpiar

# =========================
# DATOS DEL CLIENTE
# =========================
st.subheader("🏭 Datos del Cliente")
col1, col2, col3 = st.columns(3)
with col1:
    cliente_nombre    = st.text_input("Nombre de la empresa", placeholder="Herramental Monterrey SA")
    cliente_ciudad    = st.text_input("Ciudad", placeholder="Monterrey, NL")
with col2:
    cliente_industria = st.text_input("Industria", placeholder="Metalmecánica")
    cliente_contacto  = st.text_input("Contacto", placeholder="Ing. García")
with col3:
    fecha_reporte = st.date_input("Fecha del reporte", value=date.today())
    num_turnos    = st.selectbox("Turnos de operación", [1, 2, 3])

st.divider()

# =========================
# TU SOLUCION (INVERSION)
# =========================
st.subheader("🔧 Tu Solución - Inversión Total")
col1, col2 = st.columns(2)

with col1:
    costo_plc          = st.number_input("Costo PLC + componentes (MXN)", min_value=0, value=80000, step=1000)
    costo_ingenieria   = st.number_input("Ingeniería e instalación (MXN)", min_value=0, value=25000, step=1000)
    costo_capacitacion = st.number_input("Capacitación (MXN)", min_value=0, value=8000, step=500)

with col2:
    descripcion_solucion = st.text_area("Descripción de la solución",
        placeholder="PLC Allen Bradley + panel HMI para control de línea de ensamble...",
        height=120)

inversion_total = costo_plc + costo_ingenieria + costo_capacitacion
st.metric("💼 Inversión Total", f"${inversion_total:,.0f} MXN")

st.divider()

# =========================
# SITUACION ACTUAL
# =========================
st.subheader("⚠️ Situación Actual del Cliente - Costos Sin Automatizar")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Reclamos de Calidad**")
    num_reclamos     = st.number_input("Reclamos por año", min_value=0, value=12, step=1)
    costo_reclamo    = st.number_input("Costo promedio por reclamo (MXN)", min_value=0, value=15000, step=500)

    st.markdown("**Daño a Equipos**")
    num_incidentes   = st.number_input("Incidentes de daño a equipo por año", min_value=0, value=3, step=1)
    costo_incidente  = st.number_input("Costo promedio por incidente (MXN)", min_value=0, value=20000, step=1000)

with col2:
    st.markdown("**Paros de Producción**")
    horas_paro_mes   = st.number_input("Horas de paro al mes", min_value=0.0, value=8.0, step=0.5)
    costo_hora_paro  = st.number_input("Costo por hora de paro (MXN)", min_value=0, value=3500, step=500)

    st.markdown("**Mano de Obra Manual**")
    num_operadores   = st.number_input("Operadores que reemplaza la solución", min_value=0, value=2, step=1)
    salario_operador = st.number_input("Salario mensual por operador (MXN)", min_value=0, value=8500, step=500)

st.divider()

# =========================
# CALCULO ROI
# =========================
costo_reclamos_anual   = num_reclamos * costo_reclamo
costo_incidentes_anual = num_incidentes * costo_incidente
costo_paros_anual      = horas_paro_mes * 12 * costo_hora_paro
costo_mano_obra_anual  = num_operadores * salario_operador * 12

ahorro_reclamos   = costo_reclamos_anual   * 0.80
ahorro_paros      = costo_paros_anual      * 0.70
ahorro_incidentes = costo_incidentes_anual * 0.90
ahorro_mano_obra  = costo_mano_obra_anual

ahorro_total_anual = ahorro_reclamos + ahorro_paros + ahorro_incidentes + ahorro_mano_obra

payback_meses = (inversion_total / ahorro_total_anual * 12) if ahorro_total_anual > 0 else 0
roi_1yr = ((ahorro_total_anual - inversion_total) / inversion_total * 100)       if inversion_total > 0 else 0
roi_2yr = (((ahorro_total_anual * 2) - inversion_total) / inversion_total * 100) if inversion_total > 0 else 0
roi_3yr = (((ahorro_total_anual * 3) - inversion_total) / inversion_total * 100) if inversion_total > 0 else 0

# =========================
# RESULTADOS
# =========================
st.subheader("📊 Resultados del ROI")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Ahorro Anual Total",  f"${ahorro_total_anual:,.0f} MXN")
col2.metric("Payback",             f"{payback_meses:.1f} meses")
col3.metric("ROI a 1 año",         f"{roi_1yr:.0f}%")
col4.metric("ROI a 3 años",        f"{roi_3yr:.0f}%")

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Desglose de Ahorros Anuales**")
    desglose = pd.DataFrame({
        "Categoría": ["Mano de obra", "Reclamos de calidad", "Paros de producción", "Daño a equipos"],
        "Ahorro (MXN)": [ahorro_mano_obra, ahorro_reclamos, ahorro_paros, ahorro_incidentes]
    })
    fig1 = px.bar(desglose, x="Categoría", y="Ahorro (MXN)",
                  color="Categoría", text_auto=True,
                  color_discrete_sequence=["#2ecc71","#3498db","#f39c12","#e74c3c"])
    fig1.update_traces(texttemplate="$%{y:,.0f}", textposition="outside")
    fig1.update_layout(showlegend=False)
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.markdown("**Acumulado: Inversión vs Ahorro a 3 años**")
    anos = [0, 1, 2, 3]
    ahorro_acum  = [0, ahorro_total_anual, ahorro_total_anual*2, ahorro_total_anual*3]
    inversion_ln = [inversion_total]*4

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=anos, y=ahorro_acum, name="Ahorro acumulado",
                              line=dict(color="#2ecc71", width=3),
                              fill="tozeroy", fillcolor="rgba(46,204,113,0.1)"))
    fig2.add_trace(go.Scatter(x=anos, y=inversion_ln, name="Inversión",
                              line=dict(color="#e74c3c", width=2, dash="dash")))
    fig2.update_layout(xaxis_title="Año", yaxis_title="MXN", yaxis_tickformat="$,.0f")
    st.plotly_chart(fig2, use_container_width=True)

st.divider()

st.markdown("**Resumen Financiero**")
resumen = pd.DataFrame({
    "Concepto": [
        "Costo actual - Reclamos de calidad",
        "Costo actual - Daño a equipos",
        "Costo actual - Paros de producción",
        "Costo actual - Mano de obra manual",
        "---------------------",
        "TOTAL COSTOS ACTUALES",
        "---------------------",
        "Ahorro en reclamos (80%)",
        "Ahorro en daño a equipos (90%)",
        "Ahorro en paros (70%)",
        "Ahorro en mano de obra (100%)",
        "---------------------",
        "AHORRO TOTAL ANUAL",
        "INVERSIÓN TOTAL",
        "PAYBACK",
        "ROI AÑO 1",
        "ROI AÑO 2",
        "ROI AÑO 3",
    ],
    "Monto (MXN)": [
        f"${costo_reclamos_anual:,.0f}",
        f"${costo_incidentes_anual:,.0f}",
        f"${costo_paros_anual:,.0f}",
        f"${costo_mano_obra_anual:,.0f}",
        "",
        f"${costo_reclamos_anual+costo_incidentes_anual+costo_paros_anual+costo_mano_obra_anual:,.0f}",
        "",
        f"${ahorro_reclamos:,.0f}",
        f"${ahorro_incidentes:,.0f}",
        f"${ahorro_paros:,.0f}",
        f"${ahorro_mano_obra:,.0f}",
        "",
        f"${ahorro_total_anual:,.0f}",
        f"${inversion_total:,.0f}",
        f"{payback_meses:.1f} meses",
        f"{roi_1yr:.0f}%",
        f"{roi_2yr:.0f}%",
        f"{roi_3yr:.0f}%",
    ]
})
st.dataframe(resumen, use_container_width=True, hide_index=True)

st.divider()

# =========================
# GENERADOR DE PDF
# =========================
st.subheader("📄 Generar Reporte PDF")

col1, col2 = st.columns(2)
with col1:
    empresa_nombre = st.text_input("Tu empresa (para el PDF)", value="Keyence de Mexico SA de CV")
    empresa_email  = st.text_input("Tu email de contacto", value="ventas@keyence.com.mx")
with col2:
    empresa_tel  = st.text_input("Tu teléfono", value="+52 81 0000 0000")

if st.button("📥 Generar y Descargar PDF", type="primary"):
    if not cliente_nombre:
        st.warning("Escribe el nombre del cliente antes de generar el PDF.")
    else:
        # Logo fijo desde carpeta del proyecto
        logo_path = "logo.png" if os.path.exists("logo.png") else None

        DEJAVU      = "DejaVu Sans Book.ttf"
        DEJAVU_BOLD = "DejaVu Sans Bold.ttf"

        class PDF(FPDF):
            def header(self):
                if logo_path:
                    self.image(logo_path, x=10, y=6, w=30, h=14)
                self.set_font("DejaVu", "B", 14)
                self.set_text_color(30, 30, 30)
                self.cell(0, 10, empresa_nombre, align="R", new_x="LMARGIN", new_y="NEXT")
                self.set_font("DejaVu", "", 9)
                self.set_text_color(100, 100, 100)
                self.cell(0, 5, f"{empresa_email}  |  {empresa_tel}", align="R", new_x="LMARGIN", new_y="NEXT")
                self.ln(4)
                self.set_draw_color(46, 204, 113)
                self.set_line_width(0.8)
                self.line(10, self.get_y(), 200, self.get_y())
                self.ln(4)

            def footer(self):
                self.set_y(-15)
                self.set_font("DejaVu", "", 8)
                self.set_text_color(150, 150, 150)
                self.cell(0, 10, f"Página {self.page_no()} — Reporte confidencial generado el {fecha_reporte}", align="C")

        def section_title(pdf, title):
            pdf.set_fill_color(46, 204, 113)
            pdf.set_text_color(255, 255, 255)
            pdf.set_font("DejaVu", "B", 11)
            pdf.cell(0, 8, f"  {title}", fill=True, new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)
            pdf.set_text_color(30, 30, 30)

        def row_data(pdf, label, value, highlight=False):
            if highlight:
                pdf.set_fill_color(240, 255, 245)
                pdf.set_font("DejaVu", "B", 10)
            else:
                pdf.set_fill_color(255, 255, 255)
                pdf.set_font("DejaVu", "", 10)
            pdf.cell(130, 7, f"  {label}", fill=highlight, border="B")
            pdf.set_font("DejaVu", "B" if highlight else "", 10)
            pdf.cell(0, 7, value, fill=highlight, border="B", align="R", new_x="LMARGIN", new_y="NEXT")

        pdf = PDF()
        pdf.add_font("DejaVu", "",  DEJAVU)
        pdf.add_font("DejaVu", "B", DEJAVU_BOLD)
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=20)

        # Título
        pdf.set_font("DejaVu", "B", 20)
        pdf.set_text_color(30, 30, 30)
        pdf.cell(0, 12, "Reporte de Retorno de Inversión", new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.set_font("DejaVu", "", 11)
        pdf.set_text_color(80, 80, 80)
        pdf.cell(0, 7, f"Preparado para: {cliente_nombre}", new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.cell(0, 7, f"{cliente_industria} — {cliente_ciudad}", new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.ln(6)

        # Sección 1
        section_title(pdf, "1. Solución Propuesta")
        pdf.set_font("DejaVu", "", 10)
        pdf.set_text_color(60, 60, 60)
        pdf.multi_cell(0, 6, descripcion_solucion or "Solución de automatización con PLC.", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)
        row_data(pdf, "Costo PLC + componentes",  f"${costo_plc:,.0f} MXN")
        row_data(pdf, "Ingeniería e instalación",  f"${costo_ingenieria:,.0f} MXN")
        row_data(pdf, "Capacitación",              f"${costo_capacitacion:,.0f} MXN")
        row_data(pdf, "INVERSIÓN TOTAL",           f"${inversion_total:,.0f} MXN", highlight=True)
        pdf.ln(5)

        # Sección 2
        section_title(pdf, "2. Costos Actuales Sin Automatizar")
        row_data(pdf, f"Reclamos de calidad ({num_reclamos}/año × ${costo_reclamo:,.0f})",         f"${costo_reclamos_anual:,.0f} MXN")
        row_data(pdf, f"Daño a equipos ({num_incidentes}/año × ${costo_incidente:,.0f})",           f"${costo_incidentes_anual:,.0f} MXN")
        row_data(pdf, f"Paros de producción ({horas_paro_mes}h/mes × ${costo_hora_paro:,.0f}/h)",  f"${costo_paros_anual:,.0f} MXN")
        row_data(pdf, f"Mano de obra ({num_operadores} op. × ${salario_operador:,.0f}/mes)",        f"${costo_mano_obra_anual:,.0f} MXN")
        row_data(pdf, "TOTAL COSTOS ANUALES",
                 f"${costo_reclamos_anual+costo_incidentes_anual+costo_paros_anual+costo_mano_obra_anual:,.0f} MXN",
                 highlight=True)
        pdf.ln(5)

        # Sección 3
        section_title(pdf, "3. Ahorros Proyectados con la Solución")
        row_data(pdf, "Reducción de reclamos (80%)",       f"${ahorro_reclamos:,.0f} MXN/año")
        row_data(pdf, "Reducción de daño a equipos (90%)", f"${ahorro_incidentes:,.0f} MXN/año")
        row_data(pdf, "Reducción de paros (70%)",          f"${ahorro_paros:,.0f} MXN/año")
        row_data(pdf, "Ahorro en mano de obra (100%)",     f"${ahorro_mano_obra:,.0f} MXN/año")
        row_data(pdf, "AHORRO TOTAL ANUAL",                f"${ahorro_total_anual:,.0f} MXN", highlight=True)
        pdf.ln(5)

        # Sección 4
        section_title(pdf, "4. Retorno de Inversión")
        row_data(pdf, "Período de recuperación (Payback)", f"{payback_meses:.1f} meses")
        row_data(pdf, "ROI al año 1",                      f"{roi_1yr:.0f}%")
        row_data(pdf, "ROI al año 2",                      f"{roi_2yr:.0f}%")
        row_data(pdf, "ROI al año 3",                      f"{roi_3yr:.0f}%", highlight=True)
        pdf.ln(5)

        # Sección 5
        section_title(pdf, "5. Conclusión")
        pdf.set_font("DejaVu", "", 10)
        pdf.set_text_color(60, 60, 60)
        conclusion = (
            f"La implementación de la solución propuesta para {cliente_nombre} representa una inversión "
            f"de ${inversion_total:,.0f} MXN con un período de recuperación estimado de {payback_meses:.1f} meses. "
            f"A partir del mes {int(payback_meses)+1}, la solución genera un ahorro neto de "
            f"${ahorro_total_anual:,.0f} MXN anuales, representando un ROI de {roi_3yr:.0f}% al tercer año."
        )
        pdf.multi_cell(0, 6, conclusion)

        # Guardar y descargar
        pdf_path = f"ROI_{cliente_nombre.replace(' ','_')}.pdf"
        pdf.output(pdf_path)

        with open(pdf_path, "rb") as f:
            st.download_button(
                label="⬇️ Descargar PDF",
                data=f,
                file_name=pdf_path,
                mime="application/pdf"
            )

        os.remove(pdf_path)
        st.success("✅ PDF generado correctamente")
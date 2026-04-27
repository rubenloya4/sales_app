import streamlit as st
import pandas as pd
import plotly.express as px

# =========================
# CARGA Y LIMPIEZA
# =========================
@st.cache_data
def load_data(file):
    df = pd.read_excel(file, engine="openpyxl", header=23)
    df.columns = df.columns.astype(str).str.strip()
    df = df.dropna(how="all")
    df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
    # Solo filas con datos de vendedor
    df = df[df["Member"].notna()]
    df = df[df["ID"].notna()]
    return df

# =========================
# APP CONFIG
# =========================
st.set_page_config(page_title="Sales Ranking", layout="wide", page_icon="📊")

# Columnas clave
nombre        = "Member"
oficina_col   = "Office"
score         = "Final Result"
rank_col      = "Rank"
achievement   = "Achievement"
growth_col    = "Growth Last Q Year%"
ph_col        = "PH Effect"
title_col     = "Title"
ind_total     = "Individual Total"

# =========================
# PESTAÑAS
# =========================
tab1, tab2 = st.tabs(["📊 Ranking General", "🏢 Performance por Oficina"])

file = st.sidebar.file_uploader("📂 Carga archivo de ventas", type=["xlsx", "xlsm"])

if file:
    df = load_data(file)

    # Filtro de oficina (sidebar)
    st.sidebar.header("Filtros")
    oficina = st.sidebar.selectbox(
        "Oficina",
        ["Todas"] + sorted(df[oficina_col].dropna().unique().tolist())
    )
    df_filtrado = df if oficina == "Todas" else df[df[oficina_col] == oficina]

    # ==============================
    # PESTAÑA 1 — RANKING GENERAL
    # ==============================
    with tab1:
        st.title("🏆 Sales Ranking Dashboard")

        # KPIs principales
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Vendedores", int(df_filtrado[nombre].nunique()))
        col2.metric("Avg Final Result", f"{df_filtrado[score].mean():.3f}")
        col3.metric("Top Score", f"{df_filtrado[score].max():.3f}")
        col4.metric("Total PH Effect", f"${df_filtrado[ph_col].sum():,.0f}")

        st.divider()

        # KPIs operativos
        st.subheader("📈 Métricas Operativas")
        c1, c2, c3 = st.columns(3)
        c1.metric("Avg Achievement", f"{df_filtrado[achievement].mean():.2%}")
        c2.metric("Avg Growth YoY", f"{df_filtrado[growth_col].mean():.2%}")
        c3.metric("Avg Individual Total", f"{df_filtrado[ind_total].mean():.3f}")

        st.divider()

        # Semáforo
        def nivel(x):
            if x >= 1:      return "🟢 Top"
            elif x >= 0.9:  return "🟡 Medio"
            else:           return "🔴 Bajo"

        df_filtrado = df_filtrado.copy()
        df_filtrado["Nivel"] = df_filtrado[score].apply(nivel)

        # Ranking bar chart
        st.subheader("🏅 Ranking de Vendedores")
        ranking = df_filtrado.sort_values(by=score, ascending=False)

        fig = px.bar(
            ranking,
            x=nombre, y=score,
            color="Nivel",
            color_discrete_map={"🟢 Top": "#2ecc71", "🟡 Medio": "#f39c12", "🔴 Bajo": "#e74c3c"},
            text=rank_col,
            title="Final Result por Vendedor"
        )
        fig.update_traces(textposition="outside")
        fig.add_hline(y=1.0, line_dash="dash", line_color="green", annotation_text="Meta")
        fig.add_hline(y=0.9, line_dash="dash", line_color="orange", annotation_text="Mínimo")
        st.plotly_chart(fig, use_container_width=True)

        # Top 5 y Bottom 5
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🥇 Top 5")
            top5 = ranking[[rank_col, nombre, oficina_col, score]].head(5).reset_index(drop=True)
            st.dataframe(top5, use_container_width=True, hide_index=True)
        with col2:
            st.subheader("📉 Bottom 5")
            bot5 = ranking[[rank_col, nombre, oficina_col, score]].tail(5).reset_index(drop=True)
            st.dataframe(bot5, use_container_width=True, hide_index=True)

        st.divider()

        # Distribución semáforo
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🚦 Distribución del equipo")
            dist = df_filtrado["Nivel"].value_counts().reset_index()
            dist.columns = ["Nivel", "Cantidad"]
            fig2 = px.pie(dist, names="Nivel", values="Cantidad",
                          color="Nivel",
                          color_discrete_map={"🟢 Top": "#2ecc71", "🟡 Medio": "#f39c12", "🔴 Bajo": "#e74c3c"})
            st.plotly_chart(fig2, use_container_width=True)

        with col2:
            st.subheader("🎯 Achievement vs Final Result")
            fig3 = px.scatter(
                df_filtrado, x=achievement, y=score,
                color="Nivel", hover_data=[nombre, oficina_col],
                color_discrete_map={"🟢 Top": "#2ecc71", "🟡 Medio": "#f39c12", "🔴 Bajo": "#e74c3c"}
            )
            fig3.add_hline(y=1.0, line_dash="dash", line_color="green")
            st.plotly_chart(fig3, use_container_width=True)

        # Tabla completa
        st.subheader("📋 Tabla Completa")
        st.dataframe(ranking.reset_index(drop=True), use_container_width=True, hide_index=True)

    # ==============================
    # PESTAÑA 2 — POR OFICINA
    # ==============================
    with tab2:
        st.title("🏢 Performance por Oficina")

        # Resumen por oficina
        office_df = df.groupby(oficina_col).agg(
            Vendedores=(nombre, "count"),
            Avg_Score=(score, "mean"),
            Max_Score=(score, "max"),
            Avg_Achievement=(achievement, "mean"),
            Avg_Growth=(growth_col, "mean"),
            Total_PH=(ph_col, "sum")
        ).reset_index()

        # KPIs de oficina
        st.subheader("📊 Resumen por Oficina")
        st.dataframe(
            office_df.style.format({
                "Avg_Score": "{:.3f}",
                "Max_Score": "{:.3f}",
                "Avg_Achievement": "{:.2%}",
                "Avg_Growth": "{:.2%}",
                "Total_PH": "${:,.0f}"
            }),
            use_container_width=True, hide_index=True
        )

        # Gráficas comparativas
        col1, col2 = st.columns(2)
        with col1:
            fig4 = px.bar(office_df, x=oficina_col, y="Avg_Score",
                          title="Avg Final Result por Oficina",
                          color="Avg_Score", color_continuous_scale="RdYlGn")
            fig4.add_hline(y=1.0, line_dash="dash", line_color="green")
            st.plotly_chart(fig4, use_container_width=True)

        with col2:
            fig5 = px.bar(office_df, x=oficina_col, y="Total_PH",
                          title="Total PH Effect por Oficina",
                          color="Total_PH", color_continuous_scale="Blues")
            st.plotly_chart(fig5, use_container_width=True)

        # Achievement por oficina
        fig6 = px.box(df, x=oficina_col, y=achievement,
                      color=oficina_col,
                      title="Distribución de Achievement por Oficina")
        fig6.add_hline(y=1.0, line_dash="dash", line_color="green", annotation_text="Meta")
        st.plotly_chart(fig6, use_container_width=True)

        # Vendedores de la oficina seleccionada
        st.subheader("👥 Detalle por Vendedor")
        oficina_detalle = st.selectbox("Selecciona oficina para ver detalle",
                                        sorted(df[oficina_col].dropna().unique()))
        detalle = df[df[oficina_col] == oficina_detalle].sort_values(by=score, ascending=False)
        st.dataframe(detalle[[rank_col, nombre, title_col, achievement, growth_col, ph_col, score]].reset_index(drop=True),
                     use_container_width=True, hide_index=True)

else:
    st.sidebar.info("Sube tu archivo para comenzar")
    st.title("📊 Sales Dashboard")
    st.info("👈 Carga tu archivo Excel desde el panel izquierdo para comenzar")
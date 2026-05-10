import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

@st.cache_data
def load_data(file):

    # === TABLA CRUDA ===
    df_raw = pd.read_excel(file, engine="openpyxl", header=None,
                           sheet_name="CON", skiprows=5, nrows=13)
    df_raw.columns = range(len(df_raw.columns))
    df_raw = df_raw.rename(columns={
        3: "ID", 4: "Title", 5: "Office", 6: "Member",
        7: "Achievement", 8: "Growth_YoY", 9: "PH_Effect",
        10: "Growth_KVB", 11: "Growth_2Y", 12: "KVB_NPC"
    })
    df_raw = df_raw[df_raw["Office"].isin(["BAJ", "MEX", "MTY", "TIJ"])]
    for col in ["Achievement","Growth_YoY","PH_Effect","Growth_KVB","Growth_2Y","KVB_NPC"]:
        df_raw[col] = pd.to_numeric(df_raw[col], errors="coerce")

    # === PROMEDIOS Y STD ===
    df_stats = pd.read_excel(file, engine="openpyxl", header=None,
                             sheet_name="CON", skiprows=20, nrows=4)
    try:
        std_row = df_stats[df_stats[6] == "STD"].iloc[0]
        ave_row = df_stats[df_stats[6] == "AVE"].iloc[0]
        stats = {
            "STD": {"Achievement": std_row[7], "Growth YoY": std_row[8],
                    "PH Effect": std_row[9], "Growth KVB": std_row[10],
                    "Growth 2Y": std_row[11]},
            "AVE": {"Achievement": ave_row[7], "Growth YoY": ave_row[8],
                    "PH Effect": ave_row[9], "Growth KVB": ave_row[10],
                    "Growth 2Y": ave_row[11]},
        }
    except:
        stats = None

    # === TABLA PONDERADA ===
    df_pond = pd.read_excel(file, engine="openpyxl", header=None,
                            sheet_name="CON", skiprows=27, nrows=15)
    df_pond.columns = range(len(df_pond.columns))
    df_pond = df_pond.rename(columns={
        0: "Title", 1: "SrAPSM", 2: "Manager", 3: "Leader",
        4: "ID", 5: "Office", 6: "Member",
        7: "Pond_Achievement", 8: "Pond_Growth_YoY",
        9: "Pond_PH_Effect", 10: "Pond_Growth_KVB",
        11: "Pond_Growth_2Y", 12: "Pond_KVB_NPC",
        13: "Own_Result", 14: "Team_Result",
        15: "Final_Result", 16: "Rank"
    })
    df_pond = df_pond[df_pond["Office"].isin(["BAJ", "MEX", "MTY", "TIJ"])]
    for col in ["Pond_Achievement","Pond_Growth_YoY","Pond_PH_Effect",
                "Pond_Growth_KVB","Pond_Growth_2Y","Pond_KVB_NPC",
                "Own_Result","Team_Result","Final_Result"]:
        df_pond[col] = pd.to_numeric(df_pond[col], errors="coerce")
    df_pond["Rank"] = pd.to_numeric(df_pond["Rank"], errors="coerce")

    return df_raw, df_pond, stats

# =========================
# APP CONFIG
# =========================
st.set_page_config(page_title="Sales Ranking", layout="wide", page_icon="📊")

tab1, tab2, tab3 = st.tabs(["📊 Ranking General", "🏢 Por Oficina", "📋 Tablas de Datos"])

file = st.sidebar.file_uploader("📂 Carga archivo de ventas", type=["xlsx", "xlsm"])

if file:
    st.session_state["archivo"] = file

if "archivo" in st.session_state:
    file = st.session_state["archivo"]
    df_raw, df_pond, stats = load_data(file)

    # Merge
    df = df_pond.merge(df_raw[["ID","Achievement","Growth_YoY","PH_Effect",
                                "Growth_KVB","Growth_2Y","KVB_NPC"]],
                       on="ID", how="left")

    def nivel(x):
        if x >= 1.1:    return "🟢 Top"
        elif x >= 0.9:  return "🟡 Medio"
        else:           return "🔴 Bajo"

    df["Nivel"] = df["Final_Result"].apply(nivel)

    st.sidebar.header("Filtros")
    oficina = st.sidebar.selectbox(
        "Oficina", ["Todas"] + sorted(df["Office"].dropna().unique().tolist())
    )
    df_f = df if oficina == "Todas" else df[df["Office"] == oficina]

    # ==============================
    # PESTAÑA 1 — RANKING GENERAL
    # ==============================
    with tab1:
        st.title("🏆 Sales Ranking Dashboard")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Vendedores",       int(df_f["Member"].nunique()))
        col2.metric("Avg Final Result", f"{df_f['Final_Result'].mean():.3f}")
        col3.metric("Total PH Effect",  f"${df_f['PH_Effect'].sum():,.0f}")
        col4.metric("Avg PH Effect",    f"${df_f['PH_Effect'].mean():,.0f}")

        st.divider()

        st.subheader("📈 Promedio por Métrica")
        m1, m2, m3, m4, m5, m6 = st.columns(6)
        m1.metric("Achievement",   f"{df_f['Achievement'].mean():.1%}")
        m2.metric("Growth YoY",    f"{df_f['Growth_YoY'].mean():.1%}")
        m3.metric("Growth KVB",    f"{df_f['Growth_KVB'].mean():.1%}")
        m4.metric("Growth 2Y",     f"{df_f['Growth_2Y'].mean():.1%}")
        m5.metric("KVB NPC",       f"{df_f['KVB_NPC'].mean():.1f}")
        m6.metric("Avg PH Effect", f"${df_f['PH_Effect'].mean():,.0f}")

        st.divider()

        st.subheader("🏅 Ranking Final por Vendedor")
        ranking = df_f.sort_values(by="Final_Result", ascending=False)

        fig = px.bar(
            ranking, x="Member", y="Final_Result",
            color="Nivel",
            color_discrete_map={
                "🟢 Top":   "#2ecc71",
                "🟡 Medio": "#f39c12",
                "🔴 Bajo":  "#e74c3c"
            },
            text="Final_Result",
            title="Final Result por Vendedor (ponderado)"
        )
        fig.update_traces(texttemplate="%{text:.3f}", textposition="outside")
        fig.add_hline(y=1.0, line_dash="dash", line_color="green", annotation_text="Meta")
        fig.add_hline(y=0.9, line_dash="dash", line_color="orange", annotation_text="Mínimo")
        st.plotly_chart(fig, use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🥇 Top 5")
            top5 = ranking[["Rank","Member","Office","Final_Result"]].head(5).reset_index(drop=True)
            top5["Final_Result"] = top5["Final_Result"].map("{:.3f}".format)
            st.dataframe(top5, use_container_width=True, hide_index=True)
        with col2:
            st.subheader("📉 Bottom 5")
            bot5 = ranking[["Rank","Member","Office","Final_Result"]].tail(5).reset_index(drop=True)
            bot5["Final_Result"] = bot5["Final_Result"].map("{:.3f}".format)
            st.dataframe(bot5, use_container_width=True, hide_index=True)

        st.divider()

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🚦 Distribución del equipo")
            dist = df_f["Nivel"].value_counts().reset_index()
            dist.columns = ["Nivel", "Cantidad"]
            fig2 = px.pie(dist, names="Nivel", values="Cantidad",
                          color="Nivel",
                          color_discrete_map={
                              "🟢 Top":   "#2ecc71",
                              "🟡 Medio": "#f39c12",
                              "🔴 Bajo":  "#e74c3c"
                          })
            st.plotly_chart(fig2, use_container_width=True)

        with col2:
            st.subheader("🎯 Achievement vs PH Effect")
            fig3 = px.scatter(
                df_f, x="Achievement", y="PH_Effect",
                color="Nivel", hover_data=["Member","Office"],
                size="Final_Result",
                color_discrete_map={
                    "🟢 Top":   "#2ecc71",
                    "🟡 Medio": "#f39c12",
                    "🔴 Bajo":  "#e74c3c"
                }
            )
            fig3.add_vline(x=1.0, line_dash="dash", line_color="green")
            fig3.update_xaxes(tickformat=".0%")
            fig3.update_yaxes(tickformat="$,.0f")
            st.plotly_chart(fig3, use_container_width=True)

    # ==============================
    # PESTAÑA 2 — POR OFICINA
    # ==============================
    with tab2:
        st.title("🏢 Performance por Oficina")

        office_df = df.groupby("Office").agg(
            Vendedores      = ("Member",       "count"),
            Avg_Final       = ("Final_Result", "mean"),
            Max_Final       = ("Final_Result", "max"),
            Avg_Achievement = ("Achievement",  "mean"),
            Total_PH        = ("PH_Effect",    "sum"),
            Avg_PH          = ("PH_Effect",    "mean"),
        ).reset_index()

        st.subheader("📊 Resumen por Oficina")
        st.dataframe(
            office_df.style.format({
                "Avg_Final":       "{:.3f}",
                "Max_Final":       "{:.3f}",
                "Avg_Achievement": "{:.1%}",
                "Total_PH":        "${:,.0f}",
                "Avg_PH":          "${:,.0f}",
            }),
            use_container_width=True, hide_index=True
        )

        col1, col2 = st.columns(2)
        with col1:
            fig4 = px.bar(office_df, x="Office", y="Avg_Final",
                          title="Avg Final Result por Oficina",
                          color="Avg_Final", color_continuous_scale="RdYlGn")
            fig4.add_hline(y=1.0, line_dash="dash", line_color="green")
            st.plotly_chart(fig4, use_container_width=True)

        with col2:
            fig5 = px.bar(office_df, x="Office", y="Total_PH",
                          title="Total PH Effect por Oficina",
                          color="Total_PH", color_continuous_scale="Blues")
            fig5.update_yaxes(tickformat="$,.0f")
            st.plotly_chart(fig5, use_container_width=True)

        st.subheader("🕸️ Perfil por Oficina")
        categorias = ["Pond_Achievement","Pond_Growth_YoY","Pond_PH_Effect",
                      "Pond_Growth_KVB","Pond_Growth_2Y","Pond_KVB_NPC"]
        labels = ["Achievement","Growth YoY","PH Effect",
                  "Growth KVB","Growth 2Y","KVB NPC"]

        fig_radar = go.Figure()
        for off in df["Office"].unique():
            vals = df[df["Office"] == off][categorias].mean().tolist()
            vals += [vals[0]]
            fig_radar.add_trace(go.Scatterpolar(
                r=vals, theta=labels + [labels[0]],
                fill="toself", name=off
            ))
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 1.5])),
            title="Perfil ponderado por Oficina"
        )
        st.plotly_chart(fig_radar, use_container_width=True)

        st.subheader("👥 Detalle por Vendedor")
        oficina_det = st.selectbox("Selecciona oficina",
                                    sorted(df["Office"].dropna().unique()))
        det = df[df["Office"] == oficina_det].sort_values("Final_Result", ascending=False)
        det_show = det[["Rank","Member","Achievement","Growth_YoY",
                         "PH_Effect","Growth_KVB","Final_Result"]].reset_index(drop=True)
        det_show["Achievement"]  = det_show["Achievement"].map("{:.1%}".format)
        det_show["Growth_YoY"]   = det_show["Growth_YoY"].map("{:.1%}".format)
        det_show["PH_Effect"]    = det_show["PH_Effect"].map("${:,.0f}".format)
        det_show["Growth_KVB"]   = det_show["Growth_KVB"].map("{:.1%}".format)
        det_show["Final_Result"] = det_show["Final_Result"].map("{:.3f}".format)
        st.dataframe(det_show, use_container_width=True, hide_index=True)

    # ==============================
    # PESTAÑA 3 — TABLAS DE DATOS
    # ==============================
    with tab3:
        st.title("📋 Tablas de Datos")

        st.subheader("📊 Datos Crudos")
        raw_show = df_raw[["ID","Member","Office","Achievement","Growth_YoY",
                            "PH_Effect","Growth_KVB","Growth_2Y","KVB_NPC"]].copy()
        raw_show["Achievement"] = raw_show["Achievement"].map("{:.1%}".format)
        raw_show["Growth_YoY"]  = raw_show["Growth_YoY"].map("{:.1%}".format)
        raw_show["PH_Effect"]   = raw_show["PH_Effect"].map("${:,.0f}".format)
        raw_show["Growth_KVB"]  = raw_show["Growth_KVB"].map("{:.1%}".format)
        raw_show["Growth_2Y"]   = raw_show["Growth_2Y"].map("{:.1%}".format)
        st.dataframe(raw_show, use_container_width=True, hide_index=True)

        st.divider()

        st.subheader("⚖️ Datos Ponderados")
        pond_show = df_pond[["Rank","Title","Member","Office",
                              "Pond_Achievement","Pond_Growth_YoY","Pond_PH_Effect",
                              "Pond_Growth_KVB","Pond_Growth_2Y","Pond_KVB_NPC",
                              "Own_Result","Team_Result","Final_Result"]].copy()
        for col in ["Pond_Achievement","Pond_Growth_YoY","Pond_PH_Effect",
                    "Pond_Growth_KVB","Pond_Growth_2Y","Pond_KVB_NPC",
                    "Own_Result","Team_Result","Final_Result"]:
            pond_show[col] = pond_show[col].map("{:.3f}".format)
        st.dataframe(pond_show, use_container_width=True, hide_index=True)

        if stats:
            st.divider()
            st.subheader("📈 Estadísticas del Equipo")
            stats_df = pd.DataFrame(stats).T.reset_index()
            stats_df.columns = ["Métrica","Achievement","Growth YoY",
                                 "PH Effect","Growth KVB","Growth 2Y"]
            st.dataframe(
                stats_df.style.format({
                    "Achievement": "{:.1%}",
                    "Growth YoY":  "{:.1%}",
                    "PH Effect":   "${:,.0f}",
                    "Growth KVB":  "{:.1%}",
                    "Growth 2Y":   "{:.1%}",
                }),
                use_container_width=True, hide_index=True
            )

else:
    st.sidebar.info("Sube tu archivo para comenzar")
    st.title("📊 Sales Ranking Dashboard")
    st.info("👈 Carga tu archivo Excel desde el panel izquierdo para comenzar")
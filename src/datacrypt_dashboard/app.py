import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go

# Configuração Global
st.set_page_config(layout="wide", page_title="DataCrypt Dashboard")

# --- CUSTOM CSS ---
def local_css():
    st.markdown("""
    <style>
    /* Estilo dos Cards de Métricas */
    div[data-testid="stMetric"] {
        background-color: #1E293B;
        border: 1px solid #334155;
        padding: 1.2rem 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12);
    }
    
    /* Remove espaço vazio no topo (header padrão do Streamlit) e ajusta margens da página */
    header {visibility: hidden; height: 0px !important; padding: 0px !important;}
    .block-container {
        padding-top: 1rem !important; 
        padding-bottom: 1rem !important;
        margin-top: -2rem !important;
    }
    
    /* Força o menu lateral (sidebar) a ser mais estreito */
    [data-testid="stSidebar"] {
        min-width: 240px !important;
        max-width: 240px !important;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    h1 {font-weight: 600; font-size: 2rem; color: #F8FAFC; margin-bottom: -10px; margin-top: 0px;}
    h2, h3 {font-weight: 500; color: #E2E8F0; font-size: 1.2rem;}
    hr {margin-top: 1.5em; margin-bottom: 1.5em; border: 0; border-top: 1px solid #334155;}
    </style>
    """, unsafe_allow_html=True)

local_css()

API_BASE_URL = "http://localhost:8000/api/v1"

@st.cache_data(ttl=3600)
def _fetch_data_cached(endpoint: str, params: dict = None):
    url = f"{API_BASE_URL}{endpoint}"
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    return response.json().get("data", [])

def fetch_data(endpoint: str, params: dict = None):
    try:
        return _fetch_data_cached(endpoint, params)
    except requests.exceptions.RequestException as e:
        st.warning(f"Não foi possível obter dados (Endpoint: {endpoint})")
        return None

def apply_chart_theme(fig):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#94A3B8", size=10),
        margin=dict(l=10, r=10, t=30, b=10),
        xaxis=dict(showgrid=True, gridcolor="#334155", zeroline=False),
        yaxis=dict(showgrid=True, gridcolor="#334155", zeroline=False),
        legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5, title=None)
    )
    return fig

COLOR_PALETTE = ["#3B82F6", "#10B981", "#8B5CF6", "#F59E0B", "#EF4444", "#06B6D4"]

# ==========================================
# MENU LATERAL
# ==========================================
st.sidebar.title("DataCrypt")
st.sidebar.markdown("<p style='color: #94A3B8; font-size: 0.9em; margin-top: -15px;'>Inteligência Financeira</p>", unsafe_allow_html=True)
st.sidebar.markdown("---")
page = st.sidebar.radio("Navegação", ["Visão Macro Nacional", "Análise de Município", "Rankings Consolidados"])
st.sidebar.markdown("---")

def format_currency(val):
    return f"R$ {val:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")

# ==========================================
# 1. VISÃO MACRO NACIONAL
# ==========================================
def render_macro_view():
    st.title("Visão Macro Nacional")
    
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        ano = st.selectbox("Exercício Financeiro", [2020, 2019])
    with col_f2:
        uf = st.text_input("Filtrar por UF (Ex: SP)", "").strip().upper()
        
    params = {"uf": uf} if uf else {}
    st.markdown("---")
    
    data = fetch_data(f"/siconfi/agregacao/ano/{ano}", params=params)
    if data:
        df = pd.DataFrame(data)
        
        total_rec = df["receita_total"].sum() if "receita_total" in df.columns else 0
        total_des = df["despesa_total"].sum() if "despesa_total" in df.columns else 0
        
        # Linha de métricas
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Receita Total", format_currency(total_rec))
        c2.metric("Despesa Total", format_currency(total_des))
        c3.metric("Balanço Resultante", format_currency(total_rec - total_des))
        c4.metric("Margem", f"{((total_rec - total_des)/total_rec * 100):.1f}%" if total_rec else "0%")
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("Painel Analítico")
        
        # Grid de 3 colunas para gráficos
        g1, g2, g3 = st.columns(3)
        
        with g1:
            if "receita_total" in df.columns and "despesa_total" in df.columns:
                df_melted = df.melt(id_vars=["periodo"], value_vars=["receita_total", "despesa_total"], var_name="Indicador", value_name="Valor")
                df_melted["Indicador"] = df_melted["Indicador"].map({"receita_total": "Receita", "despesa_total": "Despesa"})
                fig1 = px.bar(df_melted, x="periodo", y="Valor", color="Indicador", barmode="group",
                             title="Receita vs Despesa (Bimestre)",
                             color_discrete_sequence=["#10B981", "#EF4444"])
                apply_chart_theme(fig1)
                st.plotly_chart(fig1, use_container_width=True)
                
        with g2:
            cols_despesas = [col for col in ["despesa_saude", "despesa_educacao", "investimentos"] if col in df.columns]
            if cols_despesas:
                df_lines = df.melt(id_vars=["periodo"], value_vars=cols_despesas, var_name="Área", value_name="Valor")
                df_lines["Área"] = df_lines["Área"].str.replace("despesa_", "").str.title()
                fig2 = px.line(df_lines, x="periodo", y="Valor", color="Área", markers=True,
                               title="Despesas Estratégicas",
                               color_discrete_sequence=["#3B82F6", "#8B5CF6", "#F59E0B"])
                apply_chart_theme(fig2)
                st.plotly_chart(fig2, use_container_width=True)
                
        with g3:
            # Gráfico de Rosca com proporção das despesas
            if total_des > 0 and len(cols_despesas) > 0:
                soma_despesas = {col.replace("despesa_", "").title(): df[col].sum() for col in cols_despesas}
                soma_despesas["Outras Despesas"] = total_des - sum(soma_despesas.values())
                df_pie = pd.DataFrame(list(soma_despesas.items()), columns=["Área", "Valor"])
                
                fig3 = px.pie(df_pie, values="Valor", names="Área", hole=0.6,
                              title="Distribuição do Orçamento",
                              color_discrete_sequence=COLOR_PALETTE)
                apply_chart_theme(fig3)
                fig3.update_layout(legend=dict(y=-0.5)) # Adjust pie legend specifically
                st.plotly_chart(fig3, use_container_width=True)
    elif data is not None:
        st.info("Não há dados consolidados disponíveis.")

# ==========================================
# 2. RAIO-X DE MUNICÍPIO
# ==========================================
def render_municipio_view():
    st.title("Análise de Município")
    
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        cod_ibge = st.number_input("Código IBGE", min_value=1000000, max_value=9999999, value=3550308, step=1)
    with col_f2:
        indicador = st.selectbox("Métrica", ["receita_total", "despesa_total", "despesa_saude", "despesa_educacao", "investimentos"])
        
    st.markdown("---")
    data = fetch_data(f"/siconfi/municipio/{cod_ibge}/serie-historica/{indicador}")
    
    if data:
        df = pd.DataFrame(data)
        if "ano" in df.columns and "periodo" in df.columns and "valor" in df.columns:
            df = df.sort_values(by=["ano", "periodo"])
            df["Período"] = df["ano"].astype(str) + " / B" + df["periodo"].astype(str)
            
            st.subheader(f"Evolução: {indicador.replace('_', ' ').title()}")
            g1, g2, g3 = st.columns(3)
            
            with g1:
                # Gráfico de Área
                fig_area = px.area(df, x="Período", y="valor", markers=True, title="Série Contínua",
                              color_discrete_sequence=["#3B82F6"])
                fig_area.update_traces(fillcolor="rgba(59, 130, 246, 0.2)")
                apply_chart_theme(fig_area)
                st.plotly_chart(fig_area, use_container_width=True)
                
            with g2:
                # Gráfico de Barras Separado por Ano
                fig_bar = px.bar(df, x="periodo", y="valor", color="ano", barmode="group",
                                 title="Comparativo Anual por Bimestre",
                                 color_discrete_sequence=["#1E293B", "#3B82F6"])
                apply_chart_theme(fig_bar)
                st.plotly_chart(fig_bar, use_container_width=True)
                
            with g3:
                # Boxplot para mostrar dispersão dos valores
                fig_box = px.box(df, x="ano", y="valor", points="all", title="Dispersão de Valores",
                                 color_discrete_sequence=["#8B5CF6"])
                apply_chart_theme(fig_box)
                st.plotly_chart(fig_box, use_container_width=True)
                
    elif data is not None:
         st.info("Série histórica indisponível.")

# ==========================================
# 3. TOP RANKINGS
# ==========================================
def render_ranking_view():
    st.title("Rankings Consolidados")
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        ano = st.selectbox("Exercício", [2020, 2019])
    with c2:
        indicador = st.selectbox("Métrica Comparativa", ["receita_total", "despesa_total", "despesa_saude", "despesa_educacao", "investimentos"])
    with c3:
        uf = st.text_input("UF (Opc)", "").strip().upper()
    with c4:
        limit = st.number_input("Top N", min_value=5, max_value=50, value=10, step=5)
        
    params = {"limit": limit}
    if uf: params["uf"] = uf
        
    st.markdown("---")
    data = fetch_data(f"/siconfi/ranking/{indicador}/ano/{ano}", params=params)
    
    if data:
        df = pd.DataFrame(data)
        if "cod_ibge" in df.columns and "valor" in df.columns:
            df_sorted = df.sort_values(by="valor", ascending=True)
            if "uf" in df_sorted.columns:
                df_sorted["Município"] = df_sorted["cod_ibge"].astype(str) + " - " + df_sorted["uf"]
            else:
                df_sorted["Município"] = df_sorted["cod_ibge"].astype(str)
                
            st.subheader(f"Dashboard Comparativo (Top {limit})")
            g1, g2, g3 = st.columns(3)
            
            with g1:
                # Ranking Barras Horizontais
                fig_bar = px.bar(df_sorted, x="valor", y="Município", orientation='h',
                             title="Ranking de Volume",
                             color="valor", color_continuous_scale="Blues")
                apply_chart_theme(fig_bar)
                fig_bar.update_layout(coloraxis_showscale=False)
                st.plotly_chart(fig_bar, use_container_width=True)
                
            with g2:
                # Treemap do Peso de Cada um no Top N
                fig_tree = px.treemap(df_sorted, path=["Município"], values="valor",
                                      title="Proporção no Top N",
                                      color="valor", color_continuous_scale="Blues")
                apply_chart_theme(fig_tree)
                fig_tree.update_layout(coloraxis_showscale=False, margin=dict(t=30, l=10, r=10, b=10))
                st.plotly_chart(fig_tree, use_container_width=True)
                
            with g3:
                # Tabela de dados limpa (apenas nome e formatado)
                st.markdown("<p style='font-size: 10px; color: #94A3B8; text-align:center; font-weight: bold;'>Dados Tabulares</p>", unsafe_allow_html=True)
                df_table = df_sorted.sort_values(by="valor", ascending=False)[["Município", "valor"]]
                df_table["Valor (R$)"] = df_table["valor"].apply(lambda x: f"{x:,.2f}".replace(",", "_").replace(".", ",").replace("_", "."))
                st.dataframe(df_table[["Município", "Valor (R$)"]], use_container_width=True, hide_index=True)
                
    elif data is not None:
        st.info("Ranking indisponível.")

if page == "Visão Macro Nacional":
    render_macro_view()
elif page == "Análise de Município":
    render_municipio_view()
elif page == "Rankings Consolidados":
    render_ranking_view()
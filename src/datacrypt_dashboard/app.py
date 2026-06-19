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
    /* Fundo geral da aplicação mais escuro */
    .stApp {
        background-color: #040914 !important;
    }

    /* Estilo dos Cards de Métricas */
    div[data-testid="stMetric"] {
        background-color: #1E293B;
        border: 1px solid #334155;
        padding: 1.2rem 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12);
    }
    
    /* Remove espaço vazio no topo */
    header {visibility: hidden; height: 0px !important; padding: 0px !important;}
    .block-container {
        padding-top: 2rem !important; 
        padding-bottom: 1rem !important;
        margin-top: -1.5rem !important;
    }
    
    /* Oculta completamente o menu lateral (sidebar) */
    [data-testid="collapsedControl"] { display: none !important; }
    section[data-testid="stSidebar"] { display: none !important; width: 0px !important; }
    
    /* Personaliza o st.segmented_control para o menu superior */
    div[data-testid="stSegmentedControl"] {
        background-color: rgba(30, 41, 59, 0.4);
        padding: 6px;
        border-radius: 12px;
        border: 1px solid #334155;
        width: 100%;
    }
    
    /* Aumenta as fontes do menu */
    div[data-testid="stSegmentedControl"] p {
        font-size: 1.1rem !important;
        font-weight: 500 !important;
        padding: 4px 10px !important;
    }

    /* Media query para "Meia Tela" (telas menores que 900px) */
    @media (max-width: 900px) {
        div[data-testid="stHorizontalBlock"] {
            flex-wrap: wrap !important;
        }
        div[data-testid="stHorizontalBlock"] > div {
            min-width: 100% !important;
            width: 100% !important;
            padding-bottom: 1rem;
        }
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

@st.cache_data(ttl=86400)
def get_ibge_mapping():
    try:
        res = requests.get("https://servicodados.ibge.gov.br/api/v1/localidades/municipios", timeout=10)
        if res.status_code == 200:
            return {str(m["id"]): m["nome"] for m in res.json()}
    except Exception:
        pass
    return {}

@st.cache_data(ttl=86400)
def get_ibge_full_mapping():
    try:
        res = requests.get("https://servicodados.ibge.gov.br/api/v1/localidades/municipios", timeout=10)
        if res.status_code == 200:
            def extract_uf(m):
                if m.get("microrregiao"):
                    return m["microrregiao"]["mesorregiao"]["UF"]["sigla"]
                elif m.get("regiao-imediata"):
                    return m["regiao-imediata"]["regiao-intermediaria"]["UF"]["sigla"]
                return "XX"
            
            return [
                {
                    "id": str(m["id"]),
                    "nome": m["nome"],
                    "uf": extract_uf(m)
                }
                for m in res.json()
            ]
    except Exception:
        pass
    return []

def apply_chart_theme(fig, is_currency_y=True, is_currency_x=False):
    layout_update = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#94A3B8", size=10),
        margin=dict(l=10, r=10, t=30, b=10),
        separators=",.",
        legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5, title=None)
    )
    
    xaxis_dict = dict(showgrid=True, gridcolor="#334155", zeroline=False)
    if is_currency_x:
        xaxis_dict.update(tickprefix="R$ ", tickformat=",.2f")
        
    yaxis_dict = dict(showgrid=True, gridcolor="#334155", zeroline=False)
    if is_currency_y:
        yaxis_dict.update(tickprefix="R$ ", tickformat=",.2f")
        
    layout_update["xaxis"] = xaxis_dict
    layout_update["yaxis"] = yaxis_dict
    
    fig.update_layout(**layout_update)
    return fig

COLOR_PALETTE = ["#3B82F6", "#10B981", "#8B5CF6", "#F59E0B", "#EF4444", "#06B6D4"]
AVAILABLE_YEARS = list(range(2025, 2017, -1))

# ==========================================
# CABEÇALHO SUPERIOR (HORIZONTAL)
# ==========================================
header_container = st.container()
with header_container:
    col_logo, col_nav = st.columns([1, 2.5], vertical_alignment="center")

    with col_logo:
        st.markdown(
            "<h1 style='margin: 0px; padding-top: 8px; color: #3B82F6; font-size: 1.8rem; font-weight: 700; letter-spacing: -0.5px; line-height: 1;'>DataCrypt</h1>", 
            unsafe_allow_html=True
        )

    with col_nav:
        page = st.segmented_control(
            "Navegação", 
            ["Macro (Siconfi)", "Município (Siconfi)", "Rankings (Siconfi)", "Macro (Social)", "Município (Social)"], 
            default="Macro (Siconfi)",
            label_visibility="collapsed"
        )

st.markdown("<hr style='margin-top: 1.5rem; margin-bottom: 25px; border-top: 1px solid #1E293B;'>", unsafe_allow_html=True)

if not page:
    page = "Macro (Siconfi)"

def format_currency(val):
    try:
        val = float(val)
    except (ValueError, TypeError):
        return str(val)
    return f"R$ {val:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")

# ==========================================
# 1. VISÃO MACRO NACIONAL
# ==========================================
def render_macro_view():
    st.title("Visão Macro Nacional")
    
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        ano = st.selectbox("Exercício Financeiro", AVAILABLE_YEARS)
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
                apply_chart_theme(fig3, is_currency_y=False)
                fig3.update_traces(hovertemplate="%{label}<br>R$ %{value:,.2f}<br>(%{percent})")
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
            
            ibge_map = get_ibge_mapping()
            nome_mun = ibge_map.get(str(cod_ibge), str(cod_ibge))
            
            st.subheader(f"Evolução: {indicador.replace('_', ' ').title()} - {nome_mun}")
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
        ano = st.selectbox("Exercício", AVAILABLE_YEARS)
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
            
            ibge_map = get_ibge_mapping()
            def map_nome(row):
                cod = str(row["cod_ibge"])
                nome = ibge_map.get(cod, cod)
                return f"{nome} - {row['uf']}" if "uf" in row else nome
                
            df_sorted["Município"] = df_sorted.apply(map_nome, axis=1)
                
            st.subheader(f"Dashboard Comparativo (Top {limit})")
            g1, g2, g3 = st.columns(3)
            
            with g1:
                # Ranking Barras Horizontais
                fig_bar = px.bar(df_sorted, x="valor", y="Município", orientation='h',
                             title="Ranking de Volume",
                             color="valor", color_continuous_scale="Blues")
                apply_chart_theme(fig_bar, is_currency_y=False, is_currency_x=True)
                fig_bar.update_layout(coloraxis_showscale=False)
                st.plotly_chart(fig_bar, use_container_width=True)
                
            with g2:
                # Gráfico de Rosca (Donut) para proporção no Top N
                fig_pie = px.pie(df_sorted, values="valor", names="Município", hole=0.5,
                                 title="Proporção no Top N",
                                 color_discrete_sequence=COLOR_PALETTE)
                apply_chart_theme(fig_pie, is_currency_y=False)
                fig_pie.update_traces(textposition='inside', textinfo='percent', hovertemplate="%{label}<br>R$ %{value:,.2f}<br>(%{percent})")
                fig_pie.update_layout(showlegend=False, margin=dict(t=30, l=10, r=10, b=10))
                st.plotly_chart(fig_pie, use_container_width=True)
                
            with g3:
                # Tabela de dados limpa (apenas nome e formatado)
                st.markdown("<p style='font-size: 10px; color: #94A3B8; text-align:center; font-weight: bold;'>Dados Tabulares</p>", unsafe_allow_html=True)
                df_table = df_sorted.sort_values(by="valor", ascending=False)[["Município", "valor"]]
                df_table["Valor (R$)"] = df_table["valor"].apply(lambda x: f"{x:,.2f}".replace(",", "_").replace(".", ",").replace("_", "."))
                st.dataframe(df_table[["Município", "Valor (R$)"]], use_container_width=True, hide_index=True)
                
    elif data is not None:
        st.info("Ranking indisponível.")

def render_social_macro_view():
    st.title("Agregação e Rankings (Social)")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        ano = st.selectbox("Exercício", AVAILABLE_YEARS, key="soc_ano")
    with c2:
        tipo = st.selectbox("Benefício", ["bolsa_familia", "auxilio_brasil", "novo_bolsa_familia"])
    with c3:
        uf = st.text_input("Filtrar por UF (Opc)", "").strip().upper()
        
    params = {"tipoBeneficio": tipo, "ano": ano}
    if uf: params["uf"] = uf
        
    st.markdown("---")
    
    st.subheader("Visão Consolidada Mensal")
    data_agg = fetch_data("/transparencia/beneficios/analytics/agregacao", params=params)
    
    if data_agg:
        df_agg = pd.DataFrame(data_agg)
        if "valor_total" in df_agg.columns:
            df_agg["valor_total"] = pd.to_numeric(df_agg["valor_total"], errors="coerce").fillna(0)
            df_agg["quantidade_beneficiados_total"] = pd.to_numeric(df_agg["quantidade_beneficiados_total"], errors="coerce").fillna(0)
            
            total_rs = df_agg["valor_total"].sum()
            total_pessoas = df_agg["quantidade_beneficiados_total"].sum()
            
            m1, m2 = st.columns(2)
            m1.metric("Valor Total Repassado", format_currency(total_rs))
            m2.metric("Total de Beneficiados (Soma)", f"{total_pessoas:,.0f}".replace(",", "."))
            
            df_agg = df_agg.sort_values(by="mes")
            fig_line = px.line(df_agg, x="mes", y="valor_total", markers=True, title="Evolução de Repasses por Mês", color_discrete_sequence=["#10B981"])
            apply_chart_theme(fig_line)
            st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("Nenhum dado consolidado encontrado.")
        
    st.markdown("---")
    st.subheader("Top Municípios Beneficiados")
    
    limit = st.slider("Top N Municípios", 5, 50, 10, key="soc_limit")
    params_rank = params.copy()
    params_rank["limit"] = limit
    
    data_rank = fetch_data("/transparencia/beneficios/analytics/ranking", params=params_rank)
    if data_rank:
        df_rank = pd.DataFrame(data_rank)
        if "nome_municipio" in df_rank.columns:
            df_rank["valor_total"] = pd.to_numeric(df_rank["valor_total"], errors="coerce").fillna(0)
            df_rank["quantidade_beneficiados_total"] = pd.to_numeric(df_rank["quantidade_beneficiados_total"], errors="coerce").fillna(0)
            
            df_rank["Município"] = df_rank["nome_municipio"] + " - " + df_rank["uf"]
            df_rank = df_rank.sort_values(by="valor_total", ascending=True)
            
            r1, r2 = st.columns(2)
            with r1:
                fig_bar = px.bar(df_rank, x="valor_total", y="Município", orientation='h', title="Ranking por Volume (R$)", color="valor_total", color_continuous_scale="Greens")
                apply_chart_theme(fig_bar, is_currency_y=False, is_currency_x=True)
                fig_bar.update_layout(coloraxis_showscale=False)
                st.plotly_chart(fig_bar, use_container_width=True)
            
            with r2:
                fig_pie = px.pie(df_rank, values="valor_total", names="Município", hole=0.5, title="Proporção no Top N", color_discrete_sequence=COLOR_PALETTE)
                apply_chart_theme(fig_pie, is_currency_y=False)
                fig_pie.update_traces(textposition='inside', textinfo='percent', hovertemplate="%{label}<br>R$ %{value:,.2f}<br>(%{percent})")
                fig_pie.update_layout(showlegend=False, margin=dict(t=30, l=10, r=10, b=10))
                st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("Nenhum ranking encontrado.")

def render_social_municipio_view():
    st.title("Histórico Municipal (Social)")
    
    mun_list = get_ibge_full_mapping()
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        ano = st.selectbox("Exercício", AVAILABLE_YEARS, key="soc_mun_ano")
    with c2:
        tipo = st.selectbox("Benefício", ["bolsa_familia", "auxilio_brasil", "novo_bolsa_familia"], key="soc_mun_tipo")
    with c3:
        ufs_disponiveis = sorted(list(set(m["uf"] for m in mun_list))) if mun_list else ["SP"]
        uf = st.selectbox("Estado (UF)", ufs_disponiveis, index=ufs_disponiveis.index("SP") if "SP" in ufs_disponiveis else 0)
    with c4:
        municipios_uf = [m for m in mun_list if m["uf"] == uf]
        nomes_mun = sorted([m["nome"] for m in municipios_uf]) if municipios_uf else ["Desconhecido"]
        default_mun = "São Paulo" if uf == "SP" else nomes_mun[0]
        nome_mun = st.selectbox("Município", nomes_mun, index=nomes_mun.index(default_mun) if default_mun in nomes_mun else 0)
        
    cod_ibge = None
    if municipios_uf:
        for m in municipios_uf:
            if m["nome"] == nome_mun:
                cod_ibge = m["id"]
                break
                
    st.markdown("---")
    if not cod_ibge:
        st.warning("Não foi possível carregar os códigos dos municípios. Tente novamente.")
        return
        
    st.subheader(f"Panorama Estadual: {uf} - {ano}")
    
    col_est1, col_est2 = st.columns(2)
    
    with col_est1:
        params_ranking = {"tipoBeneficio": tipo, "ano": ano, "uf": uf, "limit": 10}
        data_ranking = fetch_data("/transparencia/beneficios/analytics/ranking", params=params_ranking)
        if data_ranking:
            df_rk = pd.DataFrame(data_ranking)
            if not df_rk.empty:
                df_rk["valor_total"] = pd.to_numeric(df_rk["valor_total"], errors="coerce").fillna(0)
                if "nome_municipio" not in df_rk.columns:
                    ibge_map = {str(m["id"]): m["nome"] for m in mun_list}
                    df_rk["nome_municipio"] = df_rk["codigo_ibge"].astype(str).map(ibge_map).fillna(df_rk["codigo_ibge"].astype(str))
                df_rk = df_rk.sort_values(by="valor_total", ascending=True)
                fig_rk = px.bar(df_rk, x="valor_total", y="nome_municipio", orientation="h", title="Top 10 Maiores Repasses (R$)", color_discrete_sequence=["#F59E0B"])
                apply_chart_theme(fig_rk)
                st.plotly_chart(fig_rk, use_container_width=True)
                
    with col_est2:
        params_estado = {"tipoBeneficio": tipo, "ano": ano, "uf": uf}
        data_estado = fetch_data("/transparencia/beneficios/analytics/agregacao", params=params_estado)
        if data_estado:
            df_est = pd.DataFrame(data_estado)
            if not df_est.empty and "mes" in df_est.columns:
                df_est["quantidade_beneficiados_total"] = pd.to_numeric(df_est["quantidade_beneficiados_total"], errors="coerce").fillna(0)
                df_est = df_est.sort_values(by="mes")
                df_est["Mês"] = df_est["mes"].astype(str).str.zfill(2)
                fig_est = px.area(df_est, x="Mês", y="quantidade_beneficiados_total", markers=True, title="Evolução de Beneficiários no Estado", color_discrete_sequence=["#8B5CF6"])
                fig_est.update_traces(fillcolor="rgba(139, 92, 246, 0.2)")
                apply_chart_theme(fig_est, is_currency_y=False)
                st.plotly_chart(fig_est, use_container_width=True)

    st.markdown("---")
    
    # Quando o backend liberar o novo endpoint, basta alterar a URL e adicionar UF e Ano nos parâmetros
    params = {"tipoBeneficio": tipo, "ano": ano, "uf": uf, "codigoIbge": cod_ibge}
    data = fetch_data("/transparencia/beneficios/analytics/municipio-kpis", params=params)
    
    if data and isinstance(data, dict):
        historico = data.get("historico_mensal_municipio", [])
        df = pd.DataFrame(historico)
        if not df.empty and "mes" in df.columns:
            # O backend já filtrou pelo ano, basta fixar a coluna de ano para a formatação
            df["ano"] = ano
            
            df["valor"] = pd.to_numeric(df["valor"], errors="coerce").fillna(0)
            df["quantidade_beneficiados"] = pd.to_numeric(df["quantidade_beneficiados"], errors="coerce").fillna(0)
            
            df["Período"] = df["ano"].astype(str) + "-" + df["mes"].astype(str).str.zfill(2)
            df = df.sort_values(by="mes")
            
            st.subheader(f"Evolução de Repasses: {nome_mun} ({uf}) - {ano}")
            
            g1, g2 = st.columns(2)
            with g1:
                fig_area = px.area(df, x="Período", y="valor", markers=True, title="Volume Financeiro (R$)", color_discrete_sequence=["#10B981"])
                fig_area.update_traces(fillcolor="rgba(16, 185, 129, 0.2)")
                apply_chart_theme(fig_area)
                st.plotly_chart(fig_area, use_container_width=True)
                
            with g2:
                fig_area2 = px.area(df, x="Período", y="quantidade_beneficiados", markers=True, title="Quantidade de Beneficiados", color_discrete_sequence=["#3B82F6"])
                fig_area2.update_traces(fillcolor="rgba(59, 130, 246, 0.2)")
                apply_chart_theme(fig_area2, is_currency_y=False)
                st.plotly_chart(fig_area2, use_container_width=True)
                
            st.markdown("---")
            st.subheader("Indicadores Analíticos")
            k1, k2, k3 = st.columns(3)
            
            try:
                media_mun = float(data.get("media_beneficiarios_municipio") or 0)
            except (ValueError, TypeError):
                media_mun = 0.0
                
            try:
                valor_medio_mun = float(data.get("valor_medio_mensal_municipio") or 0)
            except (ValueError, TypeError):
                valor_medio_mun = 0.0
                
            try:
                taxa_var = float(data.get("taxa_variacao_beneficiarios_municipio") or 0)
            except (ValueError, TypeError):
                taxa_var = 0.0
            
            k1.metric(f"Média Beneficiários (Mun)", f"{media_mun:,.0f}".replace(",", "."))
            k2.metric("Média Mensal Recebida", format_currency(valor_medio_mun))
            k3.metric(f"Variação Mensal (MoM)", f"{taxa_var*100:+.1f}%")
        else:
            st.info(f"Nenhum repasse encontrado para {nome_mun} ({uf}) no ano de {ano}.")
    else:
        st.info("Nenhum dado histórico encontrado.")

if page == "Macro (Siconfi)":
    render_macro_view()
elif page == "Município (Siconfi)":
    render_municipio_view()
elif page == "Rankings (Siconfi)":
    render_ranking_view()
elif page == "Macro (Social)":
    render_social_macro_view()
elif page == "Município (Social)":
    render_social_municipio_view()
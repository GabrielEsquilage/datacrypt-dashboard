# Briefing Técnico: DataCrypt Dashboard (Frontend)

**Instrução para o Agente IA:** Você assumirá o papel de Engenheiro de Frontend Especialista em Dados. O seu objetivo é construir o dashboard interativo do "DataCrypt", uma plataforma de inteligência de dados que processa KPIs financeiros de municípios brasileiros (base Siconfi/Tesouro Nacional).

---

## 1. Stack Tecnológica Obrigatória
- **Gerenciamento de Pacotes:** `Poetry`
- **Framework Web:** `Streamlit` (Múltiplas páginas ou navegação em abas/sidebar)
- **Visualização:** `Plotly` (`plotly.express` e `plotly.graph_objects`)
- **Manipulação de Dados:** `Pandas` e `requests`

## 2. Design System e UI/UX (CRÍTICO)
O projeto deve possuir um visual "Premium" e moderno focado em **Dark Mode**. 
Crie o arquivo `.streamlit/config.toml` contendo:
```toml
[theme]
primaryColor = "#00F0FF"
backgroundColor = "#0D1117"
secondaryBackgroundColor = "#161B22"
textColor = "#E6EDF3"
font = "sans serif"
```
**Regras de Gráficos:**
- Sempre use o parâmetro `use_container_width=True` no `st.plotly_chart()`.
- Remova o fundo dos gráficos no Plotly para se mesclar ao Dark Mode nativo do Streamlit:
  ```python
  fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
  ```

## 3. Especificações da API Backend (FastAPI)
O backend já está construído e rodando em `http://localhost:8000/api/v1`. Os dados atuais extraídos na base são dos anos **2019 e 2020**.

Todos os endpoints retornam a mesma estrutura base JSON. Os dados analíticos sempre ficam dentro do array `"data"`.

### 3.1. Visão de Agregação (Estadual/Nacional)
- **URL:** `GET /siconfi/agregacao/ano/{ano}?uf={uf}`
- **Uso:** Retorna o consolidado (soma) de todos os KPIs do Brasil inteiro (ou de um Estado se passar `?uf=SP`), agrupado pelos 6 bimestres (periodo) do ano.
- **Campos do `data`:** `periodo`, `receita_total`, `despesa_total`, `despesa_saude`, `despesa_educacao`, `investimentos`, etc.

### 3.2. Visão de Série Histórica
- **URL:** `GET /siconfi/municipio/{cod_ibge}/serie-historica/{indicador}`
- **Uso:** Evolução de um único indicador (ex: `despesa_saude`) ao longo de vários anos e bimestres para um município específico.
- **Campos do `data`:** `ano`, `periodo`, `valor`

### 3.3. Visão de Rankings
- **URL:** `GET /siconfi/ranking/{indicador}/ano/{ano}?uf={uf}&limit={limit}`
- **Uso:** O "Top N" municípios para um determinado indicador, buscando sempre o último bimestre reportado de cada cidade.
- **Campos do `data`:** `cod_ibge`, `uf`, `periodo`, `valor`

## 4. Instruções de Arquitetura do Streamlit
Inicie seu desenvolvimento estruturando o arquivo `app.py`:

1. **Configuração Global:** Na linha 1, use `st.set_page_config(layout="wide", page_title="DataCrypt Dash")`.
2. **Menu Lateral (`st.sidebar`):** Crie uma barra lateral para o usuário escolher a "Página":
   - *Visão Macro Nacional:* Exibe cards agregados e gráficos de barra/linha com a agregação do ano.
   - *Raio-X de Município:* Possui inputs numéricos para o `cod_ibge` e exibe gráficos de linha usando o endpoint da série histórica.
   - *Top Rankings:* Interface para escolher o ano, o indicador e a UF para montar a tabela de ranking e um gráfico de barras horizontal.
3. **Tratamento de Exceções:** Implemente try/excepts elegantes nas requisições HTTP (`requests.get`) para exibir `st.warning` caso a API esteja fora do ar ou retorne 404.
4. **Cache:** Use `@st.cache_data` para decorar as funções de busca na API, evitando recarregar os mesmos endpoints desnecessariamente durante as interações na UI.

*Boa sorte! Sua missão principal é transformar os JSONs desta API rica em uma interface deslumbrante e de alta performance.*

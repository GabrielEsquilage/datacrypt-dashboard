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
- **Campos do `data`:** `cod_ibge`, `uf`, `periodo`, `valor'

### 3.4. Portal da Transparencia (Beneficios Sociais)

O Backend também possui endpoints analíticos para repasses sociais (ex: Bolsa Família). Os tipos de benefícios válidos no parâmetro `tipoBeneficio` são: `bolsa_familia`, `auxilio_brasil` ou `novo_bolsa_familia`.

- **Agregação Nacional/Estadual:** `GET /transparencia/beneficios/analytics/agregacao?tipoBeneficio={tipo}&ano={ano}&uf={uf}`
  - *Campos:* `mes`, `valor_total`, `quantidade_beneficiados_total`
- **Série Histórica Municipal:** `GET /transparencia/beneficios/analytics/serie-historica?tipoBeneficio={tipo}&codigoIbge={codigo_ibge}`
  - *Campos:* `ano`, `mes`, `valor`, `quantidade_beneficiados`
- **Ranking de Municípios:** `GET /transparencia/beneficios/analytics/ranking?tipoBeneficio={tipo}&ano={ano}&uf={uf}&limit={limit}`
  - *Campos:* `codigo_ibge`, `uf`, `nome_municipio`, `valor_total`, `quantidade_beneficiados_total`

## 4. Instruções de Arquitetura do Streamlit

Inicie seu desenvolvimento estruturando o arquivo `app.py`:

1. **Configuração Global:** Na linha 1, use `st.set_page_config(layout="wide", page_title="DataCrypt Dash")`.
2. **Menu Lateral (`st.sidebar`):** Crie uma barra lateral para o usuário escolher a "Página". Segregue as páginas em duas grandes categorias: **Finanças (Siconfi)** e **Social (Transparência)**:
   - *Siconfi - Visão Macro Nacional:* Exibe cards agregados e gráficos de barra/linha com a agregação do ano.
   - *Siconfi - Raio-X do Município:* Inputs numéricos para o `cod_ibge` com evolução temporal dos indicadores.
   - *Siconfi - Top Rankings:* Tabelas e barras horizontais cruzando indicadores e estados.
   - *Social - Agregação e Rankings:* Gráficos mostrando o montante injetado (R$ e quantidade de pessoas) por benefício.
   - *Social - Histórico Municipal:* Evolução mensal de repasses na cidade selecionada.
3. **Tratamento de Exceções:** Implemente try/excepts elegantes nas requisições HTTP (`requests.get`) para exibir `st.warning` caso a API esteja fora do ar ou retorne 404.
4. **Cache:** Use `@st.cache_data` para decorar as funções de busca na API, evitando recarregar os mesmos endpoints desnecessariamente durante as interações na UI.

*Boa sorte! Sua missão principal é transformar os JSONs desta API rica em uma interface deslumbrante e de alta performance.*

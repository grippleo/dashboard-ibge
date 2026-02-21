import streamlit as st
import pandas as pd
import plotly.express as px
import snowflake.connector

# ── Configuração da página ──────────────────────────────────────────────
st.set_page_config(
    page_title="Dashboard IBGE - Municípios Brasileiros",
    page_icon="🇧🇷",
    layout="wide",
)

st.title("🇧🇷 Dashboard - Localidades do Brasil (IBGE)")
st.markdown("Fonte: **Data Warehouse Snowflake** — dados extraídos da API de Localidades do IBGE.")


# ── Conexão com Snowflake ───────────────────────────────────────────────
@st.cache_data(ttl=3600)
def carregar_dados():
    """Carrega dados diretamente do Snowflake."""
    conn = snowflake.connector.connect(
        account=st.secrets["snowflake"]["account"],
        user=st.secrets["snowflake"]["user"],
        password=st.secrets["snowflake"]["password"],
        warehouse=st.secrets["snowflake"]["warehouse"],
        database=st.secrets["snowflake"]["database"],
        schema=st.secrets["snowflake"]["schema"],
    )

    # Consultar estados
    df_estados = pd.read_sql("SELECT * FROM ESTADOS", conn)

    # Consultar municípios
    df_municipios = pd.read_sql("SELECT * FROM MUNICIPIOS", conn)

    conn.close()

    # Padronizar nomes das colunas para minúsculo
    df_estados.columns = [c.lower() for c in df_estados.columns]
    df_municipios.columns = [c.lower() for c in df_municipios.columns]

    return df_estados, df_municipios


df_estados, df_municipios = carregar_dados()

st.caption(f"📡 Fonte dos dados: **Snowflake (DB_IBGE)** | Total de registros: {len(df_municipios):,} municípios")

st.divider()

# ── 1. CARDS — 3 KPIs ──────────────────────────────────────────────────
total_municipios = len(df_municipios)
total_estados = df_municipios["uf"].nunique()

mun_por_regiao = df_municipios.groupby("regiao").size().reset_index(name="qtd")
regiao_mais_municipios = mun_por_regiao.loc[mun_por_regiao["qtd"].idxmax(), "regiao"]

col1, col2, col3 = st.columns(3)
col1.metric("🏘️ Total de Municípios", f"{total_municipios:,}")
col2.metric("🗺️ Total de Estados", total_estados)
col3.metric("🏆 Região com Mais Municípios", regiao_mais_municipios)

st.divider()

# ── 2. GRÁFICO DE BARRAS — Municípios por Região ───────────────────────
ordem_regioes = ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]
mun_por_regiao["regiao"] = pd.Categorical(
    mun_por_regiao["regiao"], categories=ordem_regioes, ordered=True
)
mun_por_regiao = mun_por_regiao.sort_values("regiao")

fig_bar = px.bar(
    mun_por_regiao,
    x="regiao",
    y="qtd",
    color="regiao",
    text="qtd",
    title="Municípios por Região",
    labels={"regiao": "Região", "qtd": "Quantidade de Municípios"},
    color_discrete_sequence=px.colors.qualitative.Set2,
)
fig_bar.update_traces(textposition="outside")
fig_bar.update_layout(showlegend=False, yaxis_title="Quantidade de Municípios")

# ── 3. GRÁFICO DE PIZZA — Distribuição por Região ──────────────────────
fig_pie = px.pie(
    mun_por_regiao,
    names="regiao",
    values="qtd",
    title="Distribuição por Região",
    color_discrete_sequence=px.colors.qualitative.Set2,
    hole=0.0,
)
fig_pie.update_traces(textinfo="percent+label")

col_bar, col_pie = st.columns(2)
with col_bar:
    st.plotly_chart(fig_bar, use_container_width=True)
with col_pie:
    st.plotly_chart(fig_pie, use_container_width=True)

st.divider()

# ── 4. TABELA TOP 10 — Estados com Mais Municípios ─────────────────────
st.subheader("📋 Top 10 — Estados com Mais Municípios")

mun_por_estado = (
    df_municipios.groupby("uf")
    .size()
    .reset_index(name="Quantidade")
    .sort_values("Quantidade", ascending=False)
    .head(10)
    .reset_index(drop=True)
)
mun_por_estado.index = mun_por_estado.index + 1
mun_por_estado = mun_por_estado.rename(columns={"uf": "UF"})

st.dataframe(mun_por_estado, use_container_width=True)

# ── Rodapé ──────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "Dashboard desenvolvido como atividade da Aula 1 — "
    "Pipeline de Dados: API IBGE → Snowflake → Streamlit | "
    "Pós-graduação em Data Science — UNICAMP"
)

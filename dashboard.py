import streamlit as st
import pandas as pd
import plotly.express as px
import requests

# ── Configuração da página ──────────────────────────────────────────────
st.set_page_config(
    page_title="Dashboard IBGE - Municípios Brasileiros",
    page_icon="🇧🇷",
    layout="wide",
)

st.title("🇧🇷 Dashboard - Localidades do Brasil (IBGE)")
st.markdown("Fonte: **API de Localidades do IBGE** — dados de estados e municípios brasileiros.")


# ── Extração de dados ───────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def carregar_dados():
    """
    Tenta carregar os dados via API do IBGE.
    Caso a API esteja indisponível, usa o CSV alternativo do GitHub.
    """
    try:
        # 1. Estados
        url_estados = "https://servicodados.ibge.gov.br/api/v1/localidades/estados"
        resp_estados = requests.get(url_estados, timeout=10)
        resp_estados.raise_for_status()
        estados_json = resp_estados.json()

        df_estados = pd.DataFrame([
            {
                "codigo_uf": e["id"],
                "uf": e["sigla"],
                "estado": e["nome"],
                "regiao": e["regiao"]["nome"],
            }
            for e in estados_json
        ])

        # 2. Municípios
        url_municipios = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"
        resp_mun = requests.get(url_municipios, timeout=30)
        resp_mun.raise_for_status()
        mun_json = resp_mun.json()

        df_municipios = pd.DataFrame([
            {
                "codigo_ibge": m["id"],
                "municipio": m["nome"],
                "codigo_uf": m["microrregiao"]["mesorregiao"]["UF"]["id"],
                "uf": m["microrregiao"]["mesorregiao"]["UF"]["sigla"],
                "estado": m["microrregiao"]["mesorregiao"]["UF"]["nome"],
                "regiao": m["microrregiao"]["mesorregiao"]["UF"]["regiao"]["nome"],
            }
            for m in mun_json
        ])

        return df_estados, df_municipios, "API IBGE"

    except Exception:
        # Fallback: CSV do GitHub
        url_csv = "https://raw.githubusercontent.com/kelvins/municipios-brasileiros/main/csv/municipios.csv"
        url_estados_csv = "https://raw.githubusercontent.com/kelvins/municipios-brasileiros/main/csv/estados.csv"

        df_municipios = pd.read_csv(url_csv)
        df_estados = pd.read_csv(url_estados_csv)

        # Padronizar nomes de colunas
        df_estados = df_estados.rename(columns={"nome": "estado", "codigo_uf": "codigo_uf"})
        df_municipios = df_municipios.rename(columns={"nome": "municipio"})

        # Juntar região aos municípios
        df_municipios = df_municipios.merge(
            df_estados[["codigo_uf", "uf", "estado", "regiao"]],
            on="codigo_uf",
            how="left",
            suffixes=("", "_est"),
        )

        return df_estados, df_municipios, "CSV GitHub (fallback)"


df_estados, df_municipios, fonte = carregar_dados()

st.caption(f"📡 Fonte dos dados: **{fonte}** | Total de registros: {len(df_municipios):,} municípios")

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
mun_por_estado.index = mun_por_estado.index + 1  # ranking começando em 1
mun_por_estado = mun_por_estado.rename(columns={"uf": "UF"})

st.dataframe(mun_por_estado, use_container_width=True)

# ── Rodapé ──────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "Dashboard desenvolvido como atividade da Aula 1 — "
    "Pipeline de Dados: API IBGE → Streamlit | "
    "Pós-graduação em Data Science — UNICAMP"
)
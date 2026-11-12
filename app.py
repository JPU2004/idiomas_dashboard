import os
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from pyvis.network import Network
import html

st.set_page_config(page_title="LinguaGraph | Dashboard", page_icon="🌐", layout="wide")
st.markdown("""<style>.block-container{padding-top:2rem}div[data-testid='stMetric']{background:#17263b;border:1px solid #334761;padding:18px;border-radius:14px}div[data-testid='stMetric'] *{color:#f5f7ff!important}</style>""", unsafe_allow_html=True)

DEMO = [
    ("Inglês", "A1", "Seg/Qua", "Manhã", "Ana Silva", 20, 12),
    ("Inglês", "B1", "Ter/Qui", "Noite", "Carlos Lima", 20, 18),
    ("Espanhol", "A1", "Seg/Qua", "Noite", "Marina Costa", 18, 9),
    ("Espanhol", "B1", "Sábado", "Manhã", "Marina Costa", 18, 16),
    ("Francês", "A1", "Ter/Qui", "Tarde", "Pierre Martin", 15, 8),
    ("Francês", "A2", "Seg/Qua", "Noite", "Pierre Martin", 15, 14),
    ("Mandarim", "A1", "Sábado", "Tarde", "Li Wei", 12, 7),
    ("Russo", "A1", "Ter/Qui", "Noite", "Olga Petrova", 12, 10),
]

@st.cache_data(ttl=30)
def get_data():
    if os.getenv("USE_FALKORDB", "0") != "1":
        return pd.DataFrame(DEMO, columns=["Idioma", "Nível", "Dias", "Turno", "Professor", "Capacidade", "Matriculados"]), "Demonstração"
    try:
        from redis import Redis
        r = Redis(host=os.getenv("FALKOR_HOST", "localhost"), port=int(os.getenv("FALKOR_PORT", "6379")), decode_responses=True, socket_connect_timeout=3)
        query = "MATCH (i:Idioma)-[:OFERECE]->(t:Turma)-[:MINISTRADA_POR]->(p:Professor) RETURN i.nome, t.nivel, t.dias, t.turno, p.nome, t.capacidade, t.matriculados ORDER BY i.nome"
        result = r.execute_command("GRAPH.QUERY", "EscolaIdiomas", query, "--compact")
        rows = result[1]
        def unwrap(v):
            if isinstance(v, list) and len(v) == 2 and isinstance(v[0], int):
                return v[1]
            return v
        data = [[unwrap(x) for x in row] for row in rows]
        return pd.DataFrame(data, columns=["Idioma", "Nível", "Dias", "Turno", "Professor", "Capacidade", "Matriculados"]), "FalkorDB"
    except Exception as e:
        st.error(f"Não foi possível consultar o FalkorDB: {e}")
        st.stop()

df, origem = get_data()
for col in ["Capacidade", "Matriculados"]:
    df[col] = pd.to_numeric(df[col])
df["Vagas"] = df["Capacidade"] - df["Matriculados"]
df["Ocupação (%)"] = (df["Matriculados"] / df["Capacidade"] * 100).round(0).astype(int)
df["Status"] = df["Vagas"].apply(lambda n: "Lotada" if n <= 0 else "Últimas vagas" if n <= 3 else "Disponível")

st.title("🌐 LinguaGraph")
st.caption(f"Painel de cursos e disponibilidade de turmas · Fonte: {origem}")
with st.sidebar:
    st.header("Filtros")
    idioma = st.multiselect("Idioma", sorted(df["Idioma"].unique()))
    nivel = st.multiselect("Nível", sorted(df["Nível"].unique()))
    turno = st.multiselect("Turno", sorted(df["Turno"].unique()))
    st.divider()
    st.caption("Projeto acadêmico · Escola de Idiomas")
filtered = df.copy()
for col, selected in [("Idioma", idioma), ("Nível", nivel), ("Turno", turno)]:
    if selected:
        filtered = filtered[filtered[col].isin(selected)]

tab_dashboard, tab_grafo = st.tabs(["📊 Dashboard", "🕸️ Grafo Interativo"])
with tab_dashboard:
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Idiomas", filtered["Idioma"].nunique())
    m2.metric("Turmas", len(filtered))
    m3.metric("Professores", filtered["Professor"].nunique())
    m4.metric("Vagas disponíveis", int(filtered["Vagas"].sum()))
    st.subheader("Turmas e horários")
    st.dataframe(filtered[["Idioma", "Nível", "Dias", "Turno", "Professor", "Vagas", "Status", "Ocupação (%)"]], hide_index=True, use_container_width=True)
    left, right = st.columns(2)
    with left:
        st.subheader("Vagas por idioma")
        if not filtered.empty:
            st.bar_chart(filtered.groupby("Idioma")["Vagas"].sum())
        else:
            st.info("Nenhuma turma corresponde aos filtros.")
    with right:
        st.subheader("Ocupação das turmas")
        if not filtered.empty:
            chart = filtered.copy()
            chart["Turma"] = chart["Idioma"] + " " + chart["Nível"] + " (" + chart["Turno"] + ")"
            st.bar_chart(chart.set_index("Turma")["Ocupação (%)"])
    st.caption("Os dados são fictícios e destinados à demonstração acadêmica.")

with tab_grafo:
    st.subheader("Rede de idiomas, turmas e professores")
    st.caption("Nós representam entidades; setas representam relações armazenadas no FalkorDB.")

    @st.cache_data(ttl=30)
    def get_graph_rows():
        if origem != "FalkorDB":
            return None
        from redis import Redis
        r = Redis(host=os.getenv("FALKOR_HOST", "localhost"),
                  port=int(os.getenv("FALKOR_PORT", "6379")),
                  decode_responses=True, socket_connect_timeout=3)
        q = ("MATCH (i:Idioma)-[:OFERECE]->(t:Turma)-[:MINISTRADA_POR]->(p:Professor) "
             "RETURN id(i), i.nome, id(t), t.id, t.nivel, t.turno, t.dias, "
             "t.capacidade, t.matriculados, id(p), p.nome ORDER BY i.nome, t.id")
        result = r.execute_command("GRAPH.QUERY", "EscolaIdiomas", q, "--compact")
        def unwrap(v):
            return v[1] if isinstance(v, list) and len(v) == 2 and isinstance(v[0], int) else v
        return [[unwrap(v) for v in row] for row in result[1]]

    try:
        graph_rows = get_graph_rows()
        if graph_rows is None:
            st.warning("Modo demonstração: grafo ilustrativo com os dados fictícios do dashboard. Para visualizar o banco real, ative USE_FALKORDB=1.")
            graph_rows = [
                [f"idioma-{row.Idioma}", row.Idioma, f"turma-{idx}", idx,
                 row.Nível, row.Turno, row.Dias, row.Capacidade, row.Matriculados,
                 f"prof-{row.Professor}", row.Professor]
                for idx, row in enumerate(df.itertuples(index=False), 1)
            ]
        net = Network(height="620px", width="100%", bgcolor="#101827", font_color="#f8fafc", directed=True, cdn_resources="in_line")
        net.barnes_hut(gravity=-3500, central_gravity=0.15, spring_length=180, spring_strength=0.035, damping=0.25)
        shown = 0
        for iid, iname, tid, tnum, level, shift, days, capacity, enrolled, pid, pname in graph_rows:
            if idioma and iname not in idioma:
                continue
            if nivel and level not in nivel:
                continue
            if turno and shift not in turno:
                continue
            shown += 1
            a, b, c = f"i:{iid}", f"t:{tid}", f"p:{pid}"
            net.add_node(a, label=str(iname), title=f"Idioma: {html.escape(str(iname))}", color="#38bdf8", shape="dot", size=28)
            net.add_node(b, label=f"Turma {tnum} · {level}", title=(f"Turma {html.escape(str(tnum))} | {html.escape(str(iname))} {html.escape(str(level))}"
                         f" | {html.escape(str(days))} | {html.escape(str(shift))}"
                         f" | Matriculados: {enrolled}/{capacity}"), color="#34d399", shape="dot", size=21)
            net.add_node(c, label=str(pname), title=f"Professor: {html.escape(str(pname))}", color="#fbbf24", shape="dot", size=24)
            net.add_edge(a, b, title="OFERECE", label="OFERECE", color="#64748b", arrows="to")
            net.add_edge(b, c, title="MINISTRADA_POR", label="MINISTRADA_POR", color="#64748b", arrows="to")
        if shown:
            st.markdown("🔵 **Idioma** &nbsp;&nbsp; 🟢 **Turma** &nbsp;&nbsp; 🟡 **Professor**")
            st.caption("Arraste os nós, use a roda do mouse para zoom e passe o cursor sobre um nó para ver seus dados. Os filtros da barra lateral também se aplicam aqui.")
            components.html(net.generate_html(), height=650, scrolling=False)
            st.caption(f"{len(net.nodes)} nós e {len(net.edges)} relações exibidos nesta visualização. Fonte: {origem}.")
        else:
            st.info("Nenhuma turma corresponde aos filtros selecionados.")
    except Exception as exc:
        st.error(f"Não foi possível construir a visualização: {exc}")
        st.info("Confirme se o Docker está ativo e se a fonte FalkorDB está habilitada.")

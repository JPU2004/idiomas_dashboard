from redis import Redis

r = Redis(host="localhost", port=6379, decode_responses=True)
queries = [
    "MATCH (n) DETACH DELETE n",
    "CREATE (:Idioma {nome:'Inglês'}), (:Idioma {nome:'Espanhol'}), (:Idioma {nome:'Francês'}), (:Idioma {nome:'Mandarim'}), (:Idioma {nome:'Russo'})",
]
records = [
    ("Inglês", "A1", "Seg/Qua", "Manhã", "Ana Silva", 20, 12),
    ("Inglês", "B1", "Ter/Qui", "Noite", "Carlos Lima", 20, 18),
    ("Espanhol", "A1", "Seg/Qua", "Noite", "Marina Costa", 18, 9),
    ("Espanhol", "B1", "Sábado", "Manhã", "Marina Costa", 18, 16),
    ("Francês", "A1", "Ter/Qui", "Tarde", "Pierre Martin", 15, 8),
    ("Francês", "A2", "Seg/Qua", "Noite", "Pierre Martin", 15, 14),
    ("Mandarim", "A1", "Sábado", "Tarde", "Li Wei", 12, 7),
    ("Russo", "A1", "Ter/Qui", "Noite", "Olga Petrova", 12, 10),
]
for q in queries:
    r.execute_command("GRAPH.QUERY", "EscolaIdiomas", q)
for idx, (idioma, nivel, dias, turno, professor, capacidade, matriculados) in enumerate(records, 1):
    q = (f"MATCH (i:Idioma {{nome:'{idioma}'}}) "
         f"MERGE (p:Professor {{nome:'{professor}'}}) "
         f"CREATE (t:Turma {{id:{idx}, nivel:'{nivel}', dias:'{dias}', turno:'{turno}', capacidade:{capacidade}, matriculados:{matriculados}}}) "
         f"CREATE (i)-[:OFERECE]->(t) CREATE (t)-[:MINISTRADA_POR]->(p)")
    r.execute_command("GRAPH.QUERY", "EscolaIdiomas", q)
print("Banco EscolaIdiomas populado com sucesso!")

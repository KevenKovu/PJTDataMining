import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Caminho do CSV da PNS
base_dir = Path(__file__).resolve().parent
csv_path = base_dir.parent / "pns2019" / "pns2019.csv"

# Escolha o tipo de saída: "png" ou "pdf"
out_type = "pdf"  # troque para "png" se preferir

# Leitura do arquivo, mantendo apenas as colunas usadas
# V0001 = estado
# C006 = sexo (1=homem, 2=mulher)
# C008 = idade
# Q00201 = resposta da questão (considera verdadeiro quando vale 1)
df = pd.read_csv(
    csv_path,
    usecols=["V0001", "C006", "C008", "Q00201"],
    encoding="latin1",
    engine="c",
    dtype={"V0001": "Int64", "C006": "Int64", "C008": "Int64", "Q00201": "Int64"},
    na_values=["NA", "", " ", "nan"],
)

# Conversão para numérico
for col in ["V0001", "C006", "C008", "Q00201"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Filtro da população de interesse
# idade entre 25 e 59 anos
# sexo = 1 homem, 2 mulher
# Q00201 == 1 => verdadeiro/contado
# Inclui apenas respostas válidas (não em branco)
pop = df[df["C008"].between(25, 59, inclusive="both") & 
         df["C006"].isin([1, 2]) & 
         df["Q00201"].notna()].copy()
casos = pop[pop["Q00201"].eq(1)].copy()

# Mapeia os códigos dos estados para nomes
uf_map = {
    11: "Rondônia", 12: "Acre", 13: "Amazonas", 14: "Roraima", 15: "Pará", 16: "Amapá", 17: "Tocantins",
    21: "Maranhão", 22: "Piauí", 23: "Ceará", 24: "Rio Grande do Norte", 25: "Paraíba", 26: "Pernambuco",
    27: "Alagoas", 28: "Sergipe", 29: "Bahia",
    31: "Minas Gerais", 32: "Espírito Santo", 33: "Rio de Janeiro", 35: "São Paulo",
    41: "Paraná", 42: "Santa Catarina", 43: "Rio Grande do Sul",
    50: "Mato Grosso do Sul", 51: "Mato Grosso", 52: "Goiás", 53: "Distrito Federal"
}

# Mapeia os códigos dos estados para regiões
regiao_map = {
    11: "Norte", 12: "Norte", 13: "Norte", 14: "Norte", 15: "Norte", 16: "Norte", 17: "Norte",
    21: "Nordeste", 22: "Nordeste", 23: "Nordeste", 24: "Nordeste", 25: "Nordeste", 26: "Nordeste",
    27: "Nordeste", 28: "Nordeste", 29: "Nordeste",
    31: "Sudeste", 32: "Sudeste", 33: "Sudeste", 35: "Sudeste",
    41: "Sul", 42: "Sul", 43: "Sul",
    50: "Centro-Oeste", 51: "Centro-Oeste", 52: "Centro-Oeste", 53: "Centro-Oeste"
}

# Contagem de entrevistas e casos por estado e sexo
entrevistas = (
    pop.groupby(["V0001", "C006"]).size()
       .unstack(fill_value=0)
       .rename(columns={1: "Homens", 2: "Mulheres"})
       .reindex(columns=["Homens", "Mulheres"], fill_value=0)
)

casos_estado_sexo = (
    casos.groupby(["V0001", "C006"]).size()
         .unstack(fill_value=0)
         .rename(columns={1: "Homens", 2: "Mulheres"})
         .reindex(columns=["Homens", "Mulheres"], fill_value=0)
)

# Relativo: casos / entrevistas por estado e sexo
relativo = casos_estado_sexo.div(entrevistas.replace(0, pd.NA))
relativo = relativo.fillna(0)

# Consolidado para o relatório final
contagem = casos_estado_sexo.copy()
contagem.index = contagem.index.map(lambda x: uf_map.get(int(x), str(x)))
contagem["Total"] = contagem.sum(axis=1)
contagem = contagem.sort_values("Total", ascending=True)

# Tabela completa com números absolutos e relativos por estado
casos_nome = casos_estado_sexo.copy()
casos_nome.index = casos_nome.index.map(lambda x: uf_map.get(int(x), str(x)))

entrevistas_nome = entrevistas.copy()
entrevistas_nome.index = entrevistas_nome.index.map(lambda x: uf_map.get(int(x), str(x)))

relativo_nome = relativo.copy()
relativo_nome.index = relativo_nome.index.map(lambda x: uf_map.get(int(x), str(x)))

relatorio = pd.concat(
    [
        casos_nome.add_prefix("Casos_"),
        entrevistas_nome.add_prefix("Entrevistas_"),
    ],
    axis=1,
)
relatorio["Casos_Total"] = relatorio[["Casos_Homens", "Casos_Mulheres"]].sum(axis=1)
relatorio["Entrevistas_Total"] = relatorio[["Entrevistas_Homens", "Entrevistas_Mulheres"]].sum(axis=1)
relatorio["Taxa_relativa_Homens"] = relatorio["Casos_Homens"] / relatorio["Entrevistas_Homens"].replace(0, pd.NA)
relatorio["Taxa_relativa_Mulheres"] = relatorio["Casos_Mulheres"] / relatorio["Entrevistas_Mulheres"].replace(0, pd.NA)
relatorio["Taxa_relativa_Total"] = relatorio["Casos_Total"] / relatorio["Entrevistas_Total"].replace(0, pd.NA)
relatorio = relatorio.fillna(0)

# Exibe o relatório completo
print("\nRelatório completo: casos, entrevistas e taxa relativa por estado e sexo")
print(relatorio.to_string())

# ============ DADOS POR REGIÃO ============

# Adiciona coluna de região aos dataframes
pop["Região"] = pop["V0001"].map(regiao_map)
casos["Região"] = casos["V0001"].map(regiao_map)

# Contagem de entrevistas e casos por região e sexo
entrevistas_regiao = (
    pop.groupby(["Região", "C006"]).size()
       .unstack(fill_value=0)
       .rename(columns={1: "Homens", 2: "Mulheres"})
       .reindex(columns=["Homens", "Mulheres"], fill_value=0)
)

casos_regiao_sexo = (
    casos.groupby(["Região", "C006"]).size()
         .unstack(fill_value=0)
         .rename(columns={1: "Homens", 2: "Mulheres"})
         .reindex(columns=["Homens", "Mulheres"], fill_value=0)
)

# Relativo por região: casos / entrevistas por região e sexo
relativo_regiao = casos_regiao_sexo.div(entrevistas_regiao.replace(0, pd.NA))
relativo_regiao = relativo_regiao.fillna(0)

# Tabela completa com números absolutos e relativos por região
relatorio_regiao = pd.concat(
    [
        casos_regiao_sexo.add_prefix("Casos_"),
        entrevistas_regiao.add_prefix("Entrevistas_"),
    ],
    axis=1,
)
relatorio_regiao["Casos_Total"] = relatorio_regiao[["Casos_Homens", "Casos_Mulheres"]].sum(axis=1)
relatorio_regiao["Entrevistas_Total"] = relatorio_regiao[["Entrevistas_Homens", "Entrevistas_Mulheres"]].sum(axis=1)
relatorio_regiao["Taxa_relativa_Homens"] = relatorio_regiao["Casos_Homens"] / relatorio_regiao["Entrevistas_Homens"].replace(0, pd.NA)
relatorio_regiao["Taxa_relativa_Mulheres"] = relatorio_regiao["Casos_Mulheres"] / relatorio_regiao["Entrevistas_Mulheres"].replace(0, pd.NA)
relatorio_regiao["Taxa_relativa_Total"] = relatorio_regiao["Casos_Total"] / relatorio_regiao["Entrevistas_Total"].replace(0, pd.NA)
relatorio_regiao = relatorio_regiao.fillna(0)

# Exibe o relatório por região
print("\nRelatório por região: casos, entrevistas e taxa relativa por região e sexo")
print(relatorio_regiao.to_string())

# ============ GRÁFICOS ============

# Gráfico de barras agrupadas por estado (ordenado crescente)
ax = contagem.drop(columns=["Total"]).plot(
    kind="bar",
    figsize=(16, 8),
    width=0.8,
    color=["#4C72B0", "#DD8452"],
    edgecolor="black"
)

ax.set_title("Quantidade de casos com colesterol alto = 1 por estado e sexo (idade 25 a 59)")
ax.set_ylabel("Quantidade")
ax.set_xlabel("Estados")
ax.legend(title="Sexo")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()

output_path = base_dir / f"grafico_q00201_estado_sexo.{out_type}"
plt.savefig(output_path, dpi=300, bbox_inches="tight")
print(f"\nGráfico por estado salvo em: {output_path}")
plt.show()

# Gráfico de barras agrupadas por região (ordenado crescente)
contagem_regiao = casos_regiao_sexo.copy()
contagem_regiao["Total"] = contagem_regiao.sum(axis=1)
contagem_regiao = contagem_regiao.sort_values("Total", ascending=True)

ax = contagem_regiao.drop(columns=["Total"]).plot(
    kind="bar",
    figsize=(12, 6),
    width=0.8,
    color=["#4C72B0", "#DD8452"],
    edgecolor="black"
)

ax.set_title("Quantidade de casos colesterol alto = 1 por região e sexo (idade 25 a 59)")
ax.set_ylabel("Quantidade")
ax.set_xlabel("Regiões")
ax.legend(title="Sexo")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()

output_path = base_dir / f"grafico_q00201_regiao_sexo.{out_type}"
plt.savefig(output_path, dpi=300, bbox_inches="tight")
print(f"Gráfico por região salvo em: {output_path}")
plt.show()

# ============ GRÁFICOS DE TAXA RELATIVA (PORCENTAGEM) ============

# Gráfico de taxa relativa por estado (ordenado crescente)
taxa_estado = relatorio[["Taxa_relativa_Total"]].copy()
taxa_estado.columns = ["Taxa Relativa"]
taxa_estado = taxa_estado.sort_values("Taxa Relativa", ascending=True)
taxa_estado["Taxa Relativa"] = taxa_estado["Taxa Relativa"] * 100  # Converter para porcentagem

ax = taxa_estado.plot(
    kind="barh",
    figsize=(12, 8),
    width=0.7,
    color=["#2ecc71"],
    edgecolor="black",
    legend=False
)

ax.set_title("Taxa relativa (%) de colesterol alto = 1 por estado (idade 25 a 59)")
ax.set_xlabel("Taxa Relativa (%)")
ax.set_ylabel("Estados")
plt.tight_layout()

output_path = base_dir / f"grafico_q00201_taxa_relativa_estado.{out_type}"
plt.savefig(output_path, dpi=300, bbox_inches="tight")
print(f"\nGráfico de taxa relativa por estado salvo em: {output_path}")
plt.show()

# Gráfico de taxa relativa por região (ordenado crescente)
taxa_regiao = relatorio_regiao[["Taxa_relativa_Total"]].copy()
taxa_regiao.columns = ["Taxa Relativa"]
taxa_regiao = taxa_regiao.sort_values("Taxa Relativa", ascending=True)
taxa_regiao["Taxa Relativa"] = taxa_regiao["Taxa Relativa"] * 100  # Converter para porcentagem

ax = taxa_regiao.plot(
    kind="barh",
    figsize=(10, 6),
    width=0.7,
    color=["#3498db"],
    edgecolor="black",
    legend=False
)

ax.set_title("Taxa relativa (%) de colesterol alto = 1 por região (idade 25 a 59)")
ax.set_xlabel("Taxa Relativa (%)")
ax.set_ylabel("Regiões")
plt.tight_layout()

output_path = base_dir / f"grafico_q00201_taxa_relativa_regiao.{out_type}"
plt.savefig(output_path, dpi=300, bbox_inches="tight")
print(f"Gráfico de taxa relativa por região salvo em: {output_path}")
plt.show()

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Caminho do CSV da PNS
base_dir = Path(__file__).resolve().parent
csv_path = base_dir.parent / "pns2019" / "pns2019.csv"

# Escolha o tipo de saída: "png" ou "pdf"
out_type = "png"  # troque para "pdf" se preferir

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
pop = df[df["C008"].between(25, 59, inclusive="both") & df["C006"].isin([1, 2])].copy()
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

# Exporta a tabela em CSV
csv_relatorio = base_dir / "relatorio_q00201_estado_sexo.csv"
relatorio.to_csv(csv_relatorio, index_label="Estado")
print(f"\nRelatório exportado em: {csv_relatorio}")

# Gráfico de barras agrupadas por estado
ax = contagem.drop(columns=["Total"]).plot(
    kind="bar",
    figsize=(16, 8),
    width=0.8,
    color=["#4C72B0", "#DD8452"],
    edgecolor="black"
)

ax.set_title("Quantidade de casos com Q00201 = 1 por estado e sexo (idade 25 a 59)")
ax.set_ylabel("Quantidade")
ax.set_xlabel("Estados")
ax.legend(title="Sexo")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()

output_path = base_dir / f"grafico_q00201_estado_sexo.{out_type}"
plt.savefig(output_path, dpi=300, bbox_inches="tight")
print(f"Gráfico salvo em: {output_path}")
plt.show()

			
			


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
mask = df["C008"].between(25, 59, inclusive="both") & df["C006"].isin([1, 2]) & df["Q00201"].eq(1)
df = df[mask].copy()

# Mapeia os códigos dos estados para nomes
uf_map = {
    11: "Rondônia", 12: "Acre", 13: "Amazonas", 14: "Roraima", 15: "Pará", 16: "Amapá", 17: "Tocantins",
    21: "Maranhão", 22: "Piauí", 23: "Ceará", 24: "Rio Grande do Norte", 25: "Paraíba", 26: "Pernambuco",
    27: "Alagoas", 28: "Sergipe", 29: "Bahia",
    31: "Minas Gerais", 32: "Espírito Santo", 33: "Rio de Janeiro", 35: "São Paulo",
    41: "Paraná", 42: "Santa Catarina", 43: "Rio Grande do Sul",
    50: "Mato Grosso do Sul", 51: "Mato Grosso", 52: "Goiás", 53: "Distrito Federal"
}

# Conta por estado e sexo
contagem = (
    df.groupby(["V0001", "C006"]).size()
      .unstack(fill_value=0)
      .rename(columns={1: "Homens", 2: "Mulheres"})
      .reindex(columns=["Homens", "Mulheres"], fill_value=0)
)

contagem.index = contagem.index.map(lambda x: uf_map.get(int(x), str(x)))
contagem["Total"] = contagem.sum(axis=1)
contagem = contagem.sort_values("Total", ascending=True).drop(columns=["Total"])

# Gráfico de barras agrupadas por estado
ax = contagem.plot(
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

			
			


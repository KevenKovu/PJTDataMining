from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import xlwt


base_dir = Path(__file__).resolve().parent
csv_path = base_dir.parent / "pns2019" / "pns2019.csv"
xls_path = base_dir / "tabela_frequencia_idade.xls"
pdf_path = base_dir / "grafico_frequencia_relativa_acumulada_idade.pdf"

df = pd.read_csv(
    csv_path,
    usecols=["C008", "Q00201"],
    encoding="latin1",
    engine="c",
    dtype={"C008": "Int64", "Q00201": "Int64"},
    na_values=["NA", "", " ", "nan"],
)

for col in ["C008", "Q00201"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# População de interesse: idade entre 25 e 59 e resposta Q00201 igual a 1.
casos = df[
    df["C008"].between(25, 59, inclusive="both") & df["Q00201"].eq(1)
].copy()

# Cada idade é uma classe, inclusive as idades sem ocorrência.
idades = pd.Index(range(25, 60), name="Idade")
frequencia = casos.groupby("C008").size().reindex(idades, fill_value=0)
total = int(frequencia.sum())

tabela = pd.DataFrame({"Frequência": frequencia.astype(int)})
tabela["Frequência relativa"] = tabela["Frequência"] / total
tabela["Frequência relativa acumulada"] = tabela["Frequência relativa"].cumsum()

total_row = pd.DataFrame(
    {
        "Frequência": [total],
        "Frequência relativa": [tabela["Frequência relativa"].sum()],
        "Frequência relativa acumulada": [tabela["Frequência relativa acumulada"].iloc[-1]],
    },
    index=pd.Index(["Total"], name="Idade"),
)
tabela_com_total = pd.concat([tabela, total_row])

workbook = xlwt.Workbook()
worksheet = workbook.add_sheet("Frequencia por idade")
headers = ["Idade", "Frequência", "Frequência relativa", "Frequência relativa acumulada"]
for col_index, header in enumerate(headers):
    worksheet.write(0, col_index, header)

for row_index, (idade, row) in enumerate(tabela_com_total.iterrows(), start=1):
    worksheet.write(row_index, 0, idade)
    worksheet.write(row_index, 1, int(row["Frequência"]))
    worksheet.write(row_index, 2, float(row["Frequência relativa"]))
    worksheet.write(row_index, 3, float(row["Frequência relativa acumulada"]))

try:
    workbook.save(xls_path)
    print(f"Tabela de frequência salva em: {xls_path}")
except PermissionError:
    print(f"Não foi possível atualizar a tabela; feche o Excel e execute novamente: {xls_path}")
print(f"Total de casos: {total}")
print(tabela_com_total.to_string())

fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(
    tabela.index,
    tabela["Frequência relativa acumulada"] * 100,
    marker="o",
    markersize=4,
    linewidth=2,
    color="#176b87",
)
ax.set_title("Frequência relativa acumulada por idade (colesterol alto, 25 a 59 anos)")
ax.set_xlabel("Idade (anos)")
ax.set_ylabel("Frequência relativa acumulada (%)")
ax.set_xticks(list(idades))
ax.set_ylim(0, 105)
ax.grid(True, linestyle="--", alpha=0.35)
fig.tight_layout()
fig.savefig(pdf_path, format="pdf", bbox_inches="tight")
plt.close(fig)
print(f"Gráfico salvo em: {pdf_path}")
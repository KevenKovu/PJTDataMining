import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

# Caminho do CSV da PNS
base_dir = Path(__file__).resolve().parent
csv_path = base_dir / "pns2019.csv"

# Escolha o tipo de saída: "png" ou "pdf"
out_type = "pdf"  # troque para "png" se preferir

# Variáveis que compõem o apuramento solicitado.
# A PNS 2019 usa nomes de variáveis com sufixos/derivações no CSV real, então
# incluímos os nomes do dicionário e as variantes que realmente aparecem no arquivo.
core_columns = [
    "V0001", "V0026", "C006", "C008", "C009",
    "D009", "D00901",
    "E001", "VDF002", "I00102",
    "Q060", "Q061",
    "Q062", "Q06207", "Q06208", "Q06209", "Q06210", "Q06211", "Q06212",
    "Q06306", "Q06307", "Q06308", "Q06309", "Q06310", "Q06311",
    "J001", "J01101",
    "P006", "P00601", "P00602", "P00603", "P00604", "P00605", "P00607", "P00608", "P00609", "P00610",
    "P00611", "P00612", "P00613", "P00614", "P00615", "P00616", "P00617", "P00618", "P00619", "P00620",
    "P00621", "P00622", "P00623",
    "P01101", "P02001", "P023", "P027", "P02801",
    "P034", "P035", "P037", "P03701", "P03702", "P050",
    "P00104", "P00404", "W00101", "W00201"
]

# Pergunta principal da doença alvo: prefere Q060, mas mantém o legado Q00201 se o CSV antigo estiver em uso.
primary_candidates = ["Q060", "Q00201"]

# Flag de questionário concluído: usa a coluna real do dicionário quando existir, senão ignora a checagem.
completion_candidates = [
    "Q0001", "Q0002", "Q0003", "Q0004", "Q0005", "Q0006", "Q0007",
    "Q009", "Q010", "Q011", "Q012", "Q060", "Q00201"
]

if not csv_path.exists():
    raise FileNotFoundError(f"Arquivo da PNS não encontrado em: {csv_path}")

# Leitura do cabeçalho para identificar colunas disponíveis antes de carregar o arquivo completo.
header_df = pd.read_csv(csv_path, nrows=0, encoding="latin1", engine="c")
available_columns = set(header_df.columns.tolist())
selected_columns = [col for col in core_columns if col in available_columns]
selected_columns.extend(c for c in primary_candidates if c in available_columns and c not in selected_columns)
selected_columns.extend(c for c in completion_candidates if c in available_columns and c not in selected_columns)

# Garante que o estado e a idade continuem presentes mesmo quando a base for mais antiga.
for col in ["V0001", "C006", "C008"]:
    if col not in selected_columns and col in available_columns:
        selected_columns.append(col)

# Carrega apenas as colunas necessárias para reduzir memória e manter o código estável.
df = pd.read_csv(
    csv_path,
    usecols=selected_columns,
    encoding="latin1",
    engine="c",
    na_values=["NA", "", " ", "nan"],
    dtype={col: "string" for col in selected_columns}
)

# Converte os campos numéricos para valores numéricos de forma tolerante.
for col in df.columns:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Define a pergunta principal e a flag de questionário concluído, quando existir.
primary_col = next((col for col in primary_candidates if col in df.columns), None)
if primary_col is None:
    raise ValueError("Não foi encontrada a variável principal do alvo (Q060 ou Q00201) na base carregada.")

completion_col = next((col for col in completion_candidates if col in df.columns and col != primary_col), None)

# População de interesse: idade 25 a 59, sexo válido e questão principal respondida.
pop = df[df["C008"].between(25, 59, inclusive="both") & df["C006"].isin([1, 2])].copy()
if completion_col is not None:
    pop = pop[pop[completion_col].isin([1, True])].copy()

# Mantém a regra do questionário concluído e o alvo verdadeiro para a população principal.
pop = pop[pop[primary_col].notna()].copy()
casos = pop[pop[primary_col].eq(1)].copy()

# Mapeia os códigos dos estados para nomes
uf_map = {
    11: "Rondônia", 12: "Acre", 13: "Amazonas", 14: "Roraima", 15: "Pará", 16: "Amapá", 17: "Tocantins",
    21: "Maranhão", 22: "Piauí", 23: "Ceará", 24: "Rio Grande do Norte", 25: "Paraíba", 26: "Pernambuco",
    27: "Alagoas", 28: "Sergipe", 29: "Bahia", 31: "Minas Gerais", 32: "Espírito Santo", 33: "Rio de Janeiro", 35: "São Paulo",
    41: "Paraná", 42: "Santa Catarina", 43: "Rio Grande do Sul", 50: "Mato Grosso do Sul", 51: "Mato Grosso", 52: "Goiás", 53: "Distrito Federal"
}

regiao_map = {
    11: "Norte", 12: "Norte", 13: "Norte", 14: "Norte", 15: "Norte", 16: "Norte", 17: "Norte",
    21: "Nordeste", 22: "Nordeste", 23: "Nordeste", 24: "Nordeste", 25: "Nordeste", 26: "Nordeste", 27: "Nordeste", 28: "Nordeste", 29: "Nordeste",
    31: "Sudeste", 32: "Sudeste", 33: "Sudeste", 35: "Sudeste", 41: "Sul", 42: "Sul", 43: "Sul",
    50: "Centro-Oeste", 51: "Centro-Oeste", 52: "Centro-Oeste", 53: "Centro-Oeste"
}

# Exporta um arquivo Excel apenas com os atributos selecionados, sem colunas calculadas.
output_apuramento_xlsx = base_dir / "apuramento_idades_25_59.xlsx"
# Mantém somente as colunas originais do banco e a ordenação dos atributos solicitados.
atributos_analise = [
    "V0001", "V0026", "C006", "C008", "C009",
    "D009", "E001", "VDF002", "I00102",
    "Q060", "Q061", "Q062", "Q06306", "J001", "J01101",
    "P006", "P01101", "P02001", "P023", "P027", "P02801",
    "P034", "P035", "P037", "P050",
    "P00104", "P00404", "W00101", "W00201"
]
colunas_presentes = [col for col in atributos_analise if col in pop.columns]
planilha = pop[colunas_presentes].copy()
planilha.to_excel(output_apuramento_xlsx, index=False)
print(f"\nTabela de análise exportada em: {output_apuramento_xlsx}")
print(planilha.head().to_string(index=False))

# A partir daqui, o restante do script mantém apenas os gráficos de análise.
# Se você quiser apenas a tabela, pode comentar as seções abaixo.
entrevistas = pop.groupby(["V0001", "C006"]).size().unstack(fill_value=0).rename(columns={1: "Homens", 2: "Mulheres"}).reindex(columns=["Homens", "Mulheres"], fill_value=0)
casos_estado_sexo = casos.groupby(["V0001", "C006"]).size().unstack(fill_value=0).rename(columns={1: "Homens", 2: "Mulheres"}).reindex(columns=["Homens", "Mulheres"], fill_value=0)
relativo = casos_estado_sexo.div(entrevistas.replace(0, pd.NA)).fillna(0)

contagem = casos_estado_sexo.copy()
contagem.index = contagem.index.map(lambda x: uf_map.get(int(x), str(x)))
contagem["Total"] = contagem.sum(axis=1)
contagem = contagem.sort_values("Total", ascending=True)

casos_nome = casos_estado_sexo.copy()
casos_nome.index = casos_nome.index.map(lambda x: uf_map.get(int(x), str(x)))
entrevistas_nome = entrevistas.copy()
entrevistas_nome.index = entrevistas_nome.index.map(lambda x: uf_map.get(int(x), str(x)))
relativo_nome = relativo.copy()
relativo_nome.index = relativo_nome.index.map(lambda x: uf_map.get(int(x), str(x)))

relatorio = pd.concat([casos_nome.add_prefix("Casos_"), entrevistas_nome.add_prefix("Entrevistas_")], axis=1)
relatorio["Casos_Total"] = relatorio[["Casos_Homens", "Casos_Mulheres"]].sum(axis=1)
relatorio["Entrevistas_Total"] = relatorio[["Entrevistas_Homens", "Entrevistas_Mulheres"]].sum(axis=1)
relatorio["Taxa_relativa_Homens"] = relatorio["Casos_Homens"] / relatorio["Entrevistas_Homens"].replace(0, pd.NA)
relatorio["Taxa_relativa_Mulheres"] = relatorio["Casos_Mulheres"] / relatorio["Entrevistas_Mulheres"].replace(0, pd.NA)
relatorio["Taxa_relativa_Total"] = relatorio["Casos_Total"] / relatorio["Entrevistas_Total"].replace(0, pd.NA)
relatorio = relatorio.fillna(0)

print("\nRelatório completo: casos, entrevistas e taxa relativa por estado e sexo")
print(relatorio.to_string())

pop["Região"] = pop["V0001"].map(regiao_map)
casos["Região"] = casos["V0001"].map(regiao_map)
entrevistas_regiao = pop.groupby(["Região", "C006"]).size().unstack(fill_value=0).rename(columns={1: "Homens", 2: "Mulheres"}).reindex(columns=["Homens", "Mulheres"], fill_value=0)
casos_regiao_sexo = casos.groupby(["Região", "C006"]).size().unstack(fill_value=0).rename(columns={1: "Homens", 2: "Mulheres"}).reindex(columns=["Homens", "Mulheres"], fill_value=0)
relativo_regiao = casos_regiao_sexo.div(entrevistas_regiao.replace(0, pd.NA)).fillna(0)

relatorio_regiao = pd.concat([casos_regiao_sexo.add_prefix("Casos_"), entrevistas_regiao.add_prefix("Entrevistas_")], axis=1)
relatorio_regiao["Casos_Total"] = relatorio_regiao[["Casos_Homens", "Casos_Mulheres"]].sum(axis=1)
relatorio_regiao["Entrevistas_Total"] = relatorio_regiao[["Entrevistas_Homens", "Entrevistas_Mulheres"]].sum(axis=1)
relatorio_regiao["Taxa_relativa_Homens"] = relatorio_regiao["Casos_Homens"] / relatorio_regiao["Entrevistas_Homens"].replace(0, pd.NA)
relatorio_regiao["Taxa_relativa_Mulheres"] = relatorio_regiao["Casos_Mulheres"] / relatorio_regiao["Entrevistas_Mulheres"].replace(0, pd.NA)
relatorio_regiao["Taxa_relativa_Total"] = relatorio_regiao["Casos_Total"] / relatorio_regiao["Entrevistas_Total"].replace(0, pd.NA)
relatorio_regiao = relatorio_regiao.fillna(0)

print("\nRelatório por região: casos, entrevistas e taxa relativa por região e sexo")
print(relatorio_regiao.to_string())

ax = contagem.drop(columns=["Total"]).plot(kind="bar", figsize=(16, 8), width=0.8, color=["#4C72B0", "#DD8452"], edgecolor="black")
ax.set_title(f"Quantidade de casos com {primary_col} = 1 por estado e sexo (idade 25 a 59)")
ax.set_ylabel("Quantidade")
ax.set_xlabel("Estados")
ax.legend(title="Sexo")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
output_path = base_dir / f"grafico_{primary_col}_estado_sexo.{out_type}"
plt.savefig(output_path, dpi=300, bbox_inches="tight")
print(f"\nGráfico por estado salvo em: {output_path}")
plt.show()

contagem_regiao = casos_regiao_sexo.copy()
contagem_regiao["Total"] = contagem_regiao.sum(axis=1)
contagem_regiao = contagem_regiao.sort_values("Total", ascending=True)
ax = contagem_regiao.drop(columns=["Total"]).plot(kind="bar", figsize=(12, 6), width=0.8, color=["#4C72B0", "#DD8452"], edgecolor="black")
ax.set_title(f"Quantidade de casos {primary_col} = 1 por região e sexo (idade 25 a 59)")
ax.set_ylabel("Quantidade")
ax.set_xlabel("Regiões")
ax.legend(title="Sexo")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
output_path = base_dir / f"grafico_{primary_col}_regiao_sexo.{out_type}"
plt.savefig(output_path, dpi=300, bbox_inches="tight")
print(f"Gráfico por região salvo em: {output_path}")
plt.show()

taxa_estado = relatorio[["Taxa_relativa_Total"]].copy()
taxa_estado.columns = ["Taxa Relativa"]
taxa_estado = taxa_estado.sort_values("Taxa Relativa", ascending=True)
taxa_estado["Taxa Relativa"] = taxa_estado["Taxa Relativa"] * 100
ax = taxa_estado.plot(kind="barh", figsize=(12, 8), width=0.7, color=["#2ecc71"], edgecolor="black", legend=False)
ax.set_title(f"Taxa relativa (%) de {primary_col} = 1 por estado (idade 25 a 59)")
ax.set_xlabel("Taxa Relativa (%)")
ax.set_ylabel("Estados")
plt.tight_layout()
output_path = base_dir / f"grafico_{primary_col}_taxa_relativa_estado.{out_type}"
plt.savefig(output_path, dpi=300, bbox_inches="tight")
print(f"\nGráfico de taxa relativa por estado salvo em: {output_path}")
plt.show()

taxa_regiao = relatorio_regiao[["Taxa_relativa_Total"]].copy()
taxa_regiao.columns = ["Taxa Relativa"]
taxa_regiao = taxa_regiao.sort_values("Taxa Relativa", ascending=True)
taxa_regiao["Taxa Relativa"] = taxa_regiao["Taxa Relativa"] * 100
ax = taxa_regiao.plot(kind="barh", figsize=(10, 6), width=0.7, color=["#3498db"], edgecolor="black", legend=False)
ax.set_title(f"Taxa relativa (%) de {primary_col} = 1 por região (idade 25 a 59)")
ax.set_xlabel("Taxa Relativa (%)")
ax.set_ylabel("Regiões")
plt.tight_layout()
output_path = base_dir / f"grafico_{primary_col}_taxa_relativa_regiao.{out_type}"
plt.savefig(output_path, dpi=300, bbox_inches="tight")
print(f"Gráfico de taxa relativa por região salvo em: {output_path}")
plt.show()
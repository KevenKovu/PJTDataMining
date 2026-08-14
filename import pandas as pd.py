import pandas as pd
import matplotlib.pyplot as plt

# Caminho do arquivo CSV
caminho = "pns2019/pns2019.csv"

# Leitura automática do delimitador
df = pd.read_csv(caminho, sep=None, engine="python", encoding="latin1", low_memory=False)

# Ajuste os nomes das colunas conforme o seu CSV
# A PNS costuma usar:
# C006 = sexo (1 = homem, 2 = mulher)
# C008 = idade
# UF   = unidade federativa (ou outra coluna de estado)
state_col = "UF" if "UF" in df.columns else ("estado" if "estado" in df.columns else "V0001")
sex_col = "C006" if "C006" in df.columns else "sexo"
age_col = "C008" if "C008" in df.columns else "idade"

# Garante que as colunas estejam no tipo correto
df[age_col] = pd.to_numeric(df[age_col], errors="coerce")
df[sex_col] = pd.to_numeric(df[sex_col], errors="coerce")

# Filtro: idade entre 25 e 59 anos
df = df[df[age_col].between(25, 59, inclusive="both")].copy()

# Mantém apenas homens e mulheres
df = df[df[sex_col].isin([1, 2])].copy()

# Mapeia sexo para nomes legíveis
df["sexo_nome"] = df[sex_col].map({1: "Homens", 2: "Mulheres"})

# Se a coluna de estado tiver código numérico, transforma em texto e ordena
# Caso o seu CSV já tenha nomes dos estados, essa etapa pode ser ignorada
if pd.api.types.is_numeric_dtype(df[state_col]):
    # Exemplo de mapeamento de UF para nome do estado
    # Ajuste se necessário para os códigos da sua base
    uf_map = {
        11: "RO", 12: "AC", 13: "AM", 14: "RR", 15: "PA", 16: "AP", 17: "TO",
        21: "MA", 22: "PI", 23: "CE", 24: "RN", 25: "PB", 26: "PE", 27: "AL", 28: "SE", 29: "BA",
        31: "MG", 32: "ES", 33: "RJ", 35: "SP",
        41: "PR", 42: "SC", 43: "RS",
        50: "MS", 51: "MT", 52: "GO", 53: "DF"
    }
    df[state_col] = df[state_col].map(uf_map).fillna(df[state_col].astype(str))

# Tabela cruzada: quantidade por estado e sexo
tabela = (
    df.groupby([state_col, "sexo_nome"])
      .size()
      .unstack(fill_value=0)
      .reindex(columns=["Homens", "Mulheres"], fill_value=0)
)

# Ordena os estados em ordem crescente pela quantidade total
tabela = tabela.loc[tabela.sum(axis=1).sort_values().index]

# Plot
ax = tabela.plot(
    kind="bar",
    figsize=(14, 8),
    width=0.8,
    color=["#4C72B0", "#DD8452"]
)

plt.title("Quantidade de pessoas de 25 a 59 anos por estado e sexo")
plt.ylabel("Quantidade")
plt.xlabel("Estados")
plt.xticks(rotation=45, ha="right")
plt.legend(title="Sexo")
plt.tight_layout()
plt.show()
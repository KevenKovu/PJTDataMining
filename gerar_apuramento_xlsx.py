# -*- coding: utf-8 -*-
"""
Transformações no CSV filtrado de colesterol (PNS 2019, 25 a 59 anos).

Gera um novo CSV, preservando o arquivo original, com:
1) Filtro de renda per capita: VDF003 < R$ 3.500,00
2) QTD_COMORBIDADES
3) CONSUMO_ALCOOL
4) REGIAO
5) Remoção das colunas W00101 e W00201
"""

import sys
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# 0) CONFIGURAÇÃO
# ---------------------------------------------------------------------------

NOME_CSV = "pns_colesterol_25_59_v3.csv"
NOME_CSV_SAIDA = "pns_colesterol_25_59_v4.csv"

# --- 1) Filtro de renda per capita ---
COLUNA_RENDA_PER_CAPITA = "VDF003"
LIMITE_RENDA_PER_CAPITA = 3500.0

# --- 2) Comorbidades ---
# Q060 (colesterol alto) não entra na contagem, pois define a amostra.
COLUNAS_COMORBIDADES = [
    "Q00201",  # Hipertensão arterial
    "Q03001",  # Diabetes
    "Q06306",  # Doença do coração
    "Q068",    # AVC
    "Q074",    # Asma
    "Q079",    # Artrite/reumatismo
    "Q084",    # Problema crônico de coluna
    "Q092",    # Depressão
    "Q11604",  # Doença pulmonar crônica
    "Q124",    # Insuficiência renal crônica
    "Q120",    # Câncer
]

NOME_COL_COMORBIDADES = "QTD_COMORBIDADES"

# True: respostas ausentes contam como ausência de comorbidade.
# False: se houver resposta ausente, a contagem fica vazia.
AUSENTE_COMO_NAO = True

# --- 3) Álcool ---
COLUNAS_ALCOOL = ["P027", "P02801", "P029", "P03201", "P03202"]
NOME_COL_ALCOOL = "CONSUMO_ALCOOL"

DIAS_SEMANA_PARA_SEMPRE = 1

ROTULO_NUNCA = "Nunca"
ROTULO_AS_VEZES = "Às vezes"
ROTULO_SEMPRE = "Sempre"

# --- 4) Região ---
COLUNA_UF = "V0001"
NOME_COL_REGIAO = "REGIAO"

REGIOES_POR_UF = {
    "Norte": [
        "Rondônia", "Acre", "Amazonas", "Roraima",
        "Pará", "Amapá", "Tocantins"
    ],
    "Nordeste": [
        "Maranhão", "Piauí", "Ceará", "Rio Grande do Norte",
        "Paraíba", "Pernambuco", "Alagoas", "Sergipe", "Bahia"
    ],
    "Sudeste": [
        "Minas Gerais", "Espírito Santo",
        "Rio de Janeiro", "São Paulo"
    ],
    "Sul": [
        "Paraná", "Santa Catarina", "Rio Grande do Sul"
    ],
    "Centro-Oeste": [
        "Mato Grosso do Sul", "Mato Grosso",
        "Goiás", "Distrito Federal"
    ],
}

# Códigos numéricos das UFs: 11 a 17, 21 a 29 etc.
REGIAO_POR_PRIMEIRO_DIGITO = {
    1: "Norte",
    2: "Nordeste",
    3: "Sudeste",
    4: "Sul",
    5: "Centro-Oeste",
}

# --- 5) Colunas a remover ---
COLUNAS_REMOVER = ["W00101", "W00201"]


try:
    PASTA = Path(__file__).resolve().parent
except NameError:
    PASTA = Path.cwd()


# ---------------------------------------------------------------------------
# 1) LEITURA DO CSV
# ---------------------------------------------------------------------------

def localizar_csv():
    if len(sys.argv) > 1:
        caminho = Path(sys.argv[1])

        if caminho.exists():
            return caminho

        raise SystemExit(f"Arquivo não encontrado: {caminho}")

    for pasta in (PASTA, Path.cwd()):
        for nome in (NOME_CSV, "pnscolesterol2559v3.csv"):
            if (pasta / nome).exists():
                return pasta / nome

        achados = [
            p for p in sorted(pasta.glob("*colesterol*.csv"))
            if p.name != NOME_CSV_SAIDA
            and "tratado" not in p.name.lower()
            and "_novo" not in p.stem.lower()
        ]

        if achados:
            return achados[0]

    csvs = [p.name for p in PASTA.glob("*.csv")]

    raise SystemExit(
        f"CSV '{NOME_CSV}' não encontrado em:\n{PASTA}\n"
        f"CSVs nessa pasta: {csvs or 'nenhum'}"
    )


def ler_csv(caminho):
    with open(caminho, "r", encoding="utf-8-sig", errors="ignore") as f:
        primeira = f.readline()

    separador = ";" if primeira.count(";") > primeira.count(",") else ","

    for encoding in ("utf-8-sig", "latin1"):
        try:
            df = pd.read_csv(
                caminho,
                sep=separador,
                encoding=encoding,
                low_memory=False
            )
            return df, separador
        except UnicodeDecodeError:
            continue

    raise SystemExit("Não foi possível ler o CSV: encoding desconhecido.")


# ---------------------------------------------------------------------------
# 2) FUNÇÕES AUXILIARES
# ---------------------------------------------------------------------------

def _norm(x):
    """Normaliza texto, removendo acentos e espaços nas pontas."""

    if pd.isna(x):
        return np.nan

    return (
        unicodedata.normalize("NFKD", str(x))
        .encode("ascii", "ignore")
        .decode()
        .strip()
        .lower()
    )


def _eh_sim(serie):
    """Identifica respostas afirmativas, aceitando texto ou código 1."""

    if pd.api.types.is_numeric_dtype(serie):
        return serie == 1

    return serie.map(_norm) == "sim"


def _substituir(df, remover, nome_novo, valores):
    """Remove colunas antigas e insere uma nova na posição da primeira."""

    remover = [c for c in remover if c in df.columns]

    if nome_novo in df.columns and nome_novo not in remover:
        df = df.drop(columns=[nome_novo])

    pos = (
        min(df.columns.get_loc(c) for c in remover)
        if remover else len(df.columns)
    )

    df = df.drop(columns=remover)
    df.insert(pos, nome_novo, valores)

    return df, remover


def converter_renda_numerica(serie):
    """
    Converte renda em número.
    Aceita números, decimais com vírgula e valores no formato brasileiro,
    como '3.500,50'.
    """

    def converter(valor):
        if pd.isna(valor):
            return np.nan

        texto = str(valor).strip()
        texto = texto.replace("R$", "").replace(" ", "")

        if texto == "":
            return np.nan

        # Se houver vírgula, interpreta o formato brasileiro:
        # ponto como separador de milhar e vírgula como decimal.
        if "," in texto:
            texto = texto.replace(".", "")
            texto = texto.replace(",", ".")

        try:
            return float(texto)
        except ValueError:
            return np.nan

    return serie.map(converter)


# ---------------------------------------------------------------------------
# 3) TRANSFORMAÇÕES
# ---------------------------------------------------------------------------

def contar_comorbidades(df):
    cols = [c for c in COLUNAS_COMORBIDADES if c in df.columns]

    if not cols:
        return pd.Series(pd.NA, index=df.index, dtype="Int64")

    qtd = pd.concat(
        [_eh_sim(df[c]) for c in cols],
        axis=1
    ).sum(axis=1)

    ausentes = df[cols].isna().sum(axis=1)

    print(f"   Colunas contadas ({len(cols)}): {cols}")
    print(
        "   Pessoas com pelo menos uma resposta ausente: "
        f"{int((ausentes > 0).sum())}"
    )

    if not AUSENTE_COMO_NAO:
        qtd = qtd.where(ausentes == 0)

    return qtd.astype("Int64")


def classificar_alcool(df):
    freq = df["P027"]

    if "P02801" in df.columns:
        dias = pd.to_numeric(df["P02801"], errors="coerce")
    else:
        dias = pd.Series(np.nan, index=df.index)

    if pd.api.types.is_numeric_dtype(freq):
        freq_n = freq.map({
            1: "nao bebo nunca",
            2: "menos de uma vez por mes",
            3: "uma vez ou mais por mes",
        })
    else:
        freq_n = freq.map(_norm)

    nunca = freq_n == "nao bebo nunca"
    menos_mes = freq_n == "menos de uma vez por mes"
    mes_ou_mais = freq_n == "uma vez ou mais por mes"

    sempre = mes_ou_mais & (dias >= DIAS_SEMANA_PARA_SEMPRE)

    as_vezes = menos_mes | (
        mes_ou_mais & (dias < DIAS_SEMANA_PARA_SEMPRE)
    )

    resultado = np.select(
        [nunca, as_vezes, sempre],
        [ROTULO_NUNCA, ROTULO_AS_VEZES, ROTULO_SEMPRE],
        default=""
    )

    resultado = pd.Series(resultado, index=df.index, dtype=object)

    indeterminados = int((resultado == "").sum())

    if indeterminados:
        print(
            "   [AVISO] "
            f"{indeterminados} pessoa(s) sem informação suficiente "
            "ficaram sem classificação de álcool."
        )

    return resultado.where(resultado != "", np.nan)


def mapear_regiao(df):
    uf = df[COLUNA_UF]

    if pd.api.types.is_numeric_dtype(uf):
        regiao = (uf // 10).map(REGIAO_POR_PRIMEIRO_DIGITO)
    else:
        mapa = {
            _norm(estado): regiao
            for regiao, estados in REGIOES_POR_UF.items()
            for estado in estados
        }

        regiao = uf.map(_norm).map(mapa)

    nao_mapeadas = regiao.isna() & uf.notna()

    if nao_mapeadas.any():
        valores = sorted(uf[nao_mapeadas].astype(str).unique())

        print(
            "   [AVISO] UF não reconhecida: "
            f"{valores}"
        )

    return regiao


# ---------------------------------------------------------------------------
# 4) EXECUÇÃO
# ---------------------------------------------------------------------------

def main():
    caminho = localizar_csv()
    df, separador = ler_csv(caminho)

    print(f"Lendo: {caminho}")
    print(
        f"Antes: {df.shape[0]} registros x "
        f"{df.shape[1]} colunas\n"
    )

    n_colunas_antes = df.shape[1]

    # -----------------------------------------------------------------------
    # 1) FILTRO DE RENDA PER CAPITA
    # -----------------------------------------------------------------------

    print("1) Filtro de renda per capita")

    if COLUNA_RENDA_PER_CAPITA not in df.columns:
        raise SystemExit(
            f"A coluna '{COLUNA_RENDA_PER_CAPITA}' não foi encontrada "
            "no CSV.\n"
            f"Colunas disponíveis: {list(df.columns)}"
        )

    renda = converter_renda_numerica(df[COLUNA_RENDA_PER_CAPITA])

    n_antes_filtro = len(df)

    # Mantém somente rendas estritamente inferiores a R$ 3.500,00.
    # Registros com renda ausente ou inválida também são excluídos.
    df = df.loc[
        renda.notna() & (renda < LIMITE_RENDA_PER_CAPITA)
    ].copy()

    removidos = n_antes_filtro - len(df)

    print(f"   Variável utilizada: {COLUNA_RENDA_PER_CAPITA}")
    print(f"   Limite: abaixo de R$ {LIMITE_RENDA_PER_CAPITA:.2f}")
    print(f"   Registros antes do filtro: {n_antes_filtro}")
    print(f"   Registros removidos: {removidos}")
    print(f"   Registros mantidos: {len(df)}")

    # -----------------------------------------------------------------------
    # 2) COMORBIDADES
    # -----------------------------------------------------------------------

    if any(c in df.columns for c in COLUNAS_COMORBIDADES):
        print("\n2) Comorbidades")

        qtd = contar_comorbidades(df)

        df, removidas = _substituir(
            df,
            COLUNAS_COMORBIDADES,
            NOME_COL_COMORBIDADES,
            qtd
        )

        print(f"   Colunas removidas: {removidas}")
        print(f"   Distribuição de {NOME_COL_COMORBIDADES}:")

        print(
            df[NOME_COL_COMORBIDADES]
            .value_counts(dropna=False)
            .sort_index()
            .to_string()
        )
    else:
        print("\n2) Comorbidades: nenhuma coluna encontrada; etapa pulada.")

    # -----------------------------------------------------------------------
    # 3) CONSUMO DE ÁLCOOL
    # -----------------------------------------------------------------------

    if "P027" in df.columns:
        print("\n3) Consumo de álcool")

        alcool = classificar_alcool(df)

        df, removidas = _substituir(
            df,
            COLUNAS_ALCOOL,
            NOME_COL_ALCOOL,
            alcool
        )

        print(f"   Colunas removidas: {removidas}")
        print(f"   Distribuição de {NOME_COL_ALCOOL}:")

        print(
            df[NOME_COL_ALCOOL]
            .value_counts(dropna=False)
            .to_string()
        )
    else:
        print("\n3) Álcool: coluna P027 não encontrada; etapa pulada.")

    # -----------------------------------------------------------------------
    # 4) REGIÃO
    # -----------------------------------------------------------------------

    if COLUNA_UF in df.columns:
        print("\n4) Região")

        regiao = mapear_regiao(df)

        df, removidas = _substituir(
            df,
            [COLUNA_UF],
            NOME_COL_REGIAO,
            regiao
        )

        print(f"   Coluna removida: {removidas}")
        print(f"   Distribuição de {NOME_COL_REGIAO}:")

        print(
            df[NOME_COL_REGIAO]
            .value_counts(dropna=False)
            .to_string()
        )
    else:
        print(
            f"\n4) Região: coluna {COLUNA_UF} não encontrada; "
            "etapa pulada."
        )

    # -----------------------------------------------------------------------
    # 5) REMOÇÃO DE PESO E ALTURA
    # -----------------------------------------------------------------------

    a_remover = [
        c for c in COLUNAS_REMOVER
        if c in df.columns
    ]

    print(
        "\n5) Colunas retiradas: "
        f"{a_remover or 'nenhuma (já não existiam)'}"
    )

    df = df.drop(columns=a_remover)

    # -----------------------------------------------------------------------
    # 6) SALVAMENTO
    # -----------------------------------------------------------------------

    destino = caminho.with_name(NOME_CSV_SAIDA)

    # Nunca sobrescreve o CSV original.
    if destino.resolve() == caminho.resolve():
        destino = caminho.with_name(
            caminho.stem + "_novo.csv"
        )

    try:
        df.to_csv(
            destino,
            index=False,
            sep=separador,
            encoding="utf-8-sig"
        )
    except PermissionError:
        destino = destino.with_name(
            destino.stem + "_novo.csv"
        )

        df.to_csv(
            destino,
            index=False,
            sep=separador,
            encoding="utf-8-sig"
        )

    print("\n" + "=" * 60)
    print("PROCESSAMENTO CONCLUÍDO")
    print("=" * 60)

    print(f"Registros finais: {df.shape[0]}")
    print(f"Colunas finais: {df.shape[1]}")
    print(
        f"Variação no número de colunas: "
        f"{df.shape[1] - n_colunas_antes:+d}"
    )
    print(f"Arquivo salvo em: {destino}")


if __name__ == "__main__":
    main()
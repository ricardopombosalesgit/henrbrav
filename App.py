import streamlit as st
import pandas as pd

# Função para mapear as siglas para os grupos de posições
def agrupar_posicoes_em_portugues():
    return {
        'Goleiros': ['GK'],
        'Laterais': ['LD', 'RD'],
        'Zagueiros': ['CD', 'LCD', 'RCD'],
        'Volantes/Meio defensivos': ['CDM', 'RCDM', 'LCDM', 'LDM', 'RDM'],
        'Meio-Atacantes': ['CAM'],
        'Extremos/Pontas': ['LM', 'RM', 'LCF', 'RCF', 'LAM', 'RAM', 'LM', 'RM'],
        'Atacantes': ['CF']
    }

def calcular_pontuacao(df, posicoes, tier1_cols, tier2_cols, tier3_cols, tier_weights, min_minutos, max_idade):

    # Converter a coluna de idade para numérico, forçando erros a serem NaN
    df['Age'] = pd.to_numeric(df['Age'], errors='coerce')

    # Filtrar jogadores pela posição, minutos jogados e idade
    df_filtered = df[df['Position'].isin(posicoes) & 
                     (df['Minutes played'] >= min_minutos) & 
                     (df['Age'] <= max_idade)].copy()

    if df_filtered.empty:
        st.warning("Nenhum jogador encontrado para as condições especificadas.")
        return pd.DataFrame()  # Retorna um DataFrame vazio se não houver jogadores

    # Verificar se as colunas dos tiers estão no DataFrame antes de calcular
    all_tiers_cols = tier1_cols + tier2_cols + tier3_cols
    missing_cols = [col for col in all_tiers_cols if col not in df_filtered.columns]

    if missing_cols:
        st.error(f"As seguintes métricas estão faltando no arquivo: {missing_cols}")
        return pd.DataFrame()  # Retorna um DataFrame vazio se faltar colunas

    # Converter colunas não numéricas para numéricas
    for col in tier1_cols + tier2_cols + tier3_cols:
        if col in df_filtered.columns:
            df_filtered[col] = df_filtered[col].astype(str).str.replace('-', '0').str.replace('%', '')
            df_filtered[col] = pd.to_numeric(df_filtered[col])

    # Normalizar as métricas na escala de 0 a 10
    for col in tier1_cols + tier2_cols + tier3_cols:
        if col in df_filtered.columns:
            mean_value = df_filtered[col].mean()
            if mean_value != 0:  # Evitar divisão por zero
                df_filtered[col + '_norm'] = (df_filtered[col] / mean_value) * 10
            else:
                df_filtered[col + '_norm'] = 0 

    # Calcular a pontuação de cada tier
    df_filtered['Tier 1'] = df_filtered[[col + '_norm' for col in tier1_cols if col in df_filtered.columns]].mean(axis=1)
    df_filtered['Tier 2'] = df_filtered[[col + '_norm' for col in tier2_cols if col in df_filtered.columns]].mean(axis=1)
    df_filtered['Tier 3'] = df_filtered[[col + '_norm' for col in tier3_cols if col in df_filtered.columns]].mean(axis=1)

    # Calcular a pontuação final
    df_filtered['Pontuação Final'] = (
        tier_weights['Tier 1'] * df_filtered['Tier 1'] +
        tier_weights['Tier 2'] * df_filtered['Tier 2'] +
        tier_weights['Tier 3'] * df_filtered['Tier 3']
    )

    return df_filtered

# Função para definir os tiers com base no grupo de posições escolhido
def definir_tiers_por_grupo(grupo_escolhido):
    if grupo_escolhido == 'Goleiros':
        tier1_cols = ['Goals Conceded', 'Saves', 'Clean sheets']
        tier2_cols = ['Passes', 'Passes accurate, %', 'Long Passes', 'Long Passes Completed']
        tier3_cols = ['Crosses', 'Crosses won', 'Goal Kicks', 'Tackles successful']
        
    elif grupo_escolhido == 'Laterais':
        # Ajustando as métricas com base nas colunas existentes
        tier1_cols = ['Tackles successful', 'Crosses', 'Dribbles successful']
        tier2_cols = ['Passes', 'Passes accurate, %', 'Key passes']
        tier3_cols = ['Interceptions', 'Challenges', 'Challenges won']
        
    elif grupo_escolhido == 'Zagueiros':
        # Ajustando as métricas para Zagueiros com base nas colunas existentes
        tier1_cols = ['Tackles successful', 'Interceptions']
        tier2_cols = ['Passes', 'Passes accurate, %']
        tier3_cols = ['Challenges', 'Challenges won']
        
    elif grupo_escolhido == 'Volantes/Meio defensivos':
        tier1_cols = ['Passes', 'Passes accurate, %', 'Tackles successful', 'Interceptions']
        tier2_cols = ['Key passes', 'Dribbles', 'Dribbles successful']
        tier3_cols = ['Challenges', 'Challenges won']

    elif grupo_escolhido == 'Meio-Atacantes':
        # Substituindo as métricas ausentes por colunas existentes
        tier1_cols = ['Key passes', 'Dribbles successful', 'Shots on target']
        tier2_cols = ['Assists', 'Chances created', 'Shots']
        tier3_cols = ['Tackles successful', 'Interceptions']
        
    elif grupo_escolhido == 'Extremos/Pontas':
        tier1_cols = ['Key passes', 'Crosses', 'Dribbles successful']
        tier2_cols = ['Shots', 'Shots on target', 'Assists']
        tier3_cols = ['Tackles successful', 'Interceptions']
        
    elif grupo_escolhido == 'Atacantes':
        tier1_cols = ['Goals', 'xG per shot', 'Shots on target']
        tier2_cols = ['Assists', 'Chances created', 'Key passes']
        tier3_cols = ['Passes', 'Passes into the penalty box', 'xG conversion']
    
    return tier1_cols, tier2_cols, tier3_cols

# Pesos dos tiers
tier_weights = {'Tier 1': 0.6, 'Tier 2': 0.3, 'Tier 3': 0.1}

# --- Interface do Streamlit ---

st.title('Formulário de Avaliação de Jogadores')

# Upload do arquivo de dados
uploaded_file = st.file_uploader("Escolha um arquivo de dados", type=["xlsx", "csv"])

if uploaded_file is not None:
    # Verificar o tipo de arquivo e usar o método de leitura correto
    if uploaded_file.name.endswith('.csv'):
        try:
            df = pd.read_csv(uploaded_file, encoding='latin1')  # ou 'ISO-8859-1'
        except UnicodeDecodeError:
            st.error('Erro de codificação ao carregar o arquivo CSV. Verifique a codificação.')
    elif uploaded_file.name.endswith('.xlsx'):
        df = pd.read_excel(uploaded_file)
    else:
        st.error('Formato de arquivo não suportado. Por favor, faça upload de um arquivo CSV ou XLSX.')

    if 'df' in locals():

        # Obter as posições agrupadas em português
        grupos_posicoes = agrupar_posicoes_em_portugues()

        # Exibir o filtro de posições agrupadas
        grupo_escolhido = st.selectbox('Selecione o grupo de posições:', list(grupos_posicoes.keys()))
        posicoes_selecionadas = grupos_posicoes[grupo_escolhido]

        # Filtros
        min_minutos = st.number_input('Minutos jogados mínimos:', min_value=0, value=200)
        max_idade = st.number_input('Idade máxima:', min_value=0, value=40)

        # Definir os Tiers de acordo com o grupo de posições escolhido
        tier1_cols, tier2_cols, tier3_cols = definir_tiers_por_grupo(grupo_escolhido)

        # Calcular a pontuação
        resultados = calcular_pontuacao(df, posicoes_selecionadas, tier1_cols, tier2_cols, tier3_cols, tier_weights, min_minutos, max_idade)

        # Exibir os resultados
        if not resultados.empty:
            st.write(resultados[['Player', 'Team', 'Age', 'Minutes played', 'Pontuação Final']].sort_values('Pontuação Final', ascending=False))
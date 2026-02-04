import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt

#configuração página
st.set_page_config(
    page_title='Dashboard de correlação de testemunhos',
    page_icon='🐵',
    layout='wide',
)

#carregando dados
df = pd.read_csv('https://raw.githubusercontent.com/tito-br/Lapas-nano/refs/heads/main/dados_kf_16_18_nano.csv')



#padronizar nomes para minúsculo
df.columns = df.columns.str.lower().str.strip()


#Barra Lateral (Filtros)
st.sidebar.header('🔍 Filtros')

#Filtro de Testemunho
testemunhos_disponiveis = sorted(df['testemunho'].dropna().astype(str).unique())
testemunhos_selecionados = st.sidebar.multiselect('selecione o testemunho', testemunhos_disponiveis, default=testemunhos_disponiveis)

## filtar DataFrame pelos testemunhos selecionados
df_filtrado = df[df['testemunho'].astype(str).isin(testemunhos_selecionados)]


#filtro amostra
amostras_disponiveis = sorted(df_filtrado['amostra'].dropna().unique())
if amostras_disponiveis:
    min_val = int(min(amostras_disponiveis))
    max_val = int(max(amostras_disponiveis))
    
    intervalo_selecionado = st.sidebar.slider(
        'Selecione o intervalo de amostras (cm)',
        min_value=min_val,
        max_value=max_val,
        value=(min_val, max_val), 
        step=1
    )

    # O df_final PRECISA estar indentado (com espaços) para estar dentro do IF
    df_final = df_filtrado[
        (df_filtrado['amostra'] >= intervalo_selecionado[0]) & 
        (df_filtrado['amostra'] <= intervalo_selecionado[1])
    ]
else:
    # Caso a lista esteja vazia, o df_final será apenas o df_filtrado vazio
    df_final = df_filtrado
    st.sidebar.warning("Nenhuma amostra encontrada para os filtros selecionados.")
#filtro especie
todas_colunas_especies = df.columns[2:].tolist()

especies_disponiveis = [
    esp for esp in todas_colunas_especies 
    if df_filtrado[esp].sum() > 0
]

especies_selecionadas = st.sidebar.multiselect(
    "Selecione as Espécies", 
    especies_disponiveis, 
    default=especies_disponiveis[:3] if len(especies_disponiveis) >= 3 else especies_disponiveis
)

#divisor
st.sidebar.divider()

# --- FILTROS QUE AFETAM APENAS A VISUALIZAÇÃO DO GRÁFICO ---
st.sidebar.header('📊 Ajustes do Gráfico')

especies_grafico = st.sidebar.multiselect(
    "Espécies para exibir no Gráfico", 
    especies_disponiveis, 
    default=especies_disponiveis[:3]
)

especies_horizontes = st.sidebar.multiselect(
    "Desenhar linhas de FAD/LAD", 
    especies_disponiveis
)

# Filtro final que une Testemunho + Amostras selecionadas


## Conteúdo principal - KPI
st.title('Dashboard das espécies de Nanofósseis dos testemunhos KF-16 e KF-18')
st.markdown('Explore dados das espécies presentes nos testemunhos. Utilize os filtros à esquerda')

# --- Métricas Principais (KPIs) ---
st.subheader("📊 Visão Geral do Intervalo Selecionado")

if not df_final.empty:
    #lista filtrada só para a contagem da métrica
    #espécies disponíveis, ignora quem tem 'total' ou 'pmp'
    so_especies = [
        esp for esp in especies_disponiveis 
        if 'total' not in esp.lower() and 'pmp' not in esp.lower()
    ]
    # 1. Total de espécies REAIS (sem contar as colunas de total/pmp)
    total_especies_reais = len([e for e in so_especies if df_final[e].sum() > 0])
    
    # 2. Intervalo de profundidade (máximo - mínimo)
    prof_min = df_final['amostra'].min()
    prof_max = df_final['amostra'].max()
    intervalo = prof_max - prof_min
    
    # 3. Total de amostras analisadas
    total_amostras = df_final.shape[0]
    
    # 4. Riqueza média (contar quantas colunas de espécies > 0 em cada linha e tirar a média)
    # df_filtrado[especies_no_filtro] > 0 cria uma tabela de True/False, .sum(axis=1) conta os Trues por linha
    riqueza_por_amostra = (df_final[so_especies] > 0).sum(axis=1).mean()

else:
    total_especies_reais, intervalo, total_amostras, riqueza_por_amostra = 0, 0, 0, 0

# Criando as colunas no Streamlit
col1, col2, col3, col4 = st.columns(4)

col1.metric("Espécies Encontradas", f"{total_especies_reais}")
col2.metric("Intervalo Analisado", f"{intervalo} cm")
col3.metric("Total de Amostras", f"{total_amostras}")
col4.metric("Riqueza Média/Amostra", f"{riqueza_por_amostra:.1f}")

st.markdown("---")

#definindo calcular_biomarcadores
def calcular_biomarcadores(df, especies):
    resumo = []
    # Usamos o df_final aqui para respeitar todos os filtros de amostras/testemunhos
    for esp in especies:
        for test in df['testemunho'].unique():
            # Filtra onde a espécie realmente ocorre (> 0)
            dados_esp = df[(df['testemunho'] == test) & (df[esp] > 0)]
            
            if not dados_esp.empty:
                # FAD = First Appearance Datum (Base/Maior profundidade)
                # LAD = Last Appearance Datum (Topo/Menor profundidade)
                fad = dados_esp['amostra'].max()
                lad = dados_esp['amostra'].min()
                resumo.append({'Espécie': esp, 'Testemunho': test, 'FAD': fad, 'LAD': lad})
    
    return pd.DataFrame(resumo)

##conteúdo principal - gráfico
if especies_grafico:
    df_long = df_final.melt(
        id_vars=['amostra', 'testemunho'], 
        value_vars=especies_grafico,
        var_name='espécie', 
        value_name='abundância'
    )

    # 1. Criamos o gráfico com marcadores e linhas (mode='lines+markers')
    fig = px.line(
        df_long, 
        x='abundância', 
        y='amostra', 
        color='testemunho',
        facet_col='espécie',
        markers=True, # Adiciona os pontos, como no seu exemplo
        labels={'amostra': 'Profundidade em cm', 'abundância': 'Abundância (%)'},
        # Ajustamos o template para 'simple_white' que é o mais próximo do matplotlib
        template='simple_white' 
    )

    # 2. Configurações de Tamanho (O segredo do visual vertical)
    # No matplotlib você usou (6, 10). No plotly, multiplicamos por ~80-100 para pixels.
    fig.update_layout(
        height=800,           # Gráfico alto
        width=400 * len(especies_grafico), # Largura proporcional ao número de colunas
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    # 3. Adicionar as Linhas Horizontais (Bio-horizontes)
    if especies_horizontes:
        df_marcos = calcular_biomarcadores(df_final, especies_horizontes)
        
        for _, linha in df_marcos.iterrows():
            # FAD (Vermelho)
            fig.add_hline(
                y=linha['FAD'], 
                line_dash="dash", 
                line_color="red", 
                line_width=1,
                opacity=0.6 # Alpha do matplotlib
            )
            # Adicionando o texto lateral (como o plt.text)
            fig.add_annotation(
                x=0, y=linha['FAD'],
                text=f"FAD {linha['Espécie']}",
                showarrow=False,
                xanchor='left',
                font=dict(color="red", size=10),
                xref="paper" # Faz o texto aparecer no início do gráfico
            )

    # 4. Inverter o eixo Y e limpar as grades (Grid)
    fig.update_yaxes(
        autorange="reversed", 
        showgrid=True, 
        gridcolor='lightgrey', 
        gridwidth=0.5
    )
    fig.update_xaxes(showgrid=False)

    st.plotly_chart(fig, use_container_width=False) # False para respeitar o width que definimos

    #gráficos matplotlib
    if especies_grafico:
        st.markdown("---")
        st.subheader("Versão Estática")

    # Definimos o número de colunas baseado nas espécies selecionadas
    num_specs = len(especies_grafico)
    
    # Criamos a figura: largura proporcional ao n° de espécies, altura fixa em 10
    fig_mpl, axes = plt.subplots(1, num_specs, figsize=(3 * num_specs, 10), sharey=True)

    # Se houver apenas uma espécie, o 'axes' não é uma lista, então ajustamos:
    if num_specs == 1:
        axes = [axes]

    # Pegamos os biomarcadores para as linhas FAD/LAD
    df_marcos = calcular_biomarcadores(df_final, especies_horizontes)

    for i, esp in enumerate(especies_grafico):
        ax = axes[i]
        
        # Plotamos cada testemunho com uma cor diferente
        for test in df_final['testemunho'].unique():
            dados_test = df_final[df_final['testemunho'] == test]
            ax.plot(dados_test[esp], dados_test['amostra'], label=test, marker='o', markersize=4)

        # Adicionamos as linhas de FAD/LAD (Horizontes)
        if not df_marcos.empty:
            for _, linha in df_marcos.iterrows():
                # FAD
                ax.hlines(linha['FAD'], xmin=0, xmax=df_final[esp].max(), 
                          colors='red', linestyles='dashed', alpha=0.5)
                ax.text(0, linha['FAD'], f"FAD {linha['Espécie']}", color='red', fontsize=8, va='bottom')
                
                # LAD
                ax.hlines(linha['LAD'], xmin=0, xmax=df_final[esp].max(), 
                          colors='blue', linestyles='dotted', alpha=0.5)
                ax.text(0, linha['LAD'], f"LAD {linha['Espécie']}", color='blue', fontsize=8, va='top')

        ax.set_title(esp)
        ax.set_xlabel('Abundância (%)')
        ax.invert_yaxis() # Inverte profundidade
        ax.grid(True, linestyle=':', alpha=0.6)

    # Nome do eixo Y apenas no primeiro gráfico para não poluir
    axes[0].set_ylabel('Profundidade (cm)')
    
    # Legenda única no topo
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05), ncol=2)
    plt.tight_layout()

    # Comando mágico do Streamlit para exibir Matplotlib
    st.pyplot(fig_mpl)

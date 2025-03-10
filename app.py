import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from datetime import datetime
import calendar
import numpy as np

# Configuração da página
st.set_page_config(page_title="App de Finanças Pessoais", layout="wide", initial_sidebar_state="expanded")

# Função para verificar se a planilha existe e criar se não existir
def verificar_criar_planilha():
    arquivo_excel = 'financas.xlsx'
    
    if not os.path.exists(arquivo_excel):
        # Criando DataFrame para transações
        df_transacoes = pd.DataFrame({
            'id': [],
            'data': [],
            'descricao': [],
            'valor': [],
            'categoria': [],
            'tipo': []  # 'entrada' ou 'saida'
        })
        
        # Criando DataFrame para categorias
        categorias_entradas = ['Salário', 'Investimentos', 'Freelance', 'Presente', 'Outros']
        categorias_saidas = ['Alimentação', 'Moradia', 'Transporte', 'Saúde', 'Educação', 
                           'Lazer', 'Vestuário', 'Contas', 'Compras', 'Outros']
        
        df_categorias = pd.DataFrame({
            'tipo': ['entrada'] * len(categorias_entradas) + ['saida'] * len(categorias_saidas),
            'categoria': categorias_entradas + categorias_saidas
        })
        
        # Salvando DataFrames em planilhas separadas
        with pd.ExcelWriter(arquivo_excel) as writer:
            df_transacoes.to_excel(writer, sheet_name='Transacoes', index=False)
            df_categorias.to_excel(writer, sheet_name='Categorias', index=False)
        
        st.success(f"Arquivo '{arquivo_excel}' criado com sucesso!")
    
    return arquivo_excel

# Carregar dados
@st.cache_data
def carregar_dados(arquivo):
    try:
        transacoes = pd.read_excel(arquivo, sheet_name='Transacoes')
        if not isinstance(transacoes, pd.DataFrame):
            transacoes = pd.DataFrame({
                'id': [],
                'data': [],
                'descricao': [],
                'valor': [],
                'categoria': [],
                'tipo': []
            })
        elif not transacoes.empty:
            # Adicionar coluna ID se não existir
            if 'id' not in transacoes.columns:
                transacoes['id'] = range(1, len(transacoes) + 1)
            transacoes['data'] = pd.to_datetime(transacoes['data'])
            
        categorias = pd.read_excel(arquivo, sheet_name='Categorias')
        if not isinstance(categorias, pd.DataFrame):
            categorias = pd.DataFrame({
                'tipo': [],
                'categoria': []
            })
            
        return transacoes, categorias
    except Exception as e:
        st.error(f"Erro ao carregar os dados: {e}")
        # Retornar DataFrames vazios em caso de erro
        return pd.DataFrame({
            'id': [],
            'data': [],
            'descricao': [],
            'valor': [],
            'categoria': [],
            'tipo': []
        }), pd.DataFrame({
            'tipo': [],
            'categoria': []
        })

# Salvar todos os dados
def salvar_dados(transacoes, categorias, arquivo):
    try:
        # Garantir que a coluna ID está presente e contígua
        if 'id' not in transacoes.columns:
            transacoes['id'] = range(1, len(transacoes) + 1)
        else:
            # Reindexar IDs para garantir que sejam contíguos
            transacoes = transacoes.reset_index(drop=True)
            transacoes['id'] = range(1, len(transacoes) + 1)
        
        # Salvar de volta no arquivo
        with pd.ExcelWriter(arquivo) as writer:
            transacoes.to_excel(writer, sheet_name='Transacoes', index=False)
            categorias.to_excel(writer, sheet_name='Categorias', index=False)
            
        return True
    except Exception as e:
        st.error(f"Erro ao salvar os dados: {e}")
        return False

# Adicionar nova transação
def adicionar_transacao(nova_transacao, arquivo):
    try:
        transacoes, categorias = carregar_dados(arquivo)
        
        # Converter para o formato correto se necessário
        nova_transacao['data'] = pd.to_datetime(nova_transacao['data'])
        nova_transacao['valor'] = float(nova_transacao['valor'])
        
        # Gerar ID para a nova transação
        if 'id' not in transacoes.columns or transacoes.empty:
            nova_transacao['id'] = 1
        else:
            nova_transacao['id'] = transacoes['id'].max() + 1
        
        # Adicionar nova transação
        nova_linha = pd.DataFrame([nova_transacao])
        transacoes = pd.concat([transacoes, nova_linha], ignore_index=True)
        
        if salvar_dados(transacoes, categorias, arquivo):
            st.success("Transação adicionada com sucesso!")
            return True
        return False
    except Exception as e:
        st.error(f"Erro ao adicionar a transação: {e}")
        return False

# Editar transação existente
def editar_transacao(id_transacao, transacao_atualizada, arquivo):
    try:
        transacoes, categorias = carregar_dados(arquivo)
        
        # Converter para o formato correto se necessário
        transacao_atualizada['data'] = pd.to_datetime(transacao_atualizada['data'])
        transacao_atualizada['valor'] = float(transacao_atualizada['valor'])
        transacao_atualizada['id'] = int(id_transacao)
        
        # Encontrar o índice da transação a ser atualizada
        indice = transacoes[transacoes['id'] == id_transacao].index
        
        if len(indice) == 0:
            st.error(f"Transação com ID {id_transacao} não encontrada.")
            return False
        
        # Atualizar transação
        transacoes.loc[indice[0]] = transacao_atualizada
        
        if salvar_dados(transacoes, categorias, arquivo):
            st.success("Transação atualizada com sucesso!")
            return True
        return False
    except Exception as e:
        st.error(f"Erro ao editar a transação: {e}")
        return False

# Excluir transação
def excluir_transacao(id_transacao, arquivo):
    try:
        transacoes, categorias = carregar_dados(arquivo)
        
        # Encontrar a transação a ser excluída
        if id_transacao not in transacoes['id'].values:
            st.error(f"Transação com ID {id_transacao} não encontrada.")
            return False
        
        # Excluir transação
        transacoes = transacoes[transacoes['id'] != id_transacao]
        
        if salvar_dados(transacoes, categorias, arquivo):
            st.success("Transação excluída com sucesso!")
            return True
        return False
    except Exception as e:
        st.error(f"Erro ao excluir a transação: {e}")
        return False

# Preparar gráficos e métricas
def preparar_dashboard(transacoes):
    # Garantir que transacoes seja um DataFrame
    if not isinstance(transacoes, pd.DataFrame):
        transacoes = pd.DataFrame({
            'id': [],
            'data': [],
            'descricao': [],
            'valor': [],
            'categoria': [],
            'tipo': []
        })
        
    # Inicializar variáveis com valores padrão
    fig_pizza = None
    fig_barras = None
    fig_linha = None
    ultimas_transacoes = pd.DataFrame()
    df_mes = pd.DataFrame()
    entradas_mes = 0.0
    saidas_mes = 0.0
    saldo_mes = 0.0
        
    if transacoes.empty:
        return fig_pizza, fig_barras, fig_linha, ultimas_transacoes, df_mes, entradas_mes, saidas_mes, saldo_mes
    
    # Converter coluna de data para datetime se não estiver
    transacoes['data'] = pd.to_datetime(transacoes['data'])
    
    # Filtrar para o mês atual
    mes_atual = datetime.now().month
    ano_atual = datetime.now().year
    df_mes = transacoes[(transacoes['data'].dt.month == mes_atual) & 
                        (transacoes['data'].dt.year == ano_atual)]
    
    # Calcular saldo
    entradas = transacoes[transacoes['tipo'] == 'entrada']['valor'].sum()
    saidas = transacoes[transacoes['tipo'] == 'saida']['valor'].sum()
    saldo = entradas - saidas
    
    # Calcular entradas e saídas do mês atual
    entradas_mes = df_mes[df_mes['tipo'] == 'entrada']['valor'].sum()
    saidas_mes = df_mes[df_mes['tipo'] == 'saida']['valor'].sum()
    saldo_mes = entradas_mes - saidas_mes
    
    # Gráfico de Pizza para categorias de despesas no mês atual
    despesas_no_mes = df_mes[df_mes['tipo'] == 'saida']
    if not despesas_no_mes.empty:
        despesas_por_categoria = despesas_no_mes.groupby('categoria')['valor'].sum().reset_index()
        fig_pizza = px.pie(despesas_por_categoria, values='valor', names='categoria', 
                          title='Despesas por Categoria (Mês Atual)')
    
    # Gráfico de Barras para entradas/saídas por mês
    transacoes['ano_mes'] = transacoes['data'].dt.strftime('%Y-%m')
    resumo_mensal = transacoes.groupby(['ano_mes', 'tipo'])['valor'].sum().unstack().reset_index()
    
    if not resumo_mensal.empty and all(col in resumo_mensal.columns for col in ['entrada', 'saida']):
        resumo_mensal.fillna(0, inplace=True)
        fig_barras = px.bar(resumo_mensal, x='ano_mes', y=['entrada', 'saida'], 
                           title='Entradas e Saídas por Mês',
                           labels={'value': 'Valor', 'ano_mes': 'Mês', 'variable': 'Tipo'},
                           barmode='group')
    
    # Evolução do saldo
    if not transacoes.empty:
        transacoes_ordenadas = transacoes.sort_values('data')
        transacoes_ordenadas['saldo_acumulado'] = transacoes_ordenadas.apply(
            lambda x: x['valor'] if x['tipo'] == 'entrada' else -x['valor'], axis=1).cumsum()
        
        fig_linha = px.line(transacoes_ordenadas, x='data', y='saldo_acumulado', 
                          title='Evolução do Saldo ao Longo do Tempo')
    
    # Últimas transações
    if not transacoes.empty:
        ultimas_transacoes = transacoes.sort_values('data', ascending=False).head(5)
    
    return fig_pizza, fig_barras, fig_linha, ultimas_transacoes, df_mes, entradas_mes, saidas_mes, saldo_mes

# Formulário para cadastro/edição de transação
def form_transacao(categorias, tipo_inicial=None, dados_iniciais=None):
    col1, col2 = st.columns(2)
    
    with col1:
        if dados_iniciais:
            tipo = st.radio("Tipo de Transação", ["entrada", "saida"], index=0 if dados_iniciais['tipo'] == 'entrada' else 1)
        else:
            tipo = tipo_inicial if tipo_inicial else st.radio("Tipo de Transação", ["entrada", "saida"])
        
        # Verificar se há categorias para o tipo selecionado
        categorias_filtradas = categorias[categorias['tipo'] == tipo]['categoria'].tolist()
        if not categorias_filtradas:
            # Se não houver categorias, adicionar categorias padrão
            if tipo == 'entrada':
                categorias_filtradas = ['Salário', 'Investimentos', 'Freelance', 'Presente', 'Outros']
            else:
                categorias_filtradas = ['Alimentação', 'Moradia', 'Transporte', 'Saúde', 'Educação', 
                                       'Lazer', 'Vestuário', 'Contas', 'Compras', 'Outros']
        
        if dados_iniciais:
            categoria_index = categorias_filtradas.index(dados_iniciais['categoria']) if dados_iniciais['categoria'] in categorias_filtradas else 0
            categoria = st.selectbox("Categoria", categorias_filtradas, index=categoria_index)
            data = st.date_input("Data", pd.to_datetime(dados_iniciais['data']))
        else:
            categoria = st.selectbox("Categoria", categorias_filtradas)
            data = st.date_input("Data", datetime.now())
    
    with col2:
        if dados_iniciais:
            descricao = st.text_input("Descrição", value=dados_iniciais['descricao'])
            valor = st.number_input("Valor (R$)", min_value=0.01, step=0.01, value=float(dados_iniciais['valor']))
        else:
            descricao = st.text_input("Descrição")
            valor = st.number_input("Valor (R$)", min_value=0.01, step=0.01)
        
        # Campo de sugestão inteligente (simulado)
        if descricao.lower().startswith("super") and not dados_iniciais:
            st.info("Sugestão: Essa parece ser uma compra de supermercado. Categoria recomendada: Alimentação")
        elif (descricao.lower().startswith("conta") or descricao.lower().startswith("fatura")) and not dados_iniciais:
            st.info("Sugestão: Essa parece ser uma conta. Categoria recomendada: Contas")
    
    return {
        'data': data,
        'descricao': descricao,
        'valor': valor,
        'categoria': categoria,
        'tipo': tipo
    }

# Função principal
def main():
    st.title("App de Finanças Pessoais")
    
    # Verificar/criar planilha
    arquivo_excel = verificar_criar_planilha()
    
    # Carregar dados
    transacoes, categorias = carregar_dados(arquivo_excel)
    
    # Barra lateral para navegação
    st.sidebar.title("Menu")
    opcao = st.sidebar.radio("Selecione uma opção", 
                            ["Dashboard", "Nova Transação", "Gerenciar Transações"])
    
    if opcao == "Dashboard":
        st.header("Dashboard Financeiro")
        
        # Preparar dados para o dashboard
        fig_pizza, fig_barras, fig_linha, ultimas_transacoes, df_mes, entradas_mes, saidas_mes, saldo_mes = preparar_dashboard(transacoes)
        
        # Exibir métricas
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Entradas (Mês Atual)", f"R$ {entradas_mes:.2f}")
        with col2:
            st.metric("Saídas (Mês Atual)", f"R$ {saidas_mes:.2f}")
        with col3:
            st.metric("Saldo (Mês Atual)", f"R$ {saldo_mes:.2f}", 
                     delta=f"R$ {saldo_mes:.2f}")
        
        # Exibir gráficos
        if fig_pizza:
            st.plotly_chart(fig_pizza, use_container_width=True)
        else:
            st.info("Não há dados de despesas para o mês atual.")
        
        col1, col2 = st.columns(2)
        with col1:
            if fig_barras:
                st.plotly_chart(fig_barras, use_container_width=True)
            else:
                st.info("Dados insuficientes para gráfico de barras.")
        
        with col2:
            if fig_linha:
                st.plotly_chart(fig_linha, use_container_width=True)
            else:
                st.info("Dados insuficientes para gráfico de linha.")
        
        # Últimas transações
        st.subheader("Últimas Transações")
        if not ultimas_transacoes.empty:
            ultimas_transacoes_formatadas = ultimas_transacoes.copy()
            ultimas_transacoes_formatadas['data'] = ultimas_transacoes_formatadas['data'].dt.strftime('%d/%m/%Y')
            ultimas_transacoes_formatadas['valor'] = ultimas_transacoes_formatadas['valor'].apply(lambda x: f"R$ {x:.2f}")
            st.dataframe(ultimas_transacoes_formatadas[['data', 'descricao', 'categoria', 'tipo', 'valor']], use_container_width=True)
        else:
            st.info("Não há transações registradas.")
    
    elif opcao == "Nova Transação":
        st.header("Registrar Nova Transação")
        
        # Formulário de transação
        nova_transacao = form_transacao(categorias)
        
        if st.button("Salvar Transação"):
            if nova_transacao['descricao'] and nova_transacao['valor'] > 0:
                if adicionar_transacao(nova_transacao, arquivo_excel):
                    # Atualiza os dados após adicionar uma nova transação
                    st.cache_data.clear()
                    st.rerun()
            else:
                st.warning("Preencha todos os campos corretamente.")
    
    elif opcao == "Gerenciar Transações":
        st.header("Gerenciar Transações")
        
        if transacoes.empty:
            st.info("Não há transações registradas.")
            return
        
        # Abas para visualizar/editar/excluir
        tab1, tab2 = st.tabs(["Visualizar e Editar", "Excluir"])
        
        with tab1:
            st.subheader("Visualizar e Editar Transações")
            
            # Filtros
            col1, col2, col3 = st.columns(3)
            with col1:
                meses = list(range(1, 13))
                mes_selecionado = st.selectbox("Mês", meses, index=datetime.now().month-1, key="mes_visualizar")
            with col2:
                anos = list(range(2020, 2026))
                ano_selecionado = st.selectbox("Ano", anos, index=anos.index(datetime.now().year) if datetime.now().year in anos else 0, key="ano_visualizar")
            with col3:
                tipo_filtro = st.selectbox("Tipo", ["Todos", "entrada", "saida"], key="tipo_visualizar")
            
            # Aplicar filtros
            filtro_transacoes = transacoes.copy()
            
            # Filtrar por mês e ano
            filtro_transacoes = filtro_transacoes[
                (filtro_transacoes['data'].dt.month == mes_selecionado) & 
                (filtro_transacoes['data'].dt.year == ano_selecionado)
            ]
            
            # Filtrar por tipo
            if tipo_filtro != "Todos":
                filtro_transacoes = filtro_transacoes[filtro_transacoes['tipo'] == tipo_filtro]
            
            # Exibir resultados com opção de editar
            if not filtro_transacoes.empty:
                # Formatar para exibição
                filtro_transacoes_formatadas = filtro_transacoes.copy()
                filtro_transacoes_formatadas['data'] = filtro_transacoes_formatadas['data'].dt.strftime('%d/%m/%Y')
                filtro_transacoes_formatadas['valor'] = filtro_transacoes_formatadas['valor'].apply(lambda x: f"R$ {x:.2f}")
                
                # Adicionar coluna com botão para editar
                st.dataframe(filtro_transacoes_formatadas[['id', 'data', 'descricao', 'categoria', 'tipo', 'valor']], use_container_width=True)
                
                # Formulário para edição
                st.subheader("Editar Transação")
                id_editar = st.number_input("ID da Transação para Editar", min_value=1, 
                                        max_value=int(transacoes['id'].max()) if not transacoes.empty else 1, 
                                        step=1)
                
                if id_editar in transacoes['id'].values:
                    transacao_atual = transacoes[transacoes['id'] == id_editar].iloc[0].to_dict()
                    st.info(f"Editando transação: {transacao_atual['descricao']} - R$ {transacao_atual['valor']:.2f}")
                    
                    # Formulário preenchido com dados atuais
                    transacao_atualizada = form_transacao(categorias, dados_iniciais=transacao_atual)
                    
                    if st.button("Salvar Alterações"):
                        if editar_transacao(id_editar, transacao_atualizada, arquivo_excel):
                            # Atualiza os dados após editar
                            st.cache_data.clear()
                            st.rerun()
                else:
                    st.warning("Selecione um ID válido para editar.")
            else:
                st.info(f"Não há transações para {calendar.month_name[mes_selecionado]} de {ano_selecionado} com o filtro selecionado.")
        
        with tab2:
            st.subheader("Excluir Transações")
            
            # Filtros para exclusão
            col1, col2, col3 = st.columns(3)
            with col1:
                meses = list(range(1, 13))
                mes_selecionado = st.selectbox("Mês", meses, index=datetime.now().month-1, key="mes_excluir")
            with col2:
                anos = list(range(2020, 2026))
                ano_selecionado = st.selectbox("Ano", anos, index=anos.index(datetime.now().year) if datetime.now().year in anos else 0, key="ano_excluir")
            with col3:
                tipo_filtro = st.selectbox("Tipo", ["Todos", "entrada", "saida"], key="tipo_excluir")
            
            # Aplicar filtros
            filtro_transacoes = transacoes.copy()
            
            # Filtrar por mês e ano
            filtro_transacoes = filtro_transacoes[
                (filtro_transacoes['data'].dt.month == mes_selecionado) & 
                (filtro_transacoes['data'].dt.year == ano_selecionado)
            ]
            
            # Filtrar por tipo
            if tipo_filtro != "Todos":
                filtro_transacoes = filtro_transacoes[filtro_transacoes['tipo'] == tipo_filtro]
            
            # Exibir resultados para exclusão
            if not filtro_transacoes.empty:
                # Formatar para exibição
                filtro_transacoes_formatadas = filtro_transacoes.copy()
                filtro_transacoes_formatadas['data'] = filtro_transacoes_formatadas['data'].dt.strftime('%d/%m/%Y')
                filtro_transacoes_formatadas['valor'] = filtro_transacoes_formatadas['valor'].apply(lambda x: f"R$ {x:.2f}")
                
                st.dataframe(filtro_transacoes_formatadas[['id', 'data', 'descricao', 'categoria', 'tipo', 'valor']], use_container_width=True)
                
                # Formulário para exclusão
                st.subheader("Excluir Transação")
                id_excluir = st.number_input("ID da Transação para Excluir", min_value=1, 
                                         max_value=int(transacoes['id'].max()) if not transacoes.empty else 1, 
                                         step=1)
                
                if id_excluir in transacoes['id'].values:
                    transacao_excluir = transacoes[transacoes['id'] == id_excluir].iloc[0]
                    st.warning(f"Você está prestes a excluir: {transacao_excluir['descricao']} - R$ {transacao_excluir['valor']:.2f}")
                    
                    # Confirmar exclusão
                    if st.button("Excluir Transação", type="primary"):
                        if excluir_transacao(id_excluir, arquivo_excel):
                            # Atualiza os dados após excluir
                            st.cache_data.clear()
                            st.rerun()
                else:
                    st.warning("Selecione um ID válido para excluir.")
            else:
                st.info(f"Não há transações para {calendar.month_name[mes_selecionado]} de {ano_selecionado} com o filtro selecionado.")

if __name__ == "__main__":
    main()
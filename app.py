import os
import io
import json
import pandas as pd
import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload

# Configuração da página DEVE SER A PRIMEIRA CHAMADA
st.set_page_config(
    page_title="Busca & Registro de Referências",
    layout="wide"
)

# Dicionário de usuários e senhas válidos
USUARIOS_VALIDOS = {
    "Admin2Steps": "Acesso!2#Steps*",
}

def verificar_usuario_senha():
    # Centraliza o conteúdo usando colunas
    col1, col2, col3 = st.columns([1, 3, 1])  # A coluna do meio (col2) é mais larga

    with col2:
        # Exibe a imagem
        st.image("imagem.png", width=90)

        # Adiciona um pequeno espaço entre a imagem e os campos de entrada
        st.write("")  # Espaço vazio para melhorar o layout

        # Campos de entrada para usuário e senha
        usuario = st.text_input("Digite o usuário:")
        senha = st.text_input("Digite a senha para acessar o aplicativo:", type="password")

    # Verifica se o usuário e a senha estão corretos
    if usuario in USUARIOS_VALIDOS and senha == USUARIOS_VALIDOS[usuario]:
        st.session_state.usuario_autenticado = True  # Marca o usuário como autenticado
        st.rerun()  # Recarrega o aplicativo para remover as barras de usuário e senha
    elif usuario != "" or senha != "":
        # Centraliza a mensagem de erro
        with col2:
            st.error("Usuário ou senha incorretos. Tente novamente.")

# Configurações do Google Drive
SCOPES = ["https://www.googleapis.com/auth/drive"]
FOLDER_ID = "1abI_PNRR0N5dgKJ7EXCsAFf_LdN6mLwA"  # ID da pasta "dados_refs" no Google Drive
FILE_NAME = "refs.csv"  # Nome do arquivo CSV

# Função para autenticar no Google Drive
def authenticate_google_drive():
    try:
        # Carrega as credenciais da variável de ambiente
        google_credentials_info = json.loads(os.getenv("GOOGLE_CREDENTIALS"))
        credentials = service_account.Credentials.from_service_account_info(google_credentials_info, scopes=SCOPES)
        return build("drive", "v3", credentials=credentials)
    except Exception as e:
        st.error(f"Erro ao autenticar no Google Drive: {e}")
        return None

# Função para baixar o CSV do Google Drive
def download_csv(service):
    try:
        # Busca o arquivo CSV diretamente na pasta "dados_refs"
        query = f"'{FOLDER_ID}' in parents and name = '{FILE_NAME}'"
        response = service.files().list(q=query, fields="files(id)").execute()
        files = response.get("files", [])

        if files:
            file_id = files[0]["id"]
            request = service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            fh.seek(0)
            return pd.read_csv(fh)
        else:
            st.warning(f"Arquivo '{FILE_NAME}' não encontrado na pasta.")
            return pd.DataFrame()  # Retorna um DataFrame vazio se o arquivo não existir
    except Exception as e:
        st.error(f"Erro ao baixar o CSV do Google Drive: {e}")
        return pd.DataFrame()  # Retorna um DataFrame vazio em caso de erro

# Função para fazer upload do CSV para o Google Drive
def upload_csv(service, df):
    try:
        # Verifica se o arquivo já existe na pasta
        query = f"'{FOLDER_ID}' in parents and name = '{FILE_NAME}'"
        response = service.files().list(q=query, fields="files(id)").execute()
        files = response.get("files", [])

        if files:
            # Se o arquivo já existe, atualize-o
            file_id = files[0]["id"]
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            media = MediaIoBaseUpload(io.BytesIO(csv_buffer.getvalue().encode()), mimetype="text/csv")
            service.files().update(fileId=file_id, media_body=media).execute()
        else:
            # Se o arquivo não existe, crie-o
            file_metadata = {
                "name": FILE_NAME,
                "parents": [FOLDER_ID],
            }
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            media = MediaIoBaseUpload(io.BytesIO(csv_buffer.getvalue().encode()), mimetype="text/csv")
            service.files().create(body=file_metadata, media_body=media, fields="id").execute()
    except Exception as e:
        st.error(f"Erro ao fazer upload do CSV para o Google Drive: {e}")
        
def main(service, refs):
    # Função para buscar termos contidos no texto
    def buscar_termo(df, coluna, termo, case_sensitive=False):
        """
        Busca linhas onde a coluna contém o termo especificado.
        
        Parâmetros:
            df (pd.DataFrame): O DataFrame onde a busca será realizada.
            coluna (str): A coluna onde o termo será buscado.
            termo (str): O termo a ser buscado.
            case_sensitive (bool): Se a busca deve ser sensível a maiúsculas/minúsculas.
        
        Retorna:
            pd.DataFrame: Um DataFrame com as linhas que contêm o termo.
        """
        return df[df[coluna].str.contains(termo, case=case_sensitive, na=False)]
        
        
    col1, col2, col3 = st.columns([1, 4, 1])  # A primeira coluna ocupa 4 partes, a segunda 1 parte

    # Coloca o botão de logout na segunda coluna (canto superior direito)
  
    with col1:
        st.image("imagem.png", width=90)  # Ajuste o width conforme necessário

    with col2:
        st.title("APP PARA BUSCA DE REFERÊNCIAS 2STEPS")

    with col3:
        if st.button("Logout"):
            st.session_state.usuario_autenticado = False
            st.rerun()

    # Criando abas
    tab1, tab2, tab3 = st.tabs(["Como funciona?", "Busca de Referência", "Registro de Referência"])

    with tab1:
        st.header("Funcionamento da Busca de Referências:")
        st.write("A Busca de Referência pode ser feita por quatro campos diferentes:")
        st.write("""
                - Pelo Assunto Principal
                - Pela Campanha
                - Pelas Palavras-Chave
                - Pelo Texto de Resumo da Referência
                """)
        st.header("Registro de Referências:")
        st.write("Para o registro de referência, é importante que todos os campos sejam preenchidos. Os campos da tabela são:")
        st.write("""
                - **TÍTULO**: O título da referência que será registrada.
                - **CAMPANHA**: O nome da campanha que está em andamento.
                - **CATEGORIA**: O tipo de referência (ex.: POST, REPORTAGEM, TEXTO, ...).
                - **LOCAL**: O local ao qual o link se refere (ex.: INSTAGRAM, FACEBOOK, musicnonstop.uol.com.br, ...).
                - **ASSUNTO PRINCIPAL**: Apenas uma palavra que descreva a ideia da referência (ex.: CORRIDA, ESTILO, JUVENTUDE, ...).
                - **CAMINHO DESCRIÇÃO**: O link que leva à publicação referida.
                - **DESCRIÇÃO**: Um texto curto que descreva a referência.
                - **IDIOMA**: Idioma da referência.
                - **PALAVRAS-CHAVE**: De 3 a 5 palavras que indiquem a ideia principal da referência.
                """)
        st.write("**Dica:** Você pode usar uma IA Generativa, como GPT ou DeepSeek, para preencher os campos do registro de referência.")
        st.header("Imagem de uma amostra da tabela de referências:")
        st.image("imagem_tabela.png", caption="Tabela de Referências", use_container_width=True)

    with tab2:
        st.header("Busca de Referências")
        st.write("Por qual campo você quer fazer sua busca:")
        
        # Criando colunas para os botões
        col1, col2, col3, col4 = st.columns(4)

        # Adicionando os botões em cada coluna
        with col1:
            if st.button("Assunto Principal"):
                st.session_state.coluna_busca = "ASSUNTO_PRINCIPAL"
        with col2:
            if st.button("Campanha"):
                st.session_state.coluna_busca = "CAMPANHA"
        with col3:
            if st.button("Palavra Chave"):
                st.session_state.coluna_busca = "PALAVRAS_CHAVES"
        with col4:
            if st.button("Texto Resumo"):
                st.session_state.coluna_busca = "DESCRICAO"

        # Inicializar o estado de edição se não existir
        if "editando_referencia" not in st.session_state:
            st.session_state.editando_referencia = False
            st.session_state.indice_edicao = None
        
        # Verificando se uma coluna de busca foi selecionada
        if "coluna_busca" in st.session_state:
            coluna_busca = st.session_state.coluna_busca
            termo_busca = st.text_input(f"Digite o termo para a busca no campo {coluna_busca}: ")
            
            # Opção para busca sensível a maiúsculas/minúsculas
            case_sensitive = st.checkbox("Busca sensível a maiúsculas/minúsculas", value=False)
            
            if st.button("Buscar"):
                if termo_busca.strip():  # Verifica se o termo de busca não está vazio
                    resultados = buscar_termo(refs, coluna_busca, termo_busca, case_sensitive=case_sensitive)
                    
                    # Armazenar os resultados no session_state para uso posterior
                    st.session_state.resultados_busca = resultados
                    
                    if not resultados.empty:
                        st.write(f"Resultados da busca por '{termo_busca}' no campo '{coluna_busca}':")
                        st.session_state.mostrando_resultados = True
                    else:
                        st.write("Nenhum resultado encontrado.")
                        st.session_state.mostrando_resultados = False
                else:
                    st.warning("Por favor, insira um termo de busca.")
            
            # Se houver resultados armazenados, exibi-los
            if "resultados_busca" in st.session_state and "mostrando_resultados" in st.session_state and st.session_state.mostrando_resultados:
                # Se estiver no modo de edição, mostrar o formulário de edição
                if st.session_state.editando_referencia and st.session_state.indice_edicao is not None:
                    # Obter o índice real da referência no DataFrame original
                    idx = st.session_state.indice_edicao
                    referencia = refs.iloc[idx]
                    
                    st.subheader("Editar Referência")
                    
                    # Criar os campos de edição preenchidos com os valores atuais
                    novo_titulo = st.text_input("Título:", value=referencia['TITULO'], key="edit_titulo")
                    nova_campanha = st.text_input("Campanha:", value=referencia['CAMPANHA'], key="edit_campanha")
                    nova_categoria = st.text_input("Categoria:", value=referencia['CATEGORIA'], key="edit_categoria")
                    novo_local = st.text_input("Local:", value=referencia['LOCAL'], key="edit_local")
                    novo_assunto = st.text_input("Assunto Principal:", value=referencia['ASSUNTO_PRINCIPAL'], key="edit_assunto")
                    novo_caminho = st.text_input("Caminho (link):", value=referencia['CAMINHO'], key="edit_caminho")
                    nova_descricao = st.text_area("Descrição:", value=referencia['DESCRICAO'], key="edit_descricao")
                    novo_idioma = st.text_input("Idioma:", value=referencia['IDIOMA'], key="edit_idioma")
                    novas_palavras = st.text_input("Palavras-Chave:", value=referencia['PALAVRAS_CHAVES'], key="edit_palavras")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("Salvar Alterações"):
                            # Verificar se todos os campos foram preenchidos
                            if all([novo_titulo, nova_campanha, nova_categoria, novo_local, novo_assunto, novo_caminho, nova_descricao, novo_idioma, novas_palavras]):
                                # Verificar se palavras-chave contém de 3 a 5 palavras
                                if 3 <= len(novas_palavras.split()) <= 5:
                                    # Atualizar os valores no DataFrame
                                    refs.at[idx, 'TITULO'] = novo_titulo
                                    refs.at[idx, 'CAMPANHA'] = nova_campanha
                                    refs.at[idx, 'CATEGORIA'] = nova_categoria
                                    refs.at[idx, 'LOCAL'] = novo_local
                                    refs.at[idx, 'ASSUNTO_PRINCIPAL'] = novo_assunto
                                    refs.at[idx, 'CAMINHO'] = novo_caminho
                                    refs.at[idx, 'DESCRICAO'] = nova_descricao
                                    refs.at[idx, 'IDIOMA'] = novo_idioma
                                    refs.at[idx, 'PALAVRAS_CHAVES'] = novas_palavras
                                    
                                    # Salvar as alterações no CSV
                                    upload_csv(service, refs)
                                    
                                    # Atualizar também os resultados da busca
                                    st.session_state.resultados_busca = buscar_termo(refs, coluna_busca, termo_busca, case_sensitive=case_sensitive)
                                    
                                    st.success("Referência atualizada com sucesso!")
                                    
                                    # Sair do modo de edição
                                    st.session_state.editando_referencia = False
                                    st.session_state.indice_edicao = None
                                    
                                    # Recarregar a página para mostrar as alterações
                                    st.rerun()
                                else:
                                    st.warning("O campo 'Palavras-Chave' deve conter de 3 a 5 palavras.")
                            else:
                                st.warning("Por favor, preencha todos os campos.")
                    
                    with col2:
                        if st.button("Cancelar Edição"):
                            st.session_state.editando_referencia = False
                            st.session_state.indice_edicao = None
                            st.rerun()
                
                # Caso contrário, mostrar os resultados normalmente
                else:
                    for i, (idx, row) in enumerate(st.session_state.resultados_busca.iterrows()):
                        with st.container():
                            st.write(f"Resultado {i + 1}")
                            st.write(f"**Assunto principal:** {row['ASSUNTO_PRINCIPAL']}")
                            st.write(f"**Título:** {row['TITULO']}")
                            st.write(f"**Campanha:** {row['CAMPANHA']}")
                            st.write(f"**Descrição:** {row['DESCRICAO']}")
                            st.write(f"**Palavras-Chave:** {row['PALAVRAS_CHAVES']}")
                            st.link_button("**Link para referência**", url=row['CAMINHO'])
                            
                            # Botões de editar e excluir lado a lado
                            col1, col2 = st.columns(2)
                            with col1:
                                # O botão de editar configura o modo de edição e armazena o índice
                                if st.button(f"Editar", key=f"edit_{i}"):
                                    st.session_state.editando_referencia = True
                                    st.session_state.indice_edicao = idx  # Armazena o índice real no DataFrame
                                    st.rerun()  # Recarrega a página para mostrar o formulário de edição
                            
                            with col2:
                                # O botão de excluir mostra uma confirmação
                                if st.button(f"Excluir", key=f"delete_{i}"):
                                    # Configura o estado para mostrar a confirmação
                                    st.session_state.confirmando_exclusao = True
                                    st.session_state.indice_exclusao = idx
                                    st.rerun()
                            
                            st.write("---")
                    
                    # Exibir a caixa de confirmação se estiver confirmando exclusão
                    if "confirmando_exclusao" in st.session_state and st.session_state.confirmando_exclusao:
                        st.warning("Tem certeza que deseja excluir esta referência? Esta ação não pode ser desfeita.")
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if st.button("Sim, excluir"):
                                # Obter o índice da referência a excluir
                                idx_excluir = st.session_state.indice_exclusao
                                
                                # Excluir a referência do DataFrame
                                refs = refs.drop(idx_excluir).reset_index(drop=True)
                                
                                # Salvar o DataFrame atualizado
                                upload_csv(service, refs)
                                
                                # Atualizar os resultados da busca
                                st.session_state.resultados_busca = buscar_termo(refs, coluna_busca, termo_busca, case_sensitive=case_sensitive)
                                
                                # Se não houver mais resultados, atualizar o estado
                                if st.session_state.resultados_busca.empty:
                                    st.session_state.mostrando_resultados = False
                                
                                # Limpar o estado de confirmação
                                st.session_state.confirmando_exclusao = False
                                st.session_state.indice_exclusao = None
                                
                                st.success("Referência excluída com sucesso!")
                                st.rerun()
                        
                        with col2:
                            if st.button("Cancelar"):
                                # Limpar o estado de confirmação
                                st.session_state.confirmando_exclusao = False
                                st.session_state.indice_exclusao = None
                                st.rerun()

    with tab3:
        st.header("Registro de Referência")
        st.write("Aqui você pode registrar uma nova referência.")
        
        # Inicializar contador de formulários se não existir
        if "form_counter" not in st.session_state:
            st.session_state.form_counter = 0
        
        # Usar o contador como parte da chave para forçar a recriação dos widgets
        form_key = f"form_{st.session_state.form_counter}"
        
        with st.form(key=form_key):
            # Coletando dados do usuário
            titulo = st.text_input("Informe o Título da referência: ")
            campanha = st.text_input("Informe a Campanha da referência: ")
            categoria = st.text_input("Informe a Categoria da referência: ")
            local = st.text_input("Informe o Local da referência: ")
            assunto_principal = st.text_input("Informe o Assunto Principal da referência: ")
            caminho = st.text_input("Informe o Caminho (link completo) da referência: ")
            resumo = st.text_input("Informe o Texto de Resumo da referência: ")
            idioma = st.text_input("Informe o Idioma da referência: ")
            palavras_chave = st.text_input("Informe as Palavras-Chave (de 3 a 5) da referência: ")
            
            # Botão de submissão dentro do formulário
            submitted = st.form_submit_button("Registrar Referência")
            
            if submitted:
                # Verifica se todos os campos foram preenchidos
                if all([titulo, campanha, categoria, local, assunto_principal, caminho, resumo, idioma, palavras_chave]):
                    # Verifica se o campo "Palavras-Chave" contém de 3 a 5 palavras
                    if 3 <= len(palavras_chave.split()) <= 5:
                        # Cria um novo registro
                        novo_registro = {
                            "TITULO": titulo,
                            "CAMPANHA": campanha,
                            "CATEGORIA": categoria,
                            "LOCAL": local,
                            "ASSUNTO_PRINCIPAL": assunto_principal,
                            "CAMINHO": caminho,
                            "DESCRICAO": resumo,
                            "IDIOMA": idioma,
                            "PALAVRAS_CHAVES": palavras_chave
                        }
                        
                        # Adiciona o novo registro ao DataFrame
                        refs = pd.concat([refs, pd.DataFrame([novo_registro])], ignore_index=True)
                        
                        # Salva o DataFrame atualizado no arquivo CSV
                        upload_csv(service, refs)
                        
                        st.success("Referência registrada com sucesso!")
                        st.write("Dados registrados:")
                        st.write(novo_registro)
                        
                        # Incrementar o contador para criar um novo formulário com campos vazios
                        st.session_state.form_counter += 1
                        st.rerun()
                    else:
                        st.warning("O campo 'Palavras-Chave' deve conter de 3 a 5 palavras.")
                else:
                    st.warning("Por favor, preencha todos os campos.")


if __name__ == "__main__":
    # Verifica se o usuário já está autenticado
    if "usuario_autenticado" not in st.session_state:
        st.session_state.usuario_autenticado = False

    # Se o usuário não estiver autenticado, exibe os campos de usuário e senha
    if not st.session_state.usuario_autenticado:
        verificar_usuario_senha()
    else:
        # Se o usuário já estiver autenticado, exibe o aplicativo diretamente
        service = authenticate_google_drive()
        if service is not None:  # Verifica se a autenticação foi bem-sucedida
            refs = download_csv(service)
            if refs is not None:  # Verifica se o download do CSV foi bem-sucedido
                main(service, refs)

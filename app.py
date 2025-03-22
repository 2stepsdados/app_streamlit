import os
import io
import pandas as pd
import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload


# Configurações do Google Drive
SCOPES = ["https://www.googleapis.com/auth/drive"]
CREDENTIALS_FILE = "credentials.json"  # Arquivo de credenciais baixado
FOLDER_ID = "1abI_PNRR0N5dgKJ7EXCsAFf_LdN6mLwA"  # ID da pasta principal no Google Drive
SUBFOLDER_NAME = "dados_refs"  # Nome da subpasta onde o CSV está
FILE_NAME = "refs.csv"  # Nome do arquivo CSV

# Autenticação no Google Drive
def authenticate_google_drive():
    creds = service_account.Credentials.from_service_account_file(
        CREDENTIALS_FILE, scopes=SCOPES
    )
    return build("drive", "v3", credentials=creds)

def download_csv(service):
    # Busca a subpasta "dados_refs"
    query = f"'{FOLDER_ID}' in parents and name = '{SUBFOLDER_NAME}' and mimeType = 'application/vnd.google-apps.folder'"
    response = service.files().list(q=query, fields="files(id)").execute()
    folders = response.get("files", [])

    if folders:
        subfolder_id = folders[0]["id"]  # ID da subpasta "dados_refs"
        
        # Busca o arquivo CSV dentro da subpasta
        query = f"'{subfolder_id}' in parents and name = '{FILE_NAME}'"
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
            st.warning(f"Arquivo '{FILE_NAME}' não encontrado na subpasta '{SUBFOLDER_NAME}'.")
            return pd.DataFrame()  # Retorna um DataFrame vazio se o arquivo não existir
    else:
        st.warning(f"Subpasta '{SUBFOLDER_NAME}' não encontrada.")
        return pd.DataFrame()  # Retorna um DataFrame vazio se a subpasta não existir

def upload_csv(service, df):
    # Busca a subpasta "dados_refs"
    query = f"'{FOLDER_ID}' in parents and name = '{SUBFOLDER_NAME}' and mimeType = 'application/vnd.google-apps.folder'"
    response = service.files().list(q=query, fields="files(id)").execute()
    folders = response.get("files", [])

    if folders:
        subfolder_id = folders[0]["id"]  # ID da subpasta "dados_refs"
        
        # Verifica se o arquivo já existe na subpasta
        query = f"'{subfolder_id}' in parents and name = '{FILE_NAME}'"
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
                "parents": [subfolder_id],
            }
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            media = MediaIoBaseUpload(io.BytesIO(csv_buffer.getvalue().encode()), mimetype="text/csv")
            service.files().create(body=file_metadata, media_body=media, fields="id").execute()
    else:
        st.error(f"Subpasta '{SUBFOLDER_NAME}' não encontrada.")

def main():
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

    # Configuração da página (DEVE SER A PRIMEIRA CHAMADA)
    st.set_page_config(
        page_title="Busca & Registro de Referências",
        layout="wide"
    )

    col1, col2 = st.columns([1, 4])
    with col1:
        st.image("imagem.png", width=90)  # Ajuste o width conforme necessário
    with col2:
        st.title("APP PARA BUSCA DE REFERÊNCIAS 2STEPS")

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

        # Verificando se uma coluna de busca foi selecionada
        if "coluna_busca" in st.session_state:
            coluna_busca = st.session_state.coluna_busca
            termo_busca = st.text_input(f"Digite o termo para a busca no campo {coluna_busca}: ")
            
            # Opção para busca sensível a maiúsculas/minúsculas
            case_sensitive = st.checkbox("Busca sensível a maiúsculas/minúsculas", value=False)
            
            if st.button("Buscar"):
                if termo_busca.strip():  # Verifica se o termo de busca não está vazio
                    resultados = buscar_termo(refs, coluna_busca, termo_busca, case_sensitive=case_sensitive)
                    if not resultados.empty:
                        st.write(f"Resultados da busca por '{termo_busca}' no campo '{coluna_busca}':")
                        for idx, row in resultados.iterrows():
                            st.write(f"Resultado {idx + 1}")
                            st.write(f"**Assunto principal:** {row['ASSUNTO_PRINCIPAL']}")
                            st.write(f"**Título:** {row['TITULO']}")
                            st.write(f"**Campanha:** {row['CAMPANHA']}")
                            st.write(f"**Descrição:** {row['DESCRICAO']}")
                            st.write(f"**Palavras-Chave:** {row['PALAVRAS_CHAVES']}")
                            st.link_button("**Link para referência**", url = row['CAMINHO'])
                            st.write("---")
                    else:
                        st.write("Nenhum resultado encontrado.")
                else:
                    st.warning("Por favor, insira um termo de busca.")

    with tab3:
        st.header("Registro de Referência")
        st.write("Aqui você pode registrar uma nova referência.")
        
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
        
        if st.button("Registrar Referência"):
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
                else:
                    st.warning("O campo 'Palavras-Chave' deve conter de 3 a 5 palavras.")
            else:
                st.warning("Por favor, preencha todos os campos.")

if __name__ == "__main__":
    # Autenticar e carregar o DataFrame do Google Drive
    service = authenticate_google_drive()
    refs = download_csv(service)

    # Executar o aplicativo Streamlit
    main()
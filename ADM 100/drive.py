import os
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Configuração das credenciais
CREDENTIALS_FILE = 'credentials.json'  # Seu arquivo JSON atual
TOKEN_FILE = 'token.json'
SCOPES = ['https://www.googleapis.com/auth/drive.file']

def authenticate():
    """Autenticação usando OAuth 2.0"""
    creds = None

    # Carrega credenciais existentes se disponíveis
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # Se não há credenciais válidas, precisamos autenticar
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Carrega as credenciais do arquivo
            with open(CREDENTIALS_FILE, 'r') as f:
                client_config = json.load(f)
            
            # Configura o flow de autenticação
            flow = InstalledAppFlow.from_client_config(
                client_config,
                SCOPES,
                redirect_uri='https://developers.google.com/oauthplayground'
            )
            
            # Gera a URL de autorização
            auth_url, _ = flow.authorization_url(prompt='consent')
            
            print("\nPor favor, acesse esta URL para autorizar o aplicativo:")
            print(auth_url)
            
            # Solicita o código de autorização do usuário
            auth_code = input("\nCole o código de autorização aqui: ").strip()
            
            # Troca o código de autorização por credenciais
            flow.fetch_token(code=auth_code)
            creds = flow.credentials

            # Salva as credenciais para uso futuro
            with open(TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())

    return build('drive', 'v3', credentials=creds)

def get_drive_folder_id(service, folder_name):
    """Verifica/cria pasta no Drive."""
    try:
        print(f"Procurando pasta '{folder_name}'...")
        response = service.files().list(
            q=f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'",
            spaces='drive',
            fields='files(id, name)'
        ).execute()
        
        files = response.get('files', [])
        if files:
            print(f"Pasta encontrada!")
            return files[0].get('id')
        
        print(f"Criando nova pasta '{folder_name}'...")
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        folder = service.files().create(
            body=file_metadata,
            fields='id'
        ).execute()
        print(f"Pasta criada com sucesso!")
        return folder.get('id')

    except Exception as e:
        print(f"Erro ao verificar/criar pasta: {str(e)}")
        return None

def upload_files(service, folder_id, folder_path):
    """Upload de arquivos para o Drive."""
    if not os.path.exists(folder_path):
        print(f"Pasta local '{folder_path}' não encontrada!")
        return

    print(f"Iniciando upload de arquivos...")
    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)
        if os.path.isfile(file_path):
            try:
                print(f"Enviando {file_name}...")
                file_metadata = {
                    'name': file_name,
                    'parents': [folder_id]
                }
                media = MediaFileUpload(file_path, resumable=True)
                file = service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id'
                ).execute()
                print(f"Arquivo {file_name} enviado! ID: {file.get('id')}")
            except Exception as e:
                print(f"Erro ao enviar {file_name}: {str(e)}")

def main():
    try:
        print("Iniciando autenticação...")
        service = authenticate()
        
        if not service:
            print("Falha na autenticação!")
            return

        folder_name = 'UFV/MAT 241'
        local_folder_path = '/workspaces/MAT-241/PDF'

        folder_id = get_drive_folder_id(service, folder_name)
        if folder_id:
            upload_files(service, folder_id, local_folder_path)
            print("Processo concluído!")
        else:
            print("Erro na criação/verificação da pasta.")

    except Exception as e:
        print(f"Erro durante execução: {str(e)}")

if __name__ == '__main__':
    main()
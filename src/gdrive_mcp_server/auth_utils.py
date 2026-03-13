import io
import urllib.request
import urllib.error
import json
from typing import Optional

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

class GoogleDriveManager:
    
    def __init__(self, client_id: str, scope: str):
        self.client_id = client_id    
        self.scope = [scope]

    def verify_token(self, token: str) -> Optional[str]:
        print("\n" + "="*40)
        print("TOKEN VERIFICATION TRIGGERED")
        
        try:
            url = f"https://oauth2.googleapis.com/tokeninfo?access_token={token}" if token.startswith("ya29.") else f"https://oauth2.googleapis.com/tokeninfo?id_token={token}"
            req = urllib.request.Request(url)
            
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())

            issued_to = data.get('azp') or data.get('aud')
            if issued_to != self.client_id:
                print("FAILURE: Client ID mismatch!")
                return None

            print("SUCCESS: Token is valid and belongs to this server.")
            print("="*40 + "\n")
            return token 

        except Exception as e:
            print(f"FAILURE: Code crashed during verification: {e}")
            return None

    def get_files(self, query: str, token: str, page_size: int = 10) -> list:
        """Searches the user's personal drive using their access token."""
        creds = Credentials(token)
        service = build('drive', 'v3', credentials=creds)
        
        results = service.files().list(
            q=f"name contains '{query}'",
            pageSize=page_size,
            fields="files(id, name, mimeType, modifiedTime)"
        ).execute()
        return results.get('files', [])

    def download_file(self, file_id: str, mime_type: str, token: str) -> str:
        """Reads file content using the user's access token."""
        creds = Credentials(token)
        service = build('drive', 'v3', credentials=creds)
        
        if mime_type == "application/vnd.google-apps.document":
            request = service.files().export_media(fileId=file_id, mimeType="text/plain")
        elif mime_type == "text/plain":
            request = service.files().get_media(fileId=file_id)
        else:
            return "Unsupported file type"

        buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(buffer, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        
        return buffer.getvalue().decode("utf-8")
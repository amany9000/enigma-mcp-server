import os

class Config:
    
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    
    OAUTH_CLIENT_ID: str = os.getenv("OAUTH_CLIENT_ID", "YOUR_GOOGLE_OAUTH_CLIENT_ID.apps.googleusercontent.com")
    # GOOGLE_SA_KEY_PATH: str = os.getenv("GOOGLE_SA_KEY_PATH", "C:\\Users\\Administrator\\Documents\\projects\\Enigma\\enigma-key\\enigma-mcp_server-service-key.json")

    
    MCP_SCOPE: str = os.getenv("MCP_SCOPE", "https://www.googleapis.com/auth/drive.readonly")
    OAUTH_STRICT: bool = os.getenv("OAUTH_STRICT", "true").lower() in ("true", "1", "yes")
    TRANSPORT: str = os.getenv("TRANSPORT", "streamable-https")

    DEPLOYED_HOST: str = os.getenv("DEPLOYED_HOST", HOST+":"+str(PORT))


config = Config()
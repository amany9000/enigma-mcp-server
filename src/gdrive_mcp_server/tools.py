import mcp.types as types
from .auth_utils import GoogleDriveManager
from .config import config

drive_manager = GoogleDriveManager(
    client_id=config.OAUTH_CLIENT_ID,
    # sa_key_path=config.GOOGLE_SA_KEY_PATH,
    scope=config.MCP_SCOPE
)

def search_files(query: str, token: str, page_size=10):
    files = drive_manager.get_files(query, token, page_size)
    final_str = ''
    for file in files:
        final_str = final_str + f"{file['name']}, "
        print(f"{file['name']} (ID: {file['id']}, Type: {file['mimeType']})")
    
    if not files:
        return [types.TextContent(type="text", text=f"No files found matching '{query}'.")]
        
    return [types.TextContent(
        type="text",
        text=f"{len(files)} file(s) found: {final_str}"
    )]

def read_file(query: str, token: str, page_size=10):
    files = drive_manager.get_files(query, token, page_size)
    
    if len(files) == 0:
        return [types.TextContent(type="text", text="File not present")]
    if len(files) > 1:
        return [types.TextContent(type="text", text="More than one file present")]
    
    file_id = files[0]['id']
    file_name = files[0]['name']
    mime_type = files[0]['mimeType']
    
    content = drive_manager.download_file(file_id, mime_type, token)

    return [types.TextContent(
        type="text",
        text=f"--- Contents of {file_name} ---\n{content}\n"
    )]
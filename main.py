from typing import Dict, List, Optional
from fastapi import Cookie, Depends, FastAPI, Query, WebSocketDisconnect, status
from fastapi.websockets import WebSocket
from fastapi.requests import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import uvicorn
import websockets

app = FastAPI()

templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})

class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: List[WebSocket] = []
        self.client_list: Dict[str, str] = {}
    
    async def connect(self, websocket: WebSocket, token: str, nickname: str):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.client_list[token] = nickname
        
    def disconnect(self, websocket: WebSocket, token: str):
        self.active_connections.remove(websocket)
        self.client_list.pop(token)
        
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
    
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws/{token}/{nickname}")
async def websocket_endpoint(websocket: WebSocket, token: str, nickname: str):
    await manager.connect(websocket, token, nickname)
    await manager.broadcast(f"[{nickname}({token[-6:]})] Into the chat room")
    
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"[{nickname}({token[-6:]})]: {data}")
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, token)
        await manager.broadcast(f"[{nickname}({token[-6:]})] Left the chat room")
    


if __name__ == "__main__":
    uvicorn.run(app="main:app", reload=True, host="127.0.0.1", port=8000)
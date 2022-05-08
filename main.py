from typing import List, Optional
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
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
    
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket)
    await manager.broadcast(f"{client_id} Into the chat room")
    
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"{client_id} send a message: {data}")
            await manager.send_personal_message(f"Server reply {client_id}: The message you sent is: {data}", websocket)
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"{client_id} Left the chat room")
    


if __name__ == "__main__":
    uvicorn.run(app="main:app", reload=True, host="127.0.0.1", port=8000)
from typing import Optional
from fastapi import Cookie, Depends, FastAPI, Query, status
from fastapi.websockets import WebSocket
from fastapi.requests import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import uvicorn

app = FastAPI()

templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})

async def get_cookie_or_token(
    websocket: WebSocket,
    session: Optional[str] = Cookie(None),
    token: Optional[str] = Query(None),    
):
    if session or token:
        return session or token
    await websocket.close(code=status.WS_1008_POLICY_VIOLATION)

@app.websocket("/items/{item_id}/ws")
async def websocket_depends(
    websocket: WebSocket,
    item_id: str,
    q: Optional[str] = None,
    cookie_or_token: str = Depends(get_cookie_or_token)
):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"cookie or token value is: {cookie_or_token}")
        
        if q:
            await websocket.send_text(f"query param value is: {q}")
            
        await websocket.send_text(f"Message text was: {data}, for item ID: {item_id}")

if __name__ == "__main__":
    uvicorn.run(app="main:app", reload=True, host="127.0.0.1", port=8000)
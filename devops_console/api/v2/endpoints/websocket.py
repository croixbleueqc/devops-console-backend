from fastapi import APIRouter, WebSocket


router = APIRouter()


@router.get("/")
async def get():
    return "Hello World"


@router.websocket("/socket")
async def websocket_endpoint(websocket: WebSocket):
    """
    This channel is used to send realtime updates to the client;
    primarily in response to webhook events handled by the webhook server.
    """

    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Message text was: {data}")

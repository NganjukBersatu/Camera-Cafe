import asyncio
import websockets

async def test():
    try:
        async with websockets.connect("ws://localhost:8000/ws") as ws:
            print("BERHASIL KONEK!")
            msg = await ws.recv()
            print("PESAN DITERIMA:", msg)
    except Exception as e:
        print("GAGAL:", e)

asyncio.run(test())
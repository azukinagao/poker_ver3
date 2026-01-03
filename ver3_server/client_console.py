# client_console.py
import asyncio, json

async def run(name):
    reader, writer = await asyncio.open_connection("127.0.0.1", 7777)
    def send(obj):
        writer.write((json.dumps(obj)+"\n").encode())
    send({"type":"join","name":name})
    send({"type":"ready"})
    try:
        while True:
            line = await reader.readline()
            if not line: break
            msg = json.loads(line.decode())
            print(f"[{name}] recv:", msg)
    finally:
        writer.close()
        await writer.wait_closed()

if __name__ == "__main__":
    asyncio.run(run("test"))

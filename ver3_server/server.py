# server.py  — minimal, robust 2P heads-up table
import asyncio, json, random

RANKS = ['2','3','4','5','6','7','8','9','T','J','Q','K','A']
SUITS = ['S','H','D','C']
DECK  = [r+s for s in SUITS for r in RANKS]

def eval_strength(hand, community):
    # 仮の強さ: ランクの合計（あとで本物に差し替えOK）
    order = {r:i for i,r in enumerate(RANKS, start=2)}
    return sum(order[c[0]] for c in (hand + community))

class Table:
    def __init__(self):
        # 待機列とプレイ中の2人を分けて管理
        self.waiting = []   # list[{"reader","writer","name"}]
        self.playing = []   # list  (最大2名)
        self.hands   = {}   # seat(int) -> [c1,c2]
        self.community = []

    async def safe_send(self, writer, obj):
        try:
            writer.write((json.dumps(obj) + "\n").encode())
            await writer.drain()
            return True
        except Exception:
            return False

    async def send_status(self, writer, msg):
        await self.safe_send(writer, {"type":"status","msg":msg})

    async def broadcast(self, obj):
        keep = []
        for p in self.playing:
            ok = await self.safe_send(p["writer"], obj)
            if ok: keep.append(p)
        self.playing = keep   # 送れない相手は除外

    async def add_player(self, reader, writer, name):
        self.waiting.append({"reader":reader, "writer":writer, "name":name})
        await self.send_status(writer, "waiting")
        await self.match_if_possible()

    async def match_if_possible(self):
        # 卓が空で待機が2人以上なら着席→即ゲーム開始
        if len(self.playing) == 0 and len(self.waiting) >= 2:
            p0 = self.waiting.pop(0); p0["seat"] = 0
            p1 = self.waiting.pop(0); p1["seat"] = 1
            self.playing = [p0, p1]
            await self.safe_send(p0["writer"], {"type":"matched","seat":0})
            await self.safe_send(p1["writer"], {"type":"matched","seat":1})
            await self.broadcast({"type":"status","msg":"matched"})
            await self.start_hand()

    async def start_hand(self):
        if len(self.playing) != 2:
            return
        deck = DECK[:]; random.shuffle(deck)
        self.community = [deck.pop() for _ in range(5)]
        self.hands.clear()
        # 配札（席ごとに別々の2枚）
        for p in self.playing:
            seat = p["seat"]
            self.hands[seat] = [deck.pop(), deck.pop()]
            await self.safe_send(p["writer"], {
                "type":"deal",
                "seat": seat,
                "your_hand": self.hands[seat],
                "community": self.community
            })
        # 結果
        s0 = eval_strength(self.hands[0], self.community)
        s1 = eval_strength(self.hands[1], self.community)
        winner = "draw" if s0 == s1 else (0 if s0 > s1 else 1)
        await self.broadcast({
            "type":"result",
            "hands": {"0": self.hands[0], "1": self.hands[1]},
            "community": self.community,
            "winner": winner
        })

    async def handle(self, reader, writer):
        try:
            while True:
                line = await reader.readline()
                if not line:
                    break
                try:
                    msg = json.loads(line.decode())
                except Exception:
                    await self.safe_send(writer, {"type":"error","msg":"bad_json"})
                    continue

                t = msg.get("type")
                if t == "join":
                    name = msg.get("name","guest")
                    await self.add_player(reader, writer, name)
                elif t == "ready":
                    # 今回はready不要（自動でstart_hand）
                    pass
                else:
                    await self.safe_send(writer, {"type":"error","msg":"unknown"})
        finally:
            # クリーンアップ：切断した人を待機/卓から除去
            self.waiting = [p for p in self.waiting if p["writer"] is not writer]
            still = [p for p in self.playing if p["writer"] is not writer]
            # 相手が残っていれば waiting に戻す
            if len(self.playing) == 2 and len(still) == 1:
                await self.send_status(still[0]["writer"], "opponent_left")
                self.waiting.append(still[0])
            self.playing = []
            try:
                writer.close(); await writer.wait_closed()
            except Exception:
                pass
            await self.match_if_possible()

async def main():
    table = Table()
    async def on_client(reader, writer):
        await table.handle(reader, writer)
    server = await asyncio.start_server(on_client, host="127.0.0.1", port=7777)
    print("Server listening on 127.0.0.1:7777")
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())

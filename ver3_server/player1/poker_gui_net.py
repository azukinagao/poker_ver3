# poker_gui_net.py  — GUI client (fixed)
import tkinter as tk
from PIL import Image, ImageTk, UnidentifiedImageError
import asyncio, threading, json, os

# ==== 画像フォルダを絶対パスで参照（cards は 1つ上の階層にある想定） ====
BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
CARDS_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "cards"))
print("CARDS_DIR =", CARDS_DIR, "exists:", os.path.isdir(CARDS_DIR))

def code_to_filename(code):  # 例: 'AS','TD','7H'
    # ==== Ten は 'T' → '10' に変換（素材が 10S.png 形式だから） ====
    rank, suit = code[0], code[1]
    if rank == 'T':
        rank = '10'
    return f"{rank}{suit}.png"

class PokerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Poker (Online 2P)")

        # UI
        self.frame_player    = tk.Frame(root); self.frame_player.pack(pady=10)
        self.frame_community = tk.Frame(root); self.frame_community.pack(pady=10)
        self.frame_opponent  = tk.Frame(root); self.frame_opponent.pack(pady=10)
        self.status = tk.Label(root, text="Disconnected"); self.status.pack(pady=4)
        self.btn = tk.Button(root, text="CONNECT & READY", command=self.connect_and_ready)
        self.btn.pack(pady=10)
        self.images = []

        # ネットワーク状態
        self.reader = None
        self.writer = None
        self.seat   = None        # ==== サーバから付与される自分の席ID(0/1)
        self.my_hand = None       # ==== deal で受け取った自分の2枚を保持

    def clear_frames(self):
        for f in (self.frame_player, self.frame_community, self.frame_opponent):
            for w in f.winfo_children(): w.destroy()
        self.images.clear()

    def display_row(self, frame, title, codes):
        tk.Label(frame, text=title, font=("Arial", 14, "bold")).pack()
        row = tk.Frame(frame); row.pack()
        for code in codes:
            path = os.path.join(CARDS_DIR, code_to_filename(code))
            try:
                img = Image.open(path)
                photo = ImageTk.PhotoImage(img)
                self.images.append(photo)
                tk.Label(row, image=photo).pack(side=tk.LEFT, padx=5)
            except (FileNotFoundError, UnidentifiedImageError):
                # ==== 画像が見つからなくても止めない（開発用フォールバック）
                tk.Label(row, text=code, width=6, height=4,
                         borderwidth=2, relief="groove").pack(side=tk.LEFT, padx=5)

    def connect_and_ready(self):
        # 二重接続防止
        self.btn.config(state=tk.DISABLED)
        threading.Thread(target=self._run_loop, daemon=True).start()

    def _run_loop(self):
        asyncio.run(self.net_main())

    async def net_main(self):
        try:
            self.set_status("Connecting...")
            self.reader, self.writer = await asyncio.open_connection("127.0.0.1", 7777)
            await self.send({"type":"join","name":"You"})
            await self.send({"type":"ready"})  # サーバ側では無視されるが害はない
            self.set_status("Waiting/Matched...")
            while True:
                line = await self.reader.readline()
                if not line: break
                msg = json.loads(line.decode())
                t = msg.get("type")
                if t == "matched":
                    # ==== サーバから seat(0/1) が来る
                    self.seat = msg.get("seat")
                    self.set_status(f"matched (seat={self.seat})")
                elif t == "deal":
                    self.root.after(0, self.on_deal, msg)
                elif t == "result":
                    self.root.after(0, self.on_result, msg)
                elif t == "status":
                    self.set_status(msg.get("msg",""))
                elif t == "error":
                    self.set_status("Error: " + msg.get("msg","unknown"))
        except Exception as e:
            self.set_status(f"Error: {e}")

    async def send(self, obj):
        self.writer.write((json.dumps(obj)+"\n").encode())
        await self.writer.drain()

    def on_deal(self, msg):
        self.clear_frames()
        self.my_hand = msg["your_hand"]                # ==== 自分の手を保存
        self.display_row(self.frame_player, "Your Hand", self.my_hand)
        self.display_row(self.frame_community, "Community", msg["community"])

    def on_result(self, msg):
        # ==== 自分/相手の識別（seatが未設定なら自分の手と一致で推定）
        if self.seat is None and self.my_hand is not None:
            if msg["hands"]["0"] == self.my_hand: self.seat = 0
            elif msg["hands"]["1"] == self.my_hand: self.seat = 1

        # 相手の手
        opp_seat = 1 - int(self.seat) if self.seat is not None else 1
        opp_hand = msg["hands"][str(opp_seat)]
        self.display_row(self.frame_opponent, "Opponent Hand", opp_hand)

        # 勝敗表示
        winner = msg["winner"]
        if winner == "draw":
            self.set_status("Winner: draw")
        else:
            you_win = (int(winner) == int(self.seat)) if self.seat is not None else False
            self.set_status("You WIN!" if you_win else "You LOSE")

    def set_status(self, text):
        self.root.after(0, lambda: self.status.config(text=text))

if __name__ == "__main__":
    root = tk.Tk()
    gui = PokerGUI(root)
    root.mainloop()

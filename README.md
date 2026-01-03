# Poker ver3 (Local Server / Work in Progress)

This is **an experimental, work-in-progress version** of a poker project.
It runs a **local server on a single PC** and connects **two clients** for a
heads-up game using TCP sockets.

⚠️ **Important**  
This version is **not a complete poker game yet**.  
Only the features listed below are implemented.

---

## Current Status (What is implemented)
- Local poker server using `asyncio`
- Two-player (heads-up) matching on a single table
- Clients connect via TCP (`127.0.0.1:7777`)
- Automatic dealing:
  - 2 hole cards per player
  - 5 community cards
- Server broadcasts game result to both players
- Simple JSON-based message protocol
- GUI client (Tkinter) for visualizing cards
- Console client for debugging and testing connections

---

## What is NOT implemented yet
- ❌ Real poker hand evaluation  
  (currently uses a placeholder strength calculation)
- ❌ Betting rounds (check / call / raise / fold)
- ❌ Chip stacks and pot management
- ❌ Turn-based player actions
- ❌ Hidden opponent cards (shown immediately for now)
- ❌ Multiple hands / continuous game loop

---

## Requirements
- Python 3.10+
- Pillow (for GUI card images)

Install Pillow:
```
pip install pillow
```

---

## Directory Structure
Expected structure:

- ver3_server/
  - server.py
  - client_console.py
  - cards/
    - AS.png
    - 10H.png
    - QD.png
    - ...
  - player1/
    - poker_gui_net.py
  - player2/
    - poker_gui_net.py

---

## Card Image Naming Rule
Card images must be placed in `cards/` and named as:

- AS.png  → Ace of Spades (A♠)
- 10H.png → Ten of Hearts (10♥)
- QD.png  → Queen of Diamonds (Q♦)
- 7C.png  → Seven of Clubs (7♣)

Suit codes:
- S = Spades
- H = Hearts
- D = Diamonds
- C = Clubs

---

## How to Run (GUI clients)

Open **three terminals**.

### Terminal 1: Start server
From `ver3_server/`:
```
python server.py
```

You should see:
```
Server listening on 127.0.0.1:7777
```

### Terminal 2: Start player 1 GUI
From `ver3_server/player1/`:
```
python poker_gui_net.py
```

### Terminal 3: Start player 2 GUI
From `ver3_server/player2/`:
```
python poker_gui_net.py
```

When both clients connect, the server automatically matches them and deals cards.

---

## Console Client (for testing)
You can connect using a console-based client:

From `ver3_server/`:
```
python client_console.py
```

This client prints all messages received from the server.

---

## Notes
- This version is **a prototype for networking and synchronization**
- Game logic is intentionally simplified
- The code is intended as a foundation for future development

---

## Planned Improvements
- Replace placeholder hand strength with real poker hand evaluation
- Add betting logic and player actions
- Hide opponent hole cards until showdown
- Support multiple hands per session
- Improve GUI interaction and status display

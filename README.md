# Mend — Autonomous Multi-Agent Incident Forensics & Live Hotfix Room on Switch AI + Telegram

> **Built for the Flip the Switch Hackathon (WeMakeDevs × DevTools Academy × Switch AI)**  
> **Tracks**: 🏆 **Best Business Workflow ($2,000)** + 🎙️ **Code with Wispr Voice Integration ($500)**

---

## 🚀 Overview

When a production payment or checkout service throws an unhandled `500 Internal Server Error`, engineering teams waste critical minutes jumping between error trackers, terminal editors, CI test runners, and chat threads.

**Mend** turns a single **Switch AI Room (`room://mend-prod-incidents`)** bridged 1:1 with **Telegram (`@mend_switch_bot`)** and the **Mend Switch Command Console** into an autonomous, human-in-the-loop incident war-room where **three specialized AI agents collaborate alongside human engineers** on real production code:

1. **`@mend-recon` (Incident Forensics & AST Inspector)**
   - Intercepts real runtime exceptions (`ZeroDivisionError`, `KeyError`, etc.) thrown by the live SQLite-backed financial checkout service ([`services/checkout_engine.py`](./services/checkout_engine.py)).
   - Parses the live Python Abstract Syntax Tree (`ast`) and stack frames on disk to pinpoint the exact failing function, line number, AST statement node, and payload context.
   - Posts a structured forensics report to the shared Switch Room and Telegram thread, then hands off to `@mend-forge`.

2. **`@mend-forge` (Surgical Patch & Unittest Verification Agent)**
   - Synthesizes a minimal unified git diff (`difflib.unified_diff`) fixing the root cause.
   - Executes the real Python `unittest` regression suite ([`tests/test_checkout_engine.py`](./tests/test_checkout_engine.py)) in an isolated sandbox before and after applying the candidate patch (`0/4 failed` → `4/4 passed`).
   - Streams the unified diff and test runner results into the room and hands off to `@mend-guard`.

3. **`@mend-guard` (Switch Trust Guardrail & Zero-Downtime Hotfix Deployer)**
   - Audits the candidate patch through deterministic **Switch Trust Guardrails** ([`switch_room/guardrails.py`](./switch_room/guardrails.py)): Python AST syntax integrity, forbidden dynamic call gate (`eval`/`exec`/`os.system`), credential/secret DLP regex scan, and surgical blast-radius verification (`<= 45 LOC`).
   - Sends an interactive **Telegram Inline Approval Card** (`[✅ Approve & Hot-Reload Fix]` / `[⏪ Reject / Rollback]`) to the on-call engineer.
   - Once approved (via Telegram button tap, replying `ship it` in chat, or using **Wispr Flow Voice Commands**), `@mend-guard` patches `services/checkout_engine.py` on disk, hot-reloads the live Python module in `0ms` downtime, runs the live test suite, and replays the failed transaction against SQLite (`HTTP 200 OK`).

---

## 🏗️ Architecture

```mermaid
flowchart LR
    subgraph Prod["Live Production Service (SQLite + HTTP)"]
        API["POST /api/checkout/settle\n(services/checkout_engine.py)"]
        DB[("production_ledger.db")]
        API --> DB
    end

    subgraph SwitchRoom["Switch AI Shared Room (room://mend-prod-incidents)"]
        Recon["@mend-recon\nAST & Traceback Forensics"]
        Forge["@mend-forge\nUnified Diff & Unittest Runner"]
        Guard["@mend-guard\nSwitch Trust Guardrails (99.4%)"]
        Recon -->|AST Context| Forge
        Forge -->|Candidate Diff + 4/4 Tests| Guard
    end

    subgraph Human["Human Teammates & Interfaces"]
        TG["Telegram (@mend_switch_bot)\nInline Approval Buttons & Chat"]
        Voice["Wispr Flow / Voice Commands\n('trigger bug', 'ship it')"]
        Web["Mend Switch Web Console\n(Live Split-Screen Telemetry)"]
    end

    API -->|Unhandled 500 Exception| Recon
    Guard <-->|Two-Way Bridge| TG
    Guard <-->|Real-Time Sync| Web
    Voice --> Web
    Guard -->|Hot-Reload & Replay TX (200 OK)| API
```

---

## ✨ Key Features (100% Real Execution — Zero Dummy Data)

- **Real SQLite Financial Settlement Engine**: Processes multi-currency (`USD`, `EUR`, `GBP`, `NGN`, `KES`) settlements in [`services/checkout_engine.py`](./services/checkout_engine.py) and persists atomic ledger rows to `data/production_ledger.db`.
- **Real Reproducible Production Bugs**:
  1. **100% Promotional Voucher Bug (`ZeroDivisionError`)**: When `gross_cents == discount_cents`, `net_cents` becomes `0`, crashing `calculate_effective_fee_bps()` at line 105.
  2. **African FX Exponent Bug (`KeyError: 'NGN'`)**: When settling Nigerian Naira (`NGN`) or Kenyan Shilling (`KES`) orders, `DECIMAL_EXPONENTS[currency]` throws an unhandled `KeyError`.
- **Real Python `ast`, `difflib`, and `unittest` Execution**: `@mend-recon` and `@mend-forge` inspect actual AST nodes on disk and execute `python3 -m unittest discover -s tests -v` via `subprocess`.
- **Real Two-Way Telegram Bot Integration (`@mend_switch_bot`)**: Uses a single Telegram Bot token to bridge all 3 Switch Room agents (`@mend-recon`, `@mend-forge`, `@mend-guard`) with interactive inline keyboard approval buttons.
- **Voice-First Incident Response (Code with Wispr)**: Built-in voice command integration allowing engineers to trigger diagnostics, run tests, and ship hotfixes hands-free by voice.

---

## ⚡ Quickstart

### 1. Clone & Configure Environment
```bash
cd mend
# Add your Telegram Bot Token from @BotFather to .env
printf "Enter TELEGRAM_BOT_TOKEN (typing hidden): " && read -s val && echo && echo "TELEGRAM_BOT_TOKEN=$val" >> .env && echo "Saved."
```

### 2. Run the Test Suite Directly
```bash
python3 -m unittest discover -s tests -v
```

### 3. Launch the Mend Switch Room & Production Server
```bash
python3 server.py
```
Open **[http://127.0.0.1:8765](http://127.0.0.1:8765)** in your browser and open **`@mend_switch_bot`** in Telegram!

---

## 💬 Room Commands (Telegram & Switch Console)

| Command | Agent Triggered | Action |
| :--- | :--- | :--- |
| `trigger bug` | `@mend-recon` → `@mend-forge` → `@mend-guard` | Fires a live 100% promo voucher checkout (`$250.00`), catches the `500 ZeroDivisionError`, runs AST forensics, synthesizes the diff, runs `unittest`, and posts approval buttons to Telegram. |
| `run tests` | `@mend-forge` | Executes `python3 -m unittest discover -s tests -v` and posts live results to the room. |
| `ship it` / `approve` | `@mend-guard` | Applies the audited patch to `services/checkout_engine.py`, hot-reloads the module with zero downtime, and replays the failed transaction (`200 OK`). |
| `reset` | `switch-core` | Resets `services/checkout_engine.py` back to the unpatched baseline for repeatable live demos. |


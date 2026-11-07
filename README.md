# Mend

**Autonomous Multi-Agent Incident Forensics & Live Hotfix Room on Switch AI + Telegram**

[![Hackathon](https://img.shields.io/badge/Flip%20the%20Switch-WeMakeDevs%20%C3%97%20DevTools%20Academy-black?style=flat-square)](https://www.wemakedevs.org/hackathons/switch)
[![Track](https://img.shields.io/badge/Track-Best%20Business%20Workflow-black?style=flat-square)](https://www.wemakedevs.org/hackathons/switch)
[![Switch Protocol](https://img.shields.io/badge/Switch%20AI-Room%20Protocol-black?style=flat-square)](https://github.com/sandbox-quantum/switch)
[![Telegram](https://img.shields.io/badge/Telegram-@mend__switch__bot-blue?style=flat-square)](https://t.me/mend_switch_bot)
[![Video Demo](https://img.shields.io/badge/Loom-Walkthrough%20Video-orange?style=flat-square)](https://www.loom.com/share/2f8163a7cc5c4f3ea2e3913a704dac23)

---

## 📺 Live Video Walkthrough

**Watch the full 2-minute live demo on Loom:**  
👉 **[https://www.loom.com/share/2f8163a7cc5c4f3ea2e3913a704dac23](https://www.loom.com/share/2f8163a7cc5c4f3ea2e3913a704dac23)**

---

## What is Mend?

When a production API or website crashes in the middle of the night, engineering teams face a painful reality:
1. Monitoring tools (like Sentry or Datadog) only **alert** you that something broke—they cannot fix it.
2. AI coding assistants (like Claude Code or Cursor) are trapped inside an engineer's **laptop terminal**. If you are away from your computer, in bed, or in transit, they are useless.
3. Every minute of downtime costs revenue, user trust, and team sanity.

**Mend** bridges this gap using the **Switch AI Room Protocol**. 

Instead of isolating AI agents on a developer's machine, Mend deploys **three specialized AI teammates into a shared Telegram room (`@mend_switch_bot`)**. When a runtime crash occurs in production, the agents isolate the bug, write the code fix, test it, and present the on-call engineer with a one-tap approval button right on their phone.

---

## How It Works: The Multi-Agent Pipeline

```
  [ Production Service Crashes ]
                 │
                 ▼ (Unhandled HTTP 500)
    ┌───────────────────────────┐
    │  @mend-recon              │  Parses stack frames & Python Abstract Syntax
    │  (Forensics & AST Agent)  │  Tree (AST) on disk to locate the exact crashing line.
    └────────────┬──────────────┘
                 │
                 ▼ (Hands off root-cause context)
    ┌───────────────────────────┐
    │  @mend-forge              │  Synthesizes a minimal unified git diff and executes
    │  (Patch & Test Agent)     │  the full unittest suite (proving 4/4 passing tests).
    └────────────┬──────────────┘
                 │
                 ▼ (Hands off candidate diff)
    ┌───────────────────────────┐
    │  @mend-guard              │  Runs Switch Trust security guardrails (syntax checks,
    │  (Safety & Deploy Agent)  │  no dynamic code execution, DLP token scans, blast radius).
    └────────────┬──────────────┘
                 │
                 ▼ (Presents inline approval card on mobile)
    ┌───────────────────────────┐
    │  Human Operator           │  Reviews diff on Telegram and taps:
    │  (Telegram Mobile / Web)  │  [ Approve & Deploy Hotfix ]
    └────────────┬──────────────┘
                 │
                 ▼
  [ Zero-Downtime Hot-Reload & Failed Request Replay -> HTTP 200 OK ]
```

---

## The Three Switch Agents

| Agent | Role | Responsibility |
| :--- | :--- | :--- |
| **`@mend-recon`** | Forensics & AST Inspector | Intercepts unhandled exceptions (`ZeroDivisionError`, `KeyError`, etc.), inspects the live Python AST and stack frames on disk, and extracts the exact failing line and request payload. |
| **`@mend-forge`** | Surgical Patch & Test Runner | Generates the minimal git diff fixing the root cause, and runs `python3 -m unittest discover -s tests -v` in an isolated sandbox before and after patching (`0/4` → `4/4` passing). |
| **`@mend-guard`** | Switch Trust & Deployment Gate | Audits candidate code against Switch Trust security guardrails (clean syntax, 0 forbidden dynamic execution calls like `eval`/`os.system`, no leaked secrets, blast radius <= 45 LOC), and gates hot-reloads behind explicit human approval in Telegram. |

---

## Key Features

- **Real Execution (Zero Mock Data)**: Every action in Mend operates on real code, real Python AST parsing, real `difflib` unified diffs, real `unittest` runs, and a real SQLite database.
- **Two-Way Synchronization**: Messages sent in Telegram appear instantly on the web developer console, and console commands stream back to Telegram.
- **Switch Template Compatibility**: Includes official Switch v1 YAML templates (`templates/mend-incident-warroom.template.yaml` and `templates/mend-hotfix-workroom.template.yaml`) ready to import directly into the **Switch Console** desktop application.
- **Voice-Enabled (Code with Wispr)**: Supports voice commands (`"trigger bug"`, `"run tests"`, `"ship it"`) via microphone or Wispr Flow.

---

## Project Structure

```
mend/
├── server.py                        # Threaded HTTP backend + Telegram Bot API polling daemon
├── services/
│   └── checkout_engine.py           # Target production microservice backed by SQLite
├── switch_room/
│   ├── orchestrator.py              # Mend multi-agent orchestrator & room state manager
│   └── guardrails.py                # Switch Trust AST & DLP security audit engine
├── tests/
│   └── test_checkout_engine.py      # Real unittest regression suite (4 tests)
├── templates/
│   ├── mend-incident-warroom.template.yaml  # Official Switch Console room template
│   └── mend-hotfix-workroom.template.yaml  # Official Switch Console hotfix template
├── web/
│   └── index.html                   # High-contrast monochrome developer command center
├── data/                            # Persistent SQLite storage (production ledger + room messages)
└── scripts/
    ├── render_demo_video.py         # Automated walkthrough and screenshot pipeline
    └── encode_mp4.m                 # Native macOS AVFoundation 1080p MP4 encoder
```

---

## Quickstart (Run it Locally in 60 Seconds)

### 1. Prerequisites
- macOS or Linux with **Python 3.9+**
- (Optional) A Telegram Bot Token from [@BotFather](https://t.me/BotFather)

### 2. Clone & Setup
```bash
git clone https://github.com/<your-username>/mend.git
cd mend

# Copy environment template
cp .env.example .env

# Add your Telegram Bot Token to .env
# (If omitted, Mend runs in local web console mode)
echo "TELEGRAM_BOT_TOKEN=your_token_here" >> .env
```

### 3. Run Unit Tests
```bash
python3 -m unittest discover -s tests -v
```

### 4. Start the Mend Server
```bash
python3 server.py
```
Open **`http://127.0.0.1:8765`** in your browser and open **`@mend_switch_bot`** on Telegram!

---

## How to Test the Demo Flow

1. Open **`http://127.0.0.1:8765`** and open your Telegram chat with the bot.
2. Click **`SETTLE STANDARD ORDER`** on the web dashboard (or send `hello` in Telegram). You will see a normal transaction settle with `HTTP 200 OK`.
3. Click **`EXECUTE 100% PROMO VOUCHER`** (or send `trigger bug` in Telegram).
   - The checkout engine will encounter a real `ZeroDivisionError: division by zero` at line 105.
   - Within 2 seconds, `@mend-recon`, `@mend-forge`, and `@mend-guard` will diagnose the crash, run all tests, and send an approval card to Telegram.
4. On Telegram, tap **`[Approve & Deploy Hotfix]`** (or reply `ship it`).
   - The file `services/checkout_engine.py` will be patched on disk.
   - The module will hot-reload with zero downtime.
   - The failed voucher transaction will replay and settle with `HTTP 200 OK`.

---

## Built For

- **Flip the Switch Hackathon** hosted by **WeMakeDevs** & **DevTools Academy**, powered by **Switch AI**.
- **Tracks**: Best Business Workflow ($2,000) & Code with Wispr ($500).

---

## License

Apache 2.0. Built with pride by Popoola Rahmat.

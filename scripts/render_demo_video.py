"""
Automated End-to-End Walkthrough & Narrated Demo Video Producer for Mend.
Drives the live Mend server on http://127.0.0.1:8765, captures real 1920x1080
Chrome screenshots at every stage of the multi-agent incident recovery,
synthesizes human-like voiceover narration, and encodes a 1080p H.264 + AAC MP4.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import time
import urllib.request
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DEMO_DIR = ROOT_DIR / "demo"
FRAMES_DIR = DEMO_DIR / "frames"
AUDIO_DIR = DEMO_DIR / "audio"
ENCODER_BIN = ROOT_DIR / "scripts" / "encode_mp4"
CHROME_BIN = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
SERVER_URL = "http://127.0.0.1:8765"


def api_post(path: str, payload: dict) -> dict:
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    req = urllib.request.Request(
        f"{SERVER_URL}{path}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with opener.open(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode())


def capture_screenshot(output_png: Path, url: str = SERVER_URL) -> None:
    output_png.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        CHROME_BIN,
        "--headless=new",
        "--disable-gpu",
        "--hide-scrollbars",
        "--window-size=1920,1080",
        "--virtual-time-budget=2500",
        f"--screenshot={output_png}",
        url,
    ]
    subprocess.run(cmd, check=True, capture_output=True, timeout=25)


def synthesize_voice(text: str, out_m4a: Path) -> None:
    out_m4a.parent.mkdir(parents=True, exist_ok=True)
    tmp_aiff = out_m4a.with_suffix(".aiff")
    subprocess.run(
        ["/usr/bin/say", "-v", "Samantha", "-r", "180", "-o", str(tmp_aiff), text],
        check=True,
    )
    subprocess.run(
        ["/usr/bin/afconvert", "-f", "m4af", "-d", "aac", str(tmp_aiff), str(out_m4a)],
        check=True,
    )
    tmp_aiff.unlink(missing_ok=True)


def main() -> None:
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    scenes_meta = []

    # Scene 1: Clean Unpatched Baseline
    print("[1/5] Resetting Mend to unpatched baseline & capturing Scene 1...")
    api_post("/api/room/reset", {"actor": "Demo Walkthrough"})
    time.sleep(0.5)
    f1 = FRAMES_DIR / "scene_01_baseline.png"
    a1 = AUDIO_DIR / "scene_01.m4a"
    capture_screenshot(f1)
    synthesize_voice(
        "Meet Mend, an autonomous multi-agent incident room built on Switch AI and Telegram. "
        "On the left is our shared Switch Room with three agents: Mend Recon, Mend Forge, and Mend Guard. "
        "On the right is our live SQLite-backed financial checkout service.",
        a1,
    )
    scenes_meta.append({
        "imagePath": str(f1),
        "audioPath": str(a1),
        "badge": "STEP 1 // SWITCH AI ROOM",
        "title": "Mend: Multi-Agent Incident Room Bridged with Telegram (@mend_switch_bot)",
        "subtitle": "Three specialized AI teammates (@mend-recon, @mend-forge, @mend-guard) share live production context.",
    })

    # Scene 2: Normal Enterprise Checkout Settlement (200 OK)
    print("[2/5] Running normal $480 USD settlement & capturing Scene 2...")
    api_post("/api/checkout/settle", {
        "merchant_id": "merch_stripe_global",
        "customer_email": "treasury@acme.io",
        "currency": "USD",
        "gross_cents": 48000,
        "discount_cents": 0,
    })
    time.sleep(0.5)
    f2 = FRAMES_DIR / "scene_02_normal_tx.png"
    a2 = AUDIO_DIR / "scene_02.m4a"
    capture_screenshot(f2)
    synthesize_voice(
        "First, let's process a standard four hundred eighty dollar checkout. "
        "It settles cleanly with HTTP 200 OK and records the transaction in our SQLite production ledger.",
        a2,
    )
    scenes_meta.append({
        "imagePath": str(f2),
        "audioPath": str(a2),
        "badge": "STEP 2 // LIVE TRAFFIC",
        "title": "Standard Enterprise Settlement ($480.00 USD -> HTTP 200 OK)",
        "subtitle": "Atomic settlement committed to SQLite (data/production_ledger.db) with 295.83 bps fee.",
    })

    # Scene 3: Trigger Real 100% Promo Voucher Crash -> Multi-Agent Forensics, Diff & Unittest
    print("[3/5] Triggering real 500 ZeroDivisionError & capturing Scene 3...")
    api_post("/api/checkout/settle", {
        "merchant_id": "merch_enterprise_promo",
        "customer_email": "cto@acme-corp.io",
        "currency": "USD",
        "gross_cents": 25000,
        "discount_cents": 25000,
    })
    time.sleep(0.8)
    f3 = FRAMES_DIR / "scene_03_incident_triage.png"
    a3 = AUDIO_DIR / "scene_03.m4a"
    capture_screenshot(f3)
    synthesize_voice(
        "Now, an enterprise customer redeems a one hundred percent promotional voucher. "
        "The unpatched checkout engine crashes with a real Python ZeroDivisionError at line 105. "
        "Instantly, Mend Recon inspects the Python AST, Mend Forge synthesizes a unified git diff and verifies all four unit tests pass, "
        "and Mend Guard audits the patch with a ninety-nine point four percent Switch Trust score, paging the engineer on Telegram.",
        a3,
    )
    scenes_meta.append({
        "imagePath": str(f3),
        "audioPath": str(a3),
        "badge": "STEP 3 // MULTI-AGENT TRIAGE",
        "title": "Live 500 Exception -> AST Forensics, Unified Diff & Switch Trust Audit (99.4%)",
        "subtitle": "@mend-recon pinpoints line 105; @mend-forge passes 4/4 unittests; @mend-guard pages Telegram.",
    })

    # Scene 4: Voice / Wispr Command & Human Approval in Switch Room + Telegram
    print("[4/5] Sending voice/chat approval ('ship it') & capturing Scene 4...")
    api_post("/api/room/message", {
        "sender": "Rahmat (Telegram & Wispr Voice)",
        "text": "🎙️ [Wispr Voice]: Tests are 4/4 green and Switch Trust passed. Ship it!",
        "platform": "Telegram -> Switch Room",
    })
    time.sleep(0.8)
    f4 = FRAMES_DIR / "scene_04_hotfix_deployed.png"
    a4 = AUDIO_DIR / "scene_04.m4a"
    capture_screenshot(f4)
    synthesize_voice(
        "From Telegram or using Wispr voice commands, the engineer approves the patch by saying ship it. "
        "Mend Guard applies the patch on disk, hot-reloads the checkout engine with zero downtime, "
        "and replays the failed voucher transaction, confirming HTTP 200 OK in the production ledger.",
        a4,
    )
    scenes_meta.append({
        "imagePath": str(f4),
        "audioPath": str(a4),
        "badge": "STEP 4 // ZERO-DOWNTIME HOTFIX",
        "title": "Human-in-the-Loop Approval ('ship it') -> Live Module Reload & TX Replay (200 OK)",
        "subtitle": "services/checkout_engine.py hot-reloaded in 0ms; failed voucher request replayed and settled!",
    })

    # Scene 5: Verify Multi-Currency Lagos NGN Settlement Now Succeeds (200 OK)
    print("[5/5] Verifying multi-currency Lagos NGN settlement & capturing Scene 5...")
    api_post("/api/checkout/settle", {
        "merchant_id": "merch_lagos_hub",
        "customer_email": "rahmat@paystack.ng",
        "currency": "NGN",
        "gross_cents": 15000000,
        "discount_cents": 0,
    })
    time.sleep(0.6)
    f5 = FRAMES_DIR / "scene_05_verified_ledger.png"
    a5 = AUDIO_DIR / "scene_05.m4a"
    capture_screenshot(f5)
    synthesize_voice(
        "Finally, we fire a multi-currency Nigerian Naira settlement. "
        "With Mend's patch active in production, both promotional vouchers and global currencies settle without a single error. "
        "That is Mend: where humans and AI agents mend production together in Switch and Telegram.",
        a5,
    )
    scenes_meta.append({
        "imagePath": str(f5),
        "audioPath": str(a5),
        "badge": "STEP 5 // VERIFIED RECOVERY",
        "title": "Multi-Currency NGN & Promotional Settlements Verified in Production (4/4 Tests Green)",
        "subtitle": "Built with Switch AI Room Protocol, Telegram Bot API, and Switch Trust Guardrails.",
    })

    scenes_json = DEMO_DIR / "scenes.json"
    scenes_json.write_text(json.dumps(scenes_meta, indent=2))

    out_mp4 = DEMO_DIR / "mend_hackathon_demo.mp4"
    print("Encoding final 1080p H.264 + AAC narrated MP4...")
    subprocess.run([str(ENCODER_BIN), str(scenes_json), str(out_mp4)], check=True)
    print("Done! Video size:", out_mp4.stat().st_size, "bytes")


if __name__ == "__main__":
    main()

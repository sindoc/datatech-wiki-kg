#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shlex
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUBSCRIBERS_PATH = ROOT / "outreach" / "subscribers.json"
TEMPLATE_PATH = ROOT / "templates" / "email_invitation.txt"


def load_subscribers(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [item for item in payload.get("subscribers", []) if item.get("status") == "opted-in"]


def render_message(name: str) -> tuple[str, str]:
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    rendered = template.format(name=name)
    subject_line, _, body = rendered.partition("\n\n")
    subject = subject_line.removeprefix("Subject: ").strip()
    return subject, body.strip()


def send_one(recipient: dict) -> int:
    subject, body = render_message(recipient["name"])
    cmd = [
        "python3",
        "-m",
        "singine.command",
        "smtp",
        "send",
        "--to",
        recipient["email"],
        "--subject",
        subject,
        "--body",
        body,
    ]
    proc = subprocess.run(cmd, check=False)
    return proc.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="Preview or send updates to opted-in recipients.")
    parser.add_argument("--send", action="store_true", help="Actually send via singine smtp.")
    args = parser.parse_args()

    if not SUBSCRIBERS_PATH.exists():
        print(f"missing local subscriber file: {SUBSCRIBERS_PATH}")
        print("copy outreach/subscribers.template.json to outreach/subscribers.json and edit locally")
        return 1

    recipients = load_subscribers(SUBSCRIBERS_PATH)
    if not recipients:
        print("no opted-in recipients found")
        return 0

    for recipient in recipients:
        subject, body = render_message(recipient["name"])
        cmd = [
            "python3",
            "-m",
            "singine.command",
            "smtp",
            "send",
            "--to",
            recipient["email"],
            "--subject",
            subject,
            "--body",
            body,
        ]
        if args.send:
            code = send_one(recipient)
            print(f"sent {recipient['email']} exit={code}")
        else:
            print(shlex.join(cmd))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

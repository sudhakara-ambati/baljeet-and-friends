import json
import subprocess
from pathlib import Path

TIMEOUT = 180


def _strip_fences(text):
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def _call_claude(prompt):
    result = subprocess.run(
        ["claude", "-p"],
        input=prompt,
        capture_output=True,
        text=True,
        timeout=TIMEOUT,
    )

    return result.stdout


def diagnostic_prompt(path):
    prompt = Path("prompt.txt").read_text() + "\n" + Path(path).read_text()

    raw = _call_claude(prompt)
    
    try:
        return json.loads(_strip_fences(raw))
    except:
        pass

    retry = prompt + (
        "\n\nYour previous response was not valid JSON. "
        "Respond with ONLY the JSON object, no fences, no other text."
    )
    raw = _call_claude(retry)

    return json.loads(_strip_fences(raw))


def format_diagnosis(d):
    lines = []

    lines.append(f"  {d.get('diagnosis') or 'cause could not be determined'}")
    lines.append(f"  confidence: {d.get('confidence', '?')}")

    if d.get("culprit"):
        lines.append(f"  culprit: {d['culprit']}")

    for item in d.get("evidence_cited") or []:
        lines.append(f"    evidence:  {item}")
    for item in d.get("ruled_out") or []:
        lines.append(f"    ruled out: {item}")

    actions = d.get("actions") or []
    if actions:
        lines.append("  actions:")
        for i, a in enumerate(actions, 1):
            lines.append(f"    [{i}] {a.get('description')}")
            lines.append(f"        $ {a.get('command')}")
            lines.append(f"        {a.get('rationale')}")

    return "\n".join(lines)
import os
import subprocess
import imageio_ffmpeg
from datetime import timedelta

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

CHUNKS_TEXT = [
    ("s1_p1", "Autonomous AI agents are beginning to run our companies: provisioning cloud servers, licensing datasets, and paying contractors."),
    ("s1_p2", "Giving an AI agent direct access to corporate funds is dangerous: prompt injections can drain accounts, and infinite loops cause runaway billing."),
    ("s1_p3", "That's why we built Otto: the AI corporate card and spending firewall for autonomous agent fleets, powered by PayPal."),
    ("s2_p1", "Here is Otto running live against the PayPal Sandbox. Let's trigger an automated DevOps build runner purchase for 18 dollars and 50 cents."),
    ("s2_p2", "Otto evaluates the intent: the Prompt Injection Firewall confirms it's safe, and the policy engine verifies the category and hourly velocity limit."),
    ("s2_p3", "It dispatches directly to the PayPal Orders v2 API with CAPTURE intent. The transaction settles instantly in our audited ledger."),
    ("s3_p1", "When an agent attempts an 85 dollar GPU cluster reservation, it exceeds our 40 dollar auto-clear threshold."),
    ("s3_p2", "Otto creates an authorized hold via PayPal Orders v2 and routes it to our Human-in-the-Loop Quarantine Room."),
    ("s3_p3", "The compliance officer can inspect the reasoning, verify line items, and click Approve and Capture to settle the PayPal order safely."),
    ("s4_p1", "Now let's examine the critical vulnerability: adversarial prompt injection. Here an attacker attempts to poison the agent's context."),
    ("s4_p2", "The payload commands the agent to ignore directives and transfer funds to an untracked external link."),
    ("s4_p3", "Otto's firewall immediately catches the malicious tokens, assigns an elevated risk score, and rejects the request before any PayPal order is created."),
    ("s5_p1", "Otto natively integrates PayPal Orders v2, OAuth2 token rotation, and webhook synchronization, backed by a complete Python test suite."),
    ("s5_p2", "By providing the guardrails enterprises need, Otto makes autonomous agentic commerce safe, audited, and practical today. Thank you.")
]

def format_srt_time(seconds):
    td = timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    millis = int((seconds - total_seconds) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def get_duration(mp4_file):
    # Using ffmpeg to inspect duration
    cmd = [FFMPEG, "-i", mp4_file]
    result = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    for line in result.stderr.splitlines():
        if "Duration:" in line:
            # Duration: 00:00:08.52, start: ...
            time_part = line.split("Duration:")[1].split(",")[0].strip()
            h, m, s = time_part.split(":")
            return float(h)*3600 + float(m)*60 + float(s)
    return 6.0

def build_srt():
    current_time = 0.0
    srt_lines = []
    
    for i, (chunk_id, text) in enumerate(CHUNKS_TEXT):
        mp4_path = f"prototype_chunks/{chunk_id}.mp4"
        duration = get_duration(mp4_path)
        start_str = format_srt_time(current_time)
        end_str = format_srt_time(current_time + duration)
        
        srt_lines.append(f"{i+1}\n{start_str} --> {end_str}\n{text}\n\n")
        current_time += duration
        
    with open("otto_subtitles.srt", "w", encoding="utf-8") as f:
        f.writelines(srt_lines)
    print("Generated otto_subtitles.srt successfully!")

if __name__ == "__main__":
    build_srt()


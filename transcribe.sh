#!/bin/bash
# Run this once in your terminal from anywhere.
# Output: mir_system/transcript.txt

AUDIO="$HOME/Library/Application Support/Claude/local-agent-mode-sessions/8bc89a44-fdca-4b82-8624-9c68765359e8/6382d625-6c74-43f7-b3bb-02b59448adc7/local_20cd5f8f-7d6c-4a6d-bb57-83958aa9096e/uploads/hi.m4a"
OUT="$HOME/.gemini/antigravity/scratch/tech_projects/mir_system/transcript.txt"

# Install whisper if not present
if ! python3 -c "import whisper" 2>/dev/null; then
  echo "Installing whisper..."
  pip3 install openai-whisper --break-system-packages 2>/dev/null || pip3 install openai-whisper
fi

echo "Transcribing... (this takes a few minutes for a 40min call)"
python3 - <<'PYEOF'
import whisper, os, sys

audio_path = os.path.expanduser(
    "~/Library/Application Support/Claude/local-agent-mode-sessions/"
    "8bc89a44-fdca-4b82-8624-9c68765359e8/6382d625-6c74-43f7-b3bb-02b59448adc7/"
    "local_20cd5f8f-7d6c-4a6d-bb57-83958aa9096e/uploads/hi.m4a"
)
out_path = os.path.expanduser(
    "~/.gemini/antigravity/scratch/tech_projects/mir_system/transcript.txt"
)

model = whisper.load_model("base")
print("Model loaded. Transcribing...")
result = model.transcribe(audio_path, verbose=False)

segments = result["segments"]
lines = []
for s in segments:
    start = int(s["start"])
    m, sec = divmod(start, 60)
    lines.append(f"[{m:02d}:{sec:02d}] {s['text'].strip()}")

full = "\n".join(lines)

with open(out_path, "w") as f:
    f.write(full)

print(f"\nDone. Transcript saved to:\n{out_path}")
print(f"\n--- PREVIEW (first 20 lines) ---")
print("\n".join(lines[:20]))
PYEOF

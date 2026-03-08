import os, sys, re
from datetime import datetime as dt

def log(m): sys.stderr.write(f"!! {m}\n")

def sync(tid, res=None, stat=None, prom=None, sig=None):
    tqd = os.path.join(os.getcwd(), "agent")
    tqp = os.path.join(tqd, "TASK_QUEUE.md")
    if not os.path.exists(tqd): os.makedirs(tqd)
    if not os.path.exists(tqp):
        with open(tqp, "w") as f: f.write("# TASK QUEUE\n# LAST_GLOBAL_SYNC: 2026-01-01T00:00:00Z\n\n## ACTIVE SIGNALS\n\n## PRIORITIZED BACKLOG\n")
    try:
        with open(tqp, "r", encoding="utf-8") as f: lines = f.readlines()
        now = dt.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        in_t = False
        for i, l in enumerate(lines):
            if l.startswith("# LAST_GLOBAL_SYNC:"): lines[i] = f"# LAST_GLOBAL_SYNC: {now}\n"
            if f"**{tid}**" in l:
                in_t = True
                if stat == "DONE": lines[i] = l.replace("[ ]", "[x]")
            if in_t:
                if res and "Reserved:" in l: 
                    lines[i] = f"    - Reserved: {res} @ {now}\n" if res != "NONE" else "    - Reserved: NONE\n"
                if stat and "Updated:" in l: lines[i] = f"    - Updated: {now}\n"
                if prom and "Promise:" in l: lines[i] = f"    - Promise: {prom}\n"
                if sig and "Signals:" in l: lines[i] = f"    - Signals: {sig}\n"
                if l.strip() == "" or (l.startswith("- [ ]") and f"**{tid}**" not in l): in_t = False
        with open(tqp, "w", encoding="utf-8") as f: f.writelines(lines)
        print(f"OK: {tid}")
        return True
    except Exception as e:
        log(e); return False

if __name__ == "__main__":
    if len(sys.argv) < 2: sys.exit(1)
    tid = sys.argv[1]; res = stat = prom = sig = None
    for i in range(2, len(sys.argv), 2):
        k = sys.argv[i]; v = sys.argv[i+1] if i+1 < len(sys.argv) else None
        if k == "--reserve": res = v
        elif k == "--done": stat = "DONE"
        elif k == "--promise": prom = v
        elif k == "--signal": sig = v
    sync(tid, res, stat, prom, sig)

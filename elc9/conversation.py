"""对话存储 — 从原始 Elc9_Code.py 拆分。"""
import json, os, threading
from .config import CONV_DIR

_CONV_LOCK = threading.RLock()

def get_conv_path(conv_id):
    return os.path.join(CONV_DIR, f"{conv_id}.json")

def load_conversation_by_path(full_path):
    """按完整路径加载对话（跨 workspace）"""
    if not os.path.exists(full_path): return None
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except: return None

def load_conversation(conv_id):
    path = get_conv_path(conv_id)
    if not os.path.exists(path): return None
    try:
        with open(path,'r',encoding='utf-8') as f: return json.load(f)
    except: return None

def save_conversation(conv_id, data):
    from .config import ensure_conv_dir
    ensure_conv_dir()
    path = get_conv_path(conv_id)
    _write_conv_file(path, data)

def save_conversation_to_path(full_path, data):
    """按完整路径保存对话（跨 workspace）"""
    _write_conv_file(full_path, data)

def _write_conv_file(path, data):
    try:
        with _CONV_LOCK:
            existing = None
            if os.path.exists(path):
                try:
                    with open(path,'r',encoding='utf-8') as f: existing = json.load(f)
                except: pass
            if existing and existing.get("sub_agent_logs"):
                data["sub_agent_logs"] = existing["sub_agent_logs"]
            # 确保目录存在
            d = os.path.dirname(path)
            if d and not os.path.exists(d):
                os.makedirs(d, exist_ok=True)
            with open(path,'w',encoding='utf-8') as f: json.dump(data,f,indent=2,ensure_ascii=False)
    except Exception as e: print(f"[-] 保存对话失败: {e}")

def append_sub_agent_messages(conv_id, agent_tag, messages):
    """Thread-safe append of sub-agent messages to separate sub_agent_logs section."""
    if not conv_id: return
    from .config import ensure_conv_dir
    ensure_conv_dir()
    path = get_conv_path(conv_id)
    try:
        with _CONV_LOCK:
            data = None
            if os.path.exists(path):
                try:
                    with open(path,'r',encoding='utf-8') as f: data = json.load(f)
                except: pass
            if data is None:
                data = {"messages": [], "sub_agent_logs": []}
            if "sub_agent_logs" not in data:
                data["sub_agent_logs"] = []
            entry = {"agent": agent_tag, "messages": messages}
            data["sub_agent_logs"].append(entry)
            with open(path,'w',encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e: pass

def get_all_conversations():
    from .config import ensure_conv_dir
    ensure_conv_dir()
    files = os.listdir(CONV_DIR)
    convs = []
    for f in files:
        if f.endswith(".json"):
            cid = f[:-5]; data = load_conversation(cid)
            if data: convs.append((cid, data))
    convs.sort(key=lambda x: x[1].get("last_active",""), reverse=True)
    return convs

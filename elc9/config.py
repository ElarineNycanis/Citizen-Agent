"""配置管理 — 从原始 Elc9_Code.py 拆分。"""
import json, os, sys
from datetime import datetime

CONFIG_FILE = os.path.join(os.path.expanduser("~"), "CitizenAgentConfig.json")
CONV_DIR = "conversations"

def ensure_conv_dir():
    if not os.path.exists(CONV_DIR): os.makedirs(CONV_DIR)

def identify_workspace():
    try:
        p = os.path.abspath(sys.argv[0])
        if os.path.isfile(p): return os.path.dirname(p)
    except: pass
    return os.getcwd()

WORKSPACE_DIR = identify_workspace()

def init_workspace_identity():
    ensure_conv_dir()
    f = os.path.join(WORKSPACE_DIR, ".workspace_identity")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(f,'w',encoding='utf-8') as fp:
            json.dump({"workspace":WORKSPACE_DIR,"initialized_at":now,"status":"active","identity":"Citizen Agent"},fp,indent=2,ensure_ascii=False)
        pass  # 启动信息移至 main.py 统一显示
    except Exception as e: print(f"[-] 基地初始化失败: {e}")

init_workspace_identity()

def load_config():
    if not os.path.exists(CONFIG_FILE): return {}
    try:
        with open(CONFIG_FILE,'r',encoding='utf-8') as f: return json.load(f)
    except Exception as e: print(f"[-] 配置文件读取失败: {e}"); return {}

DEFAULT_COLORS = {
    "pink": "95",
    "green": "92",
    "yellow": "93",
    "dark_gray": "90",
    "dark_yellow": "38;2;170;165;120",
    "cyan": "38;2;100;255;220",
    "red": "91",
    "dark_red": "38;2;255;80;80",
    "reply_ai": "38;2;255;255;255",
    "white": "0",
    "agent_1": "38;2;100;255;200",
    "agent_2": "38;2;255;200;100",
    "agent_3": "38;2;150;255;150",
    "agent_4": "38;2;255;150;200",
    "agent_5": "38;2;150;180;255",
}

def get_color(config, name):
    colors = config.get("colors", {})
    code = colors.get(name, DEFAULT_COLORS.get(name, "0"))
    return f'\033[{code}m'

def save_config(config):
    try:
        tmp = CONFIG_FILE + ".tmp"
        with open(tmp,'w',encoding='utf-8') as f: json.dump(config,f,indent=2,ensure_ascii=False)
        os.replace(tmp, CONFIG_FILE)
    except Exception as e: print(f"[-] 保存配置失败: {e}")

def register_conversation(config, conv_id, title, path, workspace):
    """向 All_Conversations 注册/更新一条对话记录"""
    entries = config.get("All_Conversations", [])
    for e in entries:
        if e.get("id") == conv_id:
            e["title"] = title
            # 不覆盖 path 和 workspace——这些是对话的原始归属
            return
    entries.append({
        "id": conv_id,
        "title": title,
        "created": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "path": path,
        "workspace": workspace
    })
    config["All_Conversations"] = entries

def get_all_registered_conversations(config):
    """返回 All_Conversations，按 created 倒序"""
    entries = config.get("All_Conversations", [])
    return sorted(entries, key=lambda e: e.get("created", ""), reverse=True)

def remove_conversation_from_registry(config, conv_id):
    """从注册表中删除指定 ID"""
    config["All_Conversations"] = [e for e in config.get("All_Conversations", []) if e.get("id") != conv_id]

def find_registered_conversation(config, conv_id):
    """按 ID 查找一条注册记录，找不到返回 None"""
    for e in config.get("All_Conversations", []):
        if e.get("id") == conv_id:
            return e
    return None

"""交互函数 — 从原始 Elc9_Code.py 拆分。"""
import os, difflib
from .config import load_config, save_config, identify_workspace, get_all_registered_conversations
from .conversation import get_all_conversations, get_conv_path, load_conversation

COMMANDS = {"/history":"查看历史对话并切换","/delete":"批量删除历史对话","/new":"保存当前对话并开始新对话","/quit":"保存当前对话并退出","/discard":"丢弃当前对话（不保存）并退出","/sub":"将复杂任务委托给子代理处理","/sub_status":"查看子代理运行状态","/sub_result":"获取子代理执行结果","/create_picture":"调用 Wanx 生图模型生成图片","/help":"显示所有支持的命令及说明","/?":"同 /help，显示帮助信息"}

def confirm_yes_no(prompt):
    while True:
        ans = input(prompt).strip().lower()
        if ans in ("y","yes"): return True
        if ans in ("n","no"): return False
        print("[-] 请输入 y 或 n")

def show_history(config=None):
    if config is None:
        config = load_config()
    current_ws = identify_workspace()
    local = get_all_conversations()
    registered = get_all_registered_conversations(config)
    # 去重：本地已有的不在外部列表里重复
    local_ids = {cid for cid,_ in local}
    external = [e for e in registered if e.get("workspace") != current_ws and e.get("id") not in local_ids]

    if not local and not external: print("[-] 没有历史对话"); return None
    print("\n历史对话列表："); print("0. 新建对话")

    idx = 0
    entries = []  # [(conv_id, title, extra_info_str, full_path_or_None, workspace_or_None)]

    def fmt_path(full_path, cid):
        """缩短路径显示: F:\CitizenAgent\...\3056e155.json"""
        if not full_path: return ""
        d = os.path.dirname(full_path)
        if len(d) > 30:
            d = d[:3] + "..." + d[-25:]
        return f" | {d}\\{cid[:8]}..."

    for cid, info in local:
        idx += 1
        title = info.get("title","无标题"); created = info.get("created_at","")
        count = len(info.get("messages",[]))
        pt = info.get("total_prompt_tokens",0); ct = info.get("total_completion_tokens",0)
        conv_path = os.path.abspath(get_conv_path(cid))
        path_str = fmt_path(conv_path, cid)
        print(f"{idx}. [{cid[:8]}...] {title} | {count}条消息 | {created}{path_str} | tokens: 发{pt}/收{ct}")
        entries.append((cid, None, None))

    for e in external:
        idx += 1
        ws_short = e.get("workspace","")[:40]
        path_str = fmt_path(e.get("path",""), e["id"])
        print(f"{idx}. [外部] [{e['id'][:8]}...] {e.get('title','无标题')} | {e.get('created','')}{path_str} | {ws_short}")
        entries.append((e["id"], e.get("path"), e.get("workspace")))

    while True:
        ch = input("\n请选择对话编号 (0 新建): ").strip()
        if ch == "0": return (None, None, None)
        try:
            i = int(ch) - 1
            if 0 <= i < len(entries):
                cid, ext_path, ext_ws = entries[i]
                return (cid, ext_path, ext_ws)
        except: pass
        print("[-] 输入无效")

def delete_conversations(config=None):
    if config is None:
        config = load_config()
    current_ws = identify_workspace()
    local = get_all_conversations()
    registered = get_all_registered_conversations(config)
    local_ids = {cid for cid,_ in local}
    external = [e for e in registered if e.get("workspace") != current_ws and e.get("id") not in local_ids]

    if not local and not external: print("[-] 没有可删除的对话"); return False
    print("\n可删除的对话：")

    idx = 0
    entries = []  # [(conv_id, ext_path_or_None, title)]

    for cid, info in local:
        idx += 1
        title = info.get("title","无标题"); count = len(info.get("messages",[]))
        pt = info.get("total_prompt_tokens",0); ct = info.get("total_completion_tokens",0)
        print(f"{idx}. [{cid[:8]}...] {title} | {count}条消息 | tokens: 发{pt}/收{ct}")
        entries.append((cid, None, title))

    for e in external:
        idx += 1
        title = e.get("title","无标题")
        print(f"{idx}. [外部] [{e['id'][:8]}...] {title} | {e.get('created','')}")
        entries.append((e["id"], e.get("path"), title))

    while True:
        raw = input("\n输入序号 (用逗号分隔, 0取消): ").strip()
        if raw == "0": return False
        try:
            indices = [int(x.strip()) - 1 for x in raw.split(",")]
            if any(i < 0 or i >= len(entries) for i in indices): raise ValueError
            break
        except: print("[-] 输入无效")

    to_del = [entries[i] for i in indices]
    to_del_titles = [t for _,_,t in to_del]
    print(f"[-] 即将删除: {', '.join(to_del_titles)}")
    if not confirm_yes_no("确认删除？(y/n): "): print("[*] 取消删除"); return False

    for cid, ext_path, _ in to_del:
        if ext_path:
            # 外部对话：删除文件（如果可访问）
            if os.path.exists(ext_path): os.remove(ext_path)
        else:
            path = get_conv_path(cid)
            if os.path.exists(path): os.remove(path)
        from .config import remove_conversation_from_registry
        remove_conversation_from_registry(config, cid)

    if config.get("active_conversation") in [d[0] for d in to_del]:
        config["active_conversation"] = None
    save_config(config)
    print(f"[+] 已删除 {len(to_del)} 个对话")
    return True

"""主程序 — 从原始 Elc9_Code.py 拆分，逻辑完全不变。"""
import atexit, json, os, sys, threading, difflib, time, requests
from datetime import datetime

from .config import load_config, save_config, get_color, WORKSPACE_DIR, register_conversation
from .conversation import load_conversation, load_conversation_by_path, save_conversation, save_conversation_to_path, get_conv_path
from .api import spinner_with_tokens, process_stream, estimate_tokens
from .tools import execute_tool_call
from .sub_agent import SubAgentManager
from .ui import COMMANDS, confirm_yes_no, show_history, delete_conversations
from .input_area import claude_style_input
from .vision import find_image_paths, call_vision_model

GREEN = '\033[92m'
PINK = '\033[95m'
RESET = '\033[0m'
DARK_GRAY = '\033[90m'
CYAN = '\033[38;2;100;255;220m'
RED = '\033[91m'
DARK_RED = '\033[38;2;255;80;80m'
REPLY_AI = '\033[38;2;255;255;255m'

sub_agent_mgr = SubAgentManager()

def main():
    global PINK, GREEN, DARK_GRAY, CYAN, RED, DARK_RED, REPLY_AI

    # 启动横幅
    title = "CitizenAgent"
    title_grad = ""
    for i, ch in enumerate(title):
        t = i / max(len(title) - 1, 1)
        r = int(225 - 225 * t)
        g = int(0 + 225 * t)
        b = 225
        title_grad += f"\033[38;2;{r};{g};{b}m{ch}"
    title_grad += RESET

    print("=" * 52)
    print(f"|                   {title_grad}                   |")
    print("| Version:v1.0.0                                   |")
    print("| Made by Elarcanine                               |")
    print("| https://github.com/ElarineNycanis/Citizen-Agent  |")
    print("=" * 52)

    config = load_config()
    PINK = get_color(config, "pink")
    GREEN = get_color(config, "green")
    DARK_GRAY = get_color(config, "dark_gray")
    CYAN = get_color(config, "cyan")
    RED = get_color(config, "red")
    DARK_RED = get_color(config, "dark_red")
    REPLY_AI = get_color(config, "reply_ai")

    # ==================== 启动安全确认 ====================
    while True:
        trust = input(f"{PINK}[?] 是否信任该工具及当前环境？(y/n, 默认 n): {RESET}").strip().lower()
        if trust == "y":
            sys.stdout.write('\033[A\033[K')
            sys.stdout.flush()
            break
        elif trust == "" or trust == "n":
            sys.stdout.write('\033[A\033[K')
            sys.stdout.flush()
            print(f"{RED}[-] 已退出: 未信任当前环境{RESET}")
            return
        else:
            sys.stdout.write('\033[A\033[K')
            sys.stdout.flush()

    # 模型配置: 只使用 models 结构
    models_cfg = config.get("models", {})
    if not models_cfg:
        models_cfg = {}
        config["models"] = models_cfg

    def load_model(key, label, is_main=False):
        """加载模型配置，返回 (ok, base_url, model, api_key, endpoint, headers)"""
        cfg = models_cfg.get(key, {})
        api_key = cfg.get("api_key", "").strip()
        base_url = cfg.get("base_url", "").strip()
        model = cfg.get("model", "").strip()

        if api_key and base_url and model:
            try:
                ep = base_url.rstrip("/") + ("/chat/completions" if not base_url.rstrip("/").endswith("/chat/completions") else "")
                hdrs = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                print(f"{GREEN}[+] 已连接 {base_url}（模型 {label}）{RESET}")
                print(f"{GREEN}[+] 模型: {model}（模型 {label}）{RESET}")
                return (True, base_url, model, api_key, ep, hdrs)
            except Exception as e:
                print(f"{RED}[-] 模型 {label}：加载失败 ({e}){RESET}")
        print(f"{RED}[-] 模型 {label}：未配置或加载失败{RESET}")
        return (False, "", "", "", "", {})

    # 主模型
    main_ok, base_url, model, model_api_key, endpoint, headers = load_model("main", "main", True)

    # 视觉模型
    vis_ok, vis_url, vis_model, vis_key, vis_ep, vis_hdrs = load_model("vision", "vision")

    # 生图模型
    gen_ok, gen_url, gen_model, gen_key, gen_ep, gen_hdrs = load_model("image_gen", "image_gen")

    # 首次配置向导
    if not main_ok and not vis_ok:
        print("[*] 未检测到任何模型配置，进入交互式配置向导...")

        config["ai_name"] = input("AI 名称 (默认 AI): ").strip() or "AI"

        print("\n--- 主模型配置 ---")
        config.setdefault("models", {})["main"] = {
            "base_url": input("Base URL (默认 https://api.deepseek.com): ").strip() or "https://api.deepseek.com",
            "model": input("Model (默认 deepseek-chat): ").strip() or "deepseek-chat",
            "api_key": input("API Key: ").strip()
        }

        use_vision = input("\n是否配置视觉模型？(y/n, 默认 n): ").strip().lower()
        if use_vision == "y":
            config.setdefault("models", {})["vision"] = {
                "base_url": input("视觉 Base URL (默认 https://dashscope.aliyuncs.com/compatible-mode/v1): ").strip() or "https://dashscope.aliyuncs.com/compatible-mode/v1",
                "model": input("视觉 Model (默认 qwen-vl-plus): ").strip() or "qwen-vl-plus",
                "api_key": input("视觉 API Key: ").strip()
            }

        use_gen = input("\n是否配置生图模型？(y/n, 默认 n): ").strip().lower()
        if use_gen == "y":
            config.setdefault("models", {})["image_gen"] = {
                "base_url": input("生图 Base URL (默认 https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis): ").strip() or "https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis",
                "model": input("生图 Model (默认 wanx2.1-t2i-turbo): ").strip() or "wanx2.1-t2i-turbo",
                "api_key": input("生图 API Key: ").strip()
            }

        # 是否加载默认完整配置
        print()
        while True:
            use_default = input("是否使用默认工具配置？(y/n, 默认 y): ").strip().lower()
            if use_default == "" or use_default == "y":
                try:
                    with open("config.example.json", "r", encoding="utf-8") as ef:
                        default_cfg = json.load(ef)
                    default_cfg["models"] = config.get("models", {})
                    default_cfg["ai_name"] = config.get("ai_name", "Citizen")
                    config = default_cfg
                    print("[+] 已加载默认工具配置（含 5 个工具、颜色、错误码等）")
                except Exception as e:
                    print(f"[-] 加载默认配置失败: {e}，使用极简配置")
                sys.stdout.write('\033[A\033[K\033[A\033[K')
                sys.stdout.flush()
                break
            elif use_default == "n":
                sys.stdout.write('\033[A\033[K')
                sys.stdout.flush()
                print("[*] 使用极简配置（仅模型，无工具）")
                break
            else:
                sys.stdout.write('\033[A\033[K')
                sys.stdout.flush()

        print(f"[+] 配置完成，已保存到 CitizenAgentConfig.json")
        save_config(config)
        # 重新加载
        main_ok, base_url, model, model_api_key, endpoint, headers = load_model("main", "main", True)
        vis_ok, vis_url, vis_model, vis_key, vis_ep, vis_hdrs = load_model("vision", "vision")
        gen_ok, gen_url, gen_model, gen_key, gen_ep, gen_hdrs = load_model("image_gen", "image_gen")

    # 主模型不可用时回退到视觉模型
    if not main_ok:
        if vis_ok:
            print(f"{PINK}[!] 主模型不可用，回退使用视觉模型进行对话{RESET}")
            base_url, model, model_api_key, endpoint, headers = vis_url, vis_model, vis_key, vis_ep, vis_hdrs
            main_ok = True
        else:
            print(f"{RED}[-] 无可用模型，请检查配置文件{RESET}")
            return

    ai_name = config.get("ai_name", "AI")
    tools = config.get("tools", None)
    headers.update(config.get("extra_headers", {}))

    # 自动扫描注册本地未注册的对话
    from .conversation import get_all_conversations, get_conv_path
    for cid, info in get_all_conversations():
        conv_path = os.path.abspath(get_conv_path(cid))
        title = info.get("title", "新对话")
        register_conversation(config, cid, title, conv_path, WORKSPACE_DIR)
    save_config(config)

    active_conv = config.get("active_conversation")
    active_conv_path = None  # 外部对话的完整路径（跨 workspace）
    messages = []
    if active_conv:
        conv_data = load_conversation(active_conv)
        # 如果本地没找到，尝试从全局注册表加载（外部对话）
        if not conv_data:
            from .config import find_registered_conversation
            reg = find_registered_conversation(config, active_conv)
            if reg and reg.get("path"):
                conv_data = load_conversation_by_path(reg["path"])
                if conv_data:
                    active_conv_path = reg["path"]
                    print(f"[*] 从外部工作区加载对话: {reg.get('workspace', '未知')}")
        if conv_data:
            messages = conv_data.get("messages", [])
            while messages and messages[-1].get("tool_calls"):
                popped = messages.pop()
                print(f"[*] 已清理不完整的工具调用消息")
            has_system = any(m.get("role") == "system" for m in messages)
            if not has_system and conv_data.get("source") == "deepseek_web_import":
                tool_names = [t["function"]["name"] for t in config.get("tools", [])]
                system_prompt = f"你是一个接入了本地工具系统的 AI 助手。当前可用的工具包括: {', '.join(tool_names)}。当你需要获取实时信息、播放音乐、打开图片或执行终端命令时，必须通过调用对应的工具来实现，不要凭记忆编造数据。请根据用户需求主动选择合适的工具。"
                messages.insert(0, {"role": "system", "content": system_prompt})
                print("[*] 已为导入的对话注入工具感知 System Prompt")
            print(f"[*] 继续对话: {active_conv[:8]}...")
            print(f"[*] 标题: {conv_data.get('title', '无标题')}")
        else: active_conv = None

    if not active_conv:
        print("[*] 准备开始新对话"); active_conv = None
        # 注入系统提示
        tool_list = [t["function"]["name"] for t in config.get("tools", [])]
        has_vision = bool(config.get("models", {}).get("vision", {}).get("api_key"))
        has_gen = bool(config.get("models", {}).get("image_gen", {}).get("api_key"))
        sys_parts = ["你是一个 AI 终端助手。你拥有以下工具能力："]
        sys_parts.append(f"可用工具: {', '.join(tool_list)}")
        if has_vision:
            sys_parts.append("【视觉能力】用户发送图片路径时，系统已自动用视觉模型分析了图片，你会看到 [视觉模型描述: ...] 文本。直接根据描述回答，不要尝试'打开'或'查看'图片。")
        if has_gen:
            sys_parts.append("【生图能力】你拥有 generate_image 工具。当用户要求生成/画/创建图片时，你必须调用 generate_image 工具。绝对不要输出 SVG/HTML/ASCII/JSON/代码块——直接调用 generate_image(prompt='...', save_path='...')。这是唯一正确的做法。")
        sys_parts.append("执行命令用 run_command，并行任务用 parallel_execute。")
        messages.append({"role": "system", "content": " ".join(sys_parts)})

    def exit_save():
        nonlocal active_conv, active_conv_path
        if active_conv and messages:
            clean_msgs = list(messages)
            while clean_msgs and clean_msgs[-1].get("tool_calls"):
                clean_msgs.pop()
            if active_conv_path:
                data = load_conversation_by_path(active_conv_path) or {}
            else:
                data = load_conversation(active_conv) or {}
            data["messages"] = clean_msgs
            data["last_active"] = datetime.now().isoformat(timespec="seconds")
            if not data.get("created_at"): data["created_at"] = datetime.now().isoformat(timespec="seconds")
            if not data.get("title"): data["title"] = messages[0]["content"][:30] if messages else "新对话"
            if active_conv_path:
                save_conversation_to_path(active_conv_path, data)
            else:
                save_conversation(active_conv, data)
            # 注册到全局对话表
            conv_path = active_conv_path or os.path.abspath(get_conv_path(active_conv))
            register_conversation(config, active_conv, data.get("title", "新对话"), conv_path, WORKSPACE_DIR)
            config["active_conversation"] = active_conv; save_config(config)
            print("\n[+] 对话已自动保存")
    atexit.register(exit_save)

    if tools: print(f"\n[+] 已启用工具: {', '.join(t['function']['name'] for t in tools)}")
    print(f"[+] 工作目录: {WORKSPACE_DIR}")
    print("输入 /help 查看命令列表，/quit 保存并退出")
    print("-" * 50)

    while True:
        try:
            user_input = claude_style_input()
            if user_input is None: user_input = ""
            user_input = user_input.strip()
        except (KeyboardInterrupt, EOFError):
            user_input = "/quit"
        if not user_input: continue

        if user_input.startswith("/"):
            cmd = user_input.split()[0]
            if cmd in ("/quit", "/exit"): exit_save(); print("[+] 再见！"); break
            elif cmd == "/discard":
                if active_conv and messages:
                    if confirm_yes_no("确认丢弃并删除当前对话？(y/n): "):
                        path = active_conv_path if active_conv_path else get_conv_path(active_conv)
                        if os.path.exists(path): os.remove(path)
                        from .config import remove_conversation_from_registry
                        remove_conversation_from_registry(config, active_conv)
                        config["active_conversation"] = None; save_config(config)
                        active_conv = None; active_conv_path = None; messages = []; print("[+] 当前对话已丢弃")
                    else: print("[*] 取消")
                continue
            elif cmd in ("/help", "/?"):
                print("\n支持的命令：")
                for c, desc in COMMANDS.items():
                    if c in ("/?",): continue
                    print(f"  {c} - {desc}")
                continue
            elif cmd == "/history":
                exit_save(); chosen_id, ext_path, ext_ws = show_history(config)
                if chosen_id is not None:
                    if ext_path is not None:
                        # 外部对话：从完整路径加载
                        data = load_conversation_by_path(ext_path)
                        messages = data.get("messages", []) if data else []
                        active_conv = chosen_id
                        active_conv_path = ext_path  # 保存时用完整路径
                        config["active_conversation"] = active_conv; save_config(config)
                        print(f"[+] 已切换到外部对话 {chosen_id[:8]}... (workspace: {ext_ws})")
                    else:
                        # 本地对话
                        data = load_conversation(chosen_id)
                        messages = data.get("messages", []) if data else []
                        active_conv = chosen_id
                        active_conv_path = None
                        config["active_conversation"] = active_conv; save_config(config)
                        print(f"[+] 已切换到对话 {chosen_id[:8]}...")
                else: active_conv = None; messages = []; active_conv_path = None; config["active_conversation"] = None; save_config(config); print("[+] 准备开始新对话")
                continue
            elif cmd == "/delete":
                exit_save()
                if delete_conversations(config): active_conv = None; messages = []; active_conv_path = None; config["active_conversation"] = None; save_config(config); print("[*] 当前焦点已重置")
                continue
            elif cmd == "/new": exit_save(); active_conv = None; messages = []; active_conv_path = None; config["active_conversation"] = None; save_config(config); print("[+] 准备开始新对话"); continue
            elif cmd == "/sub":
                task = user_input[len("/sub"):].strip()
                if not task: print("[-] 请提供任务描述"); continue
                ok, msg = sub_agent_mgr.start(task, messages.copy() if messages else [])
                print(f"[{ok and 'OK' or 'FAIL'}] {msg}")
                print("[*] 子代理正在后台运行，输入 /sub_status 查看"); continue
            elif cmd == "/sub_status":
                st = sub_agent_mgr.status; print(f"[*] 子代理状态: {st}")
                if st == "done" or st == "error": print(f"[*] 结果: {sub_agent_mgr.result}"); sub_agent_mgr.get_result_and_reset()
                continue
            elif cmd == "/create_picture":
                print(f"{CYAN}> {user_input}{RESET}")
                gen_cfg = config.get("models", {}).get("image_gen", {})
                if not gen_cfg.get("api_key"):
                    print(f"{RED}[-] 未配置生图模型(image_gen)，请在 config.json 中设置{RESET}")
                    continue
                prompt = user_input[len("/create_picture"):].strip()
                if not prompt:
                    print("[-] 用法: /create_picture <图片描述> [保存路径]")
                    continue
                import re as _cp_re
                # 匹配路径: 文件(.jpg等) 或 目录(无扩展名的路径)
                path_match = _cp_re.search(r'[A-Za-z]:[\\/][^\s"\'<>]*?\.(?:jpg|jpeg|png)', prompt)
                any_path = _cp_re.search(r'[A-Za-z]:[\\/][^\s"\'<>]+', prompt)
                if path_match:
                    save_path = path_match.group(0)
                    prompt = prompt.replace(save_path, '').strip()
                elif any_path:
                    raw = any_path.group(0).rstrip('\\/')
                    if os.path.isdir(raw):
                        save_path = os.path.join(raw, f"citizen_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg")
                    else:
                        save_path = os.path.join(os.path.expanduser("~"), "Desktop", f"citizen_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg")
                    prompt = prompt.replace(any_path.group(0), '').strip()
                else:
                    save_path = os.path.join(os.path.expanduser("~"), "Desktop", f"citizen_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg")
                print(f"{DARK_GRAY}[*] 调 Wanx 生图: {prompt[:80]}...{RESET}")
                ep = gen_cfg.get("base_url","").strip()
                m_gen = gen_cfg.get("model","wanx2.1-t2i-turbo")
                ak = gen_cfg.get("api_key","").strip()
                try:
                    hdrs = {"Authorization":f"Bearer {ak}","Content-Type":"application/json","X-DashScope-Async":"enable"}
                    body = {"model":m_gen,"input":{"prompt":prompt},"parameters":{"size":"1024*1024","n":1}}
                    resp = requests.post(ep, headers=hdrs, json=body, timeout=120)
                    if resp.status_code != 200:
                        print(f"{RED}[-] Wanx API 返回 {resp.status_code}: {resp.text[:200]}{RESET}")
                        continue
                    data = resp.json()
                    task_id = data.get("output",{}).get("task_id","")
                    if not task_id:
                        print(f"{RED}[-] 未获取到任务ID{RESET}")
                        continue
                    task_url = "https://dashscope.aliyuncs.com/api/v1/tasks/" + task_id
                    import time as _cp_time
                    deadline = _cp_time.time() + config.get("image_gen_timeout", 120)
                    results = []
                    print(f"{DARK_GRAY}[*] 等待生图完成...{RESET}")
                    while _cp_time.time() < deadline:
                        tr = requests.get(task_url, headers=hdrs, timeout=30)
                        if tr.status_code == 200:
                            td = tr.json()
                            ts = td.get("output",{}).get("task_status","")
                            if ts == "SUCCEEDED":
                                results = td.get("output",{}).get("results",[])
                                break
                            elif ts == "FAILED":
                                print(f"{RED}[-] 生图任务失败: {td.get('output',{}).get('message','')}{RESET}")
                                break
                        _cp_time.sleep(2)
                    if not results:
                        print(f"{RED}[-] 生图超时或无结果{RESET}")
                        continue
                    img_url = results[0].get("url","")
                    if not img_url:
                        print(f"{RED}[-] 结果中无图片URL{RESET}")
                        continue
                    ir = requests.get(img_url, timeout=60)
                    if ir.status_code != 200:
                        print(f"{RED}[-] 下载图片失败: {ir.status_code}{RESET}")
                        continue
                    os.makedirs(os.path.dirname(save_path) if os.path.dirname(save_path) else ".", exist_ok=True)
                    with open(save_path, 'wb') as f: f.write(ir.content)
                    print(f"{GREEN}[+] 图片已生成: {save_path}{RESET}")
                except Exception as e:
                    print(f"{RED}[-] 生图失败: {e}{RESET}")
                continue
            else:
                poss = difflib.get_close_matches(cmd, COMMANDS.keys(), n=3, cutoff=0.6)
                print(f"[*] 你是不是想输入 {' 或 '.join(poss)} ？" if poss else f"[-] 未知命令: {cmd}")
                continue

        # 先回显用户原始输入(不等视觉模型)
        for line in user_input.split('\n'):
            print(f"{CYAN}> {line}{RESET}")

        # 视觉模型预处理: 检测图片路径
        images = find_image_paths(user_input)
        if images:
            sys.stdout.write(f"{DARK_GRAY}[*] 视觉模型分析中...{RESET}\r")
            sys.stdout.flush()
            visual_desc = call_vision_model(images, user_input, config)
            if visual_desc:
                sys.stdout.write(f"{DARK_GRAY}[*] 视觉模型已分析 {len(images)} 张图片{RESET}\n")
                sys.stdout.flush()
                for p in images:
                    user_input = user_input.replace(p, f"[图片: {p}]\n[视觉模型描述: {visual_desc}]")
            else:
                sys.stdout.write(f"{PINK}[!] 视觉模型调用失败{RESET}\n")
                sys.stdout.flush()

        messages.append({"role": "user", "content": user_input})

        while True:
            payload = {"model": model, "messages": messages, "stream": True}
            if tools: payload["tools"] = tools

            state = {"token_count": 0, "reply": "", "done": False, "official_id": None, "usage": None, "tool_calls": None}
            stop_spinner = threading.Event()
            spinner_thread = threading.Thread(target=spinner_with_tokens, args=(stop_spinner, state))
            spinner_thread.start()

            max_retries = config.get("max_retries", 5)
            retry_delay = config.get("retry_delay", 1)
            retry_delays = [retry_delay * (2 ** i) for i in range(max_retries)]
            conn_timeout = config.get("connection_timeout", 10)
            read_time = config.get("read_timeout", 120)
            request_ok = False

            for attempt in range(max_retries):
                try:
                    resp = requests.post(endpoint, headers=headers, json=payload, timeout=(conn_timeout, read_time), stream=True)
                    resp.raise_for_status()
                    stream_thread = threading.Thread(target=process_stream, args=(resp, state))
                    stream_thread.start(); stream_thread.join()
                    request_ok = True
                    break
                except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                    stop_spinner.set(); spinner_thread.join()
                    if attempt < max_retries - 1:
                        delay = retry_delays[attempt]
                        print(f"\n{RED}[!] 连接失败 (第 {attempt + 1}/{max_retries} 次){RESET}")
                        print(f"{RED}[!] 原因: {e}{RESET}")
                        print(f"{RED}[!] {delay}s 后重试...{RESET}")
                        time.sleep(delay)
                        stop_spinner.clear()
                        spinner_thread = threading.Thread(target=spinner_with_tokens, args=(stop_spinner, state))
                        spinner_thread.start()
                    else:
                        print(f"\n{RED}[!] 已重试 {max_retries} 次，全部失败{RESET}")
                        print(f"{PINK}[!] 可能原因: 网络未连接 / 未开启 VPN / DNS 无法解析 / API 地址不可达{RESET}")
                        if messages and messages[-1]["role"] == "user": messages.pop()
                except requests.exceptions.HTTPError as e:
                    stop_spinner.set(); spinner_thread.join()
                    body = ""
                    try: body = e.response.text[:500]
                    except: pass
                    print(f"\n{RED}[-] API 返回错误 ({e.response.status_code}): {body}{RESET}")
                    if messages and messages[-1]["role"] == "user": messages.pop()
                except requests.exceptions.RequestException as e:
                    stop_spinner.set(); spinner_thread.join()
                    print(f"\n{RED}[-] 请求失败: {e}")
                    if messages and messages[-1]["role"] == "user": messages.pop()
                    break

            stop_spinner.set(); spinner_thread.join()

            if not request_ok:
                break

            reply = state["reply"]; new_official_id = state["official_id"]
            usage = state["usage"]; tool_calls = state["tool_calls"]

            if not reply and not tool_calls:
                print("[-] 收到空回复，请重试")
                if messages and messages[-1]["role"] == "user": messages.pop()
                break

            if tool_calls:
                if active_conv is None:
                    active_conv = new_official_id or datetime.now().strftime("%Y%m%d%H%M%S%f")
                    config["active_conversation"] = active_conv; save_config(config)
                if reply: print(f"\n{REPLY_AI}{ai_name}: {reply}{RESET}")
                rc = state.get("reasoning_content")
                assistant_msg = {"role": "assistant", "content": reply or None, "tool_calls": tool_calls}
                if rc: assistant_msg["reasoning_content"] = rc
                messages.append(assistant_msg)
                show_mode = config.get("show_tool_calls", "full")
                for tc in tool_calls:
                    tc_name = tc['function']['name']
                    if show_mode == "full":
                        print(f"{DARK_GRAY}[*] 调用工具: {tc_name}，参数: {tc['function']['arguments']}{RESET}")
                    elif show_mode == "compact":
                        if tc_name not in ("parallel_execute", "run_command"):
                            print(f"    {DARK_GRAY}[*] 调用工具({tc_name}, 执行中...){RESET}")
                    res_json_str = execute_tool_call(tc, config)
                    messages.append({"role": "tool", "tool_call_id": tc["id"], "content": res_json_str})
                    if show_mode == "compact":
                        try:
                            r = json.loads(res_json_str)
                            st = r.get("status","failed")
                            if st == "success":
                                if tc_name == "parallel_execute":
                                    try:
                                        out = json.loads(r.get("output","[]"))
                                        n = len(out) if isinstance(out, list) else 0
                                        print(f"    {DARK_GRAY}[*] 并行执行({n}个任务, 已完成){RESET}")
                                    except: print(f"    {DARK_GRAY}[*] 并行执行(已完成){RESET}")
                                else:
                                    print(f"    {DARK_GRAY}[*] 调用工具({tc_name}, 已执行){RESET}")
                            elif st == "cancelled":
                                print(f"    {DARK_GRAY}[*] 调用工具({tc_name}, 已取消){RESET}")
                            elif st == "denied":
                                print(f"    {DARK_RED}[-] 调用工具({tc_name}, 被禁止){RESET}")
                            else:
                                print(f"    {DARK_RED}[-] 调用工具({tc_name}, 失败: {r.get('error_reason','')[:40]}){RESET}")
                        except: pass
                continue

            print(f"\n{REPLY_AI}{ai_name}: {reply}{RESET}")
            rc_final = state.get("reasoning_content")
            am = {"role": "assistant", "content": reply}
            if rc_final: am["reasoning_content"] = rc_final
            messages.append(am)

            pt = 0; ct = 0
            if usage and isinstance(usage, dict): pt = usage.get("prompt_tokens", 0); ct = usage.get("completion_tokens", 0)
            if not pt:
                all_t = "".join([m["content"] for m in messages if m["content"]])
                pt = estimate_tokens(all_t)
            if not ct: ct = estimate_tokens(reply)

            if active_conv is None:
                active_conv = new_official_id or datetime.now().strftime("%Y%m%d%H%M%S%f")
                config["active_conversation"] = active_conv; save_config(config)
                data = {"created_at": datetime.now().isoformat(timespec="seconds"), "title": user_input[:30] if len(messages) == 2 else "新对话", "messages": messages, "last_active": datetime.now().isoformat(timespec="seconds"), "total_prompt_tokens": pt, "total_completion_tokens": ct}
                save_conversation(active_conv, data)
                # 注册到全局对话表
                conv_path = os.path.abspath(get_conv_path(active_conv))
                register_conversation(config, active_conv, data["title"], conv_path, WORKSPACE_DIR)
                save_config(config)
                print(f"[+] 新对话已创建，ID: {active_conv[:8]}...")
            else:
                if active_conv_path:
                    data = load_conversation_by_path(active_conv_path) or {}
                else:
                    data = load_conversation(active_conv) or {}
                data["messages"] = messages; data["last_active"] = datetime.now().isoformat(timespec="seconds")
                if len(messages) == 2: data["title"] = user_input[:30]
                old_pt = data.get("total_prompt_tokens", 0); old_ct = data.get("total_completion_tokens", 0)
                data["total_prompt_tokens"] = old_pt + pt; data["total_completion_tokens"] = old_ct + ct
                if active_conv_path:
                    save_conversation_to_path(active_conv_path, data)
                else:
                    save_conversation(active_conv, data)
                # 更新全局注册表
                conv_path = active_conv_path or os.path.abspath(get_conv_path(active_conv))
                register_conversation(config, active_conv, data.get("title", "新对话"), conv_path, WORKSPACE_DIR)
                save_config(config)
            break

if __name__ == "__main__":
    try: import requests
    except ImportError: print("[-] 请安装 requests: pip install requests"); exit(1)
    main()

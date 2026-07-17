"""工具执行 — 完全复制原版 Elc9_Code.py，不做任何改动。"""
import json, os, subprocess, shlex, re, requests, threading, sys, shutil
from .conversation import load_conversation, append_sub_agent_messages
from .config import get_color

GREEN = '\033[92m'
PINK = '\033[95m'
RESET = '\033[0m'
YELLOW = '\033[93m'
DARK_GRAY = '\033[90m'
DARK_YELLOW = '\033[38;2;170;165;120m'
OUTPUT_LOCK = threading.RLock()

def _dim_color(esc):
    m = re.match(r'\033\[38;2;(\d+);(\d+);(\d+)m', esc)
    if m:
        r, g, b = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return f'\033[38;2;{r//2};{g//2};{b//2}m'
    return '\033[90m'

def execute_tool_call(tool_call, config, silent=False, tag=None, tag_color=None):
    global GREEN, PINK, YELLOW, DARK_GRAY, DARK_YELLOW
    GREEN = get_color(config, "green")
    PINK = get_color(config, "pink")
    YELLOW = get_color(config, "yellow")
    DARK_GRAY = get_color(config, "dark_gray")
    DARK_YELLOW = get_color(config, "dark_yellow")

    func_name = tool_call["function"]["name"]

    if func_name == "open_image":
        try: args = json.loads(tool_call["function"]["arguments"])
        except: return json.dumps({"status":"failed","error_code":"parse_error","error_reason":"参数解析失败","output":""},ensure_ascii=False)
        path = args.get("path","").strip()
        if not path: return json.dumps({"status":"failed","error_code":"empty_path","error_reason":"图片路径为空","output":""},ensure_ascii=False)
        if not os.path.exists(path): return json.dumps({"status":"failed","error_code":"file_not_found","error_reason":f"文件不存在: {path}","output":""},ensure_ascii=False)
        try:
            abs_path = os.path.abspath(path)
            result = subprocess.run(["am","start","-a","android.intent.action.VIEW","-d",f"file://{abs_path}","-t","image/*"],capture_output=True,text=True,timeout=10)
            if result.returncode == 0: return json.dumps({"status":"success","error_code":0,"error_reason":"","output":f"已在系统相册中打开图片: {abs_path}"},ensure_ascii=False)
            else:
                subprocess.run(["xdg-open",abs_path],capture_output=True,timeout=10)
                return json.dumps({"status":"success","error_code":0,"error_reason":"","output":f"已尝试打开图片: {abs_path}"},ensure_ascii=False)
        except Exception as e: return json.dumps({"status":"failed","error_code":"open_error","error_reason":str(e),"output":""},ensure_ascii=False)

    if func_name == "delegate_task":
        try: args = json.loads(tool_call["function"]["arguments"])
        except: return json.dumps({"status":"failed","error_code":"parse_error","error_reason":"参数解析失败","output":""},ensure_ascii=False)
        task_description = args.get("task_description","").strip()
        if not task_description: return json.dumps({"status":"failed","error_code":"empty_task","error_reason":"任务描述为空","output":""},ensure_ascii=False)
        try:
            api_key = (config.get("models",{}).get("main",{}).get("api_key","") or config.get("api_key","")).strip()
            base_url = config.get("base_url","https://api.deepseek.com").rstrip("/")
            model = config.get("model","deepseek-chat")
            tools = config.get("tools",None)
            extra_headers = config.get("extra_headers",{})
            active_conv = config.get("active_conversation")
            history_messages = []
            conv_data = load_conversation(active_conv)
            if conv_data: history_messages = conv_data.get("messages",[])
            sub_messages = []
            sub_messages.append({"role":"system","content":"你是一个委托任务代理（Delegate Agent），正在当前对话上下文中执行一个子任务。以下是当前对话的历史记录，请将其作为背景上下文参考。请专注于完成分配给你的子任务，并返回清晰、完整的结果。"})
            if history_messages:
                history_text = json.dumps(history_messages,ensure_ascii=False)
                sub_messages.append({"role":"user","content":"【当前对话历史上下文】\n"+history_text+"\n\n---\n请基于以上上下文，完成以下子任务。"})
            sub_messages.append({"role":"user","content":task_description})
            endpoint = base_url+"/chat/completions" if not base_url.endswith("/chat/completions") else base_url
            headers = {"Authorization":f"Bearer {api_key}","Content-Type":"application/json"}
            headers.update(extra_headers)
            payload = {"model":model,"messages":sub_messages,"stream":False}
            if tools: payload["tools"] = tools
            response = requests.post(endpoint,headers=headers,json=payload,timeout=300)
            if response.status_code != 200: return json.dumps({"status":"failed","error_code":"api_error","error_reason":f"API 请求失败 {response.status_code}","output":""},ensure_ascii=False)
            resp_data = response.json()
            msg = resp_data["choices"][0]["message"]
            content = msg.get("content","")
            tool_calls = msg.get("tool_calls",None)
            round_limit = 5; round_n = 0
            while tool_calls and round_n < round_limit:
                round_n += 1; sub_messages.append(msg)
                for tc in tool_calls:
                    func_n = tc["function"]["name"]
                    if func_n == "delegate_task": tool_res = json.dumps({"status":"failed","error_code":"nested_delegate","error_reason":"不支持嵌套调用","output":""},ensure_ascii=False)
                    else: tool_res = execute_tool_call(tc, config)
                    sub_messages.append({"role":"tool","tool_call_id":tc["id"],"content":tool_res})
                payload["messages"] = sub_messages
                r2 = requests.post(endpoint,headers=headers,json=payload,timeout=300)
                if r2.status_code != 200: break
                r2_data = r2.json()
                msg = r2_data["choices"][0]["message"]
                content = msg.get("content","")
                tool_calls = msg.get("tool_calls",None)
            return json.dumps({"status":"success","error_code":0,"error_reason":"","output":content},ensure_ascii=False)
        except Exception as e: return json.dumps({"status":"failed","error_code":"delegate_exception","error_reason":str(e),"output":""},ensure_ascii=False)

    if func_name == "generate_image":
        try: args = json.loads(tool_call["function"]["arguments"])
        except: return json.dumps({"status":"failed","error_code":"parse_error","error_reason":"参数解析失败","output":""},ensure_ascii=False)
        prompt = args.get("prompt","").strip()
        save_path = args.get("save_path","").strip()
        if not prompt:
            return json.dumps({"status":"failed","error_code":"empty_prompt","error_reason":"图片描述不能为空","output":""},ensure_ascii=False)

        gen_cfg = config.get("models", {}).get("image_gen", {})
        endpoint = gen_cfg.get("base_url","").strip()
        model = gen_cfg.get("model","wanx2.1-t2i-turbo")
        api_key = gen_cfg.get("api_key","").strip()
        if not endpoint or not api_key:
            return json.dumps({"status":"failed","error_code":"no_config","error_reason":"未配置生图模型(image_gen)，请在 config.json 的 models.image_gen 中设置","output":""},ensure_ascii=False)

        try:
            hdrs = {"Authorization":f"Bearer {api_key}","Content-Type":"application/json","X-DashScope-Async":"enable"}
            body = {"model":model,"input":{"prompt":prompt},"parameters":{"size":"1024*1024","n":1}}
            resp = requests.post(endpoint, headers=hdrs, json=body, timeout=120)
            if resp.status_code != 200:
                return json.dumps({"status":"failed","error_code":"api_error","error_reason":f"生图API返回 {resp.status_code}: {resp.text[:200]}","output":""},ensure_ascii=False)
            data = resp.json()
            # 异步模式: 获取 task_id 并轮询
            task_id = data.get("output",{}).get("task_id","")
            if task_id:
                import time as _time
                gen_timeout = config.get("image_gen_timeout", 120)
                task_url = "https://dashscope.aliyuncs.com/api/v1/tasks/" + task_id
                deadline = _time.time() + gen_timeout
                print(f"    {DARK_GRAY}[*] 生图任务已提交, 等待生成...{RESET}")
                while _time.time() < deadline:
                    tr = requests.get(task_url, headers=hdrs, timeout=30)
                    if tr.status_code == 200:
                        td = tr.json()
                        ts = td.get("output",{}).get("task_status","")
                        if ts == "SUCCEEDED":
                            results = td.get("output",{}).get("results",[])
                            break
                        elif ts == "FAILED":
                            return json.dumps({"status":"failed","error_code":"task_failed","error_reason":f"生图任务失败: {td.get('output',{}).get('message','')}","output":""},ensure_ascii=False)
                    elif tr.status_code != 200:
                        pass
                    _time.sleep(2)
                else:
                    return json.dumps({"status":"failed","error_code":"timeout","error_reason":f"生图任务超时({gen_timeout}秒)","output":""},ensure_ascii=False)
                if not results:
                    return json.dumps({"status":"failed","error_code":"no_result","error_reason":"生图任务完成但无结果","output":""},ensure_ascii=False)
            else:
                # 同步模式回退
                results = data.get("output",{}).get("results",[])
            if not results:
                return json.dumps({"status":"failed","error_code":"no_result","error_reason":"生图API未返回图片","output":json.dumps(data,ensure_ascii=False)},ensure_ascii=False)
                return json.dumps({"status":"failed","error_code":"no_result","error_reason":"生图API未返回图片","output":json.dumps(data,ensure_ascii=False)},ensure_ascii=False)
            img_url = results[0].get("url","")
            if not img_url:
                return json.dumps({"status":"failed","error_code":"no_url","error_reason":"生图结果中无图片URL","output":""},ensure_ascii=False)

            # 下载图片
            img_resp = requests.get(img_url, timeout=60)
            if img_resp.status_code != 200:
                return json.dumps({"status":"failed","error_code":"download_error","error_reason":f"下载图片失败: {img_resp.status_code}","output":""},ensure_ascii=False)

            if not save_path:
                from datetime import datetime
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                save_path = os.path.join(os.path.expanduser("~"), "Desktop", f"ai_image_{ts}.png")
            os.makedirs(os.path.dirname(save_path) if os.path.dirname(save_path) else ".", exist_ok=True)
            with open(save_path, 'wb') as f:
                f.write(img_resp.content)

            return json.dumps({"status":"success","error_code":0,"error_reason":"","output":f"图片已生成并保存到: {save_path}"},ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status":"failed","error_code":"exception","error_reason":str(e),"output":""},ensure_ascii=False)

    if func_name == "parallel_execute":
        try: args = json.loads(tool_call["function"]["arguments"])
        except: return json.dumps({"status":"failed","error_code":"parse_error","error_reason":"参数解析失败","output":""},ensure_ascii=False)

        if not config.get("parallel_enabled", True):
            return json.dumps({"status":"failed","error_code":"parallel_disabled","error_reason":"并行执行未启用。请使用 /more_process <任务描述> 命令来启用多代理并行处理","output":""},ensure_ascii=False)

        tasks = args.get("tasks", [])
        if not tasks or not isinstance(tasks, list):
            return json.dumps({"status":"failed","error_code":"invalid_tasks","error_reason":"tasks 必须是非空数组","output":""},ensure_ascii=False)

        max_workers = config.get("parallel_max_workers", 5)
        if len(tasks) > max_workers:
            tasks = tasks[:max_workers]

        AGENT_COLORS = [
            get_color(config, "agent_1"),
            get_color(config, "agent_2"),
            get_color(config, "agent_3"),
            get_color(config, "agent_4"),
            get_color(config, "agent_5"),
        ]
        RST = '\033[0m'

        api_key = (config.get("models",{}).get("main",{}).get("api_key","") or config.get("api_key","")).strip()
        base_url = config.get("base_url","https://api.deepseek.com").rstrip("/")
        model = config.get("model","deepseek-chat")
        tools = config.get("tools",None)
        extra_headers = config.get("extra_headers",{})
        active_conv = config.get("active_conversation")

        history_messages = []
        conv_data = load_conversation(active_conv)
        if conv_data:
            history_messages = conv_data.get("messages",[])

        endpoint = base_url + "/chat/completions" if not base_url.endswith("/chat/completions") else base_url
        headers = {"Authorization":f"Bearer {api_key}","Content-Type":"application/json"}
        headers.update(extra_headers)

        results = [None] * len(tasks)
        threads = []

        def _run_parallel_task(index, task_desc):
            color = AGENT_COLORS[index % len(AGENT_COLORS)]
            tag = f"并{index+1}"
            def _p(*a, **kw):
                OUTPUT_LOCK.acquire()
                try: print(*a, **kw)
                finally: OUTPUT_LOCK.release()
            try:
                _p(f"{color}[{tag}] 开始: {task_desc[:60]}...{RST}")

                sys_prompt = config.get("parallel_agent_prompt", "你是并行代理，必须使用工具完成子任务")
                sys_prompt = sys_prompt.replace("{index}", str(index+1)).replace("{total}", str(len(tasks)))
                msgs = [
                    {"role":"system","content":sys_prompt}
                ]
                if history_messages:
                    msgs.append({"role":"user","content":"【共享对话历史上下文】\n"+json.dumps(history_messages,ensure_ascii=False)+"\n\n---\n请忽略历史中未完成的其他任务，只完成以下子任务："})
                msgs.append({"role":"user","content":task_desc})

                payload = {"model":model,"messages":msgs,"stream":False}
                if tools: payload["tools"] = tools

                _p(f"{color}[{tag}] 请求API中...{RST}")
                resp = requests.post(endpoint, headers=headers, json=payload, timeout=300)
                _p(f"{color}[{tag}] 收到响应{RST}")
                if resp.status_code != 200:
                    results[index] = {"index":index,"task":task_desc[:80],"status":"failed","error":f"API 返回 {resp.status_code}"}
                    _p(f"{color}[{tag}] 失败: API 返回 {resp.status_code}{RST}")
                    return

                data = resp.json()
                msg = data["choices"][0]["message"]
                content = msg.get("content","")
                tool_calls = msg.get("tool_calls")
                tools_used = False

                max_rounds = config.get("parallel_max_rounds", 30)
                round_n = 0
                while tool_calls:
                    if round_n >= max_rounds:
                        _p(f"{color}[{tag}] 已达最大轮数限制({max_rounds}轮), 强制结束{RST}")
                        break
                    round_n += 1; tools_used = True
                    _p(f"{color}[{tag}] 执行工具调用(第{round_n}轮)...{RST}")
                    msgs.append(msg)
                    for tc in tool_calls:
                        fn = tc["function"]["name"]
                        if fn in ("parallel_execute","delegate_task"):
                            tool_res = json.dumps({"status":"failed","error_code":"nested_not_allowed","error_reason":f"并行任务中不允许调用 {fn}","output":""},ensure_ascii=False)
                        else:
                            tool_res = execute_tool_call(tc, config, tag=tag, tag_color=_dim_color(color))
                        msgs.append({"role":"tool","tool_call_id":tc["id"],"content":tool_res})
                    payload["messages"] = msgs
                    _p(f"{color}[{tag}] 工具结果已返回, 继续请求API...{RST}")
                    r2 = requests.post(endpoint, headers=headers, json=payload, timeout=300)
                    if r2.status_code != 200: break
                    r2_data = r2.json()
                    msg = r2_data["choices"][0]["message"]
                    content = msg.get("content","")
                    tool_calls = msg.get("tool_calls")

                conv_id = config.get("active_conversation")
                if not tools_used:
                    err_msg = config.get("parallel_no_tools_msg", "未调用任何工具")
                    results[index] = {"index":index,"task":task_desc[:80],"status":"failed","error":err_msg,"result":content or "(无返回内容)"}
                    _p(f"{color}[{tag}] 失败: {err_msg}{RST}")
                else:
                    results[index] = {"index":index,"task":task_desc[:80],"status":"success","result":content or "(无返回内容)"}
                    _p(f"{color}[{tag}] 完成{RST}")
                if conv_id and msgs:
                    work_msgs = [m for m in msgs if m.get("role") not in ("system",) and "历史上下文" not in str(m.get("content",""))[:20]]
                    if work_msgs:
                        append_sub_agent_messages(conv_id, tag, work_msgs)
            except Exception as e:
                results[index] = {"index":index,"task":task_desc[:80],"status":"failed","error":str(e)}
                _p(f"{color}[{tag}] 失败: {e}{RST}")
                conv_id = config.get("active_conversation")
                if conv_id and msgs:
                    try:
                        work_msgs = [m for m in msgs if m.get("role") not in ("system",) and "历史上下文" not in str(m.get("content",""))[:20]]
                        if work_msgs:
                            append_sub_agent_messages(conv_id, tag, work_msgs)
                    except: pass

        for i, task in enumerate(tasks):
            t = threading.Thread(target=_run_parallel_task, args=(i, task), daemon=True)
            threads.append(t); t.start()

        for t in threads:
            t.join()

        return json.dumps({"status":"success","error_code":0,"error_reason":"","output":json.dumps(results,ensure_ascii=False)},ensure_ascii=False)

    if func_name == "play_music":
        try: args = json.loads(tool_call["function"]["arguments"])
        except: return json.dumps({"status":"failed","error_code":"parse_error","error_reason":"参数解析失败","output":""},ensure_ascii=False)
        path = args.get("path","").strip()
        if not path: return json.dumps({"status":"failed","error_code":"empty_path","error_reason":"音乐路径为空","output":""},ensure_ascii=False)
        if not os.path.exists(path): return json.dumps({"status":"failed","error_code":"file_not_found","error_reason":f"找不到文件: {path}","output":""},ensure_ascii=False)
        try:
            abs_path = os.path.abspath(path)
            result = subprocess.run(["am","start","-a","android.intent.action.VIEW","-d",f"file://{abs_path}","-t","audio/*"],capture_output=True,text=True,timeout=10)
            if result.returncode == 0: return json.dumps({"status":"success","error_code":0,"error_reason":"","output":f"已调用系统选择器，请手动选择播放器: {abs_path}"},ensure_ascii=False)
            result2 = subprocess.run(["mpv","--no-video",abs_path],capture_output=True,text=True,timeout=5)
            if result2.returncode == 0: return json.dumps({"status":"success","error_code":0,"error_reason":"","output":f"已通过 mpv 播放: {abs_path}"},ensure_ascii=False)
            return json.dumps({"status":"failed","error_code":"play_failed","error_reason":"所有播放方式均失败","output":""},ensure_ascii=False)
        except subprocess.TimeoutExpired: return json.dumps({"status":"failed","error_code":"timeout","error_reason":"播放器启动超时","output":""},ensure_ascii=False)
        except Exception as e: return json.dumps({"status":"failed","error_code":"exception","error_reason":str(e),"output":""},ensure_ascii=False)

    if func_name != "run_command":
        return json.dumps({"status":"failed","error_code":"unknown_tool","error_reason":f"未知工具: {func_name}","output":""},ensure_ascii=False)

    try: args = json.loads(tool_call["function"]["arguments"])
    except: return json.dumps({"status":"failed","error_code":"parse_error","error_reason":"参数解析失败","output":""},ensure_ascii=False)
    command = args.get("command","").strip()
    if not command: return json.dumps({"status":"failed","error_code":"empty_command","error_reason":"命令为空","output":""},ensure_ascii=False)
    try: parts = shlex.split(command)
    except ValueError as e: return json.dumps({"status":"failed","error_code":"parse_error","error_reason":str(e),"output":""},ensure_ascii=False)
    if not parts: return json.dumps({"status":"failed","error_code":"invalid_command","error_reason":"无效命令","output":""},ensure_ascii=False)
    cmd_name = parts[0].split("/")[-1]
    allowed = config.get("allowed_commands",[])
    blacklist = config.get("blacklist_commands",[])
    if cmd_name in blacklist: return json.dumps({"status":"denied","error_code":"blacklisted","error_reason":f"命令 '{cmd_name}' 被禁止","output":""},ensure_ascii=False)
    was_confirmed = False
    need_confirm = cmd_name not in allowed
    if need_confirm:
        if silent:
            pass
        else:
            was_confirmed = True
            if tag:
                OUTPUT_LOCK.acquire()
            try:
                prefix = f"{tag_color}[{tag}] " if tag else ""
                preview_len = config.get("command_preview_length", 200)
                cmd_preview = command[:preview_len] + "..." if len(command) > preview_len else command
                print(f"{prefix}{DARK_YELLOW}[?] 未知命令: {cmd_preview}{RESET}")
                while True:
                    confirm = input(f"    是否允许执行？(y/n, 默认 y): ").strip().lower()
                    if confirm == "" or confirm == "y": break
                    elif confirm == "n": return json.dumps({"status":"cancelled","error_code":"user_denied","error_reason":"用户拒绝执行","output":""},ensure_ascii=False)
                    else: print("[-] 请输入 y 或 n")
                if config.get("show_tool_calls","full") == "compact":
                    tw = shutil.get_terminal_size().columns
                    dw = sum(2 if '一' <= c <= '鿿' else 1 for c in f"{prefix}[?] 未知命令: {cmd_preview}")
                    wrap = (dw + tw - 1) // tw
                    for _ in range(wrap + 1):
                        sys.stdout.write('\033[A\033[K')
                    sys.stdout.flush()
                    print(f"    {prefix}{DARK_GRAY}[*] 已授权调用工具(run_command, 执行中...){RESET}")
            finally:
                if tag:
                    OUTPUT_LOCK.release()
    else:
        if config.get("show_tool_calls","full") == "compact":
            prefix = f"{tag_color}[{tag}] " if tag else ""
            if tag:
                OUTPUT_LOCK.acquire()
            try:
                print(f"    {prefix}{DARK_GRAY}[*] 调用工具(run_command, 执行中...){RESET}")
            finally:
                if tag:
                    OUTPUT_LOCK.release()
    max_out = config.get("max_tool_output",10240)
    error_codes = config.get("error_codes",{})
    try:
        result = subprocess.run(command, shell=True, capture_output=True, timeout=30)
        rc = result.returncode
        stdout_b = result.stdout or b""; stderr_b = result.stderr or b""
        for enc in ('utf-8', 'gbk', 'gb2312', 'latin-1'):
            try:
                stdout = stdout_b.decode(enc)
                break
            except: continue
        else: stdout = stdout_b.decode('utf-8', errors='replace')
        for enc in ('utf-8', 'gbk', 'gb2312', 'latin-1'):
            try:
                stderr = stderr_b.decode(enc)
                break
            except: continue
        else: stderr = stderr_b.decode('utf-8', errors='replace')
        is_broken_pipe = (rc == 141 or "broken pipe" in stderr.lower())
        if rc == 0 or is_broken_pipe: status = "success"; error_code = rc; error_reason = "" if rc == 0 else error_codes.get(str(rc),"")
        else: status = "failed"; error_code = rc; error_reason = error_codes.get(str(rc),"")
        ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
        output_parts = []
        if stdout: output_parts.append(ansi_escape.sub('',stdout))
        if stderr and rc != 0: output_parts.append(f"[stderr]\n{ansi_escape.sub('',stderr)}")
        if rc != 0 and not is_broken_pipe: output_parts.append(f"[返回码: {rc}]")
        raw_output = "\n".join(output_parts)
        trimmed_output = raw_output[:max_out]
        if len(raw_output) > max_out: trimmed_output += "\n[输出已截断]"
        return json.dumps({"status":status,"error_code":error_code,"error_reason":error_reason,"output":trimmed_output},ensure_ascii=False)
    except subprocess.TimeoutExpired: return json.dumps({"status":"failed","error_code":"timeout","error_reason":error_codes.get("timeout","命令执行超时"),"output":"[命令超时]"},ensure_ascii=False)
    except Exception as e: return json.dumps({"status":"failed","error_code":"exception","error_reason":str(e),"output":""},ensure_ascii=False)

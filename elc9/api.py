"""流式动画与处理 — 从原始 Elc9_Code.py 拆分。"""
import json, itertools, time, sys

GREEN = '\033[92m'
RESET = '\033[0m'

def spinner_with_tokens(stop_event, state):
    sys.stdout.write(f"{GREEN}[   ] ......thinking(tokens: ↓0){RESET}")
    sys.stdout.flush()
    for c in itertools.cycle(['-', '/', '|', '\\']):
        if stop_event.is_set(): break
        tk = state.get("token_count", 0)
        sys.stdout.write(f"\r{GREEN}[ {c} ] ......thinking(tokens: ↓{tk}){RESET}")
        sys.stdout.flush()
        time.sleep(0.1)
    sys.stdout.write("\r" + " " * 60 + "\r")
    sys.stdout.flush()

def process_stream(response, state):
    reply_parts = []; char_count = 0; official_id = None; usage = None; tool_calls = []; reasoning_parts = []
    if response.encoding is None or response.encoding.lower() != 'utf-8': response.encoding = 'utf-8'
    try:
        for line in response.iter_lines(decode_unicode=True):
            if not line: continue
            data_str = ""
            if line.startswith("data: "): data_str = line[6:]
            elif line.startswith("data:"): data_str = line[5:]
            else: continue
            if data_str.strip() == "[DONE]": break
            try:
                data = json.loads(data_str)
                if official_id is None and "id" in data: official_id = data["id"]
                choices = data.get("choices", [])
                if choices:
                    delta = choices[0].get("delta") or choices[0].get("message", {})
                    rc = delta.get("reasoning_content", "")
                    if rc: reasoning_parts.append(rc)
                    content = delta.get("content", "")
                    if content: reply_parts.append(content); char_count += len(content); state["token_count"] = char_count // 4
                    tc_delta = delta.get("tool_calls")
                    if tc_delta:
                        for tc in tc_delta:
                            idx = tc.get("index", 0)
                            while len(tool_calls) <= idx: tool_calls.append({"id": "", "type": "function", "function": {"name": "", "arguments": ""}})
                            if "id" in tc: tool_calls[idx]["id"] = tc["id"]
                            if "type" in tc: tool_calls[idx]["type"] = tc["type"]
                            if "function" in tc:
                                if "name" in tc["function"]: tool_calls[idx]["function"]["name"] += tc["function"]["name"]
                                if "arguments" in tc["function"]: tool_calls[idx]["function"]["arguments"] += tc["function"]["arguments"]
                if "usage" in data: usage = data["usage"]
            except json.JSONDecodeError: pass
    except Exception as e: print(f"\n[-] 流式读取错误: {e}")
    finally:
        state["reply"] = "".join(reply_parts); state["official_id"] = official_id
        state["usage"] = usage; state["tool_calls"] = tool_calls if tool_calls else None
        state["reasoning_content"] = "".join(reasoning_parts) if reasoning_parts else None
        state["done"] = True

def estimate_tokens(text): return max(1, int(len(text) / 2.5))

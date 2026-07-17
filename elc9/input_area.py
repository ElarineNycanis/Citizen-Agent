"""输入框 — Claude Code 风格双线布局。"""
import shutil, sys
from typing import Optional

DARK_GRAY = '\033[90m'
PINK = '\033[95m'
WHITE = '\033[0m'

def _has_pt():
    try: import prompt_toolkit; return True
    except: return False

def _simple() -> Optional[str]:
    try:
        lines=[]
        while True:
            l=input(f"{PINK}> {WHITE}")
            if l=="" and lines: break
            lines.append(l)
        return "\n".join(lines)
    except: return None

def _pt_input(prompt_str="> ", placeholder="") -> Optional[str]:
    from prompt_toolkit.application import Application
    from prompt_toolkit.buffer import Buffer
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.layout import Layout
    from prompt_toolkit.layout.containers import HSplit, VSplit, Window
    from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
    from prompt_toolkit.layout.dimension import Dimension
    from prompt_toolkit.styles import Style

    result=[None]; buffer=Buffer(multiline=False)
    kb=KeyBindings()
    @kb.add('enter')
    def _(e):
        if buffer.text.strip(): result[0]=buffer.text; e.app.exit()
    @kb.add('escape','enter')
    def _(e): buffer.insert_text('\n')
    @kb.add('c-c')
    def _(e): e.app.exit()
    @kb.add('c-d')
    def _(e):
        if not buffer.text: e.app.exit()
        else: buffer.delete()

    def _sep(): return [('class:sep','─'*max(shutil.get_terminal_size().columns,10))]

    root=HSplit([
        Window(FormattedTextControl(_sep),height=Dimension.exact(1),dont_extend_height=True),
        VSplit([
            Window(FormattedTextControl([('class:prompt',prompt_str)]),width=Dimension.exact(len(prompt_str)),dont_extend_width=True),
            Window(BufferControl(buffer=buffer)),
        ],height=Dimension.exact(1)),
        Window(FormattedTextControl(_sep),height=Dimension.exact(1),dont_extend_height=True),
    ])

    from prompt_toolkit.output.defaults import create_output
    from prompt_toolkit.output.win32 import NoConsoleScreenBufferError
    try: output=create_output()
    except NoConsoleScreenBufferError:
        from prompt_toolkit.output.vt100 import Vt100_Output
        output=Vt100_Output(sys.stdout,get_size=lambda:shutil.get_terminal_size())

    app=Application(layout=Layout(root),key_bindings=kb,
                    style=Style.from_dict({'prompt':'#ff69b4 bold','sep':'#888888'}),
                    full_screen=False,erase_when_done=True,output=output)
    try: app.run()
    except: pass
    finally:
        try: app.output.reset_attributes(); app.output.flush()
        except: pass
        sys.stdout.flush()
    return result[0]

def claude_style_input(prompt_str="> ", placeholder="", should_exit=None) -> Optional[str]:
    if _has_pt(): return _pt_input(prompt_str, placeholder)
    w=max(shutil.get_terminal_size().columns,10)
    print(f"{DARK_GRAY}{'─'*w}{WHITE}"); r=_simple(); print(f"{DARK_GRAY}{'─'*w}{WHITE}")
    if r:
        lines = r.count('\n') + 3
        for _ in range(lines):
            sys.stdout.write('\033[A\033[K')
        sys.stdout.flush()
    return r

def simple_input(prompt_str="> ") -> str:
    try: return input(f"{PINK}{prompt_str}{WHITE}")
    except: return ""

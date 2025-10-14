from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
import os

app = FastAPI(title="ComfyUI Outputs Browser")

ROOT = "/workspace/ComfyUI/output"

def list_files(root: str):
    items = []
    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            p = os.path.join(dirpath, fn)
            rel = os.path.relpath(p, root)
            items.append(rel)
    items.sort()
    return items

@app.get("/", response_class=HTMLResponse)
def index():
    os.makedirs(ROOT, exist_ok=True)
    files = list_files(ROOT)
    items = "".join([
        f"<li><a href='/file/{f}' target='_blank'>{f}</a></li>" for f in files
    ])
    html = f"""
<!doctype html>
<html lang='ru'>
<head>
  <meta charset='utf-8'>
  <meta name='viewport' content='width=device-width, initial-scale=1' />
  <title>Обзор результатов ComfyUI</title>
  <style>
    :root {{ --bg:#1e1e1e; --card:#282828; --text:#ffffff; --muted:#9ca3af; --accent:#ffffff; --accent-border:#ffffff; }}
    html,body {{ margin:0; padding:0; background:var(--bg); color:var(--text); font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, Arial; }}
    .wrap {{ max-width: 1200px; margin: 0 auto; padding: 40px 20px; }}
    .title {{ font-size: 36px; font-weight: 800; margin: 0 0 8px; color: var(--accent); text-align: center; text-shadow: 0 0 10px rgba(255,255,255,0.3); }}
    .subtitle {{ margin:0 0 40px; color:var(--muted); text-align: center; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 0 auto; max-width: 1000px; }}
    .card {{ background: var(--card); border:1px solid #3a3a3a; border-radius: 12px; padding: 24px; box-sizing: border-box; }}
    ul {{ list-style: none; padding:0; margin:20px 0 0; }}
    li {{ margin:8px 0; }}
    a {{ color:var(--accent); text-decoration:none; border-bottom: 1px solid var(--accent-border); }}
    a:hover {{ text-decoration:none; border-bottom-color: var(--accent); }}
    .row {{ display:flex; gap:12px; align-items:center; }}
    .btn {{ display:inline-flex; align-items:center; gap:8px; padding:12px 20px; background: rgba(255,255,255,0.9); color:var(--bg); font-weight:700; border:2px solid rgba(255,255,255,0.5); border-radius:8px; text-decoration:none; transition: all 0.2s; }}
    .btn:hover {{ background: var(--accent); color:var(--bg); border-color: var(--accent); }}
  </style>
</head>
<body>
  <div class='wrap'>
    <h1 class='title'>Результаты ComfyUI</h1>
    <p class='subtitle'>Обзор результатов ComfyUI · папка: {ROOT}</p>
    <div class='grid'>
      <div class='card'>
        <div class='row'>
          <a class='btn' href='/download-all'>Скачать все как ZIP</a>
        </div>
        <ul>{items}</ul>
      </div>
    </div>
  </div>
</body>
</html>
"""
    return HTMLResponse(html)

@app.get("/file/{path:path}")
def get_file(path: str):
    full = os.path.join(ROOT, path)
    if not os.path.isfile(full):
        return HTMLResponse("Not found", status_code=404)
    return FileResponse(full)

@app.get("/download-all")
def download_all():
    import tempfile, zipfile
    os.makedirs(ROOT, exist_ok=True)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
    tmp.close()
    with zipfile.ZipFile(tmp.name, 'w', zipfile.ZIP_DEFLATED) as z:
        for rel in list_files(ROOT):
            z.write(os.path.join(ROOT, rel), arcname=rel)
    return FileResponse(tmp.name, filename='comfyui_outputs.zip')



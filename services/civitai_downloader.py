from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, PlainTextResponse
import os
import re
import requests
import zipfile

app = FastAPI(title="CivitAI LoRA Downloader")

INDEX_HTML = """
<!doctype html>
<html lang=\"ru\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Загрузчик LoRA с CivitAI</title>
  <style>
    :root { --bg:#1e1e1e; --card:#282828; --text:#ffffff; --muted:#9ca3af; --accent:#ffffff; --accent-border:#000000; }
    html,body { margin:0; padding:0; background:var(--bg); color:var(--text); font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, Arial; }
    .wrap { max-width: 1200px; margin: 0 auto; padding: 40px 20px; }
    .title { font-size: 36px; font-weight: 800; margin: 0 0 8px; color: var(--accent); text-align: center; text-shadow: 0 0 10px rgba(255,255,255,0.3); }
    .subtitle { margin:0 0 40px; color:var(--muted); text-align: center; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 0 auto; max-width: 1000px; }
    .card { background: var(--card); border:1px solid #3a3a3a; border-radius: 12px; padding: 24px; box-sizing: border-box; }
    .row { display:grid; grid-template-columns: 200px 1fr; gap:16px; align-items:center; margin:16px 0; }
    input[type=text], input[type=password] { width:100%; padding:12px 16px; background:#1a1a1a; border:1px solid #3a3a3a; color:var(--text); border-radius:8px; box-sizing: border-box; }
    .btn { display:inline-flex; align-items:center; gap:8px; padding:12px 20px; background: rgba(255,255,255,0.9); color:var(--bg); font-weight:700; border:2px solid rgba(255,255,255,0.5); border-radius:8px; cursor:pointer; transition: all 0.2s; }
    .btn:hover { background: var(--accent); color:var(--bg); border-color: var(--accent); }
    a { color:var(--accent); text-decoration:none; border-bottom: 1px solid rgba(255,255,255,0.3); }
    a:hover { text-decoration:none; border-bottom-color: var(--accent); }
    .hint { background:#1a1a1a; border:1px dashed #3a3a3a; padding:16px; border-radius:8px; margin-bottom:20px; }
    .result { white-space: pre-wrap; background:#1a1a1a; border:1px solid #3a3a3a; padding:16px; border-radius:8px; margin-top:20px; min-height:24px; }
    .progress { margin-top:20px; }
    .progress-bar { width:100%; height:8px; background:#1a1a1a; border:1px solid #3a3a3a; border-radius:4px; overflow:hidden; }
    .progress-fill { height:100%; background:var(--accent); width:0%; transition:width 0.3s; }
    .progress-text { margin-top:8px; color:var(--muted); font-size:14px; text-align:center; }
    .mono { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace; }
  </style>
</head>
<body>
  <div class=\"wrap\">
    <h1 class=\"title\">Загрузчик LoRA</h1>
    <p class=\"subtitle\">Загрузчик LoRA · сохранение в <span class=\"mono\">/workspace/ComfyUI/models/loras</span></p>
    <div class=\"grid\">
      <div class=\"card\">
        <div class=\"hint\"><b>Где взять API-токен?</b> Создайте токен на странице аккаунта CivitAI: <a href=\"https://civitai.com/user/account\" target=\"_blank\">civitai.com/user/account</a>.</div>
        <form method=\"post\" action=\"/download\" style=\"margin-top:12px\">
          <div class=\"row\">
            <label for=\"token\">Токен</label>
            <input id=\"token\" type=\"password\" name=\"token\" placeholder=\"Скопируйте токен с CivitAI\" value=\"{{ token_value }}\" required />
          </div>
          <div class=\"row\">
            <label for=\"url\">Ссылка на модель</label>
            <input id=\"url\" type=\"text\" name=\"url\" placeholder=\"Страница модели или API: https://civitai.com/api/download/models/123456\" value=\"{{ url_value }}\" required />
          </div>
          <div class=\"row\" style=\"grid-template-columns:1fr;\">
            <button class=\"btn\" type=\"submit\">Скачать LoRA</button>
          </div>
        </form>
        <div class=\"result\" id=\"result\">{{ result }}</div>
        <div class=\"progress\" id=\"progress\" style=\"display:none;\">
          <div class=\"progress-bar\">
            <div class=\"progress-fill\" id=\"progress-fill\"></div>
          </div>
          <div class=\"progress-text\" id=\"progress-text\">Загрузка...</div>
        </div>
      </div>
    </div>
  </div>
  <script>
    document.querySelector('form').addEventListener('submit', function(e) {
      const progress = document.getElementById('progress');
      const result = document.getElementById('result');
      const btn = document.querySelector('.btn');
      
      // Показываем прогресс
      progress.style.display = 'block';
      result.textContent = '';
      btn.disabled = true;
      btn.textContent = 'Загрузка...';
      
      // Анимация прогресса
      let progressValue = 0;
      const progressFill = document.getElementById('progress-fill');
      const progressText = document.getElementById('progress-text');
      
      const interval = setInterval(() => {
        progressValue += Math.random() * 10;
        if (progressValue > 90) progressValue = 90;
        progressFill.style.width = progressValue + '%';
        progressText.textContent = `Загрузка... ${Math.round(progressValue)}%`;
      }, 200);
      
      // Очищаем интервал через 30 секунд (максимальное время ожидания)
      setTimeout(() => {
        clearInterval(interval);
        if (progressValue < 100) {
          progressFill.style.width = '100%';
          progressText.textContent = 'Завершение...';
        }
      }, 30000);
    });
  </script>
</body>
</html>
"""

def civitai_api_url_from_page(url: str) -> str | None:
    m = re.search(r"/models/(\d+)", url)
    if m:
        return f"https://civitai.com/api/download/models/{m.group(1)}"
    return None

def unzip_file(zip_path, extract_to=None):
    """Распаковывает zip-файл прямо в указанную папку без лишней подпапки"""
    if extract_to is None:
        extract_to = os.path.dirname(zip_path)
    
    extracted_files = []
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        for member in zip_ref.namelist():
            filename = os.path.basename(member)
            # пропускаем папки внутри архива
            if not filename:
                continue
            source = zip_ref.open(member)
            target_path = os.path.join(extract_to, filename)
            with open(target_path, "wb") as target:
                with source as src:
                    target.write(src.read())
            extracted_files.append(filename)
    
    # Удаляем zip файл после распаковки
    os.remove(zip_path)
    return extracted_files

@app.get("/", response_class=HTMLResponse)
def index():
    return HTMLResponse(INDEX_HTML.replace("{{ result }}", "").replace("{{ token_value }}", "").replace("{{ url_value }}", ""))

@app.post("/download")
def download(token: str = Form(...), url: str = Form(...)):
    target_dir = "/workspace/ComfyUI/models/loras"
    os.makedirs(target_dir, exist_ok=True)

    try:
        api_url = url
        if "civitai.com/api/download/models/" not in api_url:
            maybe = civitai_api_url_from_page(url)
            if not maybe:
                html_with_error = INDEX_HTML.replace("{{ result }}", "❌ Ошибка: Не удалось извлечь ID модели из URL")
                html_with_error = html_with_error.replace("{{ token_value }}", token)
                html_with_error = html_with_error.replace("{{ url_value }}", url)
                return HTMLResponse(html_with_error)

        headers = {"Authorization": f"Bearer {token}"}
        r = requests.get(api_url, headers=headers, stream=True, timeout=120)
        
        if r.status_code != 200:
            error_msg = f"❌ Ошибка {r.status_code}: {r.text[:200]}"
            if r.status_code == 401:
                error_msg = "❌ Ошибка авторизации: Проверьте API-ключ"
            elif r.status_code == 404:
                error_msg = "❌ Модель не найдена: Проверьте URL"
            html_with_error = INDEX_HTML.replace("{{ result }}", error_msg)
            html_with_error = html_with_error.replace("{{ token_value }}", token)
            html_with_error = html_with_error.replace("{{ url_value }}", url)
            return HTMLResponse(html_with_error)

        # Получаем размер файла
        total_size = int(r.headers.get('content-length', 0))
        
        filename = re.findall('filename="?([^";]+)"?', r.headers.get('content-disposition', ''))
        fname = filename[0] if filename else os.path.basename(api_url)
        path = os.path.join(target_dir, fname)

        downloaded = 0
        with open(path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024*1024):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)

        # Форматируем размер файла
        size_mb = downloaded / (1024 * 1024)
        success_msg = f"✅ Успешно загружено!\n📁 Файл: {fname}\n💾 Размер: {size_mb:.1f} MB\n📂 Путь: {path}"
        
        # Автоматическая распаковка zip-файлов
        if fname.endswith(".zip"):
            try:
                extracted_files = unzip_file(path, target_dir)
                success_msg += f"\n📦 Архив распакован! Извлечено файлов: {len(extracted_files)}"
                if extracted_files:
                    success_msg += f"\n📄 Файлы: {', '.join(extracted_files[:3])}"
                    if len(extracted_files) > 3:
                        success_msg += f" и еще {len(extracted_files) - 3} файлов"
            except Exception as e:
                success_msg += f"\n⚠️ Ошибка распаковки: {str(e)}"
        
        # Сохраняем значения формы
        html_with_result = INDEX_HTML.replace("{{ result }}", success_msg)
        html_with_result = html_with_result.replace("{{ token_value }}", token)
        html_with_result = html_with_result.replace("{{ url_value }}", url)
        
        return HTMLResponse(html_with_result)
        
    except requests.exceptions.Timeout:
        html_with_error = INDEX_HTML.replace("{{ result }}", "❌ Таймаут: Загрузка заняла слишком много времени")
        html_with_error = html_with_error.replace("{{ token_value }}", token)
        html_with_error = html_with_error.replace("{{ url_value }}", url)
        return HTMLResponse(html_with_error)
    except requests.exceptions.ConnectionError:
        html_with_error = INDEX_HTML.replace("{{ result }}", "❌ Ошибка соединения: Проверьте интернет-соединение")
        html_with_error = html_with_error.replace("{{ token_value }}", token)
        html_with_error = html_with_error.replace("{{ url_value }}", url)
        return HTMLResponse(html_with_error)
    except Exception as e:
        html_with_error = INDEX_HTML.replace("{{ result }}", f"❌ Неожиданная ошибка: {str(e)}")
        html_with_error = html_with_error.replace("{{ token_value }}", token)
        html_with_error = html_with_error.replace("{{ url_value }}", url)
        return HTMLResponse(html_with_error)



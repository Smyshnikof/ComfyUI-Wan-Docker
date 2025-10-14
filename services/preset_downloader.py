from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, PlainTextResponse
import os
import subprocess
import threading
import uuid

# Глобальный словарь для отслеживания статуса загрузок
download_status = {}
import requests
import json
from huggingface_hub import hf_hub_download, login
import tempfile

app = FastAPI(title="Preset & Model Downloader")

# Доступные пресеты
PRESETS = {
    "WAN_T2V": {
        "name": "Wan T2V (Text-to-Video)",
        "description": "Генерация видео из текста",
        "size": "~40GB",
        "time": "15-20 мин"
    },
    "WAN_T2I": {
        "name": "Wan T2I (Text-to-Image)", 
        "description": "Генерация изображений из текста",
        "size": "~18GB",
        "time": "8-12 мин"
    },
    "WAN_I2V": {
        "name": "Wan I2V (Image-to-Video)",
        "description": "Генерация видео из изображения",
        "size": "~40GB", 
        "time": "15-20 мин"
    },
    "WAN_ANIMATE": {
        "name": "Wan Animate",
        "description": "Анимация изображений",
        "size": "~30GB",
        "time": "10-15 мин"
    }
}

INDEX_HTML = """
<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Загрузчик пресетов и моделей</title>
  <style>
    :root { --bg:#1e1e1e; --card:#282828; --text:#ffffff; --muted:#9ca3af; --accent:#ffffff; --accent-border:#000000; }
    html,body { margin:0; padding:0; background:var(--bg); color:var(--text); font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, Arial; }
    .wrap { max-width: 1200px; margin: 0 auto; padding: 40px 20px; }
    .title { font-size: 36px; font-weight: 800; margin: 0 0 8px; color: var(--accent); text-align: center; text-shadow: 0 0 10px rgba(255,255,255,0.3); }
    .subtitle { margin:0 0 40px; color:var(--muted); text-align: center; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 0 auto; max-width: 1000px; }
    .card { background: var(--card); border:1px solid #3a3a3a; border-radius: 12px; padding: 24px; box-sizing: border-box; }
    .row { display:grid; grid-template-columns: 200px 1fr; gap:16px; align-items:center; margin:16px 0; }
    .row-full { display:grid; grid-template-columns: 1fr; gap:16px; margin:16px 0; }
    input[type=text], input[type=password] { width:100%; padding:12px 16px; background:#1a1a1a; border:1px solid #3a3a3a; color:var(--text); border-radius:8px; box-sizing: border-box; }
    .btn { display:inline-flex; align-items:center; gap:8px; padding:12px 20px; background: rgba(255,255,255,0.9); color:var(--bg); font-weight:700; border:2px solid rgba(255,255,255,0.5); border-radius:8px; cursor:pointer; transition: all 0.2s; }
    .btn:hover { background: var(--accent); color:var(--bg); border-color: var(--accent); }
    .btn:disabled { opacity:0.5; cursor:not-allowed; }
    .btn-preset { 
      background: rgba(34, 197, 94, 0.9); 
      color: white; 
      border-color: rgba(34, 197, 94, 0.5); 
      box-shadow: 0 4px 12px rgba(34, 197, 94, 0.3);
    }
    .btn-preset:hover { 
      background: rgb(34, 197, 94); 
      color: white;
      border-color: rgb(34, 197, 94); 
      box-shadow: 0 8px 20px rgba(34, 197, 94, 0.5);
    }
    .btn-hf { 
      background: rgba(255, 193, 7, 0.9); 
      color: black; 
      border-color: rgba(255, 193, 7, 0.5); 
      box-shadow: 0 4px 12px rgba(255, 193, 7, 0.3);
    }
    .btn-hf:hover { 
      background: rgb(255, 193, 7); 
      color: black;
      border-color: rgb(255, 193, 7); 
      box-shadow: 0 8px 20px rgba(255, 193, 7, 0.5);
    }
    a { color:var(--accent); text-decoration:none; border-bottom: 1px solid rgba(255,255,255,0.3); }
    a:hover { text-decoration:none; border-bottom-color: var(--accent); }
    .hint { background:#1a1a1a; border:1px dashed #3a3a3a; padding:16px; border-radius:8px; margin-bottom:20px; }
    .result { white-space: pre-wrap; background:#1a1a1a; border:1px solid #3a3a3a; padding:16px; border-radius:8px; margin-top:20px; min-height:24px; }
    .progress { margin-top:20px; }
    .progress-bar { width:100%; height:8px; background:#1a1a1a; border:1px solid #3a3a3a; border-radius:4px; overflow:hidden; }
    .progress-fill { height:100%; background:var(--accent); width:0%; transition:width 0.3s; }
    .progress-text { margin-top:8px; color:var(--muted); font-size:14px; text-align:center; }
    .mono { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace; }
    .preset-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 16px; margin: 20px 0; }
    .preset-card { background: #1a1a1a; border: 1px solid #3a3a3a; border-radius: 8px; padding: 16px; cursor: pointer; transition: all 0.2s; }
    .preset-card:hover { border-color: var(--accent); background: #222; }
    .preset-card.selected { border-color: var(--accent); background: rgba(255,255,255,0.1); }
    .preset-name { font-weight: 700; margin-bottom: 8px; color: var(--accent); }
    .preset-desc { color: var(--muted); font-size: 14px; margin-bottom: 8px; }
    .preset-info { font-size: 12px; color: var(--muted); }
    .tabs { display: flex; gap: 8px; margin-bottom: 20px; justify-content: center; }
    .tab { padding: 8px 16px; background: #1a1a1a; border: 1px solid #3a3a3a; border-radius: 8px; cursor: pointer; transition: all 0.2s; }
    .tab.active { background: var(--accent); color: var(--bg); }
    .tab-content { display: none; }
    .tab-content.active { display: block; }
  </style>
</head>
<body>
  <div class="wrap">
    <h1 class="title">Загрузчик пресетов и моделей</h1>
    <p class="subtitle">Скачивание пресетов Wan и моделей с HuggingFace</p>
    
    <div class="tabs">
      <div class="tab active" onclick="switchTab('presets')">🎯 Пресеты Wan</div>
      <div class="tab" onclick="switchTab('huggingface')">🤗 HuggingFace</div>
    </div>
    
    <div class="grid">
      <!-- Пресеты -->
      <div class="card tab-content active" id="presets-tab">
        <h3>Выберите пресеты для скачивания</h3>
        <div class="preset-grid" id="preset-grid">
          {{ presets_html }}
        </div>
        <div class="row-full">
          <button class="btn btn-preset" onclick="downloadPresets()" id="download-presets-btn" disabled>
            📥 Скачать выбранные пресеты
          </button>
        </div>
        <div class="result" id="preset-result"></div>
        <div class="progress" id="preset-progress" style="display:none;">
          <div class="progress-bar">
            <div class="progress-fill" id="preset-progress-fill"></div>
          </div>
          <div class="progress-text" id="preset-progress-text">Загрузка...</div>
        </div>
      </div>
      
      <!-- HuggingFace -->
      <div class="card tab-content" id="huggingface-tab">
        <div class="hint">
          <b>Как использовать?</b> Выберите способ: прямая ссылка на файл (рекомендуется) или HuggingFace репозиторий. 
          Для приватных моделей нужен API токен с правами "Read" - см. инструкцию ниже.
        </div>
        
        <div class="tabs" style="margin-bottom: 20px;">
          <div class="tab active" onclick="switchHFMethod('url')">🔗 Прямая ссылка</div>
          <div class="tab" onclick="switchHFMethod('repo')">🤗 HuggingFace Repo</div>
        </div>
        
        <!-- Прямая ссылка метод (дефолтный) -->
        <form id="hf-url-form" method="post" action="/download_url" style="margin-top:12px;">
          <div class="row">
            <label for="hf_url">Прямая ссылка на файл</label>
            <input id="hf_url" type="text" name="url" placeholder="https://huggingface.co/username/model/resolve/main/file.safetensors" required />
          </div>
          <div class="row">
            <label for="hf_url_folder">Папка назначения</label>
            <select id="hf_url_folder" name="folder" style="width:100%; padding:12px 16px; background:#1a1a1a; border:1px solid #3a3a3a; color:var(--text); border-radius:8px;">
              <option value="diffusion_models">diffusion_models</option>
              <option value="loras">loras</option>
              <option value="vae">vae</option>
              <option value="text_encoders">text_encoders</option>
              <option value="upscale_models">upscale_models</option>
              <option value="clip_vision">clip_vision</option>
              <option value="audio_encoders">audio_encoders</option>
              <option value="checkpoints">checkpoints</option>
              <option value="clip">clip</option>
              <option value="configs">configs</option>
              <option value="controlnet">controlnet</option>
              <option value="diffusers">diffusers</option>
              <option value="embeddings">embeddings</option>
              <option value="gligen">gligen</option>
              <option value="hypernetworks">hypernetworks</option>
              <option value="ipadapter">ipadapter</option>
              <option value="model_patches">model_patches</option>
              <option value="onnx">onnx</option>
              <option value="photomaker">photomaker</option>
              <option value="sams">sams</option>
              <option value="style_models">style_models</option>
              <option value="unet">unet</option>
              <option value="vae_approx">vae_approx</option>
              <option value="vibevoice">vibevoice</option>
            </select>
          </div>
          <div class="row" style="grid-template-columns:1fr;">
            <button class="btn btn-hf" type="submit">🔗 Скачать по ссылке</button>
          </div>
        </form>
        
        <!-- HuggingFace Repo метод -->
        <form id="hf-repo-form" method="post" action="/download_hf" style="margin-top:12px; display:none;">
          <div class="row">
            <label for="hf_repo">Репозиторий</label>
            <input id="hf_repo" type="text" name="repo" placeholder="username/model-name" value="{{ hf_repo_value }}" />
          </div>
          <div class="row">
            <label for="hf_file">Файл (опционально)</label>
            <input id="hf_file" type="text" name="filename" placeholder="model.safetensors" value="{{ hf_file_value }}" />
          </div>
          <div class="row">
            <label for="hf_token">API токен (опционально)</label>
            <input id="hf_token" type="password" name="token" placeholder="hf_..." value="{{ hf_token_value }}" autocomplete="current-password" />
            <div style="margin-top: 8px; padding: 12px; background: #1a1a1a; border: 1px solid #3a3a3a; border-radius: 8px; font-size: 12px; word-wrap: break-word;">
              <div style="color: #4a9eff; font-weight: 600; margin-bottom: 8px;">📋 Как создать токен:</div>
              <div style="color: #ccc; line-height: 1.4;">
                1. Перейдите по ссылке: <a href="https://huggingface.co/settings/tokens" target="_blank" style="color: #4a9eff; text-decoration: underline;">https://huggingface.co/settings/tokens</a><br>
                2. Нажмите "New token"<br>
                3. Выберите "Read" (достаточно для скачивания)<br>
                4. Введите название токена<br>
                5. Нажмите "Create token"<br>
                6. Скопируйте токен (начинается с hf_...)
              </div>
            </div>
          </div>
          <div class="row">
            <label for="hf_folder">Папка назначения</label>
            <select id="hf_folder" name="folder" style="width:100%; padding:12px 16px; background:#1a1a1a; border:1px solid #3a3a3a; color:var(--text); border-radius:8px;">
              <option value="diffusion_models">diffusion_models</option>
              <option value="loras">loras</option>
              <option value="vae">vae</option>
              <option value="text_encoders">text_encoders</option>
              <option value="upscale_models">upscale_models</option>
              <option value="clip_vision">clip_vision</option>
              <option value="audio_encoders">audio_encoders</option>
              <option value="checkpoints">checkpoints</option>
              <option value="clip">clip</option>
              <option value="configs">configs</option>
              <option value="controlnet">controlnet</option>
              <option value="diffusers">diffusers</option>
              <option value="embeddings">embeddings</option>
              <option value="gligen">gligen</option>
              <option value="hypernetworks">hypernetworks</option>
              <option value="ipadapter">ipadapter</option>
              <option value="model_patches">model_patches</option>
              <option value="onnx">onnx</option>
              <option value="photomaker">photomaker</option>
              <option value="sams">sams</option>
              <option value="style_models">style_models</option>
              <option value="unet">unet</option>
              <option value="vae_approx">vae_approx</option>
              <option value="vibevoice">vibevoice</option>
            </select>
          </div>
          <div class="row" style="grid-template-columns:1fr;">
            <button class="btn btn-hf" type="submit">🤗 Скачать с HuggingFace</button>
          </div>
        </form>
        <div class="result" id="hf-result">{{ hf_result }}</div>
        <div class="progress" id="hf-progress" style="display:none;">
          <div class="progress-bar">
            <div class="progress-fill" id="hf-progress-fill"></div>
          </div>
          <div class="progress-text" id="hf-progress-text">Загрузка...</div>
        </div>
      </div>
    </div>
  </div>
  
  <script>
    let selectedPresets = [];
    
    function switchTab(tabName) {
      // Убираем активный класс со всех табов и контента
      document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
      
      // Активируем выбранный таб
      document.querySelector(`[onclick="switchTab('${tabName}')"]`).classList.add('active');
      document.getElementById(`${tabName}-tab`).classList.add('active');
      
      // Если переключаемся на HuggingFace, активируем таб "Прямая ссылка"
      if (tabName === 'huggingface') {
        switchHFMethod('url');
      }
    }
    
    function switchHFMethod(method) {
      // Убираем активный класс со всех табов в HuggingFace разделе
      document.querySelectorAll('#huggingface-tab .tabs .tab').forEach(tab => tab.classList.remove('active'));
      
      // Активируем выбранный таб
      document.querySelector(`#huggingface-tab [onclick="switchHFMethod('${method}')"]`).classList.add('active');
      
      // Показываем/скрываем формы
      if (method === 'url') {
        document.getElementById('hf-url-form').style.display = 'block';
        document.getElementById('hf-repo-form').style.display = 'none';
      } else {
        document.getElementById('hf-url-form').style.display = 'none';
        document.getElementById('hf-repo-form').style.display = 'block';
      }
    }
    
    function togglePreset(presetId) {
      const card = document.querySelector(`[data-preset="${presetId}"]`);
      if (selectedPresets.includes(presetId)) {
        selectedPresets = selectedPresets.filter(p => p !== presetId);
        card.classList.remove('selected');
      } else {
        selectedPresets.push(presetId);
        card.classList.add('selected');
      }
      
      const btn = document.getElementById('download-presets-btn');
      btn.disabled = selectedPresets.length === 0;
      btn.textContent = selectedPresets.length > 0 ? 
        `📥 Скачать выбранные пресеты (${selectedPresets.length})` : 
        '📥 Скачать выбранные пресеты';
    }
    
    function downloadPresets() {
      if (selectedPresets.length === 0) return;
      
      const progress = document.getElementById('preset-progress');
      const result = document.getElementById('preset-result');
      const btn = document.getElementById('download-presets-btn');
      
      // Показываем прогресс
      progress.style.display = 'block';
      result.textContent = '';
      btn.disabled = true;
      btn.textContent = 'Загрузка...';
      
      // Отправляем запрос
      const formData = new FormData();
      formData.append('presets', selectedPresets.join(','));
      
      fetch('/download_presets', {
        method: 'POST',
        body: formData
      })
      .then(response => response.json())
      .then(data => {
        if (data.task_id) {
          result.textContent = data.message;
          // Начинаем опрос статуса
          pollStatus(data.task_id);
        } else {
          result.textContent = data.message;
          progress.style.display = 'none';
          btn.disabled = false;
          btn.textContent = '📥 Скачать выбранные пресеты';
        }
      })
      .catch(error => {
        result.textContent = '❌ Ошибка: ' + error.message;
        progress.style.display = 'none';
        btn.disabled = false;
        btn.textContent = '📥 Скачать выбранные пресеты';
      });
    }
    
    function pollStatus(taskId) {
      const progress = document.getElementById('preset-progress');
      const result = document.getElementById('preset-result');
      const btn = document.getElementById('download-presets-btn');
      
      fetch(`/status/${taskId}`)
      .then(response => response.json())
      .then(data => {
        if (data.status === 'completed' || data.status === 'error') {
          result.textContent = data.message;
          progress.style.display = 'none';
          btn.disabled = false;
          btn.textContent = '📥 Скачать выбранные пресеты';
        } else if (data.status === 'running') {
          result.textContent = data.message + ' (проверяем статус...)';
          // Повторяем через 2 секунды
          setTimeout(() => pollStatus(taskId), 2000);
        } else {
          result.textContent = '❌ Неизвестный статус: ' + data.message;
          progress.style.display = 'none';
          btn.disabled = false;
          btn.textContent = '📥 Скачать выбранные пресеты';
        }
      })
      .catch(error => {
        result.textContent = '❌ Ошибка проверки статуса: ' + error.message;
        progress.style.display = 'none';
        btn.disabled = false;
        btn.textContent = '📥 Скачать выбранные пресеты';
      });
    }
    
    function pollHFStatus(taskId) {
      const progress = document.getElementById('hf-progress');
      const result = document.getElementById('hf-result');
      const btn = document.querySelector('form[action="/download_hf"] button[type="submit"]') || 
                  document.querySelector('form[action="/download_url"] button[type="submit"]');
      
      fetch(`/status/${taskId}`)
      .then(response => response.json())
      .then(data => {
        if (data.status === 'completed' || data.status === 'error') {
          result.textContent = data.message;
          progress.style.display = 'none';
          btn.disabled = false;
          btn.textContent = btn.textContent.includes('HuggingFace') ? '🤗 Скачать с HuggingFace' : '🔗 Скачать по ссылке';
        } else if (data.status === 'running') {
          result.textContent = data.message + ' (проверяем статус...)';
          // Повторяем через 2 секунды
          setTimeout(() => pollHFStatus(taskId), 2000);
        } else {
          result.textContent = '❌ Неизвестный статус: ' + data.message;
          progress.style.display = 'none';
          btn.disabled = false;
          btn.textContent = btn.textContent.includes('HuggingFace') ? '🤗 Скачать с HuggingFace' : '🔗 Скачать по ссылке';
        }
      })
      .catch(error => {
        result.textContent = '❌ Ошибка проверки статуса: ' + error.message;
        progress.style.display = 'none';
        btn.disabled = false;
        btn.textContent = btn.textContent.includes('HuggingFace') ? '🤗 Скачать с HuggingFace' : '🔗 Скачать по ссылке';
      });
    }
    
    // Обработка формы HuggingFace (только для репозитория)
    document.querySelector('form[action="/download_hf"]').addEventListener('submit', function(e) {
      e.preventDefault(); // Предотвращаем стандартную отправку формы
      
      const progress = document.getElementById('hf-progress');
      const result = document.getElementById('hf-result');
      const btn = document.querySelector('form[action="/download_hf"] button[type="submit"]');
      
      // Показываем прогресс
      progress.style.display = 'block';
      result.textContent = '';
      btn.disabled = true;
      btn.textContent = 'Загрузка...';
      
      // Отправляем форму через fetch
      const formData = new FormData(this);
      
      fetch('/download_hf', {
        method: 'POST',
        body: formData
      })
      .then(response => response.json())
      .then(data => {
        if (data.task_id) {
          result.textContent = data.message;
          // Начинаем опрос статуса
          pollHFStatus(data.task_id);
        } else {
          result.textContent = data.message;
          progress.style.display = 'none';
          btn.disabled = false;
          btn.textContent = '🤗 Скачать с HuggingFace';
        }
      })
      .catch(error => {
        result.textContent = '❌ Ошибка: ' + error.message;
        progress.style.display = 'none';
        btn.disabled = false;
        btn.textContent = '🤗 Скачать с HuggingFace';
      });
    });
    
    // Обработка формы прямой ссылки
    document.querySelector('form[action="/download_url"]').addEventListener('submit', function(e) {
      e.preventDefault(); // Предотвращаем стандартную отправку формы
      
      const progress = document.getElementById('hf-progress');
      const result = document.getElementById('hf-result');
      const btn = document.querySelector('form[action="/download_url"] button[type="submit"]');
      
      // Показываем прогресс
      progress.style.display = 'block';
      result.textContent = '';
      btn.disabled = true;
      btn.textContent = 'Загрузка...';
      
      // Отправляем форму через fetch
      const formData = new FormData(this);
      
      fetch('/download_url', {
        method: 'POST',
        body: formData
      })
      .then(response => response.json())
      .then(data => {
        if (data.task_id) {
          result.textContent = data.message;
          // Начинаем опрос статуса
          pollHFStatus(data.task_id);
        } else {
          result.textContent = data.message;
          progress.style.display = 'none';
          btn.disabled = false;
          btn.textContent = '🔗 Скачать по ссылке';
        }
      })
      .catch(error => {
        result.textContent = '❌ Ошибка: ' + error.message;
        progress.style.display = 'none';
        btn.disabled = false;
        btn.textContent = '🔗 Скачать по ссылке';
      });
    });
  </script>
</body>
</html>
"""

def generate_presets_html():
    html = ""
    for preset_id, preset_info in PRESETS.items():
        html += f'''
        <div class="preset-card" data-preset="{preset_id}" onclick="togglePreset('{preset_id}')">
          <div class="preset-name">{preset_info['name']}</div>
          <div class="preset-desc">{preset_info['description']}</div>
          <div class="preset-info">Размер: {preset_info['size']} • Время: {preset_info['time']}</div>
        </div>
        '''
    return html

@app.get("/", response_class=HTMLResponse)
def index():
    presets_html = generate_presets_html()
    return HTMLResponse(INDEX_HTML.replace("{{ presets_html }}", presets_html)
                       .replace("{{ hf_repo_value }}", "")
                       .replace("{{ hf_file_value }}", "")
                       .replace("{{ hf_token_value }}", "")
                       .replace("{{ hf_result }}", ""))

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "Preset downloader is running"}

@app.get("/status/{task_id}")
def get_status(task_id: str):
    if task_id not in download_status:
        return {"status": "not_found", "message": "Задача не найдена"}
    
    return download_status[task_id]

@app.post("/download_presets")
def download_presets(presets: str = Form(...)):
    try:
        # Парсим строку пресетов
        presets_list = [p.strip() for p in presets.split(',') if p.strip()]
        
        if not presets_list:
            return {"message": "❌ Не выбрано ни одного пресета"}
        
        # Запускаем скрипт скачивания пресетов в фоне
        import threading
        import uuid
        
        # Создаем уникальный ID для отслеживания
        task_id = str(uuid.uuid4())
        
        def run_download():
            try:
                result = subprocess.run(
                    ["bash", "/download_presets.sh", ",".join(presets_list)],
                    capture_output=True,
                    text=True,
                    timeout=1800  # 30 минут
                )
                
                if result.returncode == 0:
                    download_status[task_id] = {
                        "status": "completed",
                        "message": f"✅ Успешно скачаны пресеты: {', '.join(presets_list)}\n\n{result.stdout}"
                    }
                else:
                    download_status[task_id] = {
                        "status": "error", 
                        "message": f"❌ Ошибка скачивания пресетов:\n{result.stderr}"
                    }
            except subprocess.TimeoutExpired:
                download_status[task_id] = {
                    "status": "error",
                    "message": "❌ Таймаут: Скачивание заняло слишком много времени"
                }
            except Exception as e:
                download_status[task_id] = {
                    "status": "error",
                    "message": f"❌ Ошибка: {str(e)}"
                }
        
        # Запускаем в отдельном потоке
        thread = threading.Thread(target=run_download)
        thread.daemon = True
        thread.start()
        
        # Сохраняем статус
        download_status[task_id] = {
            "status": "running",
            "message": f"🚀 Начато скачивание пресетов: {', '.join(presets_list)}"
        }
        
        return {"message": f"🚀 Скачивание начато! ID задачи: {task_id}", "task_id": task_id}
            
    except Exception as e:
        return {"message": f"❌ Ошибка: {str(e)}"}

@app.post("/download_hf")
def download_hf(repo: str = Form(...), filename: str = Form(""), token: str = Form(""), folder: str = Form("diffusion_models")):
    try:
        # Создаем уникальный ID для отслеживания
        task_id = str(uuid.uuid4())
        
        def run_hf_download():
            try:
                target_dir = f"/workspace/ComfyUI/models/{folder}"
                os.makedirs(target_dir, exist_ok=True)
                
                # Если есть токен, логинимся
                if token:
                    login(token=token)
                
                # Скачиваем файл
                if filename:
                    # Скачиваем конкретный файл
                    file_path = hf_hub_download(
                        repo_id=repo,
                        filename=filename,
                        cache_dir=target_dir,
                        local_dir=target_dir,
                        local_dir_use_symlinks=False
                    )
                    file_name = os.path.basename(file_path)
                else:
                    # Скачиваем весь репозиторий
                    from huggingface_hub import snapshot_download
                    snapshot_download(
                        repo_id=repo,
                        cache_dir=target_dir,
                        local_dir=target_dir,
                        local_dir_use_symlinks=False
                    )
                    file_name = f"весь репозиторий {repo}"
                
                # Получаем размер файла
                if os.path.isfile(file_path):
                    size_mb = os.path.getsize(file_path) / (1024 * 1024)
                    success_msg = f"✅ Успешно загружено!\n📁 Файл: {file_name}\n💾 Размер: {size_mb:.1f} MB\n📂 Путь: {target_dir}"
                else:
                    success_msg = f"✅ Успешно загружено!\n📁 Репозиторий: {file_name}\n📂 Путь: {target_dir}"
                
                download_status[task_id] = {
                    "status": "completed",
                    "message": success_msg
                }
                
            except Exception as e:
                error_msg = f"❌ Ошибка: {str(e)}"
                
                # Если ошибка связана с токеном, предлагаем его ввести
                if "authentication" in str(e).lower() or "token" in str(e).lower():
                    error_msg += "\n\n💡 Попробуйте ввести API токен HuggingFace"
                
                download_status[task_id] = {
                    "status": "error",
                    "message": error_msg
                }
        
        # Запускаем в отдельном потоке
        thread = threading.Thread(target=run_hf_download)
        thread.daemon = True
        thread.start()
        
        # Сохраняем статус
        download_status[task_id] = {
            "status": "running",
            "message": f"🚀 Начато скачивание с HuggingFace: {repo}"
        }
        
        return {"message": f"🚀 Скачивание начато! ID задачи: {task_id}", "task_id": task_id}
        
    except Exception as e:
        return {"message": f"❌ Ошибка: {str(e)}"}

@app.post("/download_url")
def download_url(url: str = Form(...), folder: str = Form("diffusion_models")):
    try:
        # Создаем уникальный ID для отслеживания
        task_id = str(uuid.uuid4())
        
        def run_url_download():
            try:
                target_dir = f"/workspace/ComfyUI/models/{folder}"
                os.makedirs(target_dir, exist_ok=True)
                
                # Скачиваем файл по прямой ссылке
                import requests
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                response = requests.get(url, stream=True, headers=headers)
                response.raise_for_status()
                
                # Получаем имя файла из URL
                filename = url.split('/')[-1]
                # Убираем параметры запроса (?download=true и т.д.)
                if '?' in filename:
                    filename = filename.split('?')[0]
                
                # Пытаемся получить имя файла из заголовков Content-Disposition
                if 'content-disposition' in response.headers:
                    import re
                    import urllib.parse
                    content_disposition = response.headers['content-disposition']
                    
                    # Ищем filename* (RFC 5987) для UTF-8 имен
                    utf8_match = re.search(r"filename\*=UTF-8''([^;]+)", content_disposition)
                    if utf8_match:
                        filename = urllib.parse.unquote(utf8_match.group(1))
                    else:
                        # Обычный filename
                        filename_match = re.search(r'filename[^;=\n]*=(([\'"]).*?\2|[^;\n]*)', content_disposition)
                        if filename_match:
                            filename = filename_match.group(1).strip('\'"')
                
                if not filename or '.' not in filename:
                    filename = "downloaded_file"
                
                file_path = os.path.join(target_dir, filename)
                
                # Скачиваем файл
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                # Получаем размер файла
                size_mb = os.path.getsize(file_path) / (1024 * 1024)
                success_msg = f"✅ Успешно загружено!\n🔗 Ссылка: {url}\n📄 Файл: {filename}\n💾 Размер: {size_mb:.1f} MB\n📂 Путь: {target_dir}"
                
                download_status[task_id] = {
                    "status": "completed",
                    "message": success_msg
                }
                
            except Exception as e:
                error_msg = f"❌ Ошибка: {str(e)}"
                download_status[task_id] = {
                    "status": "error",
                    "message": error_msg
                }
        
        # Запускаем в отдельном потоке
        thread = threading.Thread(target=run_url_download)
        thread.daemon = True
        thread.start()
        
        # Сохраняем статус
        download_status[task_id] = {
            "status": "running",
            "message": f"🚀 Начато скачивание по ссылке: {url}"
        }
        
        return {"message": f"🚀 Скачивание начато! ID задачи: {task_id}", "task_id": task_id}
        
    except Exception as e:
        return {"message": f"❌ Ошибка: {str(e)}"}

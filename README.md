[![Build and Push Docker Images](https://github.com/Smyshnikof/ComfyUI-Wan-Docker/actions/workflows/build.yml/badge.svg)](https://github.com/Smyshnikof/ComfyUI-Wan-Docker/actions/workflows/build.yml)

> 🎥 **Основан на серии роликов по Wan 2.2** от [Егор Смышников](https://www.youtube.com/playlist?list=PLUREBJZfEOoPztQiVSV7vYegAsOtwMiZi)

> 🔄 **Автообновление каждые 8 часов** для включения последней версии.

> 💬 Обратная связь и проблемы → [GitHub Issues](https://github.com/somb1/ComfyUI-Docker/issues)

> 🚀 Этот Docker образ изначально создан для запуска на RunPod, но также может использоваться на вашем локальном компьютере.

## 📚 Документация

- **[🚀 Быстрый старт](QUICK_START.md)** - Для новичков (рекомендуется)
- **[💻 Установка через JupyterLab](JUPYTER_SETUP.md)** - Рекомендуемый метод  
- **[📖 Полный гайд](GUIDE.md)** - Подробная документация
- **[❓ FAQ](FAQ.md)** - Часто задаваемые вопросы
- **[🚀 Развертывание](DEPLOYMENT.md)** - Для разработчиков
- **[📢 Публикация](PUBLISH_GUIDE.md)** - Инструкции по публикации

## 🔌 Открытые порты

| Порт | Тип | Сервис |
| ---- | ---- | ----------- |
| 22   | TCP  | SSH         |
| 3000 | HTTP | ComfyUI     |
| 8081 | HTTP | Загрузчик пресетов и моделей |
| 8082 | HTTP | CivitAI LoRA downloader |
| 8083 | HTTP | Обзор результатов |
| 8888 | HTTP | JupyterLab  |

---

## 🏷️ Формат тегов

```text
smyshnikof/comfyui-wan:(A)-torch2.8.0-(B)
```

* **(A)**: `base` - основной образ
  * `base`: ComfyUI + Manager + кастомные ноды + веб-загрузчик пресетов
* **(B)**: версия CUDA → `cu124`, `cu126`, `cu128`

---

## 🧱 Варианты образов

| Имя образа                                 | Кастомные ноды | Пресеты | CUDA |
| ------------------------------------------ | ------------ | ---- | ---- |
| `smyshnikof/comfyui-wan:base-torch2.8.0-cu124`| ✅ Да         | ✅ Да  | 12.4 |
| `smyshnikof/comfyui-wan:base-torch2.8.0-cu126`| ✅ Да         | ✅ Да  | 12.6 |
| `smyshnikof/comfyui-wan:base-torch2.8.0-cu128`| ✅ Да         | ✅ Да  | 12.8 |

> 👉 Для переключения: **Edit Pod/Template** → установите `Container Image`.

---

## 🎮 Совместимость с видеокартами

| Видеокарта | Рекомендуемый образ | Примечание |
|------------|-------------------|------------|
| **RTX 5090** | `smyshnikof/comfyui-wan:base-torch2.8.0-cu128` | Требует CUDA 12.8+ для SageAttention2 |
| **RTX 5080** | `smyshnikof/comfyui-wan:base-torch2.8.0-cu128` | Требует CUDA 12.8+ для SageAttention2 |
| **RTX 4090** | `smyshnikof/comfyui-wan:base-torch2.8.0-cu126` | Оптимальная производительность |
| **RTX 4080** | `smyshnikof/comfyui-wan:base-torch2.8.0-cu126` | Отличная совместимость |
| **RTX 4070** | `smyshnikof/comfyui-wan:base-torch2.8.0-cu124` | Стабильная работа |
| **RTX 3090** | `smyshnikof/comfyui-wan:base-torch2.8.0-cu124` | Совместимость с Ampere |
| **RTX 3080** | `smyshnikof/comfyui-wan:base-torch2.8.0-cu124` | Совместимость с Ampere |

> ⚠️ **Важно**: RTX 5090/5080 требуют CUDA 12.8+ для корректной работы SageAttention2. При использовании CUDA 12.4/12.6 SageAttention2 не установится.

---

## ⚙️ Переменные окружения

| Переменная                | Описание                                                                | По умолчанию   |
| ----------------------- | -------------------------------------------------------------------------- | --------- |
| `ACCESS_PASSWORD`       | Пароль для JupyterLab & code-server                                      | (не установлен)   |
| `TIME_ZONE`             | [Часовой пояс](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones) (например, `Asia/Seoul`)   | `Etc/UTC` |
| `COMFYUI_EXTRA_ARGS`    | Дополнительные опции ComfyUI (например `--fast`)                        | (не установлен)   |
| `INSTALL_SAGEATTENTION` | Установить [SageAttention2](https://github.com/thu-ml/SageAttention) при запуске (`True`/`False`) | `True`    |
| `PRESET_DOWNLOAD`       | Скачать пресеты моделей при запуске (список через запятую). **См. ниже**.                  | (не установлен)   |

> 👉 Для установки: **Edit Pod/Template** → **Add Environment Variable** (Key/Value).

> ⚠️ SageAttention2 требует **GPU Ampere+** и ~5 минут для установки.

> 🎯 **Этот template идеально подходит для видеокарт 40 и 50 серии** (RTX 4090, RTX 4080, RTX 4070, RTX 5090, RTX 5080 и т.д.)  
> ⚠️ **Для RTX 5090 используйте образ с CUDA 12.8+** (`smyshnikof/comfyui:base-torch2.8.0-cu128`)

---

## 🔧 Скачивание пресетов (Wan)

> Переменная `PRESET_DOWNLOAD` принимает либо **один пресет**, либо **несколько пресетов** через запятую.\
> (например `WAN_T2V` или `WAN_T2V,WAN_T2I,WAN_I2V,WAN_ANIMATE`) \
> **Для использования всех пресетов:** `WAN_T2V,WAN_T2I,WAN_I2V,WAN_ANIMATE` \
> При установке контейнер автоматически скачает соответствующие модели при запуске.

> Также можно вручную запустить скрипт скачивания пресетов **внутри JupyterLab или code-server**:

```bash
bash /download_presets.sh PRESET1,PRESET2,...
```

> Доступные пресеты: `WAN_T2V`, `WAN_T2I`, `WAN_I2V`, `WAN_ANIMATE`.

### Wan пресеты (встроенные workflow)

Новые кастомные пресеты, которые включают скачивание моделей и готовые к использованию workflow:

- `WAN_T2V` - Text-to-Video генерация
- `WAN_T2I` - Text-to-Image генерация  
- `WAN_I2V` - Image-to-Video генерация
- `WAN_ANIMATE` - Wan Animate генерация

Соответствующие workflow копируются в `/workspace/ComfyUI/user/default/workflows/` при запуске.

---

## 📁 Логи

| Приложение         | Путь к логу                                   |
| ----------- | ------------------------------------------ |
| ComfyUI     | `/workspace/ComfyUI/user/comfyui_3000.log` |
| JupyterLab  | `/workspace/logs/jupyterlab.log`           |
| CivitAI Downloader | `/workspace/logs/civitai_downloader.log` |
| Outputs Browser | `/workspace/logs/outputs_browser.log` |

---

## 🧩 Предустановленные компоненты

### Система

* **ОС**: Ubuntu 24.04 (22.02 для CUDA 12.4)
* **Python**: 3.13
* **Фреймворк**: [ComfyUI](https://github.com/comfyanonymous/ComfyUI) + [ComfyUI Manager](https://github.com/Comfy-Org/ComfyUI-Manager) + [JupyterLab](https://jupyter.org/)
* **Библиотеки**: PyTorch 2.8.0, CUDA (12.4–12.8), Triton, [hf\_hub](https://huggingface.co/docs/huggingface_hub), [nvtop](https://github.com/Syllo/nvtop)

#### Кастомные ноды (в образе **base**)

* ComfyUI-KJNodes
* ComfyUI-WanVideoWrapper
* ComfyUI-GGUF
* ComfyUI-Easy-Use
* ComfyUI-Frame-Interpolation
* ComfyUI-mxToolkit
* ComfyUI-MultiGPU
* ComfyUI_TensorRT
* ComfyUI_UltimateSDUpscale
* comfyui-prompt-reader-node
* ComfyUI_essentials
* ComfyUI-Impact-Pack
* ComfyUI-Impact-Subpack
* efficiency-nodes-comfyui
* ComfyUI-Custom-Scripts
* ComfyUI_JPS-Nodes
* cg-use-everywhere
* ComfyUI-Crystools
* rgthree-comfy
* ComfyUI-Image-Saver
* comfy-ex-tagcomplete
* ComfyUI-VideoHelperSuite
* ComfyUI-wanBlockswap
* ComfyUI-Chibi-Nodes
* comfyui-dream-video-batches
* CRT-Nodes
* ControlAltAI-Nodes
* comfyui_controlnet_aux
* ComfyUI-Florence2

### Wan workflow

При запуске workflow из `/presets/wan` копируются в `/workspace/ComfyUI/user/default/workflows/` для быстрого доступа.

---

## 🌐 Веб-сервисы

### Загрузчик пресетов и моделей (порт 8081)
- Скачивание пресетов Wan по нажатию кнопки
- Скачивание моделей с HuggingFace
- Поддержка API токенов для приватных репозиториев
- Выбор папки назначения для моделей

### CivitAI LoRA Downloader (порт 8082)
- Простой интерфейс для скачивания LoRA с CivitAI
- Введите API токен и URL модели
- Автоматически сохраняет в `/workspace/ComfyUI/models/loras`

### Обзор результатов (порт 8083)  
- Просмотр всех файлов из `/workspace/ComfyUI/output`
- Скачивание отдельных файлов или архива со всеми результатами
- Удобная навигация по папкам
console.log('JavaScript loaded');
let selectedPresets = [];
console.log('selectedPresets initialized:', selectedPresets);

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
  console.log('togglePreset called with:', presetId);
  const card = document.querySelector(`[data-preset="${presetId}"]`);
  console.log('Card found:', card);
  
  if (selectedPresets.includes(presetId)) {
    selectedPresets = selectedPresets.filter(p => p !== presetId);
    card.classList.remove('selected');
    console.log('Removed preset:', presetId);
  } else {
    selectedPresets.push(presetId);
    card.classList.add('selected');
    console.log('Added preset:', presetId);
  }
  
  const btn = document.getElementById('download-presets-btn');
  btn.disabled = selectedPresets.length === 0;
  btn.textContent = selectedPresets.length > 0 ? 
    `📥 Скачать выбранные пресеты (${selectedPresets.length})` : 
    '📥 Скачать выбранные пресеты';
  
  console.log('Selected presets:', selectedPresets);
  
  // Обновляем информацию о Lightning LoRA
  updateLightningLoraInfo();
}

function updateLightningLoraInfo() {
  const lightningText = document.getElementById('lightning-lora-text');
  const lightningDetails = document.getElementById('lightning-lora-details');
  const lightningList = document.getElementById('lightning-lora-list');
  
  if (selectedPresets.length === 0) {
    lightningText.textContent = '⚡ Дополнительно докачать экспериментальные Lightning LoRA';
    lightningDetails.style.display = 'none';
    // Отключаем чекбокс и делаем его полупрозрачным
    document.getElementById('lightning-lora-checkbox').disabled = true;
    document.getElementById('lightning-lora-checkbox').parentElement.style.opacity = '0.5';
    return;
  }
  
  const lightningModels = {
    'WAN_T2V': [
      'T2V-Lightning-250928-high_noise_model.safetensors',
      'T2V-Lightning-250928-low_noise_model.safetensors'
    ],
    'WAN_I2V': [
      'I2V-Lightning-Seko-V1-high_noise_model.safetensors',
      'I2V-Lightning-Seko-V1-low_noise_model.safetensors'
    ],
    'WAN_FLF': [
      'FLF-Lightning-Seko-V1-high_noise_model.safetensors',
      'FLF-Lightning-Seko-V1-low_noise_model.safetensors'
    ]
  };
  
  const selectedLightningModels = [];
  selectedPresets.forEach(preset => {
    if (lightningModels[preset]) {
      selectedLightningModels.push(...lightningModels[preset]);
    }
  });
  
  if (selectedLightningModels.length > 0) {
    const count = selectedLightningModels.length;
    const fileWord = count === 1 ? 'файл' : count < 5 ? 'файла' : 'файлов';
    lightningText.textContent = `⚡ Дополнительно докачать экспериментальные Lightning LoRA (${count} ${fileWord})`;
    
    // Показываем чекбокс и делаем его активным
    document.getElementById('lightning-lora-checkbox').disabled = false;
    document.getElementById('lightning-lora-checkbox').parentElement.style.opacity = '1';
    
    // Показываем список файлов только если галочка поставлена
    const checkbox = document.getElementById('lightning-lora-checkbox');
    if (checkbox.checked) {
      lightningDetails.style.display = 'block';
      lightningList.innerHTML = selectedLightningModels.map(model => 
        `• ${model}`
      ).join('<br>');
    } else {
      lightningDetails.style.display = 'none';
    }
  } else {
    lightningText.textContent = '⚡ Экспериментальные Lightning LoRA недоступны для выбранных пресетов';
    lightningDetails.style.display = 'none';
    // Отключаем чекбокс и делаем его полупрозрачным
    document.getElementById('lightning-lora-checkbox').disabled = true;
    document.getElementById('lightning-lora-checkbox').parentElement.style.opacity = '0.5';
  }
}

function downloadPresets() {
  if (selectedPresets.length === 0) return;
  
  const progress = document.getElementById('preset-progress');
  const result = document.getElementById('preset-result');
  const btn = document.getElementById('download-presets-btn');
  const lightningCheckbox = document.getElementById('lightning-lora-checkbox');
  
  // Показываем прогресс
  progress.style.display = 'block';
  result.textContent = '';
  btn.disabled = true;
  btn.textContent = 'Загрузка...';
  
  // Отправляем запрос
  const formData = new FormData();
  formData.append('presets', selectedPresets.join(','));
  formData.append('lightning_lora', lightningCheckbox.checked ? 'true' : 'false');
  
  fetch('/download_presets', {
    method: 'POST',
    body: formData
  })
  .then(response => response.json())
  .then(data => {
    if (data.task_id) {
      const lightningStatus = lightningCheckbox.checked ? ' (включая Lightning LoRA)' : '';
      result.textContent = data.message + lightningStatus;
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
      let message = data.message;
      const lightningCheckbox = document.getElementById('lightning-lora-checkbox');
      if (lightningCheckbox && lightningCheckbox.checked && data.status === 'completed') {
        message += '\n⚡ Lightning LoRA также скачаны (экспериментальные версии)';
      }
      result.textContent = message;
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

// Остальные функции для HuggingFace...

// Инициализация
document.addEventListener('DOMContentLoaded', function() {
  // Инициализируем состояние Lightning LoRA при загрузке страницы
  updateLightningLoraInfo();
});

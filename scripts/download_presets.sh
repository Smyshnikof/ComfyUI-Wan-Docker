#!/bin/bash

WGET_OPTS="--show-progress"

if [[ "$1" == "--quiet" ]]; then
    WGET_OPTS="-q"
    shift
fi

# download_if_missing <URL> <TARGET_DIR> [CUSTOM_FILENAME] [CURRENT_NUM] [TOTAL_NUM]
download_if_missing() {
    local url="$1"
    local dest_dir="$2"
    local custom_filename="$3"
    local current_num="${4:-0}"
    local total_num="${5:-0}"

    local filename
    if [ -n "$custom_filename" ]; then
        filename="$custom_filename"
    else
        filename=$(basename "$url")
    fi
    local filepath="$dest_dir/$filename"

    mkdir -p "$dest_dir"

    if [ -f "$filepath" ]; then
        echo "PROGRESS:$current_num:$total_num:SKIP:$filename"
        echo "SUMMARY:SKIP:$filename"
        return 0
    fi

    echo "PROGRESS:$current_num:$total_num:DOWNLOADING:1:$filename"
    
    local tmpdir="/workspace/tmp"
    mkdir -p "$tmpdir"
    local tmpfile="$tmpdir/${filename}.part"
    local wget_log="$tmpdir/wget_${current_num}.log"
    local progress_pid_file="$tmpdir/progress_${current_num}.pid"

    # Запускаем парсер прогресса в фоне
    local last_percent_file="$tmpdir/last_percent_${current_num}.txt"
    (
        local last_reported=0
        while [ -f "$progress_pid_file" ]; do
            if [ -f "$wget_log" ]; then
                # Читаем последнюю строку с процентом из лога
                local last_line=$(tail -1 "$wget_log" 2>/dev/null)
                if [[ "$last_line" =~ ([0-9]+)% ]]; then
                    local percent="${BASH_REMATCH[1]}"
                    # Выводим только если процент изменился (чтобы не дублировать сообщения)
                    if [ "$percent" -ne "$last_reported" ]; then
                        echo "PROGRESS:$current_num:$total_num:DOWNLOADING:$percent:$filename"
                        last_reported="$percent"
                    fi
                fi
            fi
            sleep 0.5
        done
    ) &
    local progress_pid=$!
    echo $progress_pid > "$progress_pid_file"

    # Скачиваем файл
    wget --progress=bar:force:noscroll -O "$tmpfile" "$url" > "$wget_log" 2>&1
    local wget_exit=$?
    
    # Читаем последний процент из лога перед остановкой парсера
    if [ -f "$wget_log" ]; then
        local last_line=$(tail -1 "$wget_log" 2>/dev/null)
        if [[ "$last_line" =~ ([0-9]+)% ]]; then
            local final_percent="${BASH_REMATCH[1]}"
            echo "PROGRESS:$current_num:$total_num:DOWNLOADING:$final_percent:$filename"
        fi
    fi
    
    # Останавливаем парсер прогресса
    rm -f "$progress_pid_file" "$wget_log" "$last_percent_file"
    kill $progress_pid 2>/dev/null || true
    wait $progress_pid 2>/dev/null || true
    
    if [ $wget_exit -eq 0 ] && [ -f "$tmpfile" ] && [ -s "$tmpfile" ]; then
        mv -f "$tmpfile" "$filepath"
        echo "PROGRESS:$current_num:$total_num:COMPLETED:100:$filename"
        echo "SUMMARY:DOWNLOADED:$filename"
        return 0
    else
        echo "PROGRESS:$current_num:$total_num:FAILED:0:$filename"
        echo "SUMMARY:FAILED:$filename"
        rm -f "$tmpfile"
        return 1
    fi
}

IFS=',' read -ra PRESETS <<< "$1"
LIGHTNING_LORA="${2:-false}"

# Глобальные переменные для отслеживания прогресса
TOTAL_FILES=0
CURRENT_FILE=0

# Функция-обертка для автоматического подсчета файлов
download_with_progress() {
    CURRENT_FILE=$((CURRENT_FILE + 1))
    download_if_missing "$1" "$2" "$3" "$CURRENT_FILE" "$TOTAL_FILES"
}

echo "**** Проверка пресетов и скачивание соответствующих файлов ****"
if [[ "$LIGHTNING_LORA" == "true" ]]; then
    echo "**** Lightning LoRA включен - будут скачаны экспериментальные быстрые LoRA модели ****"
fi

# Подсчитываем общее количество файлов
for preset in "${PRESETS[@]}"; do
    case "${preset}" in
        WAN_T2V)
            TOTAL_FILES=$((TOTAL_FILES + 6))
            if [[ "$LIGHTNING_LORA" == "true" ]]; then
                TOTAL_FILES=$((TOTAL_FILES + 2))
            fi
            ;;
        WAN_T2I)
            TOTAL_FILES=$((TOTAL_FILES + 8))
            ;;
        WAN_I2V)
            TOTAL_FILES=$((TOTAL_FILES + 6))
            if [[ "$LIGHTNING_LORA" == "true" ]]; then
                TOTAL_FILES=$((TOTAL_FILES + 2))
            fi
            ;;
        WAN_I2V_LOOP)
            TOTAL_FILES=$((TOTAL_FILES + 6))
            if [[ "$LIGHTNING_LORA" == "true" ]]; then
                TOTAL_FILES=$((TOTAL_FILES + 2))
            fi
            ;;
        WAN_ANIMATE)
            TOTAL_FILES=$((TOTAL_FILES + 7))
            ;;
        WAN_FLF)
            TOTAL_FILES=$((TOTAL_FILES + 6))
            if [[ "$LIGHTNING_LORA" == "true" ]]; then
                TOTAL_FILES=$((TOTAL_FILES + 2))
            fi
            ;;
        WAN_LIGHTX2V)
            TOTAL_FILES=$((TOTAL_FILES + 8))
            ;;
        WAN_I2I_REFINER)
            TOTAL_FILES=$((TOTAL_FILES + 8))
            ;;
    esac
done

echo "TOTAL_FILES:$TOTAL_FILES"
CURRENT_FILE=0

for preset in "${PRESETS[@]}"; do
    case "${preset}" in
        WAN_T2V)
            echo "Preset: WAN_T2V (Wan T2V)"
            download_with_progress "https://huggingface.co/Kijai/WanVideo_comfy_fp8_scaled/resolve/main/T2V/Wan2_2-T2V-A14B-LOW_fp8_e4m3fn_scaled_KJ.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_with_progress "https://huggingface.co/Kijai/WanVideo_comfy_fp8_scaled/resolve/main/T2V/Wan2_2-T2V-A14B_HIGH_fp8_e4m3fn_scaled_KJ.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_with_progress "https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/umt5-xxl-enc-bf16.safetensors" "/workspace/ComfyUI/models/text_encoders"
            download_with_progress "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors" "/workspace/ComfyUI/models/vae"
            download_with_progress "https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/LoRAs/Wan22-Lightning/old/Wan2.2-Lightning_T2V-v1.1-A14B-4steps-lora_HIGH_fp16.safetensors" "/workspace/ComfyUI/models/loras"
            download_with_progress "https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/LoRAs/Wan22-Lightning/old/Wan2.2-Lightning_T2V-v1.1-A14B-4steps-lora_LOW_fp16.safetensors" "/workspace/ComfyUI/models/loras"
            
            # Lightning LoRA (experimental fast versions)
            if [[ "$LIGHTNING_LORA" == "true" ]]; then
                echo "Скачивание Lightning LoRA для T2V..."
                download_with_progress "https://huggingface.co/lightx2v/Wan2.2-Lightning/resolve/main/Wan2.2-T2V-A14B-4steps-lora-250928/high_noise_model.safetensors" "/workspace/ComfyUI/models/loras" "T2V-Lightning-250928-high_noise_model.safetensors"
                download_with_progress "https://huggingface.co/lightx2v/Wan2.2-Lightning/resolve/main/Wan2.2-T2V-A14B-4steps-lora-250928/low_noise_model.safetensors" "/workspace/ComfyUI/models/loras" "T2V-Lightning-250928-low_noise_model.safetensors"
            fi
            ;;
        WAN_T2I)
            echo "Preset: WAN_T2I (Wan T2I)"
            download_with_progress "https://huggingface.co/Kijai/WanVideo_comfy_fp8_scaled/resolve/main/T2V/Wan2_2-T2V-A14B-LOW_fp8_e4m3fn_scaled_KJ.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_with_progress "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" "/workspace/ComfyUI/models/text_encoders"
            download_with_progress "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors" "/workspace/ComfyUI/models/vae"
            download_with_progress "https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/LoRAs/Wan22-Lightning/old/Wan2.2-Lightning_T2V-v1.1-A14B-4steps-lora_HIGH_fp16.safetensors" "/workspace/ComfyUI/models/loras"
            download_with_progress "https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/LoRAs/Wan22-Lightning/old/Wan2.2-Lightning_T2V-v1.1-A14B-4steps-lora_LOW_fp16.safetensors" "/workspace/ComfyUI/models/loras"
            download_with_progress "https://huggingface.co/uwg/upscaler/resolve/main/ESRGAN/4x-UltraSharp.pth" "/workspace/ComfyUI/models/upscale_models"
            download_with_progress "https://huggingface.co/uwg/upscaler/resolve/main/ESRGAN/4x_NMKD-Siax_200k.pth" "/workspace/ComfyUI/models/upscale_models"
            download_with_progress "https://huggingface.co/uwg/upscaler/resolve/main/ESRGAN/4x_RealisticRescaler_100000_G.pth" "/workspace/ComfyUI/models/upscale_models"
            download_with_progress "https://huggingface.co/uwg/upscaler/resolve/main/ESRGAN/4x_fatal_Anime_500000_G.pth" "/workspace/ComfyUI/models/upscale_models"
            download_with_progress "https://huggingface.co/uwg/upscaler/resolve/main/ESRGAN/BSRGAN.pth" "/workspace/ComfyUI/models/upscale_models"
            ;;
        WAN_I2V)
            echo "Preset: WAN_I2V (Wan I2V)"
            download_with_progress "https://huggingface.co/Kijai/WanVideo_comfy_fp8_scaled/resolve/main/I2V/Wan2_2-I2V-A14B-HIGH_fp8_e4m3fn_scaled_KJ.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_with_progress "https://huggingface.co/Kijai/WanVideo_comfy_fp8_scaled/resolve/main/I2V/Wan2_2-I2V-A14B-LOW_fp8_e4m3fn_scaled_KJ.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_with_progress "https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/umt5-xxl-enc-bf16.safetensors" "/workspace/ComfyUI/models/text_encoders"
            download_with_progress "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors" "/workspace/ComfyUI/models/vae"
            download_with_progress "https://huggingface.co/jrewingwannabe/Wan2.2-Lightning_I2V-A14B-4steps-lora/resolve/main/Wan2.2-Lightning_I2V-A14B-4steps-lora_HIGH_fp16.safetensors" "/workspace/ComfyUI/models/loras"
            download_with_progress "https://huggingface.co/jrewingwannabe/Wan2.2-Lightning_I2V-A14B-4steps-lora/resolve/main/Wan2.2-Lightning_I2V-A14B-4steps-lora_LOW_fp16.safetensors" "/workspace/ComfyUI/models/loras"
            
            # Lightning LoRA (experimental fast versions)
            if [[ "$LIGHTNING_LORA" == "true" ]]; then
                echo "Скачивание Lightning LoRA для I2V..."
                download_with_progress "https://huggingface.co/lightx2v/Wan2.2-Lightning/resolve/main/Wan2.2-I2V-A14B-4steps-lora-rank64-Seko-V1/high_noise_model.safetensors" "/workspace/ComfyUI/models/loras" "I2V-Lightning-Seko-V1-high_noise_model.safetensors"
                download_with_progress "https://huggingface.co/lightx2v/Wan2.2-Lightning/resolve/main/Wan2.2-I2V-A14B-4steps-lora-rank64-Seko-V1/low_noise_model.safetensors" "/workspace/ComfyUI/models/loras" "I2V-Lightning-Seko-V1-low_noise_model.safetensors"
            fi
            ;;
        WAN_I2V_LOOP)
            echo "Preset: WAN_I2V_LOOP (Wan I2V Loop)"
            download_with_progress "https://huggingface.co/Kijai/WanVideo_comfy_fp8_scaled/resolve/main/I2V/Wan2_2-I2V-A14B-HIGH_fp8_e4m3fn_scaled_KJ.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_with_progress "https://huggingface.co/Kijai/WanVideo_comfy_fp8_scaled/resolve/main/I2V/Wan2_2-I2V-A14B-LOW_fp8_e4m3fn_scaled_KJ.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_with_progress "https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/umt5-xxl-enc-bf16.safetensors" "/workspace/ComfyUI/models/text_encoders"
            download_with_progress "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors" "/workspace/ComfyUI/models/vae"
            download_with_progress "https://huggingface.co/jrewingwannabe/Wan2.2-Lightning_I2V-A14B-4steps-lora/resolve/main/Wan2.2-Lightning_I2V-A14B-4steps-lora_HIGH_fp16.safetensors" "/workspace/ComfyUI/models/loras"
            download_with_progress "https://huggingface.co/jrewingwannabe/Wan2.2-Lightning_I2V-A14B-4steps-lora/resolve/main/Wan2.2-Lightning_I2V-A14B-4steps-lora_LOW_fp16.safetensors" "/workspace/ComfyUI/models/loras"
            
            # Lightning LoRA (experimental fast versions)
            if [[ "$LIGHTNING_LORA" == "true" ]]; then
                echo "Скачивание Lightning LoRA для I2V Loop..."
                download_with_progress "https://huggingface.co/lightx2v/Wan2.2-Lightning/resolve/main/Wan2.2-I2V-A14B-4steps-lora-rank64-Seko-V1/high_noise_model.safetensors" "/workspace/ComfyUI/models/loras" "I2V-Lightning-Seko-V1-high_noise_model.safetensors"
                download_with_progress "https://huggingface.co/lightx2v/Wan2.2-Lightning/resolve/main/Wan2.2-I2V-A14B-4steps-lora-rank64-Seko-V1/low_noise_model.safetensors" "/workspace/ComfyUI/models/loras" "I2V-Lightning-Seko-V1-low_noise_model.safetensors"
            fi
            ;;
        WAN_ANIMATE)
            echo "Preset: WAN_ANIMATE (Wan Animate)"
            download_with_progress "https://huggingface.co/Kijai/WanVideo_comfy_fp8_scaled/resolve/main/Wan22Animate/Wan2_2-Animate-14B_fp8_e4m3fn_scaled_KJ.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_with_progress "https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/Wan2_1_VAE_bf16.safetensors" "/workspace/ComfyUI/models/vae"
            download_with_progress "https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/Wan2_1_VAE_fp32.safetensors" "/workspace/ComfyUI/models/vae"
            download_with_progress "https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/umt5-xxl-enc-bf16.safetensors" "/workspace/ComfyUI/models/text_encoders"
            download_with_progress "https://huggingface.co/OreX/Models/resolve/main/WAN/clip_vision_h.safetensors" "/workspace/ComfyUI/models/clip_vision"
            download_with_progress "https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/LoRAs/Wan22_relight/WanAnimate_relight_lora_fp16.safetensors" "/workspace/ComfyUI/models/loras"
            download_with_progress "https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/Lightx2v/lightx2v_I2V_14B_480p_cfg_step_distill_rank64_bf16.safetensors" "/workspace/ComfyUI/models/loras"
            ;;
        WAN_FLF)
            echo "Preset: WAN_FLF (Wan First Last Frame)"
            download_with_progress "https://huggingface.co/Kijai/WanVideo_comfy_fp8_scaled/resolve/main/Fun/Wan2_2-Fun-InP-A14B-HIGH_fp8_e4m3fn_scaled_KJ.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_with_progress "https://huggingface.co/Kijai/WanVideo_comfy_fp8_scaled/resolve/main/Fun/Wan2_2-Fun-InP-A14B-LOW_fp8_e4m3fn_scaled_KJ.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_with_progress "https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/umt5-xxl-enc-bf16.safetensors" "/workspace/ComfyUI/models/text_encoders"
            download_with_progress "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors" "/workspace/ComfyUI/models/vae"
            download_with_progress "https://huggingface.co/jrewingwannabe/Wan2.2-Lightning_I2V-A14B-4steps-lora/resolve/main/Wan2.2-Lightning_I2V-A14B-4steps-lora_HIGH_fp16.safetensors" "/workspace/ComfyUI/models/loras"
            download_with_progress "https://huggingface.co/jrewingwannabe/Wan2.2-Lightning_I2V-A14B-4steps-lora/resolve/main/Wan2.2-Lightning_I2V-A14B-4steps-lora_LOW_fp16.safetensors" "/workspace/ComfyUI/models/loras"
            
            # Lightning LoRA (experimental fast versions) - using I2V version for FLF
            if [[ "$LIGHTNING_LORA" == "true" ]]; then
                echo "Скачивание Lightning LoRA для FLF (используется версия I2V)..."
                download_with_progress "https://huggingface.co/lightx2v/Wan2.2-Lightning/resolve/main/Wan2.2-I2V-A14B-4steps-lora-rank64-Seko-V1/high_noise_model.safetensors" "/workspace/ComfyUI/models/loras" "FLF-Lightning-Seko-V1-high_noise_model.safetensors"
                download_with_progress "https://huggingface.co/lightx2v/Wan2.2-Lightning/resolve/main/Wan2.2-I2V-A14B-4steps-lora-rank64-Seko-V1/low_noise_model.safetensors" "/workspace/ComfyUI/models/loras" "FLF-Lightning-Seko-V1-low_noise_model.safetensors"
            fi
            ;;
        WAN_LIGHTX2V)
            echo "Preset: WAN_LIGHTX2V (Wan LightX2V)"
            download_with_progress "https://huggingface.co/lightx2v/Wan2.2-Distill-Models/resolve/main/wan2.2_i2v_A14b_high_noise_lightx2v_4step.safetensors" "/workspace/ComfyUI/models/diffusion_models" "wan2.2_i2v_A14b_high_noise_lightx2v_4step.safetensors"
            download_with_progress "https://huggingface.co/lightx2v/Wan2.2-Distill-Models/resolve/main/wan2.2_i2v_A14b_low_noise_lightx2v_4step.safetensors" "/workspace/ComfyUI/models/diffusion_models" "wan2.2_i2v_A14b_low_noise_lightx2v_4step.safetensors"
            download_with_progress "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp16.safetensors" "/workspace/ComfyUI/models/text_encoders" "umt5_xxl_fp16.safetensors"
            download_with_progress "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors" "/workspace/ComfyUI/models/vae" "wan_2.1_vae.safetensors"
            download_with_progress "https://huggingface.co/rahul7star/wan2.2Lora/resolve/main/Wan2.2-Fun-A14B-InP-high-noise-MPS.safetensors" "/workspace/ComfyUI/models/loras" "Wan2.2-Fun-A14B-InP-high-noise-MPS.safetensors"
            download_with_progress "https://huggingface.co/rahul7star/wan2.2Lora/resolve/main/Wan2.2-Fun-A14B-InP-low-noise-HPS2.1.safetensors" "/workspace/ComfyUI/models/loras" "Wan2.2-Fun-A14B-InP-low-noise-HPS2.1.safetensors"
            download_with_progress "https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/Lightx2v/lightx2v_I2V_14B_480p_cfg_step_distill_rank256_bf16.safetensors" "/workspace/ComfyUI/models/loras" "lightx2v_I2V_14B_480p_cfg_step_distill_rank256_bf16.safetensors"
            download_with_progress "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/clip_vision/clip_vision_h.safetensors" "/workspace/ComfyUI/models/clip_vision" "clip_vision_h.safetensors"
            ;;
        WAN_I2I_REFINER)
            echo "Preset: WAN_I2I_REFINER (Wan I2I Refiner)"
            download_with_progress "https://huggingface.co/Kijai/WanVideo_comfy_fp8_scaled/resolve/main/T2V/Wan2_2-T2V-A14B-LOW_fp8_e4m3fn_scaled_KJ.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_with_progress "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" "/workspace/ComfyUI/models/text_encoders"
            download_with_progress "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors" "/workspace/ComfyUI/models/vae"
            download_with_progress "https://huggingface.co/uwg/upscaler/resolve/main/ESRGAN/4x-UltraSharp.pth" "/workspace/ComfyUI/models/upscale_models"
            download_with_progress "https://huggingface.co/uwg/upscaler/resolve/main/ESRGAN/4x_NMKD-Siax_200k.pth" "/workspace/ComfyUI/models/upscale_models"
            download_with_progress "https://huggingface.co/uwg/upscaler/resolve/main/ESRGAN/4x_RealisticRescaler_100000_G.pth" "/workspace/ComfyUI/models/upscale_models"
            download_with_progress "https://huggingface.co/uwg/upscaler/resolve/main/ESRGAN/4x_fatal_Anime_500000_G.pth" "/workspace/ComfyUI/models/upscale_models"
            download_with_progress "https://huggingface.co/uwg/upscaler/resolve/main/ESRGAN/BSRGAN.pth" "/workspace/ComfyUI/models/upscale_models"
            ;;
        *)
            echo "Не найден пресет WAN для '${preset}', пропускаем."
            ;;
    esac
done

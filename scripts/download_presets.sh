#!/bin/bash

WGET_OPTS="--show-progress"

if [[ "$1" == "--quiet" ]]; then
    WGET_OPTS="-q"
    shift
fi

# download_if_missing <URL> <TARGET_DIR>
download_if_missing() {
    local url="$1"
    local dest_dir="$2"

    local filename
    filename=$(basename "$url")
    local filepath="$dest_dir/$filename"

    mkdir -p "$dest_dir"

    if [ -f "$filepath" ]; then
        echo "File already exists: $filepath (skipping)"
        return
    fi

    echo "Downloading: $filename → $dest_dir"
    
    local tmpdir="/workspace/tmp"
    mkdir -p "$tmpdir"
    local tmpfile="$tmpdir/${filename}.part"

    if wget $WGET_OPTS -O "$tmpfile" "$url"; then
        mv -f "$tmpfile" "$filepath"
        echo "Download completed: $filepath"
    else
        echo "Download failed: $url"
        rm -f "$tmpfile"
        return 1
    fi
}

IFS=',' read -ra PRESETS <<< "$1"

echo "**** Checking presets and downloading corresponding files ****"

for preset in "${PRESETS[@]}"; do
    case "${preset}" in
        WAN_T2V)
            echo "Preset: WAN_T2V (Wan T2V)"
            download_if_missing "https://huggingface.co/Kijai/WanVideo_comfy_fp8_scaled/resolve/main/T2V/Wan2_2-T2V-A14B-LOW_fp8_e4m3fn_scaled_KJ.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/Kijai/WanVideo_comfy_fp8_scaled/resolve/main/T2V/Wan2_2-T2V-A14B_HIGH_fp8_e4m3fn_scaled_KJ.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/umt5-xxl-enc-bf16.safetensors" "/workspace/ComfyUI/models/text_encoders"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors" "/workspace/ComfyUI/models/vae"
            download_if_missing "https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/LoRAs/Wan22-Lightning/old/Wan2.2-Lightning_T2V-v1.1-A14B-4steps-lora_HIGH_fp16.safetensors" "/workspace/ComfyUI/models/loras"
            download_if_missing "https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/LoRAs/Wan22-Lightning/old/Wan2.2-Lightning_T2V-v1.1-A14B-4steps-lora_LOW_fp16.safetensors" "/workspace/ComfyUI/models/loras"
            ;;
        WAN_T2I)
            echo "Preset: WAN_T2I (Wan T2I)"
            download_if_missing "https://huggingface.co/Kijai/WanVideo_comfy_fp8_scaled/resolve/main/T2V/Wan2_2-T2V-A14B-LOW_fp8_e4m3fn_scaled_KJ.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" "/workspace/ComfyUI/models/text_encoders"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors" "/workspace/ComfyUI/models/vae"
            download_if_missing "https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/LoRAs/Wan22-Lightning/old/Wan2.2-Lightning_T2V-v1.1-A14B-4steps-lora_HIGH_fp16.safetensors" "/workspace/ComfyUI/models/loras"
            download_if_missing "https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/LoRAs/Wan22-Lightning/old/Wan2.2-Lightning_T2V-v1.1-A14B-4steps-lora_LOW_fp16.safetensors" "/workspace/ComfyUI/models/loras"
            download_if_missing "https://huggingface.co/uwg/upscaler/resolve/main/ESRGAN/4x-UltraSharp.pth" "/workspace/ComfyUI/models/upscale_models"
            download_if_missing "https://huggingface.co/uwg/upscaler/resolve/main/ESRGAN/4x_NMKD-Siax_200k.pth" "/workspace/ComfyUI/models/upscale_models"
            download_if_missing "https://huggingface.co/uwg/upscaler/resolve/main/ESRGAN/4x_RealisticRescaler_100000_G.pth" "/workspace/ComfyUI/models/upscale_models"
            download_if_missing "https://huggingface.co/uwg/upscaler/resolve/main/ESRGAN/4x_fatal_Anime_500000_G.pth" "/workspace/ComfyUI/models/upscale_models"
            download_if_missing "https://huggingface.co/uwg/upscaler/resolve/main/ESRGAN/BSRGAN.pth" "/workspace/ComfyUI/models/upscale_models"
            ;;
        WAN_I2V)
            echo "Preset: WAN_I2V (Wan I2V)"
            download_if_missing "https://huggingface.co/Kijai/WanVideo_comfy_fp8_scaled/resolve/main/I2V/Wan2_2-I2V-A14B-HIGH_fp8_e4m3fn_scaled_KJ.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/Kijai/WanVideo_comfy_fp8_scaled/resolve/main/I2V/Wan2_2-I2V-A14B-LOW_fp8_e4m3fn_scaled_KJ.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/umt5-xxl-enc-bf16.safetensors" "/workspace/ComfyUI/models/text_encoders"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors" "/workspace/ComfyUI/models/vae"
            download_if_missing "https://huggingface.co/jrewingwannabe/Wan2.2-Lightning_I2V-A14B-4steps-lora/resolve/main/Wan2.2-Lightning_I2V-A14B-4steps-lora_HIGH_fp16.safetensors" "/workspace/ComfyUI/models/loras"
            download_if_missing "https://huggingface.co/jrewingwannabe/Wan2.2-Lightning_I2V-A14B-4steps-lora/resolve/main/Wan2.2-Lightning_I2V-A14B-4steps-lora_LOW_fp16.safetensors" "/workspace/ComfyUI/models/loras"
            ;;
        WAN_ANIMATE)
            echo "Preset: WAN_ANIMATE (Wan Animate)"
            download_if_missing "https://huggingface.co/Kijai/WanVideo_comfy_fp8_scaled/resolve/main/Wan22Animate/Wan2_2-Animate-14B_fp8_e4m3fn_scaled_KJ.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/Wan2_1_VAE_bf16.safetensors" "/workspace/ComfyUI/models/vae"
            download_if_missing "https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/umt5-xxl-enc-bf16.safetensors" "/workspace/ComfyUI/models/text_encoders"
            download_if_missing "https://huggingface.co/OreX/Models/resolve/main/WAN/clip_vision_h.safetensors" "/workspace/ComfyUI/models/clip_vision"
            download_if_missing "https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/LoRAs/Wan22_relight/WanAnimate_relight_lora_fp16.safetensors" "/workspace/ComfyUI/models/loras"
            download_if_missing "https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/Lightx2v/lightx2v_I2V_14B_480p_cfg_step_distill_rank64_bf16.safetensors" "/workspace/ComfyUI/models/loras"
            ;;
        *)
            echo "No matching WAN preset for '${preset}', skipping."
            ;;
    esac
done

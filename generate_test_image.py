import json
import sys
import os
import re
import time
import base64
import httpx
from datetime import datetime

if sys.stdout:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr:
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

API_KEY = os.environ.get("LMAB_API_KEY", "sk-lmab-your-api-key-here")
BASE_URL = os.environ.get("LMAB_BASE_URL", "http://localhost:8000/api/v1")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "generated_images")

# Görsel üretim modelleri
image_models_to_try = [
    "gpt-image-2 (medium)"
]

prompt = "A cute anime girl with bikini, sitting on the beach, with a sunset in the background, highly detailed, 4k, cinematic lighting, by artgerm and greg rutkowski"

def save_image_from_content(content: str, model_name: str):
    """Modelden dönen metin içerisindeki görsel URL'lerini veya base64 verilerini tespit edip kaydeder."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    clean_model = re.sub(r'[^a-zA-Z0-9_-]', '_', model_name)
    
    saved_files = []

    # 1. Markdown resim linkleri: ![alt](url)
    markdown_urls = re.findall(r'!\[.*?\]\((https?://[^\s\)]+)\)', content)
    # 2. Düz resim URL'leri: https://... (.png, .jpg, .webp, r2/supabase storage vb.)
    direct_urls = re.findall(r'(https?://[^\s<>"\'\)]+\.(?:png|jpg|jpeg|webp|gif)(?:\?[^\s<>"\'\)]*)?)', content, re.IGNORECASE)
    # 3. LMArena CDN / R2 / Supabase Storage URL'leri
    storage_urls = re.findall(r'(https?://[^\s<>"\'\)]*(?:r2\.cloudflarestorage|supabase|arena\.ai|lmarena\.ai)[^\s<>"\'\)]*)', content, re.IGNORECASE)

    all_urls = list(dict.fromkeys(markdown_urls + direct_urls + storage_urls))

    # URL'leri indir ve kaydet
    for idx, url in enumerate(all_urls, 1):
        try:
            print(f"📥 Görsel indiriliyor: {url[:80]}...")
            resp = httpx.get(url, timeout=60.0, follow_redirects=True)
            if resp.status_code == 200 and len(resp.content) > 500:
                file_ext = "png"
                content_type = resp.headers.get("content-type", "")
                if "jpeg" in content_type or "jpg" in content_type:
                    file_ext = "jpg"
                elif "webp" in content_type:
                    file_ext = "webp"
                
                filename = f"{clean_model}_{timestamp}_{idx}.{file_ext}"
                filepath = os.path.join(OUTPUT_DIR, filename)
                with open(filepath, "wb") as f:
                    f.write(resp.content)
                saved_files.append(filepath)
                print(f"🎉 GÖRSEL KAYDEDİLDİ: {filepath} ({len(resp.content)} bayt)")
        except Exception as e:
            print(f"⚠️ Görsel indirme hatası ({url[:40]}): {e}")

    # 4. Base64 formatında dönen görseller: data:image/...;base64,...
    base64_matches = re.findall(r'data:image/(png|jpeg|jpg|webp);base64,([A-Za-z0-9+/=]+)', content)
    for idx, (ext, b64_str) in enumerate(base64_matches, 1):
        try:
            img_data = base64.b64decode(b64_str)
            filename = f"{clean_model}_{timestamp}_b64_{idx}.{ext}"
            filepath = os.path.join(OUTPUT_DIR, filename)
            with open(filepath, "wb") as f:
                f.write(img_data)
            saved_files.append(filepath)
            print(f"🎉 BASE64 GÖRSELİ KAYDEDİLDİ: {filepath} ({len(img_data)} bayt)")
        except Exception as e:
            print(f"⚠️ Base64 decode hatası: {e}")

    return saved_files

def generate():
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    for model in image_models_to_try:
        print("\n" + "=" * 65)
        print(f"🎨 Deneniyor: Model = '{model}'")
        print(f"📝 Prompt = '{prompt}'")
        print("=" * 65)

        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "stream": True
        }

        try:
            with httpx.Client(timeout=120.0) as client:
                with client.stream("POST", f"{BASE_URL}/chat/completions", headers=headers, json=payload) as resp:
                    print(f"HTTP Yanıt Kodu: {resp.status_code}")
                    full_content = ""
                    for line in resp.iter_lines():
                        if not line:
                            continue
                        if line.startswith("data: ") and line.strip() != "data: [DONE]":
                            try:
                                chunk = json.loads(line[6:])
                                delta = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                                if delta:
                                    print(delta, end="", flush=True)
                                    full_content += delta
                            except Exception:
                                pass
                    print()
                    if full_content:
                        print(f"\n✅ Model Yanıtı:\n{full_content}\n")
                        saved = save_image_from_content(full_content, model)
                        if saved:
                            print(f"\n📂 Toplam {len(saved)} görsel '{OUTPUT_DIR}' klasörüne kaydedildi!")
                        return
                    else:
                        print(f"⚠️ Model '{model}' boş akış döndürdü veya token yetkisi gerekti.")
        except Exception as e:
            print(f"❌ İstek hatası ({model}): {e}")

if __name__ == "__main__":
    generate()

import json
import sys
import os
import re
import base64
import time
import httpx
from datetime import datetime

if sys.stdout:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr:
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

API_KEY = os.environ.get("LMAB_API_KEY", "sk-lmab-your-api-key-here")
BASE_URL = os.environ.get("LMAB_BASE_URL", "http://localhost:8000/api/v1")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "generated_images")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def test_model(model_name: str, prompt: str):
    print("\n" + "=" * 65)
    print(f"🚀 MODEL DENENİYOR: {model_name}")
    print(f"📝 PROMPT: {prompt}")
    print("=" * 65)

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}],
        "stream": True
    }

    full_text = ""
    start_time = time.time()
    
    try:
        with httpx.Client(timeout=90.0) as client:
            print("📡 Sunucuya bağlanılıyor...", flush=True)
            with client.stream("POST", f"{BASE_URL}/chat/completions", headers=headers, json=payload) as resp:
                print(f"⚡ Bağlantı Kuruldu! HTTP {resp.status_code}", flush=True)
                
                if resp.status_code != 200:
                    print(f"❌ Hata Kodu: {resp.status_code} - {resp.read().decode('utf-8', errors='ignore')}")
                    return False
                
                chunk_count = 0
                for line in resp.iter_lines():
                    if not line:
                        continue
                    
                    # Keep-alive heartbeat
                    if line.startswith(": keep-alive") or line.startswith(":"):
                        sys.stdout.write("⏳ ")
                        sys.stdout.flush()
                        continue
                    
                    if line.startswith("data: "):
                        data_str = line[6:].strip()
                        if data_str == "[DONE]":
                            print("\n🏁 [DONE] Akış tamamlandı.", flush=True)
                            break
                        try:
                            data_json = json.loads(data_str)
                            delta = data_json.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            if delta:
                                sys.stdout.write(delta)
                                sys.stdout.flush()
                                full_text += delta
                                chunk_count += 1
                        except Exception:
                            pass
        
        elapsed = round(time.time() - start_time, 2)
        print(f"\n⏱️ Toplam Süre: {elapsed} saniye | Alınan Veri: {len(full_text)} karakter")
        
        if full_text:
            print("\n" + "-" * 40)
            print(f"📄 Model Yanıtı:\n{full_text}")
            print("-" * 40)
            
            # Görsel linklerini bul ve kaydet
            img_urls = re.findall(r'(https?://[^\s<>"\'\)]+\.(?:png|jpg|jpeg|webp))', full_text, re.IGNORECASE)
            r2_urls = re.findall(r'(https?://[^\s<>"\'\)]*(?:r2\.cloudflarestorage|arena\.ai|supabase)[^\s<>"\'\)]*)', full_text, re.IGNORECASE)
            all_urls = list(dict.fromkeys(img_urls + r2_urls))
            
            for idx, u in enumerate(all_urls, 1):
                try:
                    print(f"📥 Görsel indiriliyor: {u[:70]}...")
                    r = httpx.get(u, timeout=30.0)
                    if r.status_code == 200:
                        save_path = os.path.join(OUTPUT_DIR, f"{model_name}_{int(time.time())}_{idx}.png")
                        with open(save_path, "wb") as f:
                            f.write(r.content)
                        print(f"🎉 GÖRSEL KAYDEDİLDİ: {save_path} ({len(r.content)} bayt)")
                except Exception as e:
                    print(f"⚠️ İndirme hatası: {e}")
            return True
        else:
            print("⚠️ Model boş yanıt döndürdü.")
            return False

    except Exception as e:
        print(f"\n❌ Bağlantı/Zaman Aşımı Hatası: {e}")
        return False

if __name__ == "__main__":
    test_models = [
        "grok-imagine-image",
        "gpt-image-2 (medium)",
        "wan2.6-image",
        "flux-2-pro"
    ]
    prompt = "A cute neon cyberpunk red panda, 8k digital art"
    
    for m in test_models:
        success = test_model(m, prompt)
        if success:
            break


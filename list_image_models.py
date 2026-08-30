import json
import os
import sys

if sys.stdout:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

models_file = r"C:\Users\YİĞİT\Desktop\LMArenaBridge\models.json"
with open(models_file, "r", encoding="utf-8") as f:
    models = json.load(f)

print(f"Total Models in LMArena: {len(models)}")

image_generation_models = []
vision_input_models = []

for m in models:
    name = m.get("publicName") or m.get("displayName") or m.get("name")
    m_id = m.get("id")
    org = m.get("organization")
    caps = m.get("capabilities") or {}
    
    input_caps = caps.get("inputCapabilities") or {}
    output_caps = caps.get("outputCapabilities") or {}
    
    has_image_input = bool(input_caps.get("image"))
    has_image_output = bool(output_caps.get("image"))
    
    if has_image_output:
        image_generation_models.append((name, m_id, org, output_caps.get("image")))
    if has_image_input:
        vision_input_models.append((name, m_id, org, input_caps.get("image")))

print("\n" + "="*70)
print(f"🎨 IMAGE GENERATION / TEXT-TO-IMAGE MODELS ({len(image_generation_models)} models):")
print("="*70)
for name, m_id, org, img_cap in image_generation_models:
    print(f"  • {name} (Org: {org}, ID: {m_id}) -> Output: {img_cap}")

print("\n" + "="*70)
print(f"👁️ VISION / MULTIMODAL IMAGE-INPUT MODELS ({len(vision_input_models)} models):")
print("="*70)
for name, m_id, org, img_cap in vision_input_models[:30]:
    print(f"  • {name} (Org: {org}, ID: {m_id}) -> Input: {img_cap}")
if len(vision_input_models) > 30:
    print(f"  ... and {len(vision_input_models) - 30} more vision models.")


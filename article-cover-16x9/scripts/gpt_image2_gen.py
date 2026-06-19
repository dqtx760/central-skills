"""
GPT-Image-2 via Apimart API: Submit -> Poll -> Download
Usage: python gpt_image2_gen.py <prompt_text> <output_path> [size] [resolution]

Requires env var: APIMART_API_KEY (get yours at https://apimart.ai/keys)
"""
import sys
import json
import time
import requests
import os
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API_URL = "https://api.apimart.ai/v1/images/generations"
TASK_URL = "https://api.apimart.ai/v1/tasks/{task_id}"
API_KEY = os.environ.get("APIMART_API_KEY")

if not API_KEY:
    print("ERROR: APIMART_API_KEY environment variable not set.")
    print("Get your API key at https://apimart.ai/keys")
    print("Then set it: set APIMART_API_KEY=sk-xxx  (Windows) or export APIMART_API_KEY=sk-xxx (macOS/Linux)")
    sys.exit(1)

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def generate_image(prompt, output_path, size="16:9", resolution="1k"):
    # Step 1: Submit generation task
    print(f"  [1/3] Submitting... (model=gpt-image-2, size={size}, resolution={resolution})")
    resp = requests.post(API_URL, headers=HEADERS, json={
        "model": "gpt-image-2",
        "prompt": prompt,
        "n": 1,
        "size": size,
        "resolution": resolution
    }, verify=False)
    
    if resp.status_code != 200:
        print(f"  ERROR: Submit failed ({resp.status_code}): {resp.text}")
        return False
    
    data = resp.json()
    task_id = data["data"][0]["task_id"]
    print(f"  [1/3] Submitted! task_id={task_id}")

    # Step 2: Poll for completion
    print(f"  [2/3] Polling...", end="", flush=True)
    max_attempts = 60  # 60 * 5s = 5 min max
    for i in range(max_attempts):
        time.sleep(5)
        t_resp = requests.get(TASK_URL.format(task_id=task_id), headers={
            "Authorization": f"Bearer {API_KEY}"
        }, verify=False)
        if t_resp.status_code != 200:
            print(f" [poll-err {t_resp.status_code}]", end="", flush=True)
            continue
        try:
            t_data = t_resp.json()["data"]
        except (KeyError, TypeError) as e:
            print(f" [parse-err: {t_resp.text[:80]}]", end="", flush=True)
            continue
        status = t_data["status"]
        progress = t_data.get("progress", 0)
        print(f" {progress}%", end="", flush=True)
        
        if status == "completed":
            print(" DONE!")
            break
        elif status == "failed":
            print(f" FAILED!")
            print(f"  ERROR: Task failed: {json.dumps(t_data, ensure_ascii=False)}")
            return False
    else:
        print(" TIMEOUT!")
        return False

    # Step 3: Download image
    print(f"  [3/3] Downloading...")
    images = t_data.get("result", {}).get("images", [])
    if not images or not images[0].get("url"):
        print("  ERROR: No image URL in response")
        return False

    img_url = images[0]["url"][0] if isinstance(images[0]["url"], list) else images[0]["url"]
    img_resp = requests.get(img_url, verify=False)
    if img_resp.status_code != 200:
        print(f"  ERROR: Download failed ({img_resp.status_code})")
        return False

    # Ensure output directory exists
    out_dir = os.path.dirname(output_path)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir)

    with open(output_path, "wb") as f:
        f.write(img_resp.content)
    
    file_size = len(img_resp.content) / 1024 / 1024
    print(f"  [3/3] Saved to {output_path} ({file_size:.1f} MB)")
    return True


def main():
    if len(sys.argv) < 3:
        print("Usage: python gpt_image2_gen.py <prompt> <output_file> [size] [resolution]")
        sys.exit(1)
    
    prompt = sys.argv[1]
    output_path = sys.argv[2]
    size = sys.argv[3] if len(sys.argv) > 3 else "16:9"
    resolution = sys.argv[4] if len(sys.argv) > 4 else "1k"
    
    success = generate_image(prompt, output_path, size, resolution)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

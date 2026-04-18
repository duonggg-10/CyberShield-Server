# api/utils.py
import json
import requests
import os
import time

# Cache đơn giản để giảm số lượng request đến GitHub
_config_cache = {
    "data": None,
    "last_updated": 0
}
CACHE_TTL = 300  # 5 phút

def get_dynamic_config():
    """Lấy cấu hình động từ URL GitHub hoặc fallback nếu có lỗi."""
    global _config_cache

    current_time = time.time()
    if _config_cache["data"] and (current_time - _config_cache["last_updated"] < CACHE_TTL):
        return _config_cache["data"]

    remote_url = os.environ.get('REMOTE_CONFIG_URL', 'https://raw.githubusercontent.com/duonggg-10/CyberShield-Server-config/main/config.json')

    try:
        response = requests.get(remote_url, timeout=10)
        if response.status_code == 200:
            config_data = response.json()
            _config_cache["data"] = config_data
            _config_cache["last_updated"] = current_time
            return config_data
    except Exception as e:
        print(f"🔴 [CONFIG] Lỗi khi lấy cấu hình từ {remote_url}: {e}")

    # Fallback nếu không lấy được từ GitHub, thử đọc file cục bộ
    try:
        if os.path.exists('config.json'):
            with open('config.json', 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass

    # Cuối cùng là fallback mặc định
    return {
        "analysis_provider": "AUTO",
        "enable_email_alerts": True,
        "pre_filter_model_id": "openai/gpt-3.5-turbo"
    }

def print_masked_api_keys(key_list: list, key_name: str):

    """
    In danh sách các API keys đã được che một phần để bảo mật và định dạng đẹp hơn.
    """
    if not key_list:
        print(f"🟡 [CONFIG] Không có {key_name} nào được thiết lập.")
        return

    masked_keys = [f"...{key[-4:]}" for key in key_list]
    print(f"🟢 [CONFIG] {key_name} đã tải ({len(key_list)} key): {', '.join(masked_keys)}")
import requests
import os
from dotenv import load_dotenv

load_dotenv()

# Lấy Jina API Key
JINA_API_KEY = os.getenv("JINA_API_KEY")
if not JINA_API_KEY:
    raise ValueError("❌ Không tìm thấy Jina API Key trong biến môi trường!")

# Endpoint mới theo docs chính thức của Jina AI
JINA_API_URL = "https://api.jina.ai/v1/embeddings"
JINA_MODEL_NAME = "jina-embeddings-v3"
JINA_TASK = "text-matching"  # Tùy task bạn cần, docs có giải thích rõ
JINA_DIMENSIONS = 384  # Dùng bản base, docs nói rõ dimension này

def get_embedding(text: str):
    """
    Gọi API Jina AI để lấy embedding cho văn bản.
    """
    if not text or not isinstance(text, str):
        raise ValueError("❌ Đầu vào phải là một chuỗi văn bản hợp lệ.")

    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {JINA_API_KEY}",
        }

        payload = {
            "model": JINA_MODEL_NAME,
            "task": JINA_TASK,
            "dimensions": JINA_DIMENSIONS,
            "input": [text]  # Bọc vào list
        }

        response = requests.post(JINA_API_URL, headers=headers, json=payload)
        response.raise_for_status()

        result = response.json()
        if "data" not in result or not result["data"]:
            raise ValueError("⚠️ Phản hồi từ API không chứa trường 'data' hợp lệ.")

        return result["data"][0]["embedding"]

    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"🚫 Lỗi gọi API Jina AI: {str(e)}")
    except ValueError as e:
        raise RuntimeError(f"🚫 Phản hồi lỗi từ Jina AI: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"🚫 Lỗi không xác định: {str(e)}")

# Test CLI nhỏ gọn
if __name__ == "__main__":
    while True:
        user_input = input("\n💬 Nhập văn bản (hoặc 'exit'): ")
        if user_input.lower() == 'exit':
            break
        try:
            vector = get_embedding(user_input)
            print(f"✅ Vector embedding có {len(vector)} chiều.")
            print("▶️ 5 phần tử đầu:", vector[:5], "...")
        except Exception as err:
            print(f"[❌ ERROR]: {err}")

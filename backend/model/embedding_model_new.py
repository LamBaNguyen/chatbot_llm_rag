from huggingface_hub import InferenceClient
import numpy as np
# from sklearn.metrics.pairwise import cosine_similarity
import os

# Lưu token Hugging Face của bạn
token = os.getenv("YOUR_HF_API_TOKEN")
if not token:
    raise ValueError("Không tìm thấy Hugging Face API token. Bạn cần set biến môi trường 'YOUR_HF_API_TOKEN' hoặc gán trực tiếp.")

# Khởi tạo InferenceClient
client = InferenceClient(token=token)

# Hàm get_embedding (dùng InferenceClient để gọi API)
def get_embedding(text: str):
    if not text or not isinstance(text, str):
        raise ValueError("❌ Đầu vào phải là một chuỗi văn bản hợp lệ.")

    try:
        # Lấy embedding từ API
        embedding_vector = client.feature_extraction(
            text,
            model="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )
        # Chuyển embedding thành list
        embedding_vector = np.array(embedding_vector).tolist()

        # Kiểm tra chiều của vector (thường là 384 với MiniLM-L12-v2)
        # if len(embedding_vector) != 384:
        #     raise ValueError(f"❗ Vector trả về có chiều không đúng: {len(embedding_vector)}. Dữ liệu đầu vào: '{text}'")

        return embedding_vector

    except Exception as e:
        raise RuntimeError(f"🚫 Lỗi khi gọi Hugging Face API: {e}")

# # Test thử
# if __name__ == "__main__":
    while True:
        sample_text = input("\n💬 Nhập văn bản (hoặc gõ 'exit' để thoát): ")
        if sample_text.lower() == 'exit':
            break
        try:
            embedding = get_embedding(sample_text)
            print(f"✅ Vector embedding có {len(embedding)} chiều:")
            print(embedding[:5], "...")  # In thử 5 phần tử đầu

            # Tính độ tương đồng với các câu khác
            source_sentence = "That is a happy person"
            sentences = [
                "That is a happy dog",
                "That is a very happy person",
                "Today is a sunny day"
            ]

            if sample_text == source_sentence:
                source_embedding = embedding
                for sentence in sentences:
                    sentence_embedding = get_embedding(sentence)
                    similarity = cosine_similarity(
                        np.array(source_embedding).reshape(1, -1),
                        np.array(sentence_embedding).reshape(1, -1)
                    )[0][0]
                    print(f"\nCâu: '{sentence}'")
                    print(f"Độ tương đồng: {similarity:.4f}")

        except Exception as err:
            print(f"[ERROR]: {err}")
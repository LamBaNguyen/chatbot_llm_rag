from sentence_transformers import SentenceTransformer
import os

# Đảm bảo thư mục lưu trữ đã tồn tại
model_dir = './models/paraphrase-multilingual-MiniLM-L12-v2'
os.makedirs(model_dir, exist_ok=True)

# Tải mô hình từ Hugging Face
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

# Lưu mô hình vào thư mục đã tạo
model.save(model_dir)

print(f"✅ Đã tải và lưu model vào: {model_dir}")

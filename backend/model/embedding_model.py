from sentence_transformers import SentenceTransformer

model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
# vector = model.encode("Xin chào các bạn")
# print(len(vector))  # Sẽ ra 384

def get_embedding(text):
    return model.encode(text).tolist()
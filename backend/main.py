from typing import List, Dict
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
# from llm import semantic_search, generate_response, classify_query_intent, client
from llm_cloud import semantic_search, generate_response, classify_query_intent, client, set_model_name
import time
import asyncio
import os

app = FastAPI()
# port = int(os.getenv("PORT", 8000))

# Cho phép CORS để React kết nối
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000","https://aidulichbinhdinh-nbl.onrender.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Định nghĩa model cho request body
class ChatRequest(BaseModel):
    query: str
    history: List[Dict[str, str]]
class SetModelRequest(BaseModel):
    model_name: str
    
# ===== API đổi model =====
@app.post("/set_model")
async def set_model(request: SetModelRequest):
    try:
        set_model_name(request.model_name)
        print(f"✅ Đã đổi model thành: {request.model_name}")
        return {"message": f"Đã đổi model thành {request.model_name}"}
    except Exception as e:
        print(f"❌ Lỗi đổi model: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/chat")
async def chat(request: ChatRequest):
    start_time = time.time()  # Bắt đầu đo tổng thời gian
    
    try:
        async with asyncio.timeout(30):  # Timeout sau 30 giây
            query = request.query
            history = request.history

            if not query.strip():
                total_time = time.time() - start_time
                print(f"Total processing time: {total_time:.2f}s")
                return {"response": "Vui lòng nhập câu hỏi!", "error": True, "source": None}
            
            # Phân loại intent câu hỏi
            intent = classify_query_intent(query, client)
            # print(f"Intent detected: {intent}")
            if intent == "greeting":
                return {"response": "🥰 Chào bạn nha! Mình luôn sẵn sàng hỗ trợ nếu bạn cần tìm hiểu về du lịch Bình Định nè!", "error": False, "source": "greeting"}
            elif intent == "unrelated":
                return {"response": "😥 Xin lỗi, câu hỏi của bạn nằm ngoài lĩnh vực du lịch, văn hóa, lịch sử Bình Định. Bạn thử hỏi mình những câu liên quan đến vùng đất này nha!", "error": False, "source": "general"}

            # Đo thời gian cho semantic_search
            search_start = time.time()
            context, error = semantic_search(query)
            search_time = time.time() - search_start
            print(f"semantic_search took {search_time:.2f}s")
            
            if error:
                total_time = time.time() - start_time
                print(f"Total processing time: {total_time:.2f}s")
                return {"response": error, "error": True, "source": None}
            
            # Xác định nguồn dựa trên context
            # source = "elasticsearch" if context else "openai"
            
            # Đo thời gian cho generate_response
            generate_start = time.time()
            response, error = generate_response(query, context, history, client)
            generate_time = time.time() - generate_start
            print(f"generate_response took {generate_time:.2f}s")
            
            if error:
                total_time = time.time() - start_time
                print(f"Total processing time: {total_time:.2f}s")
                return {"response": error, "error": True, "source": None}
            
            # In tổng thời gian và nguồn
            total_time = time.time() - start_time
            print(f"Total processing time: {total_time:.2f}s")
            # print(f"Nguồn: {'Dữ liệu Bình Định' if source == 'elasticsearch' else 'Kiến thức chung'}")
            
            return {
                "search_results": context,
                "response": response,
                "error": False,
                # "source": "Dữ liệu Bình Định" if source == "elasticsearch" else "Kiến thức chung"
                
            }
    
    except asyncio.TimeoutError:
        total_time = time.time() - start_time
        print(f"Total processing time: {total_time:.2f}s (Timed out)")
        raise HTTPException(status_code=504, detail="Mình xử lý hơi lâu, bạn hỏi lại nhé!")
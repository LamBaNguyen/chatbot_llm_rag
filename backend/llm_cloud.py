import time
import threading
import queue
import sys
import select
from elasticsearch import Elasticsearch
# from model.embedding_model import get_embedding
# from model.embedding_model_new import get_embedding
from model.embedding_model_of_jina import get_embedding
from openai import OpenAI
import os
from dotenv import load_dotenv
import hashlib
import tiktoken

# Đo thời gian khởi động
start_time = time.time()
print(f"Starting backend at {time.time() - start_time:.2f}s")

load_dotenv()
print(f"Loaded env at {time.time() - start_time:.2f}s")

# Khởi tạo Elasticsearch
es = Elasticsearch(
    os.getenv("ELASTICSEARCH_URL"),
    api_key=os.getenv("ELASTICSEARCH_API_KEY")
)
print(f"Elasticsearch connected at {time.time() - start_time:.2f}s!")

INDEX_NAME = "chatbot_elastic"

token = os.getenv("GITHUB_TOKEN")
endpoint = "https://models.github.ai/inference"
model_name = "openai/gpt-4.1"
client = OpenAI(
    base_url=endpoint,
    api_key=token,
)
print(f"OpenAI client initialized at {time.time() - start_time:.2f}s!")

print(f"Backend fully initialized at {time.time() - start_time:.2f}s!")

# Khởi tạo bộ mã hóa tiktoken
encoding = tiktoken.encoding_for_model("gpt-4o")

# function để đổi model
def set_model_name(new_model_name: str):
    global model_name
    model_name = new_model_name
    print(f"✅ Model name đã đổi thành: {model_name}")

def semantic_search(query, top_k=2, max_context_tokens=5000, stop_event=None):
    """
    Tìm kiếm ngữ nghĩa trong Elasticsearch, trả về danh sách tài liệu và context đã được giới hạn token.
    Args:
        query (str): Câu truy vấn.
        top_k (int): Số lượng tài liệu tối đa trả về.
        max_context_tokens (int): Số token tối đa cho phép của context.
        stop_event: Sự kiện để dừng tác vụ nếu cần.
    Returns:
        tuple: (danh sách tài liệu, lỗi nếu có).
    """
    if stop_event and stop_event.is_set():
        return None, "Tác vụ tìm kiếm đã bị dừng."
    
    # Chuyển query thành chữ thường và tạo embedding
    query = query.lower()
    vector = get_embedding(query)
    keywords = query.split()
    
    # Xây dựng truy vấn Elasticsearch
    es_query = {
        "size": top_k,
        "query": {
            "bool": {
                "must": [
                    {
                         "match": {
                            "text": {
                                "query": query,
                                "operator": "or",
                                "minimum_should_match": "60%"
                            }
                        }
                    }
                ],
                "should": [
                    {
                        "match": {
                            "text": {
                                "query": query,
                                "operator": "or",
                                "fuzziness": "AUTO"
                            }
                        }
                    },
                    {
                        "script_score": {
                            "query": {"match_all": {}},
                            "script": {
                                "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                                "params": {"query_vector": vector}
                            }
                        }
                    }
                ],
                "minimum_should_match": 1
            }
        },
        "highlight": {
            "fields": {
                "text": {
                    "pre_tags": ["<mark>"],
                    "post_tags": ["</mark>"]
                }
            }
        }
    }
    
    try:
        res = es.search(index=INDEX_NAME, body=es_query)
        if stop_event and stop_event.is_set():
            return None, "Tác vụ tìm kiếm đã bị dừng."
        # print(res["hits"]["hits"])
        if not res["hits"]["hits"]:
            return None, "Mình không hiểu câu này lắm 😥. Bạn thử hỏi ngắn gọn hơn ^^"
        
        # Tìm điểm số cao nhất
        # max_score = max(hit["_score"] for hit in res["hits"]["hits"])?
        
        # Kiểm tra nếu điểm số cao nhất dưới ngưỡng
        # if max_score < similarity_threshold:
        #     return None, "Câu hỏi này không liên quan đến du lịch Bình Định."
        
        # Lọc trùng lặp dựa trên nội dung tài liệu
        results = res["hits"]["hits"]
        seen_hashes = set()
        unique_results = []
        for hit in results:
            source = hit['_source']
            doc_content = f"{source.get('title', '')}{source.get('content', '')}{source.get('link', '')}"
            doc_hash = hashlib.md5(doc_content.encode('utf-8')).hexdigest()
            if doc_hash not in seen_hashes:
                seen_hashes.add(doc_hash)
                unique_results.append(hit)
        
        if not unique_results:
            return None, "Không tìm thấy kết quả nào chứa từ khóa."
        
        # Sắp xếp theo điểm tương đồng (_score) để ưu tiên các tài liệu quan trọng
        sorted_results = sorted(unique_results, key=lambda x: x["_score"], reverse=True)
        
        # Chọn các tài liệu sao cho tổng số token của context không vượt quá max_context_tokens
        selected_results = []
        current_tokens = 0
        
        for hit in sorted_results[:top_k]:
            # Tạo chuỗi context cho tài liệu này
            context_snippet = f"**{hit['_source']['title']}**\n{hit['_source']['content']}\n{hit['_source']['link']}"
            snippet_tokens = len(encoding.encode(context_snippet))
            
            # Nếu thêm tài liệu này vượt quá giới hạn token, bỏ qua
            if current_tokens + snippet_tokens > max_context_tokens:
                break
            
            selected_results.append(hit)
            current_tokens += snippet_tokens
        
        if not selected_results:
            return None, "Không tìm thấy nội dung phù hợp trong giới hạn token."
        
        # Tạo context từ các tài liệu đã chọn
        context = "\n".join([f"**{hit['_source']['title']}**\n{hit['_source']['content']}\n{hit['_source']['link']}" for hit in selected_results])
        
        # In context để kiểm tra (có thể bỏ comment nếu cần)
        print("===== KẾT QUẢ ELASTICSEARCH TÌM ĐƯỢC =====")
        print(context)
        print(f"Số token của context: {len(encoding.encode(context))}")
        # print("Max_score: ", max_score)
        return selected_results, None  # Trả về danh sách tài liệu đã chọn
    
    
    except Exception as e:
        return None, f"Lỗi Elasticsearch: {str(e)}"
    
def build_prompt(documents, query: str, max_context_tokens=5000) -> str:
    """
    Xây dựng prompt cho LLM, đảm bảo tổng số token của context không vượt quá giới hạn.
    Args:
        documents: Danh sách tài liệu từ semantic_search.
        query (str): Câu truy vấn.
        max_context_tokens (int): Số token tối đa cho context.
    Returns:
        str: Prompt đã được tối ưu số token.
    """
    # Prompt hệ thống rút gọn
    system_prompt = (
        "Bạn là hướng dẫn viên du lịch thân thiện, chuyên về Bình Định, được tạo bởi **Nguyễn Bá Lâm** (Phù Mỹ, Bình Định).\n"
        "Trả lời gần gũi, đúng trọng tâm, dùng **Markdown**:\n"
        "- Ưu tiên dữ liệu bên dưới, bổ sung kiến thức ngoài nếu cần (ghi rõ).\n"
        "- Nếu người dùng hỏi nhiều ý (ví dụ: địa điểm + món ăn), hãy cố gắng trả lời đầy đủ cả hai nếu liên quan đến Bình Định."
        "- Giữ câu trả lời ~400 token, dùng gạch đầu dòng (-), in đậm **tiêu đề**.\n"
        "- Từ chối lịch sự nếu không liên quan đến du lịch, văn hóa, lịch sử Bình Định.\n"
        "- Chỉ dùng liên kết của tài liệu đầu tiên.\n"
    )
    
    if documents:
        # Tạo context với thông tin tài liệu
        context_parts = []
        current_tokens = 0
        
        for doc in documents:
            snippet = f"**{doc['_source']['title']}**\n{doc['_source']['content']}"
            snippet_tokens = len(encoding.encode(snippet))
            
            if current_tokens + snippet_tokens > max_context_tokens:
                break
                
            context_parts.append(snippet)
            current_tokens += snippet_tokens
        
        context = "\n\n".join(context_parts)
        
        prompt = (
            f"{system_prompt}\n\n"
            f"**Dữ liệu chính:**\n{context}\n\n"
            f"**Câu hỏi:** {query}\n\n"
        )
        
        # Kiểm tra tổng số token của prompt (không tính link)
        total_tokens = len(encoding.encode(prompt))
        print(f"Số token của prompt (không tính history): {total_tokens}")
        
        return prompt
    else:
        return (
            f"{system_prompt}\n\n"
            f"**Xin lỗi nhé!** Mình không có dữ liệu chính về “{query}”. "
            "Hỏi mình về du lịch Bình Định nhé! 😊"
        )
    
def truncate_text(text, max_tokens):
    """
    Cắt bớt văn bản để không vượt quá số token cho phép.
    Args:
        text (str): Văn bản cần cắt.
        max_tokens (int): Số token tối đa.
    Returns:
        str: Văn bản đã cắt bớt.
    """
    if not text:
        return text
    tokens = encoding.encode(text)
    if len(tokens) <= max_tokens:
        return text
    truncated_tokens = tokens[:max_tokens]
    return encoding.decode(truncated_tokens)

def generate_response(query, documents, history, client, stop_event=None, max_total_tokens=8000):
    """
    Tạo phản hồi từ GPT-4o-mini, đảm bảo tổng số token không vượt quá giới hạn.
    Args:
        query (str): Câu truy vấn.
        documents: Danh sách tài liệu từ semantic_search.
        history: Lịch sử hội thoại.
        client: Client để gọi LLM.
        stop_event: Sự kiện để dừng tác vụ.
        max_total_tokens (int): Số token tối đa cho toàn bộ messages.
    Returns:
        tuple: (phản hồi, lỗi nếu có).
    """
    if stop_event and stop_event.is_set():
        return None, "Tác vụ trả lời đã bị dừng."
    
    try:
        # Xây dựng prompt
        prompt = build_prompt(documents, query, max_context_tokens=5000)
        
        # Tạo messages
        messages = [{"role": "system", "content": prompt}]
        
        # Giới hạn history (chỉ lấy 5 tin nhắn gần nhất)
        history = history[-5:] if len(history) > 5 else history
        
        # Thêm history vào messages, cắt bớt nếu cần
        history_tokens = 0
        truncated_history = []
        for msg in history:
            role = msg["role"]
            if role == "bot":
                role = "assistant"
            content = msg["content"]
            msg_tokens = len(encoding.encode(content))
            
            if history_tokens + msg_tokens > 1000:  # Giới hạn history dưới 1000 token
                content = truncate_text(content, 1000 - history_tokens)
                msg_tokens = len(encoding.encode(content))
            
            history_tokens += msg_tokens
            truncated_history.append({"role": role, "content": content})
        
        messages.extend(truncated_history)
        messages.append({"role": "user", "content": query})
        
        # Tính tổng số token của messages
        total_tokens = sum(len(encoding.encode(msg["content"])) for msg in messages)
        print(f"Tổng số token của messages (ban đầu): {total_tokens}")
        
        # Nếu vượt quá giới hạn, cắt bớt context và query
        if total_tokens > max_total_tokens:
            # Ước tính số token của system prompt và history
            system_tokens = len(encoding.encode(messages[0]["content"]))
            history_tokens = sum(len(encoding.encode(msg["content"])) for msg in messages[1:-1])
            query_tokens = len(encoding.encode(query))
            
            # Số token còn lại cho context
            remaining_tokens = max_total_tokens - (system_tokens + history_tokens + query_tokens)
            if remaining_tokens < 1000:  # Nếu không đủ chỗ cho context, cắt bớt query
                remaining_tokens = max(1000, remaining_tokens)
                max_query_tokens = max_total_tokens - (system_tokens + history_tokens + remaining_tokens)
                query = truncate_text(query, max_query_tokens)
                messages[-1]["content"] = query
                query_tokens = len(encoding.encode(query))
                remaining_tokens = max_total_tokens - (system_tokens + history_tokens + query_tokens)
            
            # Cắt bớt context trong prompt
            if documents:
                context_parts = []
                current_tokens = 0
                for doc in documents:
                    snippet = f"**{doc['_source']['title']}**\n{doc['_source']['content']}"
                    snippet_tokens = len(encoding.encode(snippet))
                    if current_tokens + snippet_tokens > remaining_tokens:
                        break
                    context_parts.append(snippet)
                    current_tokens += snippet_tokens
                
                context = "\n\n".join(context_parts)
                messages[0]["content"] = (
                    f"{messages[0]['content'].split('**Dữ liệu chính:**')[0]}"
                    f"**Dữ liệu chính:**\n{context}\n\n"
                    f"**Câu hỏi:** {query}\n\n"
                )
            
            total_tokens = sum(len(encoding.encode(msg["content"])) for msg in messages)
            print(f"Tổng số token của messages (sau khi cắt): {total_tokens}")
        
        # Gửi đến LLM
        result_queue = queue.Queue()
        
        def run_openai():
            try:
                response = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    max_tokens=500,
                    temperature=0.5,
                )
                result_queue.put((response.choices[0].message.content, None))
            except Exception as e:
                result_queue.put((None, f"Lỗi LLM: {str(e)}"))
        
        openai_thread = threading.Thread(target=run_openai)
        openai_thread.start()
        openai_thread.join(timeout=30)
        
        if openai_thread.is_alive():
            if stop_event:
                stop_event.set()
            return None, "Mình xử lý hơi lâu, bạn hỏi lại nhé!"
        
        content, error = result_queue.get()
        if error:
            return None, error
        
        if stop_event and stop_event.is_set():
            return None, "Tác vụ trả lời đã bị dừng."
        
        # Thêm liên kết của tài liệu đầu tiên
        if documents:
            first_doc = documents[0]['_source']
            content += f'\n\n<a href="{first_doc["link"]}">Đọc thêm tại đây nhé😊</a>'
        
        # Đảm bảo câu trả lời kết thúc tự nhiên
        if content.endswith("...") or not content.strip().endswith(("!", ".", "?", "😊")):
            last_punct = max(content.rfind(p) for p in [".", "!", "?", "😊"])
            if last_punct != -1:
                content = content[:last_punct + 1]
        
        return content, None
    
    except Exception as e:
        return None, f"Lỗi trong generate_response: {str(e)}"
       
def process_query(query, history, result_queue, stop_event):
     # Phân loại câu hỏi
    label = classify_query_intent(query, client)
    
    if label == "greeting":
        result_queue.put((
            "🥰 Chào bạn nha! Mình luôn sẵn sàng hỗ trợ nếu bạn cần tìm hiểu về du lịch Bình Định nè!",
            None
        ))
        return
    
    if label == "unrelated":
        result_queue.put((
            "😥 Xin lỗi, câu hỏi của bạn nằm ngoài lĩnh vực du lịch, văn hóa, lịch sử Bình Định.\n"
            "Bạn thử hỏi mình những câu liên quan đến vùng đất này nha!",
            None
        ))
        return
    #Yes
    # Tìm kiếm ngữ nghĩa
    documents, error = semantic_search(query, stop_event=stop_event)
    if stop_event.is_set():
        result_queue.put((None, "Mình xử lý hơi lâu, bạn hỏi lại nhé!"))
        return
        
    if error:
        result_queue.put((None, error))
        documents = None

    # Tạo câu trả lời
    response, error = generate_response(query, documents, history, client, stop_event=stop_event)
    if stop_event.is_set():
        result_queue.put((None, "Mình xử lý hơi lâu, bạn hỏi lại nhé!"))
        return
        
    if error:
        result_queue.put((None, error))
    else:
        result_queue.put((response, None))

def check_for_stop(timeout=0.1):
    if sys.stdin in select.select([sys.stdin], [], [], timeout)[0]:
        line = sys.stdin.readline().strip()
        if line.lower() == "stop":
            return True
    return False

#hàm dùng GPT đánh giá câu hỏi có thuộc lĩnh vực chatbot học không?
def classify_query_intent(query: str, client) -> str:
    """
    Phân loại câu hỏi thành:
    - 'related': liên quan đến du lịch, văn hóa, lịch sử ở Bình Định
    - 'unrelated': không liên quan
    - 'greeting': lời chào, cảm ơn, tạm biệt, xã giao
    """
    system_prompt = (
        "Bạn là bộ phân loại thông minh. Phân loại câu hỏi đầu vào thành 1 trong 3 loại sau:\n"
        "- related: nếu liên quan đến du lịch, văn hóa, lịch sử, ẩm thực, ăn uống, vui chơi ở Bình Định\n"
        "- unrelated: nếu không liên quan gì đến chủ đề trên\n"
        "- greeting: nếu là lời chào hỏi, cảm ơn, chúc, tạm biệt, v.v.\n\n"
        "Chỉ trả lời 1 từ: related / unrelated / greeting.\n"
        "Ví dụ:\n"
        "- 'Có những địa điểm du lịch nào ở Quy Nhơn?' → related\n"
        "- 'Tôi nên học Python ở đâu?' → unrelated\n"
        "- 'Chào bạn!' → greeting\n"
        "- 'Tạm biệt nhé, hẹn gặp lại!' → greeting\n"
        "- 'Nghệ thuật hát tuồng ở Bình Định ra sao?' → related\n"
        "- 'iPhone 15 ra mắt năm nào?' → unrelated\n"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Câu hỏi: {query}\nTrả lời (related/unrelated/greeting):"}
    ]

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            max_tokens=5,
            temperature=0,
        )
        label = response.choices[0].message.content.strip().lower()
        print(f"[DEBUG] GPT phân loại '{query}' → {label}")
        return label if label in ["related", "unrelated", "greeting"] else "related"
    except Exception as e:
        print("Lỗi khi phân loại câu hỏi:", str(e))
        return "related"

def chatbot():
    history = []
    print("💬 Chào bạn! Mình là chatbot du lịch Bình Định. Hỏi mình bất cứ điều gì nhé! (Nhập 'exit' để thoát, hoặc 'stop' để dừng tác vụ đang chạy)")
    
    while True:
        query = input("🔍 Nhập câu hỏi: ")
        if query.lower() == 'exit':
            print("👋 Tạm biệt! Hẹn gặp lại bạn!")
            break
        
        # Tạo stop event và queue
        stop_event = threading.Event()
        result_queue = queue.Queue()

        # Chạy xử lý query trong luồng riêng
        process_thread = threading.Thread(target=process_query, args=(query, history, result_queue, stop_event))
        process_thread.start()

        # Đợi thread hoàn thành
        process_thread.join()
        response, error = result_queue.get()

        if error:
            print(error)
        else:
            print("💬 Trả lời:", response)
            history.append({"role": "user", "content": query})
            history.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    chatbot()

# Binh Dinh Tourism Chatbot: Building a Smart RAG LLM System

**Project Description**: Develop a Retrieval-Augmented Generation (RAG) Chatbot as an Interactive Tour Guide for Binh Dinh Province to Enhance Tourist Engagement.

---

## 💻 Technologies Used

- **Backend**: FastAPI
- **Frontend**: React.js + Tailwind
- **Vector Database**: ElasticSearch (Elastic Cloud)
- **API Server**: Uvicorn

---

## 🚀 Getting Started

These instructions will help you set up and run the project locally.

### Backend

1. **Clone the repository**:

   ```bash
   git clone https://github.com/LamBaNguyen/chatbot_with_rag_llm.git
   cd project
   ```

2. **Create a virtual environment** (recommended):

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Run the FastAPI backend**:

   To start the backend server, run the following command:

   ```bash
   uvicorn main:app --reload --port 8000
   ```

   The FastAPI backend should now be running at [http://localhost:8000](http://localhost:8000).

### Frontend

1. **Navigate to the frontend directory**:

   ```bash
   cd frontend
   ```

2. **Install frontend dependencies**:

   ```bash
   npm install
   ```

3. **Start the React frontend**:

   To run the frontend development server, execute:

   ```bash
   npm start
   ```

   The React app should now be running at [http://localhost:3000](http://localhost:3000).

---

## 🔧 Configuration

### ElasticSearch (Elastic Cloud)

This project uses ElasticSearch as the vector database. You will need to set up an ElasticSearch cluster on Elastic Cloud.

1. **Create an ElasticSearch cluster** on [Elastic Cloud](https://cloud.elastic.co/).
2. **Obtain your ElasticSearch credentials**, including the URL, username, and password.
3. **Configure the connection** to ElasticSearch in the backend. You should replace the default URL and credentials in the backend code with your ElasticSearch cluster's details.

Example configuration in `main.py`:

```python
from elasticsearch import Elasticsearch

# Replace with your ElasticSearch Cloud credentials
es = Elasticsearch(
    cloud_id="your_cloud_id",
    api_key="your_key"
)
```

---

## 📡 API Endpoints

Here are some of the available API endpoints:

- **GET `/api/endpoint`**: Description of the endpoint.
- **POST `/api/endpoint`**: Description of the endpoint.

For more detailed information on the API routes and usage, please refer to the FastAPI interactive docs available at [http://localhost:8000/docs](http://localhost:8000/docs).

---

## 🛠️ Features

- **FastAPI Backend**: A fast and modern web framework for building APIs with Python.
- **ElasticSearch for Vector Storage**: Utilizing Elastic Cloud for scalable and efficient vector database storage.
- **React Frontend**: A responsive and dynamic UI built with React.
- **Real-time data updates**: (If applicable) Real-time updates between the frontend and backend.

---

## 🏗️ Future Improvements

- **Improve Search Functionality**: Enhance the search algorithms to include semantic search capabilities using ElasticSearch.
- **Frontend Enhancements**: Add more interactive UI components and improve accessibility.
- **API Rate Limiting**: Implement API rate limiting for better resource management.

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🤝 Contributing

We welcome contributions! If you want to improve this project, feel free to submit a pull request or open an issue.

---

## 👨‍💻 Authors

- **NguyenBaLam** - *Initial work* - [My GitHub](https://github.com/LamBaNguyen)

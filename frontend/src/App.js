import React, { useState, useEffect, useRef, memo } from "react";
import axios from "axios";
import ReactMarkdown from "react-markdown";
import rehypeRaw from "rehype-raw";
import { ToastContainer, toast } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import "tailwindcss/tailwind.css";
import "./App.css";

function App() {
  const [query, setQuery] = useState("");
  const [selectedModel, setSelectedModel] = useState("openai/gpt-4.1");
  const [conversations, setConversations] = useState(() => {
    const saved = localStorage.getItem("conversations");
    return saved ? JSON.parse(saved) : [];
  });
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [editingConversationId, setEditingConversationId] = useState(null);
  const [newTitle, setNewTitle] = useState("");
  const [showScrollButton, setShowScrollButton] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [showSidebar, setShowSidebar] = useState(false);
  const messagesEndRef = useRef(null);
  const messagesContainerRef = useRef(null);
  const lastMessageCountRef = useRef({});

  const popularPlaces = [
    { name: "Địa điểm 🏕️", query: "Địa điểm vui chơi" },
    { name: "Lễ hội 🥁", query: "Lễ hội truyền thống tại Bình Định" },
    { name: "Ăn uống 🍜", query: "Món ngon" },
    { name: "Chỗ ở 💤", query: "Khách sạn" },
    { name: "Thư giãn ⛱️", query: "Địa điểm thư giãn" },
  ];

  const createNewConversation = () => {
    const newId = conversations.length
      ? conversations[conversations.length - 1].id + 1
      : 1;
    const newConversation = {
      id: newId,
      title: `Cuộc hội thoại ${newId}`,
      messages: [
        {
          role: "assistant",
          content: `**Chào bạn!** 🌴  
          Mình là chatbot du lịch Bình Định, rất vui được gặp bạn! Mình ở đây để:  
          - **Giới thiệu địa điểm**: Hỏi mình về Quy Nhơn, Eo Gió, hay bất kỳ nơi nào ở Bình Định nhé!  
          - **Gợi ý hoạt động**: Muốn biết đi đâu, ăn gì, chơi gì? Mình sẽ giúp!  
          Bạn muốn khám phá điều gì hôm nay? 😊`,
          isNew: false,
        },
      ],
      isLoading: false,
    };
    setConversations([...conversations, newConversation]);
    setCurrentConversationId(newId);
  };

  useEffect(() => {
    if (conversations.length === 0) {
      createNewConversation();
    }
  }, []);

  useEffect(() => {
    localStorage.setItem("conversations", JSON.stringify(conversations));
  }, [conversations]);

  useEffect(() => {
    const currentConversation = conversations.find(
      (conv) => conv.id === currentConversationId
    );
    if (currentConversation) {
      lastMessageCountRef.current[currentConversationId] =
        currentConversation.messages.length;

      currentConversation.messages.forEach((msg, index) => {
        if (msg.isNew) {
          setTimeout(() => {
            setConversations((prev) =>
              prev.map((conv) =>
                conv.id === currentConversationId
                  ? {
                      ...conv,
                      messages: conv.messages.map((m, i) =>
                        i === index ? { ...m, isNew: false } : m
                      ),
                    }
                  : conv
              )
            );
          }, 2000);
        }
      });
    }
  }, [conversations, currentConversationId]);

  useEffect(() => {
    scrollToBottom();
  }, [currentConversationId, conversations]);

  useEffect(() => {
    const handleScroll = () => {
      const container = messagesContainerRef.current;
      if (container) {
        const isAtBottom =
          container.scrollHeight - container.scrollTop <=
          container.clientHeight + 10;
        setShowScrollButton(!isAtBottom);
      }
    };

    const container = messagesContainerRef.current;
    if (container) {
      container.addEventListener("scroll", handleScroll);
      return () => container.removeEventListener("scroll", handleScroll);
    }
  }, [currentConversationId]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const currentConversation = conversations.find(
    (conv) => conv.id === currentConversationId
  ) || { messages: [], isLoading: false };

  const filteredConversations = conversations.filter((conv) =>
    conv.title.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    const userMessage = { role: "user", content: query, isNew: true };
    const updatedConversations = conversations.map((conv) => {
      if (conv.id === currentConversationId) {
        if (conv.messages.length === 1) {
          conv.title = query.slice(0, 20) + (query.length > 20 ? "..." : "");
        }
        return {
          ...conv,
          messages: [...conv.messages, userMessage],
          isLoading: true,
        };
      }
      return conv;
    });
    setConversations(updatedConversations);
    setQuery("");

    try {
      const history = currentConversation.messages.map((msg) => ({
        role: msg.role,
        content: msg.content,
      }));
      // console.log(process.env.REACT_APP_SERVER_URL);
      // console.log(`${process.env.REACT_APP_SERVER_URL}/chat`);
      const response = await axios.post(
        `${process.env.REACT_APP_SERVER_URL}/chat`
        // `http://localhost:8000/chat`
        ,
        {
          query,
          history,
        }
      );

      if (response.data.error) {
        toast.error(response.data.response);
        setConversations((prev) =>
          prev.map((conv) =>
            conv.id === currentConversationId
              ? { ...conv, isLoading: false }
              : conv
          )
        );
        return;
      }

      const botMessage = {
        role: "assistant",
        content: response.data.response,
        isNew: true,
      };
      setConversations((prev) =>
        prev.map((conv) =>
          conv.id === currentConversationId
            ? {
                ...conv,
                messages: [...conv.messages, botMessage],
                isLoading: false,
              }
            : conv
        )
      );
    } catch (error) {
      console.error("Error:", error);
      toast.error("Có lỗi xảy ra khi gửi câu hỏi!");
      setConversations((prev) =>
        prev.map((conv) =>
          conv.id === currentConversationId
            ? { ...conv, isLoading: false }
            : conv
        )
      );
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const deleteConversation = (id) => {
    const updatedConversations = conversations.filter((conv) => conv.id !== id);
    setConversations(updatedConversations);
    if (currentConversationId === id) {
      if (updatedConversations.length > 0) {
        setCurrentConversationId(updatedConversations[0].id);
      } else {
        setCurrentConversationId(null);
        createNewConversation();
      }
    }
  };

  const startEditing = (conv) => {
    setEditingConversationId(conv.id);
    setNewTitle(conv.title);
  };

  const saveNewTitle = (id) => {
    const updatedConversations = conversations.map((conv) =>
      conv.id === id ? { ...conv, title: newTitle } : conv
    );
    setConversations(updatedConversations);
    setEditingConversationId(null);
    setNewTitle("");
  };

  const toggleDarkMode = () => {
    setIsDarkMode(!isDarkMode);
  };

  const markdownComponents = {
    a: ({ href, children }) => (
      <a
        href={href}
        className="text-blue-600 underline hover:text-blue-800 transition-colors dark:text-blue-400 dark:hover:text-blue-300"
        target="_blank"
        rel="noopener noreferrer"
      >
        {children}
      </a>
    ),
  };

  const Message = memo(({ msg }) => (
    <div
      className={`flex ${
        msg.role === "user" ? "justify-end" : "justify-start"
      } mb-4 ${
        msg.isNew
          ? msg.role === "user"
            ? "animate-fade-slide-right"
            : "animate-fade-slide-left"
          : ""
      }`}
    >
      <div
        className={`flex items-start gap-3 max-w-[80%] sm:max-w-[70%] ${
          msg.role === "user" ? "flex-row-reverse" : ""
        }`}
      >
        <span className="text-2xl sm:text-3xl">
          {msg.role === "user" ? "🧑" : "🌴"}
        </span>
        <div
          className={`p-3 sm:p-4 rounded-2xl shadow-md message-content ${
            msg.role === "user"
              ? "bg-blue-600 text-white"
              : "bg-white text-gray-800 dark:bg-gray-700 dark:text-gray-200"
          }`}
        >
          {msg.role === "assistant" ? (
            <ReactMarkdown
              components={markdownComponents}
              rehypePlugins={[rehypeRaw]}
            >
              {msg.content}
            </ReactMarkdown>
          ) : (
            <span>{msg.content}</span>
          )}
        </div>
      </div>
    </div>
  ));

  const handlePlaceClick = (placeQuery) => {
    setQuery(placeQuery);
    handleSubmit({ preventDefault: () => {} });
  };
  const handleChangeModel = async (e) => {
    const newModel = e.target.value;
    setSelectedModel(newModel);
    try {
      await axios.post(
        `${process.env.REACT_APP_SERVER_URL}/set_model`
        // `http://localhost:8000/set_model`
        ,
        {
          model_name: newModel,
        }
      );
      toast.success(`Đã đổi model thành ${newModel}`);
    } catch (err) {
      toast.error("Đổi model thất bại!");
    }
  };
  return (
    <div
      className={`h-screen w-screen flex flex-col ${
        isDarkMode ? "dark" : ""
      } bg-gray-50 dark:bg-gray-900`}
    >
      <button
        className="sm:hidden fixed top-4 left-4 z-20 bg-blue-600 dark:bg-green-600 text-white p-2 rounded-lg hover:bg-blue-700 dark:hover:bg-green-700 transition-colors"
        onClick={() => setShowSidebar(!showSidebar)}
      >
        {showSidebar ? "✖" : "☰"}
      </button>

      <div className="flex-1 flex h-full w-full flex-col sm:flex-row">
        <div
          className={`w-full sm:w-1/4 bg-white dark:bg-gray-800 shadow-lg p-4 overflow-y-auto sidebar flex flex-col ${
            showSidebar ? "sidebar-open" : "sidebar-closed"
          }`}
        >
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold text-blue-800 dark:text-gray-200">
              Lịch sử hội thoại
            </h2>
            <div className="flex gap-2">
              <button
                onClick={createNewConversation}
                className="bg-blue-600 dark:bg-green-600 text-white px-3 py-1 rounded-lg hover:bg-blue-700 dark:hover:bg-green-700 transition-colors"
              >
                Mới
              </button>
              <button
                onClick={toggleDarkMode}
                className="bg-gray-200 dark:bg-gray-600 text-gray-800 dark:text-gray-200 px-3 py-1 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-500 transition-colors"
              >
                {isDarkMode ? "☀️" : "🌙"}
              </button>
            </div>
          </div>
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Tìm kiếm cuộc hội thoại..."
            className="w-full p-2 mb-4 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-gray-200 dark:border-gray-600"
          />
          {filteredConversations.map((conv) => (
            <div
              key={conv.id}
              className={`flex items-center justify-between p-2 mb-2 rounded-lg cursor-pointer transition-all duration-300 transform hover:scale-105 hover:bg-blue-50 dark:hover:bg-gray-700 animate-fade-in ${
                conv.id === currentConversationId
                  ? "bg-blue-100 dark:bg-gray-700"
                  : "bg-gray-100 dark:bg-gray-800"
              }`}
              onClick={() => {
                setCurrentConversationId(conv.id);
                setShowSidebar(false);
              }}
            >
              {editingConversationId === conv.id ? (
                <div className="flex-1 flex gap-2">
                  <input
                    type="text"
                    value={newTitle}
                    onChange={(e) => setNewTitle(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") saveNewTitle(conv.id);
                    }}
                    className="flex-1 p-1 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-gray-200"
                  />
                  <button
                    onClick={() => saveNewTitle(conv.id)}
                    className="text-green-500 hover:text-green-700"
                  >
                    💾
                  </button>
                </div>
              ) : (
                <>
                  <span className="text-gray-800 dark:text-gray-200 truncate flex-1">
                    {conv.title}
                  </span>
                  <div className="flex gap-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        startEditing(conv);
                      }}
                      className="text-blue-500 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300"
                    >
                      ✏️
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        deleteConversation(conv.id);
                      }}
                      className="text-red-500 hover:text-red-700"
                    >
                      🗑️
                    </button>
                  </div>
                </>
              )}
            </div>
          ))}
          {/* Link đến GitHub source */}
          <a
            href="https://github.com/LamBaNguyen/chatbot_llm_rag"
            target="_blank"
            className="mt-auto text-blackmt-auto text-black hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300 text-center text-xs font-light-400 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-600 block text-center"
          >
            © NBL 2025. All rights reserved.
          </a>
        </div>

        <div className="w-full sm:w-3/4 bg-white dark:bg-gray-800 shadow-lg flex flex-col overflow-hidden relative">
          <div
            ref={messagesContainerRef}
            className="flex-1 overflow-y-auto p-4 sm:p-6 pb-[200px] sm:pb-[180px]" // Tăng padding-bottom để tránh bị che
            style={{
              background: isDarkMode
                ? "linear-gradient(to bottom, rgba(0,0,0,0.1), rgba(0,0,0,0.5)), url('https://images.unsplash.com/photo-1507521628349-dee9b8e5895d?ixlib=rb-4.0.3&auto=format&fit=crop&w=1350&q=80')"
                : "linear-gradient(to bottom, rgba(255,255,255,0.1), rgba(255,255,255,0.5)), url('https://images.unsplash.com/photo-1507521628349-dee9b8e5895d?ixlib=rb-4.0.3&auto=format&fit=crop&w=1350&q=80')",
              backgroundSize: "cover",
              backgroundPosition: "center",
            }}
          >
            {currentConversation.messages.map((msg, index) => (
              <Message key={index} msg={msg} />
            ))}
            {currentConversation.isLoading && (
              <div className="flex justify-start mb-4">
                <div className="flex items-start gap-3 max-w-[80%] sm:max-w-[70%]">
                  <span className="text-2xl sm:text-3xl">🤖</span>
                  <div className="p-3 sm:p-4 rounded-2xl shadow-md bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-200">
                    <span className="inline-flex items-center">
                      Đang trả lời
                      <span className="inline-flex ml-1">
                        <span className="animate-typing">.</span>
                        <span className="animate-typing animation-delay-200">
                          .
                        </span>
                        <span className="animate-typing animation-delay-400">
                          .
                        </span>
                      </span>
                    </span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
          {showScrollButton && (
            <button
              onClick={scrollToBottom}
              className="absolute bottom-48 sm:bottom-44 left-1/2 -translate-x-1/2 bg-blue-600 dark:bg-green-600 text-white p-3 rounded-full shadow-lg hover:bg-blue-700 dark:hover:bg-green-700 transition-all duration-300 z-10"
              title="Cuộn xuống tin nhắn mới nhất"
            >
              ↓
            </button>
          )}
          <div className="absolute bottom-4 sm:bottom-6 left-1/2 transform -translate-x-1/2 w-full max-w-[90%] sm:max-w-5xl rounded-xl bg-gray-100 dark:bg-gray-900 p-3 sm:p-4 shadow-xl">
            <div className="relative mb-3 flex">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Hỏi về Quy Nhơn, Eo Gió..."
                className="w-full p-3 sm:p-3 bg-transparent rounded-lg !border-none outline-none shadow-none text-gray-800 dark:text-gray-200 focus:outline-none focus:ring-0 placeholder-gray-400 dark:placeholder-gray-500 text-sm sm:text-base pr-10"
                disabled={currentConversation.isLoading}
              />
              {/* Dropdown chọn model */}
              <select
                value={selectedModel}
                onChange={handleChangeModel}
                className="p-2 rounded-lg border bg-white mr-[60px] text-blue-500 "
                disabled={currentConversation.isLoading}
              >
                <option value="openai/gpt-4.1">GPT-4.1</option>
                <option value="openai/gpt-4o">GPT-4o</option>
                <option value="openai/gpt-4o-mini">GPT-4o-mini</option>
                {/* Thêm các model khác nếu cần */}
              </select>
              <button
                type="button"
                onClick={handleSubmit}
                className={`absolute right-2 top-1/2 -translate-y-1/2 p-2 rounded-full transition-colors duration-200 ${
                  currentConversation.isLoading
                    ? "bg-gray-400 text-gray-700 cursor-not-allowed"
                    : "bg-blue-600 dark:bg-green-600 text-white hover:bg-blue-700 dark:hover:bg-green-700"
                }`}
                disabled={currentConversation.isLoading}
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-5 w-5 sm:h-6 sm:w-6"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                  />
                </svg>
              </button>
            </div>

            <div className="inline-flex flex-wrap gap-2 justify-center">
              {popularPlaces.map((place, index) => (
                <button
                  key={index}
                  onClick={() => handlePlaceClick(place.query)}
                  className={`px-2 sm:px-3 py-1 rounded-full text-xs sm:text-sm transition-colors ${
                    currentConversation.isLoading
                      ? "bg-gray-400 text-gray-700 cursor-not-allowed"
                      : "bg-blue-500 dark:bg-green-500 text-white hover:bg-blue-600 dark:hover:bg-green-600"
                  }`}
                  disabled={currentConversation.isLoading}
                >
                  {place.name}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
      <ToastContainer />
    </div>
  );
}

export default App;

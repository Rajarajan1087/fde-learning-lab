import React, { useState, useRef, useEffect } from 'react';
import ChatBubble from './components/ChatBubble';

interface Message {
  role: 'user' | 'assistant';
  content: string | any[];
}

function App() {
  const [messages, setMessages] = useState<Message[]>([
    { role: 'assistant', content: 'Hi there! I am your HR Verification Agent. To help verify your details, could you please provide your full name, email address, phone number, and an image of your Aadhar card?' }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const removeImage = () => {
    setImagePreview(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if ((!input.trim() && !imagePreview) || isLoading) return;

    let finalContent: string | any[] = input.trim();
    if (imagePreview) {
      finalContent = [
        { type: "text", text: input.trim() || "Here is the image" },
        { type: "image_url", image_url: { url: imagePreview } }
      ];
    }

    const userMessage = { role: 'user', content: finalContent } as Message;
    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    setInput('');
    removeImage();
    setIsLoading(true);

    try {
      const backendPort = import.meta.env.VITE_BACKEND_PORT || '8000';
      const response = await fetch(`http://localhost:${backendPort}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: newMessages, model: 'google/gemini-3.1-pro-preview' })
      });
      
      const data = await response.json();
      
      if (response.ok) {
        setMessages([...newMessages, { role: data.role, content: data.content }]);
      } else {
        console.error("Error from backend:", data);
        setMessages([...newMessages, { role: 'assistant', content: `Error: ${data.detail || 'Something went wrong'}` }]);
      }
    } catch (error) {
      console.error("Failed to fetch:", error);
      setMessages([...newMessages, { role: 'assistant', content: 'Network Error: Failed to connect to backend' }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app-container">
      <div className="header">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="url(#gradient)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <defs>
            <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#a3b1ff" />
              <stop offset="100%" stopColor="#d8b4fe" />
            </linearGradient>
          </defs>
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
        </svg>
        <h1>AI Chat</h1>
      </div>

      <div className="messages-container">
        {messages.length === 0 && (
          <div style={{ margin: 'auto', textAlign: 'center', opacity: 0.5, maxWidth: '300px' }}>
            <p>Welcome! Send a message or upload an Aadhar card image to start the HR verification demo.</p>
          </div>
        )}
        
        {messages.map((msg, idx) => (
          <ChatBubble key={idx} role={msg.role} content={msg.content} />
        ))}
        
        {isLoading && (
          <div className="chat-bubble-wrapper assistant">
            <div className="chat-bubble assistant">
              <div className="typing-indicator">
                <div className="typing-dot"></div>
                <div className="typing-dot"></div>
                <div className="typing-dot"></div>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="input-area">
        {imagePreview && (
          <div style={{ position: 'relative', display: 'inline-block', marginBottom: '10px' }}>
            <img src={imagePreview} alt="preview" style={{ height: '60px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.2)' }} />
            <button 
              onClick={removeImage} 
              style={{ position: 'absolute', top: '-8px', right: '-8px', background: '#ef4444', color: 'white', border: 'none', borderRadius: '50%', width: '20px', height: '20px', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '12px' }}>
              ✕
            </button>
          </div>
        )}
        <form className="input-form" onSubmit={handleSubmit}>
          <input 
            type="file" 
            ref={fileInputRef} 
            accept="image/*" 
            onChange={handleFileChange} 
            style={{ display: 'none' }} 
          />
          <button 
            type="button" 
            onClick={() => fileInputRef.current?.click()}
            style={{ background: 'transparent', border: 'none', color: 'rgba(255,255,255,0.7)', cursor: 'pointer', padding: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center', transition: 'color 0.2s' }}
            title="Attach Aadhar Card Image"
            onMouseEnter={(e) => e.currentTarget.style.color = 'white'}
            onMouseLeave={(e) => e.currentTarget.style.color = 'rgba(255,255,255,0.7)'}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"></path>
            </svg>
          </button>
          <input
            type="text"
            className="input-field"
            placeholder="Type your message..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isLoading}
          />
          <button type="submit" className="send-button" disabled={(!input.trim() && !imagePreview) || isLoading}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="22" y1="2" x2="11" y2="13"></line>
              <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
            </svg>
          </button>
        </form>
      </div>
    </div>
  );
}

export default App;

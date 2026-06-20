import React from 'react';

interface ChatBubbleProps {
  role: 'user' | 'assistant';
  content: string | any[];
}

const ChatBubble: React.FC<ChatBubbleProps> = ({ role, content }) => {
  const renderContent = () => {
    if (typeof content === 'string') {
      return content;
    }
    
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {content.map((item, idx) => {
          if (item.type === 'text') {
            return <span key={idx}>{item.text}</span>;
          }
          if (item.type === 'image_url') {
            return <img key={idx} src={item.image_url.url} alt="uploaded" style={{ maxWidth: '100%', borderRadius: '8px', maxHeight: '300px', objectFit: 'contain' }} />;
          }
          return null;
        })}
      </div>
    );
  };

  return (
    <div className={`chat-bubble-wrapper ${role}`}>
      <div className={`chat-bubble ${role}`}>
        {renderContent()}
      </div>
    </div>
  );
};

export default ChatBubble;

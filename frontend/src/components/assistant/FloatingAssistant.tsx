import React, { useState, useRef, useEffect } from 'react';
import {
  Send,
  Sparkles,
  Bot,
  User as UserIcon,
  RotateCcw,
  Minimize2,
} from 'lucide-react';
import { chatApi } from '../../services/chatApi';
import { ChatMessage } from '../../types/chat';

interface FloatingAssistantProps {
  currentMode?: 'user' | 'developer';
  activeProjectName?: string | null;
  onNavigateTab?: (tab: any) => void;
}

const DEFAULT_WELCOME_MESSAGE: ChatMessage = {
  id: 'welcome-msg',
  role: 'assistant',
  content:
    'Hello! I am your **Global AI Assistant** on SE IntelliPlatform.\n\nAsk me any software engineering question, explore programming concepts, or ask how to use our **User Mode** and **Developer Mode** workspaces.',
  timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
};

const SUGGESTED_QUESTIONS = [
  'How do User Mode and Developer Mode differ?',
  'How do I create and preview a new application?',
  'Explain frontend and backend communication patterns',
  'What tools does Code Studio provide?',
];

export const FloatingAssistant: React.FC<FloatingAssistantProps> = ({
  currentMode,
  activeProjectName,
  onNavigateTab: _onNavigateTab,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [inputMessage, setInputMessage] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([DEFAULT_WELCOME_MESSAGE]);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    if (typeof messagesEndRef.current?.scrollIntoView === 'function') {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  };

  useEffect(() => {
    if (isOpen) {
      scrollToBottom();
      inputRef.current?.focus();
    }
  }, [isOpen, messages, isLoading]);

  const handleSendMessage = async (textToSend?: string) => {
    const text = (textToSend !== undefined ? textToSend : inputMessage).trim();
    if (!text || isLoading) return;

    setErrorMessage(null);
    setInputMessage('');

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    const updatedHistory = [...messages, userMsg];
    setMessages(updatedHistory);
    setIsLoading(true);

    try {
      const response = await chatApi.sendMessage({
        message: text,
        conversation_history: updatedHistory.map((m) => ({
          role: m.role,
          content: m.content,
        })),
        context: {
          current_mode: currentMode,
          active_project: activeProjectName,
        },
      });

      const aiMsg: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: response.response,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, aiMsg]);
    } catch (err: any) {
      const message = err?.message || 'Failed to receive response from AI service. Please verify your connection or try again.';
      setErrorMessage(message);

      const errorMsg: ChatMessage = {
        id: `err-${Date.now()}`,
        role: 'assistant',
        content: `⚠️ **Unable to complete request:** ${message}`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        isError: true,
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleResetConversation = () => {
    setMessages([DEFAULT_WELCOME_MESSAGE]);
    setErrorMessage(null);
  };

  return (
    <aside
      className="floating-ai-assistant-container"
      aria-label="Global AI Assistant"
      style={{
        position: 'fixed',
        bottom: '1.5rem',
        right: '1.5rem',
        zIndex: 900,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'flex-end',
      }}
    >
      {/* 1. Sleek Floating Launcher Button */}
      {!isOpen && (
        <button
          type="button"
          id="btn-floating-assistant-launcher"
          onClick={() => setIsOpen(true)}
          title="Open Global AI Assistant"
          aria-label="Open Global AI Assistant"
          style={{
            width: '56px',
            height: '56px',
            borderRadius: '9999px',
            background: 'linear-gradient(135deg, #7c3aed, #4f46e5)',
            border: '1px solid rgba(255, 255, 255, 0.2)',
            color: '#ffffff',
            boxShadow: '0 8px 24px rgba(124, 58, 237, 0.45), 0 2px 8px rgba(0, 0, 0, 0.5)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'transform 0.2s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.2s ease',
            position: 'relative',
          }}
        >
          <Sparkles size={24} color="#ffffff" />
          <span
            style={{
              position: 'absolute',
              top: '-2px',
              right: '-2px',
              width: '12px',
              height: '12px',
              borderRadius: '9999px',
              background: '#10b981',
              border: '2px solid #0a0d14',
            }}
          />
        </button>
      )}

      {/* 2. Responsive Chat Panel */}
      {isOpen && (
        <div
          role="region"
          aria-label="AI Assistant Chat Window"
          style={{
            width: '380px',
            maxWidth: 'calc(100vw - 2rem)',
            height: '560px',
            maxHeight: 'calc(100vh - 6rem)',
            background: 'var(--bg-glass-modal, #0e1422)',
            border: '1px solid rgba(139, 92, 246, 0.3)',
            borderRadius: '16px',
            boxShadow: '0 20px 50px rgba(0, 0, 0, 0.65), 0 0 30px rgba(139, 92, 246, 0.15)',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            backdropFilter: 'blur(20px)',
            WebkitBackdropFilter: 'blur(20px)',
            animation: 'fadeInUp 0.2s ease-out',
          }}
        >
          {/* Header */}
          <div
            style={{
              padding: '1rem 1.25rem',
              background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.18) 0%, rgba(79, 70, 229, 0.12) 100%)',
              borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
              <div
                style={{
                  width: 34,
                  height: 34,
                  borderRadius: '10px',
                  background: 'linear-gradient(135deg, #7c3aed, #4f46e5)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxShadow: '0 2px 8px rgba(124, 58, 237, 0.35)',
                }}
              >
                <Bot size={18} color="#ffffff" />
              </div>
              <div>
                <div style={{ fontWeight: 700, fontSize: '0.92rem', color: '#ffffff', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <span>AI Assistant</span>
                  <span
                    style={{
                      fontSize: '0.65rem',
                      fontWeight: 600,
                      color: '#a78bfa',
                      background: 'rgba(139, 92, 246, 0.15)',
                      padding: '0.1rem 0.4rem',
                      borderRadius: '4px',
                      textTransform: 'uppercase',
                    }}
                  >
                    Global
                  </span>
                </div>
                <div style={{ fontSize: '0.72rem', color: '#94a3b8' }}>
                  General Q&A, Guidance & Learning
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
              <button
                type="button"
                onClick={handleResetConversation}
                title="Restart Conversation"
                aria-label="Restart Conversation"
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: '#94a3b8',
                  cursor: 'pointer',
                  padding: '0.3rem',
                  borderRadius: '4px',
                  display: 'flex',
                  alignItems: 'center',
                }}
              >
                <RotateCcw size={14} />
              </button>

              <button
                type="button"
                id="btn-close-floating-assistant"
                onClick={() => setIsOpen(false)}
                title="Minimize Assistant"
                aria-label="Minimize Assistant"
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: '#94a3b8',
                  cursor: 'pointer',
                  padding: '0.3rem',
                  borderRadius: '4px',
                  display: 'flex',
                  alignItems: 'center',
                }}
              >
                <Minimize2 size={15} />
              </button>
            </div>
          </div>

          {/* Messages Area */}
          <div
            style={{
              flex: 1,
              overflowY: 'auto',
              padding: '1.25rem',
              display: 'flex',
              flexDirection: 'column',
              gap: '1rem',
            }}
          >
            {messages.map((msg) => {
              const isAssistant = msg.role === 'assistant';
              return (
                <div
                  key={msg.id}
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: isAssistant ? 'flex-start' : 'flex-end',
                    gap: '0.25rem',
                  }}
                >
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'flex-start',
                      gap: '0.5rem',
                      maxWidth: '88%',
                      flexDirection: isAssistant ? 'row' : 'row-reverse',
                    }}
                  >
                    <div
                      style={{
                        width: 26,
                        height: 26,
                        borderRadius: '8px',
                        background: isAssistant ? 'rgba(139, 92, 246, 0.2)' : 'rgba(99, 102, 241, 0.25)',
                        border: isAssistant ? '1px solid rgba(139, 92, 246, 0.35)' : '1px solid rgba(99, 102, 241, 0.4)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        flexShrink: 0,
                        marginTop: '2px',
                      }}
                    >
                      {isAssistant ? <Bot size={14} color="#c4b5fd" /> : <UserIcon size={14} color="#818cf8" />}
                    </div>

                    <div
                      style={{
                        padding: '0.75rem 0.95rem',
                        borderRadius: isAssistant ? '4px 12px 12px 12px' : '12px 4px 12px 12px',
                        background: isAssistant
                          ? msg.isError
                            ? 'rgba(239, 68, 68, 0.15)'
                            : 'rgba(22, 30, 52, 0.7)'
                          : 'linear-gradient(135deg, #4f46e5, #4338ca)',
                        border: isAssistant
                          ? msg.isError
                            ? '1px solid rgba(239, 68, 68, 0.3)'
                            : '1px solid rgba(255, 255, 255, 0.08)'
                          : '1px solid rgba(99, 102, 241, 0.4)',
                        color: msg.isError ? '#fca5a5' : '#f8fafc',
                        fontSize: '0.84rem',
                        lineHeight: 1.5,
                        wordBreak: 'break-word',
                        whiteSpace: 'pre-wrap',
                      }}
                    >
                      {msg.content}
                    </div>
                  </div>

                  <span style={{ fontSize: '0.68rem', color: '#64748b', padding: '0 0.5rem' }}>
                    {msg.timestamp}
                  </span>
                </div>
              );
            })}

            {isLoading && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#a78bfa', fontSize: '0.82rem' }}>
                <Sparkles size={14} className="animate-spin" />
                <span>Thinking...</span>
              </div>
            )}

            {errorMessage && (
              <div
                style={{
                  padding: '0.5rem 0.75rem',
                  borderRadius: '6px',
                  background: 'rgba(239, 68, 68, 0.15)',
                  border: '1px solid rgba(239, 68, 68, 0.3)',
                  color: '#fca5a5',
                  fontSize: '0.78rem',
                }}
              >
                Service message: {errorMessage}
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Suggested Prompts if start of conversation */}
          {messages.length <= 1 && (
            <div style={{ padding: '0 1rem 0.75rem 1rem', display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
              <span style={{ fontSize: '0.72rem', fontWeight: 600, color: '#64748b' }}>
                Suggested Questions:
              </span>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
                {SUGGESTED_QUESTIONS.map((q, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => handleSendMessage(q)}
                    style={{
                      background: 'rgba(139, 92, 246, 0.1)',
                      border: '1px solid rgba(139, 92, 246, 0.25)',
                      borderRadius: '6px',
                      padding: '0.35rem 0.6rem',
                      fontSize: '0.74rem',
                      color: '#c4b5fd',
                      cursor: 'pointer',
                      textAlign: 'left',
                      transition: 'all 0.15s ease',
                    }}
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Input Footer */}
          <div
            style={{
              padding: '0.85rem 1rem',
              background: 'rgba(10, 14, 26, 0.95)',
              borderTop: '1px solid rgba(255, 255, 255, 0.08)',
              display: 'flex',
              gap: '0.5rem',
              alignItems: 'flex-end',
            }}
          >
            <textarea
              ref={inputRef}
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask anything or request guidance..."
              rows={1}
              style={{
                flex: 1,
                resize: 'none',
                background: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: '8px',
                padding: '0.55rem 0.75rem',
                color: '#f8fafc',
                fontSize: '0.825rem',
                fontFamily: 'inherit',
                outline: 'none',
                minHeight: '38px',
                maxHeight: '90px',
              }}
            />

            <button
              type="button"
              id="btn-floating-assistant-send"
              onClick={() => handleSendMessage()}
              disabled={!inputMessage.trim() || isLoading}
              aria-label="Send message"
              style={{
                width: '38px',
                height: '38px',
                borderRadius: '8px',
                background: inputMessage.trim() && !isLoading ? '#7c3aed' : 'rgba(255, 255, 255, 0.08)',
                border: 'none',
                color: inputMessage.trim() && !isLoading ? '#ffffff' : '#64748b',
                cursor: inputMessage.trim() && !isLoading ? 'pointer' : 'default',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                transition: 'all 0.15s ease',
                flexShrink: 0,
              }}
            >
              <Send size={15} />
            </button>
          </div>
        </div>
      )}
    </aside>
  );
};

'use client';

import { useState, useRef, useEffect } from 'react';
import { createClient } from '@/lib/supabase/client';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Send, Loader, Plus } from 'lucide-react';
import { generateChatTitle } from '@/lib/utils/timezone';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

interface ChatInterfaceProps {
  user: any;
  sessionId?: string;
  onNewChat?: () => void;
}

export default function ChatInterface({ user, sessionId: initialSessionId, onNewChat }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string>('');
  const [sessionTitle, setSessionTitle] = useState<string>('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Track initial session ID and load it
  useEffect(() => {
    if (initialSessionId) {
      setSessionId(initialSessionId);
    }
  }, [initialSessionId]);

  // Load existing chat session when sessionId changes
  useEffect(() => {
    const loadSession = async () => {
      if (!sessionId) {
        return;
      }
      
      const supabase = createClient();
      const { data, error } = await supabase
        .from('chat_history')
        .select('*')
        .eq('id', sessionId)
        .single();

      if (error) {
        console.error('Error loading session:', error);
        return;
      }

      if (data) {
        setSessionTitle(data.title);
        setMessages(data.messages || []);
      }
    };

    loadSession();
  }, [sessionId]);

  // Create a new chat session only when explicitly needed
  const createNewSession = async (firstMessage?: string) => {
    const supabase = createClient();
    
    // Generate title from first message or use default
    let title = 'New Chat';
    if (firstMessage && firstMessage.trim()) {
      const words = firstMessage.trim().split(' ').slice(0, 5).join(' ');
      title = words.length > 0 ? words : 'New Chat';
    }

    const { data, error } = await supabase
      .from('chat_history')
      .insert({
        user_id: user?.id,
        title: title,
        messages: [],
      })
      .select()
      .single();

    if (data) {
      setSessionId(data.id);
      setSessionTitle(data.title);
      setMessages([]);
    }

    return data?.id;
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!input.trim()) return;

    // Create new session if needed, pass first message as title
    let currentSessionId = sessionId;
    if (!currentSessionId) {
      const newSessionId = await createNewSession(input);
      setSessionId(newSessionId || '');
      return; // Will retry with new session
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date().toISOString(),
    };

    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    setInput('');
    setLoading(true);

    try {
      // Call your backend API endpoint
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: input,
          sessionId: currentSessionId,
          userId: user?.id,
        }),
      });

      const data = await response.json();

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.response || 'Sorry, I could not process your request.',
        timestamp: new Date().toISOString(),
      };

      const updatedMessages = [...newMessages, assistantMessage];
      setMessages(updatedMessages);

      // Save to chat history
      const supabase = createClient();
      await supabase
        .from('chat_history')
        .update({
          messages: updatedMessages,
          updated_at: new Date().toISOString(),
        })
        .eq('id', currentSessionId);
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'An error occurred while processing your request. Please try again.',
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="bg-gray-50 dark:bg-slate-800/50 border-gray-200 dark:border-slate-700/50 p-6">
      {/* Header */}
      <div className="border-b border-gray-200 p-4 flex items-center justify-between">
        <h3 className="text-sm font-semibold black">{sessionTitle || 'New Chat'}</h3>
        <Button
          onClick={() => {
            setMessages([]);
            setSessionId('');
            setSessionTitle('');
            if (onNewChat) onNewChat();
          }}
          variant="ghost"
          size="sm"
          className="black hover:text-blue-400"
        >
          <Plus className="w-4 h-4 mr-1" />
          New
        </Button>
      </div>

      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full black">
            <div className="text-center">
              <p className="mb-2">Start a conversation about disaster management</p>
              <p className="text-sm">Ask me about disaster types, affected areas, or response strategies</p>
            </div>
          </div>
        ) : (
          messages.map(message => (
            <div
              key={message.id}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-xs lg:max-w-md px-4 py-3 rounded-lg ${
                  message.role === 'user'
                    ? 'bg-blue-600 text-white rounded-br-none'
                    : 'bg-gray-50 text-black rounded-bl-none'
                }`}
              >
                <p className="text-sm">{message.content}</p>
                <span className="text-xs opacity-70 mt-1 block">
                  {new Date(message.timestamp).toLocaleTimeString()}
                </span>
              </div>
            </div>
          ))
        )}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-slate-700 text-gray-100 px-4 py-3 rounded-lg rounded-bl-none flex items-center gap-2">
              <Loader className="w-4 h-4 animate-spin" />
              <span className="text-sm">Analyzing your query...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t border-slate-700/50 p-4">
        <form onSubmit={handleSendMessage} className="flex gap-2">
          <Input
            type="text"
            placeholder="Ask about disaster updates..."
            value={input}
            onChange={e => setInput(e.target.value)}
            disabled={loading}
            className="bg-slate-700/50 border-slate-600 text-white placeholder-gray-400 focus:border-blue-500"
          />
          <Button
            type="submit"
            disabled={loading || !input.trim()}
            className="bg-blue-600 hover:bg-blue-700 text-white"
          >
            <Send className="w-4 h-4" />
          </Button>
        </form>
      </div>
    </Card>
  );
}

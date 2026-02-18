'use client';

import { useEffect, useState } from 'react';
import { createClient } from '@/lib/supabase/client';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Trash2, Plus, MessageCircle } from 'lucide-react';

interface ChatSession {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

interface ChatHistorySidebarProps {
  onSelectSession: (sessionId: string) => void;
  onNewChat: () => void;
  selectedSessionId?: string;
}

export default function ChatHistorySidebar({ onSelectSession, onNewChat, selectedSessionId }: ChatHistorySidebarProps) {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchSessions = async () => {
    const supabase = createClient();
    const {
      data: { user },
    } = await supabase.auth.getUser();

    if (user) {
      const { data } = await supabase
        .from('chat_history')
        .select('id, title, created_at, updated_at')
        .eq('user_id', user.id)
        .order('updated_at', { ascending: false })
        .limit(20);

      if (data) {
        setSessions(data);
      }
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchSessions();
  }, []);

  const deleteSession = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    const supabase = createClient();
    await supabase.from('chat_history').delete().eq('id', id);
    setSessions(sessions.filter(s => s.id !== id));
  };

  const handleNewChat = () => {
    onNewChat();
    fetchSessions();
  };

  return (
    <div className="w-64 bg-slate-900/50 border-r border-slate-700/50 p-4 flex flex-col h-screen">
      <div className="mb-6">
        <Button 
          onClick={handleNewChat}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          New Chat
        </Button>
      </div>

      <div className="flex-1 overflow-y-auto space-y-2">
        <h3 className="text-sm font-semibold text-gray-400 px-2 mb-4">Chat History</h3>
        {loading ? (
          <div className="text-gray-400 text-sm px-2">Loading...</div>
        ) : sessions.length > 0 ? (
          sessions.map(session => (
            <div
              key={session.id}
              onClick={() => onSelectSession(session.id)}
              className={`group p-3 rounded-lg transition-all cursor-pointer ${
                selectedSessionId === session.id
                  ? 'bg-blue-600/20 border border-blue-500/30'
                  : 'hover:bg-slate-800/50'
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <MessageCircle className="w-3 h-3 text-blue-400 flex-shrink-0" />
                    <p className="text-sm text-gray-200 truncate">{session.title}</p>
                  </div>
                  <p className="text-xs text-gray-500 mt-1 ml-5">
                    {new Date(session.created_at).toLocaleDateString()}
                  </p>
                </div>
                <button
                  onClick={(e) => deleteSession(e, session.id)}
                  className="opacity-0 group-hover:opacity-100 transition-opacity p-1 hover:bg-red-500/20 rounded"
                >
                  <Trash2 className="w-4 h-4 text-red-400" />
                </button>
              </div>
            </div>
          ))
        ) : (
          <div className="text-gray-400 text-sm px-2">No chat history yet</div>
        )}
      </div>

      {/* User Info */}
      <div className="border-t border-slate-700/50 pt-4 mt-4">
        <Button variant="outline" className="w-full text-gray-300 border-slate-600 hover:bg-slate-800/50">
          Sign Out
        </Button>
      </div>
    </div>
  );
}

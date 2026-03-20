'use client';

import { useEffect, useState } from 'react';
import { createClient } from '@/lib/supabase/client';
import { redirect } from 'next/navigation';
import DisasterStatusOverview from '@/components/DisasterStatusOverview';
import AdvancedVisualizations from '@/components/AdvancedVisualizations';
import ChatHistorySidebar from '@/components/ChatHistorySidebar';
import ChatInterface from '@/components/ChatInterface';
import ChatModal from '@/components/ChatModal';
import TopNavigation from '@/components/TopNavigation';

export default function DashboardPage() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [chatModalOpen, setChatModalOpen] = useState(false);
  const [selectedSessionId, setSelectedSessionId] = useState<string | undefined>();

  useEffect(() => {
    const checkAuth = async () => {
      const supabase = createClient();
      const {
        data: { user: currentUser },
      } = await supabase.auth.getUser();

      if (!currentUser) {
        redirect('/auth/login');
      }

      setUser(currentUser);
      setLoading(false);
    };

    checkAuth();
  }, []);

  const handleSelectSession = (sessionId: string) => {
    console.log('[v0] Dashboard: Select session', sessionId);
    setSelectedSessionId(sessionId);
    setChatModalOpen(true);
  };

  const handleNewChat = () => {
    console.log('[v0] Dashboard: New chat');
    setSelectedSessionId(undefined);
  };

  const handleOpenChat = () => {
    setChatModalOpen(true);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-white dark:bg-gradient-to-br dark:from-slate-950 dark:via-slate-900 dark:to-slate-950">
        <div className="animate-spin">
          <svg className="w-12 h-12 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" opacity="0.3" />
            <path d="M12 2a10 10 0 0 1 10 10" strokeWidth="2" strokeLinecap="round" />
          </svg>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white dark:bg-gradient-to-br dark:from-slate-950 dark:via-slate-900 dark:to-slate-950 text-foreground">
      <TopNavigation 
        onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
        onOpenChat={handleOpenChat}
      />

      <div className="flex flex-1">
        {/* Chat Sidebar */}
        {sidebarOpen && (
          <ChatHistorySidebar 
            onSelectSession={handleSelectSession}
            onNewChat={handleNewChat}
            selectedSessionId={selectedSessionId}
          />
        )}

        {/* Main Content */}
        <div className="flex-1 overflow-auto">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
            {/* Disaster Status Overview */}
            <section>
              <h1 className="text-3xl font-bold mb-6 bg-gradient-to-r from-blue-500 to-cyan-500 dark:from-blue-400 dark:to-cyan-400 bg-clip-text text-transparent">
                Disaster Management Dashboard
              </h1>
              <DisasterStatusOverview />
            </section>

            {/* Advanced Visualizations */}
            <section>
              <h2 className="text-2xl font-bold mb-6 text-gray-900 dark:text-gray-100">Analytics & Insights</h2>
              <AdvancedVisualizations />
            </section>

            {/* Chat Interface */}
            <section>
              <h2 className="text-2xl font-bold mb-6 text-gray-900 dark:text-gray-100">AI Disaster Assistant</h2>
              <ChatInterface 
                user={user} 
                sessionId={selectedSessionId}
                onNewChat={handleNewChat}
              />
            </section>
          </div>
        </div>
      </div>

      {/* Chat Modal - Alternative modal view */}
      <ChatModal
        isOpen={chatModalOpen}
        onClose={() => setChatModalOpen(false)}
        user={user}
        selectedSessionId={selectedSessionId}
        onSessionSelected={handleSelectSession}
      />
    </div>
  );
}

'use client';

import { Menu, LogOut, Bell, MessageCircle, Sun, Moon } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { createClient } from '@/lib/supabase/client';
import { useRouter } from 'next/navigation';
import { useTheme } from '@/lib/context/ThemeContext';

interface TopNavigationProps {
  onToggleSidebar: () => void;
  onOpenChat: () => void;
}

export default function TopNavigation({ onToggleSidebar, onOpenChat }: TopNavigationProps) {
  const router = useRouter();
  const { theme, toggleTheme } = useTheme();

  const handleSignOut = async () => {
    const supabase = createClient();
    await supabase.auth.signOut();
    router.push('/auth/login');
  };

  return (
    <nav className="bg-white dark:bg-slate-900/80 border-b border-gray-200 dark:border-slate-700/50 backdrop-blur-md sticky top-0 z-40">
      <div className="flex items-center justify-between px-6 py-4">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={onToggleSidebar}
            className="text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
          >
            <Menu className="w-5 h-5" />
          </Button>

          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">DM</span>
            </div>
            <h1 className="text-lg font-bold bg-gradient-to-r from-blue-500 to-cyan-500 dark:from-blue-400 dark:to-cyan-400 bg-clip-text text-transparent">
              Disaster Manager
            </h1>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <Button
            onClick={onOpenChat}
            className="bg-blue-600 hover:bg-blue-700 text-white flex items-center gap-2"
          >
            <MessageCircle className="w-5 h-5" />
            AI Chat
          </Button>

          <Button
            variant="ghost"
            size="icon"
            className="text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white relative"
          >
            <Bell className="w-5 h-5" />
            <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
          </Button>

          <Button
            variant="ghost"
            size="icon"
            onClick={toggleTheme}
            className="text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
            title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
          >
            {theme === 'dark' ? (
              <Sun className="w-5 h-5" />
            ) : (
              <Moon className="w-5 h-5" />
            )}
          </Button>

          <Button
            variant="ghost"
            size="icon"
            onClick={handleSignOut}
            className="text-gray-600 dark:text-gray-400 hover:text-red-500 dark:hover:text-red-400 dark:hover:bg-red-500/10"
          >
            <LogOut className="w-5 h-5" />
          </Button>
        </div>
      </div>
    </nav>
  );
}

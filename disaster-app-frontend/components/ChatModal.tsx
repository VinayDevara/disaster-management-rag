'use client';

import { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import ChatInterface from '@/components/ChatInterface';

interface ChatModalProps {
  isOpen: boolean;
  onClose: () => void;
  user: any;
  selectedSessionId?: string;
  onSessionSelected?: (sessionId: string) => void;
}

export default function ChatModal({
  isOpen,
  onClose,
  user,
  selectedSessionId,
  onSessionSelected,
}: ChatModalProps) {
  const [currentSessionId, setCurrentSessionId] = useState<string>('');

  // Update session when selectedSessionId changes
  useEffect(() => {
    if (selectedSessionId) {
      setCurrentSessionId(selectedSessionId);
    }
  }, [selectedSessionId, isOpen]);

  const handleNewChat = () => {
    setCurrentSessionId('');
  };

  if (!isOpen) return null;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl h-[85vh] bg-slate-800 border-slate-700 flex flex-col p-0">
        <DialogHeader className="border-b border-slate-700/50 px-6 py-4">
          <DialogTitle className="text-white text-xl">AI Disaster Assistant</DialogTitle>
        </DialogHeader>
        <div className="flex-1 overflow-hidden">
          <ChatInterface
            user={user}
            sessionId={currentSessionId}
            onNewChat={handleNewChat}
          />
        </div>
      </DialogContent>
    </Dialog>
  );
}

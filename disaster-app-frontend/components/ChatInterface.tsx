'use client';

import { useState, useRef, useEffect } from 'react';
import { createClient } from '@/lib/supabase/client';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Send, Loader, Plus, Activity, ShieldAlert, AlertTriangle, CheckCircle2, ChevronUp, ChevronDown } from 'lucide-react';
import { generateChatTitle } from '@/lib/utils/timezone';
import Markdown from '@/components/Markdown';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  trajectory_id?: string;
}

interface AuditDetails {
  transition: string;
  from_step: number;
  to_step: number;
  premise: string;
  hypothesis: string;
  classification: 'entailment' | 'neutral' | 'contradiction';
  scores: { contradiction: number; entailment?: number; neutral?: number };
  reasoning: string;
}

interface AuditResult {
  has_fault: boolean;
  faulty_step: number | null;
  explanation: string;
  details: AuditDetails[];
  audited_by: string;
  error?: string;
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

  // Auditing States
  const [auditingStates, setAuditingStates] = useState<Record<string, boolean>>({});
  const [auditResults, setAuditResults] = useState<Record<string, AuditResult>>({});
  const [expandedAudits, setExpandedAudits] = useState<Record<string, boolean>>({});
  const [auditMethods, setAuditMethods] = useState<Record<string, 'nli' | 'llm' | 'full_llm'>>({});

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
        trajectory_id: data.trajectory_id,
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

  const handleAuditTrajectory = async (messageId: string, trajectoryId: string) => {
    setAuditingStates(prev => ({ ...prev, [messageId]: true }));
    const method = auditMethods[messageId] || 'nli';
    try {
      const response = await fetch('/api/audit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          trajectory_id: trajectoryId,
          method: method
        }),
      });

      if (!response.ok) {
        throw new Error(`Error auditing trajectory: ${response.statusText}`);
      }

      const data = await response.json();
      setAuditResults(prev => ({ ...prev, [messageId]: data }));
    } catch (error: any) {
      console.error('Trajectory audit failed:', error);
      setAuditResults(prev => ({
        ...prev,
        [messageId]: {
          has_fault: false,
          faulty_step: null,
          explanation: '',
          details: [],
          audited_by: method,
          error: error.message || 'Failed to analyze trajectory.'
        }
      }));
    } finally {
      setAuditingStates(prev => ({ ...prev, [messageId]: false }));
    }
  };

  return (
    <Card className="bg-gray-50 dark:bg-slate-800/50 border-gray-200 dark:border-slate-700/50 p-6 flex flex-col h-full min-h-[600px] max-h-[750px]">
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
              className={`flex flex-col ${message.role === 'user' ? 'items-end' : 'items-start'} space-y-1.5`}
            >
              <div
                className={`max-w-xs lg:max-w-md px-4 py-3 rounded-lg ${
                  message.role === 'user'
                    ? 'bg-blue-600 text-white rounded-br-none'
                    : 'bg-white dark:bg-slate-700/60 border border-slate-100 dark:border-slate-700 text-black dark:text-white rounded-bl-none'
                }`}
              >
                {message.role === 'user' ? (
                  <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                ) : (
                  <Markdown content={message.content} />
                )}
                <span className="text-[10px] opacity-60 mt-1.5 block text-right">
                  {new Date(message.timestamp).toLocaleTimeString()}
                </span>
              </div>

              {/* Trajectory Auditing Section */}
              {message.role === 'assistant' && message.trajectory_id && (
                <div className="w-full max-w-md lg:max-w-lg mt-2 text-xs">
                  <div className="bg-slate-100/50 dark:bg-slate-900/40 rounded-lg p-3 border border-slate-200/40 dark:border-slate-800/40 flex flex-col gap-2 shadow-sm">
                    {/* Control Row */}
                    <div className="flex items-center justify-between gap-3 flex-wrap">
                      <div className="flex items-center gap-1.5 text-slate-500 dark:text-slate-400">
                        <Activity className="w-3.5 h-3.5 text-blue-500 animate-pulse" />
                        <span className="font-mono text-[10px] bg-slate-200/50 dark:bg-slate-800 px-1.5 py-0.5 rounded">
                          {message.trajectory_id}
                        </span>
                      </div>
                      
                      <div className="flex items-center gap-2">
                        {/* Audit Strategy Dropdown */}
                        <select
                          value={auditMethods[message.id] || 'nli'}
                          onChange={(e) => setAuditMethods(prev => ({ ...prev, [message.id]: e.target.value as any }))}
                          className="bg-white dark:bg-slate-800 border border-slate-250 dark:border-slate-700 rounded px-2 py-0.5 text-[10px] text-slate-700 dark:text-slate-300 focus:outline-none focus:ring-1 focus:ring-blue-500 cursor-pointer"
                          disabled={auditingStates[message.id]}
                        >
                          <option value="nli">Natural Language Inference (Local NLI)</option>
                          <option value="llm">Step LLM Classifier</option>
                          <option value="full_llm">Full Trajectory LLM Audit</option>
                        </select>

                        <Button
                          onClick={() => handleAuditTrajectory(message.id, message.trajectory_id!)}
                          disabled={auditingStates[message.id]}
                          size="sm"
                          variant="ghost"
                          className="h-6 text-[10px] bg-blue-50 dark:bg-blue-950/40 hover:bg-blue-100 dark:hover:bg-blue-900/40 border border-blue-150 dark:border-blue-900/50 text-blue-600 dark:text-blue-400 font-semibold px-2"
                        >
                          {auditingStates[message.id] ? (
                            <>
                              <Loader className="w-3 h-3 mr-1 animate-spin" />
                              Auditing...
                            </>
                          ) : (
                            <>
                              <ShieldAlert className="w-3 h-3 mr-1" />
                              Audit Trajectory
                            </>
                          )}
                        </Button>
                      </div>
                    </div>

                    {/* Results Panel */}
                    {auditResults[message.id] && (
                      <div className="mt-2 bg-white dark:bg-slate-900/60 rounded-lg p-3.5 border border-slate-200/50 dark:border-slate-800/80 shadow-inner flex flex-col gap-3 transition-all duration-300">
                        {auditResults[message.id].error ? (
                          <div className="flex items-start gap-2 text-red-500">
                            <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                            <div>
                              <p className="font-semibold">Audit Execution Failed</p>
                              <p className="text-slate-400 mt-0.5">{auditResults[message.id].error}</p>
                            </div>
                          </div>
                        ) : (
                          <div className="space-y-3">
                            {/* Badges Header */}
                            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-2 gap-2 flex-wrap">
                              <div>
                                {auditResults[message.id].has_fault ? (
                                  <span className="inline-flex items-center gap-1 bg-amber-50 dark:bg-amber-950/30 text-amber-600 dark:text-amber-400 px-2 py-0.5 rounded-full font-bold border border-amber-100 dark:border-amber-900/40">
                                    <AlertTriangle className="w-3 h-3" />
                                    Fault Localized: Step {auditResults[message.id].faulty_step}
                                  </span>
                                ) : (
                                  <span className="inline-flex items-center gap-1 bg-emerald-50 dark:bg-emerald-950/30 text-emerald-600 dark:text-emerald-400 px-2 py-0.5 rounded-full font-bold border border-emerald-100 dark:border-emerald-900/40">
                                    <CheckCircle2 className="w-3 h-3" />
                                    Logically Sound
                                  </span>
                                )}
                              </div>
                              <span className="text-[9px] text-slate-400 dark:text-slate-500 font-medium">
                                Audited via: <span className="font-mono bg-slate-100 dark:bg-slate-800 px-1 py-0.5 rounded text-slate-500 dark:text-slate-400">{auditResults[message.id].audited_by}</span>
                              </span>
                            </div>

                            {/* Summary Text */}
                            <div className="text-slate-700 dark:text-slate-350 leading-relaxed font-medium">
                              {auditResults[message.id].explanation}
                            </div>

                            {/* Contradiction details box */}
                            {auditResults[message.id].has_fault && (
                              <div className="bg-amber-50/20 dark:bg-amber-950/10 border border-amber-200/50 dark:border-amber-900/20 rounded-lg p-3 space-y-2">
                                <p className="font-bold text-amber-700 dark:text-amber-400 flex items-center gap-1">
                                  <ShieldAlert className="w-3.5 h-3.5" />
                                  Logical Discrepancy details:
                                </p>
                                {(() => {
                                  const faultStep = auditResults[message.id].details.find(
                                    d => d.to_step === auditResults[message.id].faulty_step
                                  );
                                  if (!faultStep) return null;
                                  return (
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-1 text-[10px]">
                                      <div className="bg-white dark:bg-slate-900 p-2.5 rounded border border-slate-200/60 dark:border-slate-800">
                                        <span className="font-bold text-slate-400 uppercase block mb-1 text-[8px] tracking-wider">Premise (Step {faultStep.from_step} Context)</span>
                                        <pre className="whitespace-pre-wrap font-mono text-slate-600 dark:text-slate-450 max-h-36 overflow-y-auto leading-normal text-[9px]">
                                          {faultStep.premise}
                                        </pre>
                                      </div>
                                      <div className="bg-white dark:bg-slate-900 p-2.5 rounded border border-amber-200/80 dark:border-amber-900/30">
                                        <span className="font-bold text-amber-600 dark:text-amber-500 uppercase block mb-1 text-[8px] tracking-wider">Hypothesis (Step {faultStep.to_step} Assertion)</span>
                                        <pre className="whitespace-pre-wrap font-mono text-amber-700 dark:text-amber-500 max-h-36 overflow-y-auto leading-normal text-[9px]">
                                          {faultStep.hypothesis}
                                        </pre>
                                      </div>
                                    </div>
                                  );
                                })()}
                              </div>
                            )}

                            {/* Toggle Detailed Breakdown */}
                            <div className="pt-1.5">
                              <Button
                                onClick={() => setExpandedAudits(prev => ({ ...prev, [message.id]: !prev[message.id] }))}
                                variant="ghost"
                                size="sm"
                                className="h-5 text-[9px] text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200 p-0 flex items-center gap-1 focus:bg-transparent hover:bg-transparent"
                              >
                                {expandedAudits[message.id] ? (
                                  <>
                                    <ChevronUp className="w-3 h-3" />
                                    Hide Transition Timeline
                                  </>
                                ) : (
                                  <>
                                    <ChevronDown className="w-3 h-3" />
                                    Show Transition Timeline ({auditResults[message.id].details.length} transitions)
                                  </>
                                )}
                              </Button>

                              {expandedAudits[message.id] && (
                                <div className="mt-3 border-l border-slate-200 dark:border-slate-800 pl-3 space-y-3.5 pt-1">
                                  {auditResults[message.id].details.map((detail, index) => (
                                    <div key={index} className="relative">
                                      {/* Dots */}
                                      <span className={`absolute -left-[16.5px] top-1 w-1.5 h-1.5 rounded-full ring-2 ring-white dark:ring-slate-900 ${
                                        detail.classification === 'contradiction'
                                          ? 'bg-amber-500 animate-ping'
                                          : detail.classification === 'entailment'
                                          ? 'bg-emerald-500'
                                          : 'bg-slate-450'
                                      }`} />
                                      
                                      <div className="bg-slate-50/50 dark:bg-slate-900/20 p-2.5 rounded-lg border border-slate-200/20 dark:border-slate-800/40">
                                        <div className="flex items-center justify-between gap-2 flex-wrap mb-1">
                                          <span className="font-semibold text-slate-800 dark:text-slate-200 text-[10px]">
                                            {detail.transition}
                                          </span>
                                          <span className={`px-1.5 py-0.5 rounded text-[8px] font-bold border ${
                                            detail.classification === 'contradiction'
                                              ? 'bg-amber-50 text-amber-600 border-amber-100 dark:bg-amber-950/20 dark:text-amber-400 dark:border-amber-900/30'
                                              : detail.classification === 'entailment'
                                              ? 'bg-emerald-50 text-emerald-600 border-emerald-100 dark:bg-emerald-950/20 dark:text-emerald-400 dark:border-emerald-900/30'
                                              : 'bg-slate-100 text-slate-500 border-slate-200 dark:bg-slate-850 dark:text-slate-400 dark:border-slate-800'
                                          }`}>
                                            {detail.classification.toUpperCase()}
                                          </span>
                                        </div>
                                        <p className="text-slate-500 dark:text-slate-400 leading-relaxed text-[9px]">
                                          {detail.reasoning}
                                        </p>
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              )}
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

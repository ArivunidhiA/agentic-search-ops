/** Operator chat component with command allowlist (NOT free-form chatbot) */

import { useState, useRef, useEffect } from 'react';
import { Send, AlertCircle } from 'lucide-react';
import { escapeHtml } from '../../utils/formatters';

interface ChatMessage {
  type: 'command' | 'response' | 'error';
  content: string;
  timestamp: Date;
}

// ALLOWLIST: Only these commands are allowed
const ALLOWED_COMMANDS = [
  'status',
  'progress',
  'why discard',
  'pause',
  'resume',
  'failures',
] as const;

type AllowedCommand = typeof ALLOWED_COMMANDS[number];

interface OperatorChatProps {
  jobId?: string;
  onCommand?: (command: string) => Promise<string>;
}

export const OperatorChat = ({ jobId, onCommand }: OperatorChatProps) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const isCommandAllowed = (input: string): AllowedCommand | null => {
    const normalized = input.trim().toLowerCase();
    
    // Check exact matches first
    if (ALLOWED_COMMANDS.includes(normalized as AllowedCommand)) {
      return normalized as AllowedCommand;
    }
    
    // Check for "why discard [source]" pattern
    if (normalized.startsWith('why discard ')) {
      return 'why discard';
    }
    
    return null;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!input.trim()) return;
    
    const command = input.trim();
    const allowedCommand = isCommandAllowed(command);
    
    // Add user command to messages
    const userMessage: ChatMessage = {
      type: 'command',
      content: command,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsProcessing(true);

    if (!allowedCommand) {
      // Command not in allowlist
      const errorMessage: ChatMessage = {
        type: 'error',
        content: `Command not recognized. Allowed commands: ${ALLOWED_COMMANDS.join(', ')}`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
      setIsProcessing(false);
      return;
    }

    // Execute command
    try {
      let response = '';
      
      if (onCommand) {
        response = await onCommand(allowedCommand);
      } else {
        // Default responses for demo
        switch (allowedCommand) {
          case 'status':
            response = 'Job status: Running. Current step: EXECUTING';
            break;
          case 'progress':
            response = 'Progress: 45% complete. 23/50 documents processed.';
            break;
          case 'why discard':
            response = 'Source discarded due to low relevance score (0.23 < threshold 0.5)';
            break;
          case 'pause':
            response = 'Job will pause at next checkpoint.';
            break;
          case 'resume':
            response = 'Job resumed from checkpoint.';
            break;
          case 'failures':
            response = 'Top failure reasons: 1) Rate limit (5), 2) Invalid format (3), 3) Timeout (2)';
            break;
        }
      }
      
      const responseMessage: ChatMessage = {
        type: 'response',
        content: response,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, responseMessage]);
    } catch (err) {
      const errorMessage: ChatMessage = {
        type: 'error',
        content: err instanceof Error ? err.message : 'Command execution failed',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow flex flex-col h-[600px]">
      <div className="px-6 py-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900">Operator Chat</h3>
        <p className="text-xs text-gray-500 mt-1">
          Restricted command interface. Allowed: {ALLOWED_COMMANDS.join(', ')}
        </p>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 py-8">
            <p className="text-sm">No commands yet. Type a command to get started.</p>
            <p className="text-xs mt-2">Example: "status" or "progress"</p>
          </div>
        )}
        
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${msg.type === 'command' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-lg px-4 py-2 ${
                msg.type === 'command'
                  ? 'bg-primary-600 text-white'
                  : msg.type === 'error'
                  ? 'bg-red-50 text-red-800 border border-red-200'
                  : 'bg-gray-100 text-gray-900'
              }`}
            >
              <div
                dangerouslySetInnerHTML={{ __html: escapeHtml(msg.content) }}
                className="text-sm whitespace-pre-wrap"
              />
              <p className="text-xs opacity-70 mt-1">
                {msg.timestamp.toLocaleTimeString()}
              </p>
            </div>
          </div>
        ))}
        
        {isProcessing && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-lg px-4 py-2">
              <p className="text-sm text-gray-600">Processing...</p>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSubmit} className="px-4 py-4 border-t border-gray-200">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Enter command..."
            className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            disabled={isProcessing}
          />
          <button
            type="submit"
            disabled={isProcessing || !input.trim()}
            className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
        <p className="text-xs text-gray-500 mt-2">
          <AlertCircle className="w-3 h-3 inline mr-1" />
          Only allowlisted commands are accepted. Free-form input is not allowed.
        </p>
      </form>
    </div>
  );
};

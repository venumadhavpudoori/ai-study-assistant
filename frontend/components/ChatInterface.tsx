"use client";

import React, { useState, useEffect, useRef, useMemo } from 'react';
import { chatService } from '@/lib/api';
import CitationLink from './CitationLink';

interface Message {
    id: number;
    role: 'user' | 'assistant';
    content: string;
    sources?: Array<{ document_id: number; page_number: number }>;
}

export default function ChatInterface({ conversationId }: { conversationId: string }) {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const scrollRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        fetchMessages();
    }, [conversationId]);

    useEffect(() => {
        scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const fetchMessages = async () => {
        try {
            const data = await chatService.getMessages(conversationId);
            setMessages(data);
        } catch (err) {
            console.error("Failed to load messages", err);
        }
    };

    const handleSend = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim()) return;

        const text = input;
        setInput('');
        setIsLoading(true);

        try {
            const response = await chatService.sendMessage(conversationId, text);
            // Optimistically add user message and then the response
            setMessages(prev => [
                ...prev,
                { id: Date.now(), role: 'user', content: text },
                response
            ]);
        } catch (err) {
            alert("Failed to send message");
        } finally {
            setIsLoading(false);
        }
    };

    const renderContent = (content: string, sources?: any[]) => {
        if (!sources) return <>{content}</>;

        // Regex to find [n] citations
        const parts = content.split(/(\[\d+\])/g);
        return parts.map((part, i) => {
            const match = part.match(/^\[(\d+)\]$/);
            if (match) {
                const index = parseInt(match[1]) - 1;
                const source = sources[index];
                if (source) {
                    return <CitationLink key={i} citationIndex={index + 1} documentId={source.document_id} pageNumber={source.page_number} />;
                }
            }
            return part;
        });
    };

    return (
        <div className="flex flex-col h-full bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.length === 0 && (
                    <div className="h-full flex items-center justify-center text-gray-400 text-sm italic">
                        No messages yet. Ask a question about your documents!
                    </div>
                )}
                {messages.map((msg) => (
                    <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-[80%] p-3 rounded-lg ${
                            msg.role === 'user'
                            ? 'bg-blue-600 text-white rounded-br-none'
                            : 'bg-gray-100 text-gray-800 rounded-bl-none'
                        }`}>
                            <div className="text-sm leading-relaxed">
                                {renderContent(msg.content, msg.sources)}
                            </div>
                        </div>
                    </div>
                ))}
                <div ref={scrollRef} />
            </div>

            {/* Input Area */}
            <form onSubmit={handleSend} className="p-4 border-t border-gray-200 bg-gray-50">
                <div className="flex gap-2">
                    <input
                        type="text"
                        className="flex-1 p-2 rounded-md border border-gray-300 focus:ring-2 focus:ring-blue-500 outline-none"
                        placeholder="Ask a question..."
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        disabled={isLoading}
                    />
                    <button
                        type="submit"
                        disabled={isLoading}
                        className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:bg-blue-300 transition-colors"
                    >
                        {isLoading ? '...' : 'Send'}
                    </button>
                </div>
            </form>
        </div>
    );
}

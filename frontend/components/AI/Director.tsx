"use client";

import React, { useState } from 'react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Mic, Send, Sparkles } from 'lucide-react';

interface Message {
    role: 'user' | 'assistant';
    content: string;
}

export default function Director() {
    const [messages, setMessages] = useState<Message[]>([
        { role: 'assistant', content: 'Hello! I am your AI Music Director. How can I help you produce this track?' }
    ]);
    const [input, setInput] = useState('');

    const handleSend = () => {
        if (!input.trim()) return;

        const newMsg: Message = { role: 'user', content: input };
        setMessages([...messages, newMsg]);
        setInput('');

        // Mock response for now
        setTimeout(() => {
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: `I'm analyzing your request: "${input}". I can help you mix, mute tracks, or change the key.`
            }]);
        }, 1000);
    };

    return (
        <div className="flex flex-col h-full bg-zinc-900 border-l border-zinc-800 w-80">
            <div className="p-4 border-b border-zinc-800 flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-purple-400" />
                <span className="font-bold">AI Director</span>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.map((msg, i) => (
                    <div
                        key={i}
                        className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                        <div className={`max-w-[80%] p-3 rounded-lg text-sm ${msg.role === 'user'
                            ? 'bg-blue-600 text-white'
                            : 'bg-zinc-800 text-zinc-300'
                            }`}>
                            {msg.content}
                        </div>
                    </div>
                ))}
            </div>

            <div className="p-4 border-t border-zinc-800 flex gap-2">
                <Button variant="ghost" size="icon" className="text-zinc-400">
                    <Mic className="h-4 w-4" />
                </Button>
                <Input
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                    placeholder="Ask me anything..."
                    className="bg-zinc-800 border-zinc-700"
                />
                <Button size="icon" onClick={handleSend}>
                    <Send className="h-4 w-4" />
                </Button>
            </div>
        </div>
    );
}

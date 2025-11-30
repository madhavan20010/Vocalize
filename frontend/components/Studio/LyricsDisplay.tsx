"use client";

import React from 'react';
import { cn } from '@/lib/utils';

export interface LyricWord {
    word: string;
    start: number;
    end: number;
}

interface LyricsDisplayProps {
    lyrics: LyricWord[];
}

export default function LyricsDisplay({ lyrics }: LyricsDisplayProps) {
    if (!lyrics || lyrics.length === 0) {
        return (
            <div className="w-full h-48 flex items-center justify-center text-zinc-500 italic">
                No lyrics available
            </div>
        );
    }

    // Group words into lines for better readability
    // Since we don't have explicit line breaks, we'll group by ~8 words
    const lines: LyricWord[][] = [];
    let currentLine: LyricWord[] = [];

    lyrics.forEach((word, i) => {
        currentLine.push(word);
        if ((i + 1) % 8 === 0 || i === lyrics.length - 1) {
            lines.push(currentLine);
            currentLine = [];
        }
    });

    return (
        <div className="w-full h-64 bg-zinc-950/50 border border-zinc-800 rounded-lg overflow-hidden relative">
            <div className="absolute inset-0 overflow-y-auto p-6 space-y-4 scrollbar-thin scrollbar-thumb-zinc-700 scrollbar-track-transparent">
                {lines.map((line, lineIdx) => (
                    <p key={lineIdx} className="text-zinc-300 text-lg leading-relaxed text-center">
                        {line.map(w => w.word).join(' ')}
                    </p>
                ))}
            </div>
        </div>
    );
}

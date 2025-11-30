"use client";

import React from 'react';
import { Loader2 } from 'lucide-react';

interface ProgressBarProps {
    progress: number; // 0 to 100
    status: string;
    isVisible: boolean;
}

const ProgressBar: React.FC<ProgressBarProps> = ({ progress, status, isVisible }) => {
    if (!isVisible) return null;

    return (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center">
            <div className="bg-zinc-900 border border-zinc-800 p-8 rounded-2xl w-full max-w-md shadow-2xl">
                <div className="flex flex-col items-center gap-4 mb-6">
                    <div className="relative">
                        <div className="absolute inset-0 bg-blue-500 blur-xl opacity-20 rounded-full"></div>
                        <Loader2 className="h-12 w-12 text-blue-500 animate-spin relative z-10" />
                    </div>
                    <h3 className="text-xl font-bold text-white">Importing Track</h3>
                </div>

                <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                        <span className="text-zinc-400">{status}</span>
                        <span className="text-blue-400 font-mono">{Math.round(progress)}%</span>
                    </div>
                    <div className="h-2 bg-zinc-800 rounded-full overflow-hidden">
                        <div
                            className="h-full bg-blue-500 transition-all duration-300 ease-out"
                            style={{ width: `${progress}%` }}
                        />
                    </div>
                </div>

                <p className="text-xs text-zinc-500 mt-6 text-center">
                    This process involves AI stem separation and may take 1-2 minutes.
                </p>
            </div>
        </div>
    );
};

export default ProgressBar;

"use client";

import { useState } from 'react';
import { createClient } from '@/lib/supabase';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Music } from 'lucide-react';

export default function LoginPage() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const router = useRouter();
    const supabase = createClient();

    const handleLogin = async () => {
        setLoading(true);
        setError(null);
        try {
            const { error } = await supabase.auth.signInWithPassword({
                email,
                password,
            });
            if (error) throw error;
            router.push('/');
        } catch (e: any) {
            setError(e.message);
        } finally {
            setLoading(false);
        }
    };

    const handleSignUp = async () => {
        setLoading(true);
        setError(null);
        try {
            const { error } = await supabase.auth.signUp({
                email,
                password,
            });
            if (error) throw error;
            alert('Check your email for the confirmation link!');
        } catch (e: any) {
            setError(e.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="h-screen bg-black text-white flex items-center justify-center font-sans">
            <div className="w-full max-w-md p-8 bg-zinc-900 rounded-2xl border border-zinc-800 shadow-2xl">
                <div className="flex flex-col items-center gap-4 mb-8">
                    <div className="h-12 w-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center">
                        <Music className="h-6 w-6 text-white" />
                    </div>
                    <h1 className="text-2xl font-bold">Welcome to Vocalize</h1>
                    <p className="text-zinc-400 text-sm">Sign in to sync your projects across devices</p>
                </div>

                <div className="space-y-4">
                    {error && (
                        <div className="p-3 bg-red-900/20 border border-red-900 rounded-lg text-red-400 text-sm">
                            {error}
                        </div>
                    )}

                    <div>
                        <label className="block text-sm text-zinc-400 mb-1">Email</label>
                        <input
                            type="email"
                            className="w-full bg-zinc-800 border-zinc-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                        />
                    </div>

                    <div>
                        <label className="block text-sm text-zinc-400 mb-1">Password</label>
                        <input
                            type="password"
                            className="w-full bg-zinc-800 border-zinc-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                        />
                    </div>

                    <div className="flex gap-4 pt-4">
                        <Button
                            className="flex-1 bg-blue-600 hover:bg-blue-700"
                            onClick={handleLogin}
                            disabled={loading}
                        >
                            {loading ? 'Loading...' : 'Sign In'}
                        </Button>
                        <Button
                            variant="outline"
                            className="flex-1 border-zinc-700 hover:bg-zinc-800 text-white"
                            onClick={handleSignUp}
                            disabled={loading}
                        >
                            Sign Up
                        </Button>
                    </div>

                    <div className="text-center pt-4">
                        <button onClick={() => router.push('/')} className="text-xs text-zinc-500 hover:text-zinc-300">
                            Continue as Guest (Local Mode)
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}

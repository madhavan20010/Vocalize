"use client";

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Play, Pause, RotateCcw, Volume2, Mic, Settings, Sliders, Zap, Music, Mic2, Save, FolderOpen, Download, LogOut, User, Menu, X } from 'lucide-react';
import { createClient } from '@/lib/supabase';
import { useRouter } from 'next/navigation';
import { Button } from '../ui/button';
import { Slider } from '../ui/slider';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import Waveform from './Waveform';
import { motion, AnimatePresence } from 'framer-motion';

import LyricsDisplay, { LyricWord } from './LyricsDisplay';

interface Stems {
    vocals: string;
    drums: string;
    bass: string;
    other: string;
}

export default function StudioLayout() {
    // Project State
    const [url, setUrl] = useState('');
    const [isImporting, setIsImporting] = useState(false);
    const [importProgress, setImportProgress] = useState(0);
    const [importStatus, setImportStatus] = useState('');
    const [stems, setStems] = useState<Stems | null>(null);
    const [key, setKey] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    // Playback State
    const [isPlaying, setIsPlaying] = useState(false);
    const [currentTime, setCurrentTime] = useState(0);
    const [duration, setDuration] = useState(0);
    const wavesurferRefs = useRef<any[]>([]);
    const isSeekingRef = useRef(false);

    // Mixing State
    const [autotuneStrength, setAutotuneStrength] = useState([0]); // 0 to 100

    // Karaoke State
    const [lyrics, setLyrics] = useState<LyricWord[]>([]);
    const [isTranscribing, setIsTranscribing] = useState(false);

    // Project Management State
    const [volumes, setVolumes] = useState<{ [key: string]: number }>({ vocals: 1, drums: 1, bass: 1, other: 1 });
    const [showLoadModal, setShowLoadModal] = useState(false);
    const [showSaveModal, setShowSaveModal] = useState(false);
    const [projectName, setProjectName] = useState('');
    const [savedProjects, setSavedProjects] = useState<any[]>([]);

    // UI State
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

    // Auth State
    const [user, setUser] = useState<any>(null);
    const supabase = createClient();
    const router = useRouter();

    useEffect(() => {
        const checkUser = async () => {
            const { data: { user } } = await supabase.auth.getUser();
            setUser(user);
        };
        checkUser();
    }, []);

    const handleSignOut = async () => {
        await supabase.auth.signOut();
        setUser(null);
        router.push('/login');
    };

    // Clear refs when stems change
    useEffect(() => {
        wavesurferRefs.current = [];
        setCurrentTime(0);
        setDuration(0);
        setIsPlaying(false);
        setLyrics([]);
        setIsTranscribing(false);
    }, [stems]);

    const resetProject = () => {
        setUrl('');
        setStems(null);
        setKey(null);
        setError(null);
        setIsPlaying(false);
        setCurrentTime(0);
        setDuration(0);
        setAutotuneStrength([0]);
        setLyrics([]);
        setIsTranscribing(false);
        setVolumes({ vocals: 1, drums: 1, bass: 1, other: 1 });
        setIsMobileMenuOpen(false);
    };

    const handleSaveProject = async () => {
        if (!stems || !projectName.trim()) return;

        const name = projectName.trim();

        try {
            const res = await fetch('http://localhost:8000/projects/save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name,
                    audio_url: url,
                    stems,
                    lyrics,
                    key
                }),
            });
            const data = await res.json();
            if (data.status === 'success') {
                setShowSaveModal(false);
                setProjectName('');
                // Optional: Show a toast or small notification here
            } else {
                setError('Failed to save: ' + data.message);
            }
        } catch (e) {
            console.error(e);
            setError('Error saving project');
        }
    };

    const fetchProjects = async () => {
        try {
            const res = await fetch('http://localhost:8000/projects/list');
            const data = await res.json();
            setSavedProjects(data);
            setShowLoadModal(true);
            setIsMobileMenuOpen(false);
        } catch (e) {
            console.error(e);
            alert('Error listing projects');
        }
    };

    const handleLoadProject = async (id: string) => {
        try {
            const res = await fetch(`http://localhost:8000/projects/load/${id}`);
            const data = await res.json();
            if (data.status === 'success') {
                const p = data.data;
                setUrl(p.audio_url || '');
                setStems(p.stems);
                setKey(p.key);
                setLyrics(p.lyrics || []);
                setShowLoadModal(false);
                // Reset playback
                setIsPlaying(false);
                setCurrentTime(0);
            } else {
                setError('Failed to load: ' + data.message);
            }
        } catch (e) {
            console.error(e);
            setError('Error loading project');
        }
    };

    const handleExport = async (format: 'mp3' | 'mp4') => {
        if (!stems) return;
        setIsImporting(true);
        setImportStatus(`Exporting as ${format.toUpperCase()}...`);
        setImportProgress(50);
        setIsMobileMenuOpen(false);

        try {
            const res = await fetch('http://localhost:8000/export', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    stems,
                    volumes,
                    pitch_shift: autotuneStrength[0],
                    format
                }),
            });

            if (!res.ok) throw new Error('Export failed');

            // Trigger download
            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `mix.${format}`; // Backend sends filename but we can override or use it
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);

            setImportProgress(100);
            setTimeout(() => setIsImporting(false), 500);
        } catch (e) {
            console.error(e);
            setError('Export failed');
            setIsImporting(false);
        }
    };

    const registerWaveform = useCallback((ws: any) => {
        if (!wavesurferRefs.current.includes(ws)) {
            wavesurferRefs.current.push(ws);

            // Sync duration (use max duration to avoid cutting off)
            const newDuration = ws.getDuration();
            if (newDuration > 0) {
                setDuration(prev => Math.max(prev, newDuration));
            }

            // Sync playback events
            ws.on('timeupdate', (time: number) => {
                if (!isSeekingRef.current && wavesurferRefs.current[0] === ws) {
                    setCurrentTime(time);
                }
            });

            ws.on('finish', () => {
                // If all finished, stop
                setIsPlaying(false);
            });
        }
    }, []);

    const fetchLyrics = async (vocalsUrl: string) => {
        setIsTranscribing(true);
        try {
            console.log('Fetching lyrics for:', vocalsUrl);
            const res = await fetch('http://localhost:8000/transcribe', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ audio_url: vocalsUrl }),
            });

            if (!res.ok) throw new Error('Failed to fetch lyrics');

            const data = await res.json();
            console.log('Lyrics received:', data);
            if (data.lyrics && Array.isArray(data.lyrics)) {
                console.log('Setting lyrics state with', data.lyrics.length, 'items');
                setLyrics(data.lyrics);
            } else {
                console.warn('Lyrics data format incorrect:', data);
            }
        } catch (err) {
            console.error('Lyrics fetch error:', err);
        } finally {
            setIsTranscribing(false);
        }
    };

    const handleProcess = async () => {
        if (!url) return;
        setIsImporting(true);
        setImportProgress(10);
        setImportStatus('Downloading audio...');
        setError(null);
        setIsMobileMenuOpen(false);

        try {
            // 1. Process Audio (Download + Split + Key)
            const res = await fetch('http://localhost:8000/process', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ youtube_url: url }),
            });

            if (!res.ok) throw new Error('Failed to process audio');

            setImportProgress(50);
            setImportStatus('Separating stems (this may take a moment)...');

            const data = await res.json();
            setStems(data.stems);
            setKey(data.key);

            setImportProgress(100);
            setImportStatus('Ready!');

            setTimeout(() => {
                setIsImporting(false);
                // Trigger background transcription
                if (data.stems.vocals) {
                    fetchLyrics(data.stems.vocals);
                }
            }, 500);

        } catch (err) {
            setError(err instanceof Error ? err.message : 'Something went wrong');
            setIsImporting(false);
        }
    };

    // Load stems
    useEffect(() => {
        if (url) {
            handleProcess();
        }
    }, [url]);

    const handleGlobalSeek = (val: number[]) => {
        const time = val[0];
        setCurrentTime(time);
        isSeekingRef.current = true;

        wavesurferRefs.current.forEach(ws => {
            const progress = time / ws.getDuration();
            if (isFinite(progress)) {
                ws.seekTo(progress);
            }
        });

        // Debounce releasing seek lock
        setTimeout(() => {
            isSeekingRef.current = false;
        }, 100);
    };

    const toggleGlobalPlay = () => {
        const playing = !isPlaying;
        setIsPlaying(playing);
        wavesurferRefs.current.forEach(ws => {
            playing ? ws.play() : ws.pause();
        });
    };

    const handlePitchShift = async () => {
        if (!stems || !url) return;
        setIsImporting(true); // Reuse loading overlay
        setImportProgress(50);
        setImportStatus(`Shifting pitch by ${autotuneStrength[0]} semitones...`);

        try {
            const res = await fetch('http://localhost:8000/pitch_shift_stems', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    stems: stems,
                    semitones: autotuneStrength[0]
                }),
            });

            if (!res.ok) throw new Error('Failed to shift pitch');

            const data = await res.json();
            setStems(data.stems); // Update stems with shifted versions
            setImportProgress(100);
            setImportStatus('Done!');

            setTimeout(() => {
                setIsImporting(false);
            }, 500);

        } catch (err) {
            setError(err instanceof Error ? err.message : 'Pitch shift failed');
            setIsImporting(false);
        }
    };

    const formatTime = (seconds: number) => {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    // Reusable Controls Component
    const Controls = ({ mobile = false }) => (
        <div className={`flex ${mobile ? 'flex-col items-start gap-4 w-full' : 'items-center gap-6'}`}>
            {!stems ? (
                <div className={`flex ${mobile ? 'flex-col w-full gap-2' : 'items-center gap-2 w-96'}`}>
                    <input
                        type="text"
                        placeholder="Paste YouTube URL..."
                        className="flex-1 bg-zinc-900 border-zinc-800 rounded-full px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all w-full"
                        value={url}
                        onChange={(e) => setUrl(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleProcess()}
                    />
                    <Button
                        onClick={handleProcess}
                        disabled={!url || isImporting}
                        className={`rounded-full bg-white text-black hover:bg-zinc-200 font-medium px-6 ${mobile ? 'w-full' : ''}`}
                    >
                        Import
                    </Button>
                </div>
            ) : (
                <div className={`flex ${mobile ? 'flex-col w-full gap-4' : 'items-center gap-4 bg-zinc-900 rounded-full px-2 py-1 border border-zinc-800'}`}>
                    <div className={`flex items-center ${mobile ? 'justify-between w-full bg-zinc-900 p-2 rounded-xl border border-zinc-800' : 'gap-2'}`}>
                        <Button
                            size="icon"
                            variant="ghost"
                            className="rounded-full h-8 w-8 hover:bg-zinc-800"
                            onClick={() => {
                                setCurrentTime(0);
                                handleGlobalSeek([0]);
                            }}
                        >
                            <RotateCcw className="h-4 w-4 text-zinc-400" />
                        </Button>
                        <Button
                            size="icon"
                            className="rounded-full h-10 w-10 bg-white text-black hover:bg-zinc-200"
                            onClick={toggleGlobalPlay}
                        >
                            {isPlaying ? <Pause className="h-4 w-4 fill-current" /> : <Play className="h-4 w-4 fill-current ml-1" />}
                        </Button>
                        <div className="text-xs font-mono text-zinc-400 w-24 text-center">
                            {formatTime(currentTime)} / {formatTime(duration)}
                        </div>
                    </div>
                </div>
            )}

            {stems && (
                <div className={`flex ${mobile ? 'flex-col w-full gap-2' : 'items-center gap-2'}`}>
                    <Button
                        variant="outline"
                        onClick={() => setShowSaveModal(true)}
                        className={`border-zinc-800 hover:bg-zinc-900 text-zinc-400 hover:text-white gap-2 ${mobile ? 'w-full justify-start' : ''}`}
                    >
                        <Save className="h-4 w-4" />
                        Save
                    </Button>
                    <Button
                        variant="outline"
                        onClick={() => handleExport('mp3')}
                        className={`border-zinc-800 hover:bg-zinc-900 text-zinc-400 hover:text-white gap-2 ${mobile ? 'w-full justify-start' : ''}`}
                    >
                        <Download className="h-4 w-4" />
                        Download
                    </Button>
                    <Button
                        variant="outline"
                        onClick={resetProject}
                        className={`border-zinc-800 hover:bg-zinc-900 text-zinc-400 hover:text-white ${mobile ? 'w-full justify-start' : ''}`}
                    >
                        New Project
                    </Button>
                </div>
            )}
            <Button
                variant="ghost"
                onClick={fetchProjects}
                className={`text-zinc-400 hover:text-white gap-2 ${mobile ? 'w-full justify-start' : ''}`}
            >
                <FolderOpen className="h-4 w-4" />
                Open
            </Button>

            {user ? (
                <div className={`flex items-center gap-2 ${mobile ? 'w-full pt-4 border-t border-zinc-800' : 'pl-4 border-l border-zinc-800'}`}>
                    <div className="h-8 w-8 rounded-full bg-blue-600 flex items-center justify-center">
                        <User className="h-4 w-4 text-white" />
                    </div>
                    <div className={mobile ? 'flex-1' : 'hidden'}>
                        <span className="text-sm font-medium text-white block">{user.email}</span>
                    </div>
                    <Button variant="ghost" size="icon" onClick={handleSignOut}>
                        <LogOut className="h-4 w-4 text-zinc-400 hover:text-white" />
                    </Button>
                </div>
            ) : (
                <Button
                    variant="ghost"
                    onClick={() => router.push('/login')}
                    className={`text-zinc-400 hover:text-white ${mobile ? 'w-full justify-start' : ''}`}
                >
                    Login
                </Button>
            )}
        </div>
    );

    return (
        <div className="h-screen bg-black text-white flex overflow-hidden font-sans selection:bg-blue-500/30">
            {/* Mobile Menu Overlay */}
            <AnimatePresence>
                {isMobileMenuOpen && (
                    <>
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            onClick={() => setIsMobileMenuOpen(false)}
                            className="fixed inset-0 bg-black/80 backdrop-blur-sm z-40 md:hidden"
                        />
                        <motion.div
                            initial={{ x: '-100%' }}
                            animate={{ x: 0 }}
                            exit={{ x: '-100%' }}
                            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
                            className="fixed top-0 left-0 bottom-0 w-3/4 max-w-sm bg-zinc-950 border-r border-zinc-800 z-50 p-6 overflow-y-auto md:hidden"
                        >
                            <div className="flex justify-between items-center mb-8">
                                <div className="flex items-center gap-3">
                                    <div className="h-8 w-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                                        <Music className="h-5 w-5 text-white" />
                                    </div>
                                    <span className="font-bold text-lg">Menu</span>
                                </div>
                                <Button variant="ghost" size="icon" onClick={() => setIsMobileMenuOpen(false)}>
                                    <X className="h-5 w-5 text-zinc-400" />
                                </Button>
                            </div>
                            <Controls mobile={true} />
                        </motion.div>
                    </>
                )}
            </AnimatePresence>

            {/* Save Project Modal */}
            {showSaveModal && (
                <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center px-4">
                    <div className="bg-zinc-900 p-6 rounded-2xl border border-zinc-800 max-w-md w-full shadow-2xl">
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="text-xl font-bold text-white">Save Project</h3>
                            <Button variant="ghost" size="sm" onClick={() => setShowSaveModal(false)}>Close</Button>
                        </div>
                        <div className="space-y-4">
                            <div>
                                <label className="text-sm text-zinc-400 block mb-2">Project Name</label>
                                <input
                                    type="text"
                                    className="w-full bg-zinc-800 border-zinc-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    placeholder="My Awesome Mix"
                                    value={projectName}
                                    onChange={(e) => setProjectName(e.target.value)}
                                    onKeyDown={(e) => e.key === 'Enter' && handleSaveProject()}
                                />
                            </div>
                            <div className="flex justify-end gap-2">
                                <Button variant="ghost" onClick={() => setShowSaveModal(false)}>Cancel</Button>
                                <Button onClick={handleSaveProject} disabled={!projectName.trim()}>Save</Button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Load Project Modal */}
            {showLoadModal && (
                <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center px-4">
                    <div className="bg-zinc-900 p-6 rounded-2xl border border-zinc-800 max-w-md w-full shadow-2xl">
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="text-xl font-bold text-white">Open Project</h3>
                            <Button variant="ghost" size="sm" onClick={() => setShowLoadModal(false)}>Close</Button>
                        </div>
                        <div className="space-y-2 max-h-96 overflow-y-auto">
                            {savedProjects.length === 0 ? (
                                <p className="text-zinc-500 text-center py-4">No saved projects</p>
                            ) : (
                                savedProjects.map(p => (
                                    <div key={p.id} className="flex items-center justify-between p-3 bg-zinc-800/50 rounded-lg hover:bg-zinc-800 transition-colors cursor-pointer" onClick={() => handleLoadProject(p.id)}>
                                        <div>
                                            <div className="font-medium text-white">{p.name}</div>
                                            <div className="text-xs text-zinc-500">{new Date(p.updated_at).toLocaleDateString()}</div>
                                        </div>
                                        <FolderOpen className="h-4 w-4 text-zinc-400" />
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* Loading Overlay */}
            {isImporting && (
                <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center px-4">
                    <div className="bg-zinc-900 p-8 rounded-2xl border border-zinc-800 max-w-md w-full shadow-2xl">
                        <div className="flex flex-col items-center gap-6">
                            <div className="relative h-16 w-16">
                                <div className="absolute inset-0 border-4 border-zinc-800 rounded-full"></div>
                                <div className="absolute inset-0 border-4 border-blue-500 rounded-full border-t-transparent animate-spin"></div>
                                <Music className="absolute inset-0 m-auto h-6 w-6 text-blue-500 animate-pulse" />
                            </div>
                            <div className="text-center space-y-2">
                                <h3 className="text-xl font-bold text-white">Processing</h3>
                                <p className="text-zinc-400 text-sm">{importStatus}</p>
                            </div>
                            <div className="w-full space-y-2">
                                <div className="h-2 bg-zinc-800 rounded-full overflow-hidden">
                                    <div
                                        className="h-full bg-blue-500 transition-all duration-500 ease-out"
                                        style={{ width: `${importProgress}%` }}
                                    />
                                </div>
                                <div className="flex justify-between text-xs text-zinc-500 font-mono">
                                    <span>{importProgress}%</span>
                                    <span>Please wait...</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Main Studio Area */}
            <div className="flex-1 flex flex-col min-w-0 bg-zinc-950">
                {/* Header */}
                <header className="h-16 border-b border-zinc-800 flex items-center justify-between px-4 md:px-6 bg-zinc-950/50 backdrop-blur-md z-10">
                    <div className="flex items-center gap-4">
                        <Button variant="ghost" size="icon" className="md:hidden" onClick={() => setIsMobileMenuOpen(true)}>
                            <Menu className="h-5 w-5 text-white" />
                        </Button>
                        <div className="flex items-center gap-4">
                            <div className="h-8 w-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                                <Music className="h-5 w-5 text-white" />
                            </div>
                            <h1 className="font-bold text-lg tracking-tight hidden md:block">Vocalize <span className="text-blue-400">Karaoke</span></h1>
                        </div>
                    </div>

                    <div className="hidden md:block">
                        <Controls />
                    </div>
                </header>

                {/* Workspace */}
                <div className="flex-1 flex flex-col overflow-hidden relative">
                    {/* Global Timeline Slider */}
                    {stems && (
                        <div className="px-4 md:px-8 pt-6 pb-2 bg-zinc-950/30 border-b border-zinc-800/50">
                            <div className="flex justify-between items-end mb-2">
                                <span className="text-xs font-bold text-zinc-500 uppercase tracking-wider">Global Timeline</span>
                                <span className="text-sm font-mono font-bold text-blue-400">
                                    {formatTime(currentTime)} <span className="text-zinc-600">/</span> {formatTime(duration)}
                                </span>
                            </div>
                            <Slider
                                value={[currentTime]}
                                min={0}
                                max={duration || 100}
                                step={0.1}
                                onValueChange={handleGlobalSeek}
                                className="cursor-pointer"
                            />
                        </div>
                    )}

                    <div className="flex-1 p-4 md:p-8 overflow-y-auto pb-40">
                        {error && (
                            <div className="p-4 mb-4 text-red-400 bg-red-900/20 border border-red-900 rounded-lg">
                                {error}
                            </div>
                        )}

                        {!stems ? (
                            <div className="h-full flex flex-col items-center justify-center text-zinc-500 gap-4 text-center">
                                <Music className="h-16 w-16 opacity-20" />
                                <p>Import a song to start producing</p>
                                <Button variant="outline" className="md:hidden" onClick={() => setIsMobileMenuOpen(true)}>
                                    Open Menu to Import
                                </Button>
                            </div>
                        ) : (
                            <div className="space-y-8">
                                <div className="space-y-1">
                                    <div className="space-y-1">
                                        <Waveform name="Vocals" url={stems.vocals} color="#f472b6" onReady={registerWaveform} onVolumeChange={v => setVolumes(prev => ({ ...prev, vocals: v }))} />
                                        <Waveform name="Drums" url={stems.drums} color="#fbbf24" onReady={registerWaveform} onVolumeChange={v => setVolumes(prev => ({ ...prev, drums: v }))} />
                                        <Waveform name="Bass" url={stems.bass} color="#60a5fa" onReady={registerWaveform} onVolumeChange={v => setVolumes(prev => ({ ...prev, bass: v }))} />
                                        <Waveform name="Other" url={stems.other} color="#a78bfa" onReady={registerWaveform} onVolumeChange={v => setVolumes(prev => ({ ...prev, other: v }))} />
                                    </div>
                                </div>

                                {/* Tools Section */}
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 p-6 bg-zinc-900/30 rounded-xl border border-zinc-800">
                                    <div className="space-y-4">
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-2">
                                                <Zap className="h-5 w-5 text-yellow-400" />
                                                <span className="font-bold">Pitch Shift</span>
                                            </div>
                                            <span className="text-xs text-zinc-400">{autotuneStrength[0]} semitones</span>
                                        </div>

                                        <Select
                                            value={autotuneStrength[0].toString()}
                                            onValueChange={(val) => setAutotuneStrength([parseInt(val)])}
                                        >
                                            <SelectTrigger className="w-full bg-zinc-900 border-zinc-700">
                                                <SelectValue placeholder="Select Pitch" />
                                            </SelectTrigger>
                                            <SelectContent className="bg-zinc-900 border-zinc-700 text-white">
                                                {Array.from({ length: 25 }, (_, i) => i - 12).map((val: number) => (
                                                    <SelectItem key={val} value={val.toString()}>
                                                        {val > 0 ? `+${val}` : val} Semitones
                                                    </SelectItem>
                                                ))}
                                            </SelectContent>
                                        </Select>
                                        <Button
                                            size="sm"
                                            onClick={handlePitchShift}
                                            disabled={autotuneStrength[0] === 0}
                                            className="w-full bg-yellow-600 hover:bg-yellow-700 text-white"
                                        >
                                            Apply Shift
                                        </Button>
                                        <p className="text-xs text-zinc-500">Shift the pitch of the entire track.</p>
                                    </div>

                                    <div className="flex flex-col justify-center items-center text-center space-y-2 text-zinc-500">
                                        <Mic2 className="h-8 w-8 opacity-50" />
                                        <p className="text-sm">Lyrics Available</p>
                                    </div>
                                </div>

                                {/* Lyrics Section (Studio Mode) - Moved here as requested */}
                                <div className="p-6 bg-zinc-900/30 rounded-xl border border-zinc-800">
                                    <div className="flex items-center justify-between mb-4">
                                        <div className="flex items-center gap-2">
                                            <Mic2 className="h-5 w-5 text-purple-400" />
                                            <span className="font-bold">Lyrics</span>
                                        </div>
                                        {isTranscribing && (
                                            <span className="text-xs text-zinc-400 animate-pulse">Fetching lyrics...</span>
                                        )}
                                    </div>

                                    <LyricsDisplay
                                        lyrics={lyrics}
                                    />
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Right Sidebar - AI Director */}

        </div>
    );
}

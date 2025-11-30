"use client";

import React, { useEffect, useRef, useState } from 'react';
import WaveSurfer from 'wavesurfer.js';
import { Button } from '../ui/button';
import { Slider } from '../ui/slider';
import { Volume2, VolumeX } from 'lucide-react';

interface WaveformProps {
    url: string;
    name: string;
    color?: string;
    onReady?: (ws: WaveSurfer) => void;
    onVolumeChange?: (volume: number) => void;
    onSeek?: (progress: number) => void;
    delay?: number; // Delay in seconds
    mixStrength?: number; // -100 to 100
}

export default function Waveform({ url, name, color = '#4f46e5', onReady, onSeek, onVolumeChange, delay = 0, mixStrength = 0 }: WaveformProps) {
    const containerRef = useRef<HTMLDivElement>(null);
    const wavesurfer = useRef<WaveSurfer | null>(null);
    const [volume, setVolume] = useState(1);
    const [isMuted, setIsMuted] = useState(false);

    // Filters
    const audioContextRef = useRef<AudioContext | null>(null);
    const sourceRef = useRef<MediaElementAudioSourceNode | null>(null);
    const eqRef = useRef<BiquadFilterNode | null>(null);
    const compressorRef = useRef<DynamicsCompressorNode | null>(null);
    const reverbNodeRef = useRef<ConvolverNode | null>(null);
    const reverbGainRef = useRef<GainNode | null>(null);
    const dryGainRef = useRef<GainNode | null>(null);

    // Helper: Create Impulse Response for Reverb
    const createImpulseResponse = (context: AudioContext, duration: number, decay: number) => {
        const rate = context.sampleRate;
        const length = rate * duration;
        const impulse = context.createBuffer(2, length, rate);
        const left = impulse.getChannelData(0);
        const right = impulse.getChannelData(1);

        for (let i = 0; i < length; i++) {
            const n = i; // Sample index
            // Simple exponential decay noise
            const noise = (Math.random() * 2 - 1) * Math.pow(1 - n / length, decay);
            left[i] = noise;
            right[i] = noise;
        }
        return impulse;
    };

    // Initialize WaveSurfer
    useEffect(() => {
        if (!containerRef.current) return;

        wavesurfer.current = WaveSurfer.create({
            container: containerRef.current,
            waveColor: color,
            progressColor: '#1e1b4b',
            url: url,
            height: 60,
            barWidth: 2,
            barGap: 1,
            barRadius: 2,
            normalize: true,
        });

        wavesurfer.current.on('ready', () => {
            if (onReady && wavesurfer.current) onReady(wavesurfer.current);

            // Initialize Web Audio API for Smart Mix
            const mediaElement = wavesurfer.current?.getMediaElement();
            if (mediaElement && !audioContextRef.current) {
                try {
                    const AudioContext = window.AudioContext || (window as any).webkitAudioContext;
                    const ctx = new AudioContext();
                    audioContextRef.current = ctx;

                    // Create Source
                    const source = ctx.createMediaElementSource(mediaElement);
                    sourceRef.current = source;

                    // Create Nodes
                    eqRef.current = ctx.createBiquadFilter();
                    eqRef.current.type = 'highshelf';
                    eqRef.current.frequency.value = 3000; // Boost highs
                    eqRef.current.gain.value = 0;

                    compressorRef.current = ctx.createDynamicsCompressor();
                    compressorRef.current.threshold.value = -24;
                    compressorRef.current.knee.value = 30;
                    compressorRef.current.ratio.value = 12;
                    compressorRef.current.attack.value = 0.003;
                    compressorRef.current.release.value = 0.25;

                    // Reverb Setup
                    reverbNodeRef.current = ctx.createConvolver();
                    reverbNodeRef.current.buffer = createImpulseResponse(ctx, 2.0, 2.0); // 2s tail
                    reverbGainRef.current = ctx.createGain();
                    reverbGainRef.current.gain.value = 0; // Start dry

                    dryGainRef.current = ctx.createGain();
                    dryGainRef.current.gain.value = 1;

                    // Connect Graph:
                    // Source -> EQ -> Compressor -> Split [Dry, Reverb] -> Destination

                    // 1. Source -> EQ
                    sourceRef.current.connect(eqRef.current);

                    // 2. EQ -> Compressor
                    eqRef.current.connect(compressorRef.current);

                    // 3. Compressor -> Dry Gain -> Dest
                    compressorRef.current.connect(dryGainRef.current);
                    dryGainRef.current.connect(ctx.destination);

                    // 4. Compressor -> Reverb -> Reverb Gain -> Dest
                    compressorRef.current.connect(reverbNodeRef.current);
                    reverbNodeRef.current.connect(reverbGainRef.current);
                    reverbGainRef.current.connect(ctx.destination);

                } catch (e) {
                    console.error("Web Audio Init Error:", e);
                }
            }
        });

        wavesurfer.current.on('interaction', (newProgress) => {
            if (onSeek) onSeek(newProgress);
        });

        return () => {
            wavesurfer.current?.destroy();
            audioContextRef.current?.close();
        };
    }, [url, color, onReady, onSeek]);

    // Update Filters when mixStrength changes
    useEffect(() => {
        if (!eqRef.current || !compressorRef.current || !reverbGainRef.current || !dryGainRef.current) return;

        // Normalize strength (-100 to 100) -> (0 to 1) for Reverb
        // We only apply effects for positive strength for now
        const s = Math.max(0, mixStrength / 100);

        // EQ: Boost highs
        eqRef.current.gain.value = s * 15;

        // Compressor: More compression
        compressorRef.current.threshold.value = -24 - (s * 30);
        compressorRef.current.ratio.value = 12 + (s * 8);

        // Reverb: Mix in wet signal
        // Dry: 1.0 -> 0.6
        // Wet: 0.0 -> 0.4
        dryGainRef.current.gain.value = 1.0 - (s * 0.4);
        reverbGainRef.current.gain.value = s * 0.4;

        // Resume AudioContext
        if (audioContextRef.current?.state === 'suspended') {
            audioContextRef.current.resume();
        }

    }, [mixStrength]);

    // Handle Delay (Silence padding)
    useEffect(() => {
        if (wavesurfer.current && delay > 0) {
            // Note: Real timeline offset requires the Timeline plugin or manual silence padding.
            // For simplicity in this version, we are just storing the delay.
            // A robust DAW implementation would be much more complex.
        }
    }, [delay]);

    const handleVolumeChange = (val: number[]) => {
        const newVol = val[0];
        setVolume(newVol);
        wavesurfer.current?.setVolume(newVol);
        if (newVol > 0 && isMuted) setIsMuted(false);
        if (onVolumeChange) onVolumeChange(newVol);
    };

    const toggleMute = () => {
        if (wavesurfer.current) {
            const newMute = !isMuted;
            setIsMuted(newMute);
            wavesurfer.current.setMuted(newMute);
        }
    };

    return (
        <div className="flex items-center gap-4 p-4 bg-zinc-900/50 rounded-lg border border-zinc-800 mb-2">
            <div className="w-24 font-bold text-zinc-400 uppercase text-sm">{name}</div>

            <div className="flex-1" ref={containerRef} />

            <div className="flex items-center gap-2">
                <Button variant="ghost" size="icon" onClick={toggleMute}>
                    {isMuted || volume === 0 ? <VolumeX className="h-4 w-4" /> : <Volume2 className="h-4 w-4" />}
                </Button>
                <div className="w-24">
                    <Slider
                        value={[isMuted ? 0 : volume]}
                        max={1}
                        step={0.01}
                        onValueChange={handleVolumeChange}
                    />
                </div>
            </div>
        </div>
    );
};



"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, Music, Mic2, Layers, Wand2 } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function LandingPage() {
    return (
        <div className="min-h-screen bg-black text-white selection:bg-purple-500/30">
            {/* Navigation */}
            <nav className="fixed top-0 w-full z-50 border-b border-white/10 bg-black/50 backdrop-blur-xl">
                <div className="container mx-auto px-6 h-16 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center">
                            <Music className="w-5 h-5 text-white" />
                        </div>
                        <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-white/60">
                            Vocalize
                        </span>
                    </div>
                    <div className="flex items-center gap-4">
                        <Link href="/login">
                            <Button variant="ghost" className="text-zinc-400 hover:text-white">
                                Login
                            </Button>
                        </Link>
                        <Link href="/studio">
                            <Button className="bg-white text-black hover:bg-zinc-200 rounded-full px-6">
                                Open Studio
                            </Button>
                        </Link>
                    </div>
                </div>
            </nav>

            {/* Hero Section */}
            <section className="relative pt-32 pb-20 lg:pt-48 lg:pb-32 overflow-hidden">
                <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-purple-900/20 via-black to-black" />

                <div className="container mx-auto px-6 relative z-10">
                    <div className="max-w-4xl mx-auto text-center">
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.5 }}
                        >
                            <h1 className="text-5xl md:text-7xl font-bold tracking-tight mb-8">
                                AI Music Production <br />
                                <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 via-pink-400 to-blue-400">
                                    Reimagined.
                                </span>
                            </h1>
                        </motion.div>

                        <motion.p
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.5, delay: 0.1 }}
                            className="text-xl text-zinc-400 mb-12 max-w-2xl mx-auto leading-relaxed"
                        >
                            Separate stems, transcribe lyrics, and remix tracks in seconds.
                            Powered by state-of-the-art AI, running directly in your browser.
                        </motion.p>

                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.5, delay: 0.2 }}
                            className="flex flex-col sm:flex-row items-center justify-center gap-4"
                        >
                            <Link href="/studio">
                                <Button size="lg" className="h-14 px-8 text-lg rounded-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 border-0 shadow-lg shadow-purple-500/25">
                                    Start Creating <ArrowRight className="ml-2 w-5 h-5" />
                                </Button>
                            </Link>
                            <Link href="https://github.com/madhavan-pts/antigravity" target="_blank">
                                <Button size="lg" variant="outline" className="h-14 px-8 text-lg rounded-full border-zinc-800 bg-zinc-900/50 hover:bg-zinc-900 hover:border-zinc-700">
                                    View on GitHub
                                </Button>
                            </Link>
                        </motion.div>
                    </div>
                </div>

                {/* Floating Elements Animation */}
                <div className="absolute top-1/2 left-0 w-full h-full -z-10 pointer-events-none opacity-50">
                    {/* Abstract shapes could go here */}
                </div>
            </section>

            {/* Features Grid */}
            <section className="py-24 bg-zinc-950/50 border-t border-white/5">
                <div className="container mx-auto px-6">
                    <div className="grid md:grid-cols-3 gap-8">
                        <FeatureCard
                            icon={<Layers className="w-8 h-8 text-purple-400" />}
                            title="Stem Separation"
                            description="Isolate vocals, drums, bass, and other instruments with high-fidelity AI models."
                        />
                        <FeatureCard
                            icon={<Mic2 className="w-8 h-8 text-pink-400" />}
                            title="Auto Transcription"
                            description="Get perfectly synced lyrics and translations for any song automatically."
                        />
                        <FeatureCard
                            icon={<Wand2 className="w-8 h-8 text-blue-400" />}
                            title="Smart Mixing"
                            description="Professional mixing tools and effects to blend your tracks seamlessly."
                        />
                    </div>
                </div>
            </section>

            {/* Footer */}
            <footer className="py-12 border-t border-white/5">
                <div className="container mx-auto px-6 text-center text-zinc-500">
                    <p>© 2024 Vocalize AI. Built with Next.js, Supabase, and Modal.</p>
                </div>
            </footer>
        </div>
    );
}

function FeatureCard({ icon, title, description }: { icon: React.ReactNode, title: string, description: string }) {
    return (
        <motion.div
            whileHover={{ y: -5 }}
            className="p-8 rounded-3xl bg-zinc-900/50 border border-white/5 hover:border-white/10 transition-colors"
        >
            <div className="mb-6 p-4 rounded-2xl bg-white/5 w-fit">
                {icon}
            </div>
            <h3 className="text-xl font-bold mb-3 text-white">{title}</h3>
            <p className="text-zinc-400 leading-relaxed">{description}</p>
        </motion.div>
    );
}

import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
    title: "Vocalize - AI Music Studio",
    description: "Separate stems, transcribe lyrics, and remix tracks in seconds with AI.",
    openGraph: {
        title: "Vocalize - AI Music Studio",
        description: "Separate stems, transcribe lyrics, and remix tracks in seconds with AI.",
        type: "website",
        locale: "en_US",
        siteName: "Vocalize",
    },
    twitter: {
        card: "summary_large_image",
        title: "Vocalize - AI Music Studio",
        description: "Separate stems, transcribe lyrics, and remix tracks in seconds with AI.",
    },
};

export default function RootLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    return (
        <html lang="en">
            <body className="antialiased">{children}</body>
        </html>
    );
}

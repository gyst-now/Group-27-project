import type { Metadata } from 'next';
import './globals.css';
export const metadata: Metadata = { title: 'University Catalog Advisor', description: 'Explore selected official UIUC 2026–2027 CS, MATH, and Computer Science degree catalog sources.' };
export default function Layout({children}: Readonly<{children: React.ReactNode}>) { return <html lang="en"><body>{children}</body></html>; }

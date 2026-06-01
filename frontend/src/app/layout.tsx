import type { Metadata } from 'next';
import './globals.css';
import { Toaster } from 'sonner';
import { AuthProvider } from '@/lib/auth-context';
import AuthGuard from '@/components/AuthGuard';
import HeaderNav from '@/components/HeaderNav';

export const metadata: Metadata = {
  title: '故障分析システム',
  description: '故障報告の構造化・分析・検索システム',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ja">
      <body className="antialiased bg-gray-50 min-h-screen">
        <AuthProvider>
          <AuthGuard>
            <HeaderNav />
            <main className="max-w-7xl mx-auto px-4 py-8">{children}</main>
          </AuthGuard>
          <Toaster richColors position="top-right" />
        </AuthProvider>
      </body>
    </html>
  );
}

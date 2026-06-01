'use client';

import Link from 'next/link';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { toast } from 'sonner';
import { useAuth } from '@/lib/auth-context';
import { apiClient } from '@/lib/api';

function ChangePasswordModal({ onClose }: { onClose: () => void }) {
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      await apiClient.patch('/api/auth/me/password', {
        current_password: currentPassword,
        new_password: newPassword,
      });
      toast.success('パスワードを変更しました');
      onClose();
    } catch (err: unknown) {
      const axiosError = err as { response?: { data?: { detail?: string } } };
      toast.error(axiosError.response?.data?.detail || 'パスワード変更に失敗しました');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-white rounded-lg shadow-xl w-full max-w-sm p-6" onClick={(e) => e.stopPropagation()}>
        <h2 className="text-lg font-semibold text-gray-800 mb-4">パスワード変更</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">現在のパスワード</label>
            <input
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              required
              className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">新しいパスワード</label>
            <input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
              className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div className="flex gap-2 pt-2">
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex-1 bg-blue-700 text-white py-2 rounded text-sm font-medium hover:bg-blue-800 disabled:opacity-50 transition-colors"
            >
              {isSubmitting ? '変更中...' : '変更する'}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="flex-1 border border-gray-300 text-gray-600 py-2 rounded text-sm hover:bg-gray-50 transition-colors"
            >
              キャンセル
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function HeaderNav() {
  const { user, logout } = useAuth();
  const router = useRouter();
  const [showPasswordModal, setShowPasswordModal] = useState(false);

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  return (
    <>
      <header className="bg-blue-700 text-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
          <span className="text-xl font-bold tracking-tight">故障分析システム</span>
          <nav className="flex items-center gap-6 text-sm font-medium">
            <Link href="/input" className="hover:text-blue-200 transition-colors">
              データ入力
            </Link>
            <Link href="/dashboard" className="hover:text-blue-200 transition-colors">
              ダッシュボード
            </Link>
            <Link href="/search" className="hover:text-blue-200 transition-colors">
              検索
            </Link>
            {user?.role === 'admin' && (
              <Link href="/admin/users" className="hover:text-blue-200 transition-colors">
                ユーザー管理
              </Link>
            )}
            {user && (
              <div className="flex items-center gap-3 ml-4 pl-4 border-l border-blue-500">
                <span className="text-blue-200">{user.username}</span>
                <button
                  onClick={() => setShowPasswordModal(true)}
                  className="bg-blue-600 hover:bg-blue-500 px-3 py-1 rounded text-xs transition-colors"
                >
                  PW変更
                </button>
                <button
                  onClick={handleLogout}
                  className="bg-blue-600 hover:bg-blue-500 px-3 py-1 rounded text-xs transition-colors"
                >
                  ログアウト
                </button>
              </div>
            )}
          </nav>
        </div>
      </header>
      {showPasswordModal && <ChangePasswordModal onClose={() => setShowPasswordModal(false)} />}
    </>
  );
}

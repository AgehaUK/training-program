'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { toast } from 'sonner';
import { useAuth } from '@/lib/auth-context';
import { apiClient } from '@/lib/api';

interface User {
  id: number;
  username: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

export default function AdminUsersPage() {
  const { user } = useAuth();
  const router = useRouter();
  const [users, setUsers] = useState<User[]>([]);
  const [newUsername, setNewUsername] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [newRole, setNewRole] = useState('user');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [resetTarget, setResetTarget] = useState<User | null>(null);
  const [resetPassword, setResetPassword] = useState('');
  const [isResetting, setIsResetting] = useState(false);

  useEffect(() => {
    if (user && user.role !== 'admin') {
      router.replace('/');
    }
  }, [user, router]);

  const fetchUsers = async () => {
    try {
      const res = await apiClient.get<User[]>('/api/users');
      setUsers(res.data);
    } catch {
      setError('ユーザー一覧の取得に失敗しました');
    }
  };

  useEffect(() => {
    if (user?.role === 'admin') {
      fetchUsers();
    }
  }, [user]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsSubmitting(true);
    try {
      await apiClient.post('/api/users', {
        username: newUsername,
        password: newPassword,
        role: newRole,
      });
      setNewUsername('');
      setNewPassword('');
      setNewRole('user');
      await fetchUsers();
    } catch (err: unknown) {
      const axiosError = err as { response?: { data?: { detail?: string } } };
      setError(axiosError.response?.data?.detail || 'ユーザー作成に失敗しました');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('このユーザーを削除しますか？')) return;
    try {
      await apiClient.delete(`/api/users/${id}`);
      await fetchUsers();
    } catch (err: unknown) {
      const axiosError = err as { response?: { data?: { detail?: string } } };
      setError(axiosError.response?.data?.detail || '削除に失敗しました');
    }
  };

  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!resetTarget) return;
    setIsResetting(true);
    try {
      await apiClient.patch(`/api/users/${resetTarget.id}/password`, { new_password: resetPassword });
      toast.success(`${resetTarget.username} のパスワードを変更しました`);
      setResetTarget(null);
      setResetPassword('');
    } catch {
      toast.error('パスワード変更に失敗しました');
    } finally {
      setIsResetting(false);
    }
  };

  if (user?.role !== 'admin') return null;

  return (
    <>
    <div className="space-y-8">
      <h1 className="text-2xl font-bold text-gray-800">ユーザー管理</h1>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-600 rounded px-4 py-3 text-sm">
          {error}
        </div>
      )}

      {/* ユーザー追加フォーム */}
      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-lg font-semibold text-gray-700 mb-4">新規ユーザー追加</h2>
        <form onSubmit={handleCreate} className="flex flex-wrap gap-3 items-end">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">ユーザー名</label>
            <input
              type="text"
              value={newUsername}
              onChange={(e) => setNewUsername(e.target.value)}
              required
              className="border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">パスワード</label>
            <input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
              className="border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">ロール</label>
            <select
              value={newRole}
              onChange={(e) => setNewRole(e.target.value)}
              className="border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="user">user</option>
              <option value="admin">admin</option>
            </select>
          </div>
          <button
            type="submit"
            disabled={isSubmitting}
            className="bg-blue-700 text-white px-4 py-2 rounded text-sm font-medium hover:bg-blue-800 disabled:opacity-50 transition-colors"
          >
            {isSubmitting ? '追加中...' : '追加'}
          </button>
        </form>
      </div>

      {/* ユーザー一覧 */}
      <div className="bg-white shadow rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="text-left px-4 py-3 font-medium text-gray-600">ID</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">ユーザー名</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">ロール</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">作成日時</th>
              <th className="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id} className="border-b border-gray-100 hover:bg-gray-50">
                <td className="px-4 py-3 text-gray-500">{u.id}</td>
                <td className="px-4 py-3 font-medium text-gray-800">{u.username}</td>
                <td className="px-4 py-3">
                  <span
                    className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${
                      u.role === 'admin'
                        ? 'bg-blue-100 text-blue-700'
                        : 'bg-gray-100 text-gray-600'
                    }`}
                  >
                    {u.role}
                  </span>
                </td>
                <td className="px-4 py-3 text-gray-500">
                  {new Date(u.created_at).toLocaleString('ja-JP')}
                </td>
                <td className="px-4 py-3 text-right">
                  <div className="flex justify-end gap-3">
                    <button
                      onClick={() => { setResetTarget(u); setResetPassword(''); }}
                      className="text-blue-500 hover:text-blue-700 text-xs font-medium transition-colors"
                    >
                      PW変更
                    </button>
                    {u.id !== user?.id && (
                      <button
                        onClick={() => handleDelete(u.id)}
                        className="text-red-500 hover:text-red-700 text-xs font-medium transition-colors"
                      >
                        削除
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>

    {resetTarget && (

      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setResetTarget(null)}>
        <div className="bg-white rounded-lg shadow-xl w-full max-w-sm p-6" onClick={(e) => e.stopPropagation()}>
          <h2 className="text-lg font-semibold text-gray-800 mb-1">パスワードリセット</h2>
          <p className="text-sm text-gray-500 mb-4">{resetTarget.username} の新しいパスワードを設定します</p>
          <form onSubmit={handleResetPassword} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">新しいパスワード</label>
              <input
                type="password"
                value={resetPassword}
                onChange={(e) => setResetPassword(e.target.value)}
                required
                autoFocus
                className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div className="flex gap-2 pt-2">
              <button
                type="submit"
                disabled={isResetting}
                className="flex-1 bg-blue-700 text-white py-2 rounded text-sm font-medium hover:bg-blue-800 disabled:opacity-50 transition-colors"
              >
                {isResetting ? '変更中...' : '変更する'}
              </button>
              <button
                type="button"
                onClick={() => setResetTarget(null)}
                className="flex-1 border border-gray-300 text-gray-600 py-2 rounded text-sm hover:bg-gray-50 transition-colors"
              >
                キャンセル
              </button>
            </div>
          </form>
        </div>
      </div>
    )}
    </>
  );
}

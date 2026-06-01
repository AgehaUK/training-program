'use client';

import { useEffect, useState } from 'react';
import { toast } from 'sonner';
import { apiClient } from '@/lib/api';

interface ReportListItem {
  id: number;
  occurred_at: string;
  equipment_name: string;
  symptom: string;
  cause: string | null;
  cost: number | null;
  downtime_hours: number | null;
  failure_mode: string | null;
}

interface ReportDetail {
  id: number;
  original_text: string;
  occurred_at: string;
  equipment_name: string;
  symptom: string;
  cause: string | null;
  action_taken: string | null;
  cost: number | null;
  downtime_hours: number | null;
  failure_mode: string | null;
  source: string;
  created_at: string;
}

interface FailureMode { id: number; name: string; }
interface Filters { keyword: string; from: string; to: string; failure_mode_id: string; cost_min: string; cost_max: string; }
type SortKey = 'occurred_at' | 'cost' | 'downtime_hours';
type SortOrder = 'asc' | 'desc';

const PER_PAGE = 15;

export default function SearchPage() {
  const [filters, setFilters] = useState<Filters>({ keyword: '', from: '', to: '', failure_mode_id: '', cost_min: '', cost_max: '' });
  const [sort, setSort] = useState<SortKey>('occurred_at');
  const [order, setOrder] = useState<SortOrder>('desc');
  const [page, setPage] = useState(1);
  const [reports, setReports] = useState<ReportListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [failureModes, setFailureModes] = useState<FailureMode[]>([]);
  const [detail, setDetail] = useState<ReportDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  useEffect(() => {
    apiClient.get('/api/failure-modes').then((res) => setFailureModes(res.data.data ?? []));
  }, []);

  const buildParams = (f: Filters, s: SortKey, o: SortOrder, p: number) => {
    const params: Record<string, string> = {};
    if (f.keyword) params.keyword = f.keyword;
    if (f.from) params.from = f.from;
    if (f.to) params.to = f.to;
    if (f.failure_mode_id) params.failure_mode_id = f.failure_mode_id;
    if (f.cost_min) params.cost_min = f.cost_min;
    if (f.cost_max) params.cost_max = f.cost_max;
    params.sort = s; params.order = o;
    params.page = String(p); params.per_page = String(PER_PAGE);
    return params;
  };

  const fetchReports = async (f: Filters, s: SortKey, o: SortOrder, p: number) => {
    setLoading(true);
    try {
      const res = await apiClient.get('/api/reports', { params: buildParams(f, s, o, p) });
      setReports(res.data.data.reports);
      setTotal(res.data.data.total);
      setSearched(true);
    } catch { toast.error('検索に失敗しました'); } finally { setLoading(false); }
  };

  const handleSearch = () => { setPage(1); fetchReports(filters, sort, order, 1); };
  const handleReset = () => {
    const empty: Filters = { keyword: '', from: '', to: '', failure_mode_id: '', cost_min: '', cost_max: '' };
    setFilters(empty); setSort('occurred_at'); setOrder('desc'); setPage(1);
    fetchReports(empty, 'occurred_at', 'desc', 1);
  };
  const handleSort = (col: SortKey) => {
    const newOrder = sort === col && order === 'desc' ? 'asc' : 'desc';
    setSort(col); setOrder(newOrder); setPage(1);
    fetchReports(filters, col, newOrder, 1);
  };
  const handlePageChange = (p: number) => { setPage(p); fetchReports(filters, sort, order, p); };
  const handleRowClick = async (id: number) => {
    setDetailLoading(true);
    try {
      const res = await apiClient.get(`/api/reports/${id}`);
      setDetail(res.data.data);
    } catch { toast.error('詳細の取得に失敗しました'); } finally { setDetailLoading(false); }
  };

  const totalPages = Math.ceil(total / PER_PAGE);
  const sortIndicator = (col: SortKey) =>
    sort !== col ? <span className="text-gray-300 ml-1">↕</span> : <span className="ml-1">{order === 'desc' ? '↓' : '↑'}</span>;

  return (
    <div className="max-w-6xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-800 mb-1">故障事例検索</h1>
        <p className="text-gray-500 text-sm">キーワード・条件で過去の故障事例を検索します</p>
      </div>

      <div className="bg-white border border-gray-200 rounded-lg p-5 mb-6 shadow-sm">
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-600 mb-1">キーワード</label>
          <div className="flex gap-2">
            <input type="text" placeholder="設備名・症状・原因・対策を検索..." value={filters.keyword}
              onChange={(e) => setFilters({ ...filters, keyword: e.target.value })}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              className="flex-1 border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button onClick={handleSearch} disabled={loading}
              className="px-5 py-2 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 disabled:opacity-50 transition-colors">
              {loading ? '検索中...' : '検索'}
            </button>
            <button onClick={handleReset} disabled={loading}
              className="px-4 py-2 border border-gray-300 text-gray-600 text-sm rounded hover:bg-gray-50 disabled:opacity-50 transition-colors">
              リセット
            </button>
          </div>
        </div>

        <details>
          <summary className="cursor-pointer text-sm text-blue-600 hover:text-blue-800 select-none">詳細フィルター ▾</summary>
          <div className="mt-3 flex flex-wrap gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">開始日</label>
              <input type="date" value={filters.from} onChange={(e) => setFilters({ ...filters, from: e.target.value })}
                className="border border-gray-300 rounded px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">終了日</label>
              <input type="date" value={filters.to} onChange={(e) => setFilters({ ...filters, to: e.target.value })}
                className="border border-gray-300 rounded px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">故障モード</label>
              <select value={filters.failure_mode_id} onChange={(e) => setFilters({ ...filters, failure_mode_id: e.target.value })}
                className="border border-gray-300 rounded px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                <option value="">すべて</option>
                {failureModes.map((m) => <option key={m.id} value={String(m.id)}>{m.name}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">コスト下限（円）</label>
              <input type="number" placeholder="例: 10000" value={filters.cost_min}
                onChange={(e) => setFilters({ ...filters, cost_min: e.target.value })}
                className="border border-gray-300 rounded px-3 py-1.5 text-sm w-32 focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">コスト上限（円）</label>
              <input type="number" placeholder="例: 100000" value={filters.cost_max}
                onChange={(e) => setFilters({ ...filters, cost_max: e.target.value })}
                className="border border-gray-300 rounded px-3 py-1.5 text-sm w-32 focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
          </div>
        </details>
      </div>

      {searched && (
        <div className="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
          <div className="px-5 py-3 border-b border-gray-100">
            <span className="text-sm text-gray-600">{loading ? '検索中...' : `${total} 件`}</span>
          </div>

          {reports.length === 0 && !loading ? (
            <div className="py-16 text-center text-gray-400 text-sm">条件に一致する故障事例が見つかりませんでした</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left font-medium text-gray-600 cursor-pointer hover:bg-gray-100 select-none" onClick={() => handleSort('occurred_at')}>発生日{sortIndicator('occurred_at')}</th>
                    <th className="px-4 py-3 text-left font-medium text-gray-600">設備名</th>
                    <th className="px-4 py-3 text-left font-medium text-gray-600">症状</th>
                    <th className="px-4 py-3 text-left font-medium text-gray-600">故障モード</th>
                    <th className="px-4 py-3 text-right font-medium text-gray-600 cursor-pointer hover:bg-gray-100 select-none" onClick={() => handleSort('cost')}>コスト{sortIndicator('cost')}</th>
                    <th className="px-4 py-3 text-right font-medium text-gray-600 cursor-pointer hover:bg-gray-100 select-none" onClick={() => handleSort('downtime_hours')}>停止時間{sortIndicator('downtime_hours')}</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {reports.map((r) => (
                    <tr key={r.id} onClick={() => handleRowClick(r.id)} className="hover:bg-blue-50 cursor-pointer transition-colors">
                      <td className="px-4 py-3 text-gray-700 whitespace-nowrap">{r.occurred_at}</td>
                      <td className="px-4 py-3 text-gray-800 font-medium">{r.equipment_name}</td>
                      <td className="px-4 py-3 text-gray-600 max-w-xs truncate">{r.symptom}</td>
                      <td className="px-4 py-3">
                        {r.failure_mode ? <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">{r.failure_mode}</span> : <span className="text-gray-400">-</span>}
                      </td>
                      <td className="px-4 py-3 text-right text-gray-700">{r.cost != null ? `¥${r.cost.toLocaleString()}` : '-'}</td>
                      <td className="px-4 py-3 text-right text-gray-700">{r.downtime_hours != null ? `${r.downtime_hours}h` : '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {totalPages > 1 && (
            <div className="px-5 py-3 border-t border-gray-100 flex items-center justify-between">
              <span className="text-xs text-gray-500">{page} / {totalPages} ページ</span>
              <div className="flex gap-1">
                <button onClick={() => handlePageChange(page - 1)} disabled={page <= 1 || loading}
                  className="px-3 py-1.5 border border-gray-300 rounded text-sm text-gray-600 hover:bg-gray-50 disabled:opacity-40">前へ</button>
                {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
                  const p = Math.max(1, Math.min(page - 2, totalPages - 4)) + i;
                  return (
                    <button key={p} onClick={() => handlePageChange(p)} disabled={loading}
                      className={`px-3 py-1.5 border rounded text-sm transition-colors ${p === page ? 'bg-blue-600 border-blue-600 text-white' : 'border-gray-300 text-gray-600 hover:bg-gray-50'}`}>
                      {p}
                    </button>
                  );
                })}
                <button onClick={() => handlePageChange(page + 1)} disabled={page >= totalPages || loading}
                  className="px-3 py-1.5 border border-gray-300 rounded text-sm text-gray-600 hover:bg-gray-50 disabled:opacity-40">次へ</button>
              </div>
            </div>
          )}
        </div>
      )}

      {(detail || detailLoading) && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={() => setDetail(null)}>
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            {detailLoading ? (
              <div className="p-10 text-center text-gray-400">読み込み中...</div>
            ) : detail ? (
              <>
                <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
                  <h2 className="text-lg font-semibold text-gray-800">故障レポート詳細</h2>
                  <button onClick={() => setDetail(null)} className="text-gray-400 hover:text-gray-600 text-xl leading-none">✕</button>
                </div>
                <div className="px-6 py-5 space-y-4">
                  <div className="bg-gray-50 rounded-lg p-4">
                    <p className="text-xs font-medium text-gray-400 mb-1">元テキスト</p>
                    <p className="text-sm text-gray-700 leading-relaxed">{detail.original_text}</p>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <DetailField label="発生日" value={detail.occurred_at} />
                    <DetailField label="設備名" value={detail.equipment_name} />
                    <DetailField label="故障モード" value={detail.failure_mode} />
                    <DetailField label="コスト" value={detail.cost != null ? `¥${detail.cost.toLocaleString()}` : null} />
                    <DetailField label="停止時間" value={detail.downtime_hours != null ? `${detail.downtime_hours}h` : null} />
                    <DetailField label="データソース" value={detail.source} />
                  </div>
                  <DetailField label="症状" value={detail.symptom} fullWidth />
                  <DetailField label="原因" value={detail.cause} fullWidth />
                  <DetailField label="対策" value={detail.action_taken} fullWidth />
                  <p className="text-xs text-gray-400 text-right">登録日時: {detail.created_at}</p>
                </div>
              </>
            ) : null}
          </div>
        </div>
      )}
    </div>
  );
}

function DetailField({ label, value, fullWidth = false }: { label: string; value: string | null | undefined; fullWidth?: boolean }) {
  return (
    <div className={fullWidth ? 'col-span-2' : ''}>
      <p className="text-xs font-medium text-gray-400 mb-0.5">{label}</p>
      <p className="text-sm text-gray-800">{value ?? <span className="text-gray-400">-</span>}</p>
    </div>
  );
}

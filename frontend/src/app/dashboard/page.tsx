'use client';

import { useEffect, useState } from 'react';
import {
  Bar, BarChart, CartesianGrid, Cell, Legend, Line, LineChart,
  Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts';
import { toast } from 'sonner';
import { apiClient } from '@/lib/api';

interface SummaryData {
  total_count: number;
  total_cost: number;
  avg_downtime_hours: number;
}
interface FailureModeCount { failure_mode: string; count: number; }
interface MonthlyTrend { month: string; count: number; }
interface CostRanking { equipment_name: string; total_cost: number; }
interface Filters { from_date: string; to_date: string; equipment_name: string; }
type SuggestionsState = 'idle' | 'loading' | 'done' | 'error';

const PIE_COLORS = ['#3b82f6','#10b981','#f59e0b','#ef4444','#8b5cf6','#ec4899','#06b6d4'];

export default function DashboardPage() {
  const [filters, setFilters] = useState<Filters>({ from_date: '', to_date: '', equipment_name: '' });
  const [summary, setSummary] = useState<SummaryData | null>(null);
  const [failureModes, setFailureModes] = useState<FailureModeCount[]>([]);
  const [trend, setTrend] = useState<MonthlyTrend[]>([]);
  const [costTop10, setCostTop10] = useState<CostRanking[]>([]);
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState('');
  const [suggestionsState, setSuggestionsState] = useState<SuggestionsState>('idle');

  const buildQuery = (f: Filters) => {
    const params = new URLSearchParams();
    if (f.from_date) params.append('from_date', f.from_date);
    if (f.to_date) params.append('to_date', f.to_date);
    if (f.equipment_name) params.append('equipment_name', f.equipment_name);
    const qs = params.toString();
    return qs ? `?${qs}` : '';
  };

  const fetchAll = async (f: Filters) => {
    setLoading(true);
    try {
      const qs = buildQuery(f);
      const [summaryRes, modesRes, trendRes, costRes] = await Promise.all([
        apiClient.get(`/api/dashboard/summary${qs}`),
        apiClient.get(`/api/dashboard/failure-modes${qs}`),
        apiClient.get(`/api/dashboard/trend${qs}`),
        apiClient.get(`/api/dashboard/cost-top10${qs}`),
      ]);
      setSummary(summaryRes.data.data);
      setFailureModes(modesRes.data.data);
      setTrend(trendRes.data.data);
      setCostTop10(costRes.data.data);
    } catch { toast.error('データの読み込みに失敗しました'); } finally { setLoading(false); }
  };

  useEffect(() => { fetchAll(filters); }, []); // eslint-disable-line

  const handleReset = () => {
    const reset = { from_date: '', to_date: '', equipment_name: '' };
    setFilters(reset);
    fetchAll(reset);
  };

  const handleSuggestions = async () => {
    setSuggestionsState('loading');
    setSuggestions('');
    try {
      const res = await apiClient.post('/api/dashboard/suggestions', {
        from_date: filters.from_date || null,
        to_date: filters.to_date || null,
        equipment_name: filters.equipment_name || null,
      });
      setSuggestions(res.data.data);
      setSuggestionsState('done');
    } catch {
      setSuggestionsState('error');
      toast.error('示唆の生成に失敗しました');
    }
  };

  return (
    <div className="max-w-6xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-800 mb-1">ダッシュボード</h1>
        <p className="text-gray-500 text-sm">故障傾向の可視化・KPI 分析</p>
      </div>

      {/* フィルター */}
      <div className="bg-white border border-gray-200 rounded-lg p-4 mb-6 shadow-sm">
        <div className="flex flex-wrap gap-3 items-end">
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">開始日</label>
            <input type="date" value={filters.from_date}
              onChange={(e) => setFilters({ ...filters, from_date: e.target.value })}
              className="border border-gray-300 rounded px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">終了日</label>
            <input type="date" value={filters.to_date}
              onChange={(e) => setFilters({ ...filters, to_date: e.target.value })}
              className="border border-gray-300 rounded px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">設備名</label>
            <input type="text" placeholder="例: 設備A" value={filters.equipment_name}
              onChange={(e) => setFilters({ ...filters, equipment_name: e.target.value })}
              className="border border-gray-300 rounded px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <button onClick={() => fetchAll(filters)} disabled={loading}
            className="px-4 py-1.5 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 disabled:opacity-50 transition-colors">
            {loading ? '読込中...' : '適用'}
          </button>
          <button onClick={handleReset} disabled={loading}
            className="px-4 py-1.5 border border-gray-300 text-gray-600 text-sm rounded hover:bg-gray-50 disabled:opacity-50 transition-colors">
            リセット
          </button>
        </div>
      </div>

      {/* KPI カード */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <KpiCard label="総故障件数" value={summary ? `${summary.total_count} 件` : '---'} color="blue" />
        <KpiCard label="総修理コスト" value={summary ? `¥${summary.total_cost.toLocaleString()}` : '---'} color="red" />
        <KpiCard label="平均停止時間" value={summary ? `${summary.avg_downtime_hours} 時間` : '---'} color="amber" />
      </div>

      {/* チャート */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white border border-gray-200 rounded-lg p-5 shadow-sm">
          <h2 className="text-base font-semibold text-gray-700 mb-4">故障モード別件数</h2>
          {failureModes.length === 0 ? <EmptyState /> : (
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie data={failureModes} dataKey="count" nameKey="failure_mode"
                  cx="50%" cy="50%" outerRadius={90}>
                  {failureModes.map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
                </Pie>
                <Tooltip formatter={(value, _name, props) => [
                  `${value} 件 (${((props.payload.percent ?? 0) * 100).toFixed(1)}%)`,
                  props.payload.failure_mode,
                ]} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="bg-white border border-gray-200 rounded-lg p-5 shadow-sm">
          <h2 className="text-base font-semibold text-gray-700 mb-4">月次故障件数トレンド</h2>
          {trend.length === 0 ? <EmptyState /> : (
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={trend} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="month" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} allowDecimals={false} />
                <Tooltip formatter={(value) => [`${value} 件`, '故障件数']} />
                <Line type="monotone" dataKey="count" stroke="#3b82f6" strokeWidth={2} dot={{ r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="bg-white border border-gray-200 rounded-lg p-5 shadow-sm lg:col-span-2">
          <h2 className="text-base font-semibold text-gray-700 mb-4">設備別修理コスト TOP10</h2>
          {costTop10.length === 0 ? <EmptyState /> : (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={costTop10} layout="vertical" margin={{ top: 5, right: 30, left: 80, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" horizontal={false} />
                <XAxis type="number" tick={{ fontSize: 12 }}
                  tickFormatter={(v) => `¥${(v / 10000).toFixed(0)}万`} />
                <YAxis dataKey="equipment_name" type="category" tick={{ fontSize: 12 }} width={75} />
                <Tooltip formatter={(value) => [`¥${(value as number).toLocaleString()}`, '総修理コスト']} />
                <Bar dataKey="total_cost" fill="#3b82f6" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* 示唆出しカード */}
      <div className="mt-6 bg-white border border-gray-200 rounded-lg p-5 shadow-sm">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h2 className="text-base font-semibold text-gray-700">AI 改善施策の示唆</h2>
            <p className="text-xs text-gray-400 mt-0.5">現在の集計データをもとに Claude が改善提案を生成します</p>
          </div>
          <button
            onClick={handleSuggestions}
            disabled={suggestionsState === 'loading'}
            className="px-4 py-2 bg-purple-600 text-white text-sm rounded-lg hover:bg-purple-700 disabled:opacity-50 transition-colors flex items-center gap-2"
          >
            {suggestionsState === 'loading' ? (
              <>
                <span className="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                生成中...
              </>
            ) : '✦ 示唆を生成'}
          </button>
        </div>
        {suggestionsState === 'done' && suggestions && (
          <div className="bg-purple-50 border border-purple-100 rounded-lg p-4 text-sm text-gray-700 whitespace-pre-line leading-relaxed">
            {suggestions}
          </div>
        )}
        {suggestionsState === 'error' && (
          <p className="text-red-500 text-sm">示唆の生成に失敗しました。しばらくしてから再度お試しください。</p>
        )}
        {suggestionsState === 'idle' && (
          <p className="text-gray-400 text-sm">「示唆を生成」ボタンをクリックすると、現在表示中のデータに基づいた改善提案が表示されます。</p>
        )}
      </div>
    </div>
  );
}

function KpiCard({ label, value, color }: { label: string; value: string; color: 'blue' | 'red' | 'amber' }) {
  const colorMap = { blue: 'border-blue-200 bg-blue-50 text-blue-700', red: 'border-red-200 bg-red-50 text-red-700', amber: 'border-amber-200 bg-amber-50 text-amber-700' };
  return (
    <div className={`border rounded-lg p-5 shadow-sm ${colorMap[color]}`}>
      <p className="text-xs font-medium opacity-70 mb-1">{label}</p>
      <p className="text-2xl font-bold">{value}</p>
    </div>
  );
}

function EmptyState() {
  return <div className="flex items-center justify-center h-[260px] text-gray-400 text-sm">データがありません</div>;
}

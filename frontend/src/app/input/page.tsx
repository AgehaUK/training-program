'use client';

import { useEffect, useState } from 'react';
import { toast } from 'sonner';
import { apiClient } from '@/lib/api';

interface StructurizedResult {
  occurred_at: string | null;
  equipment_name: string | null;
  symptom: string | null;
  cause: string | null;
  action_taken: string | null;
  cost: number | null;
  downtime_hours: number | null;
  failure_mode: string | null;
}

interface FailureMode {
  id: number;
  name: string;
}

const SAMPLE_TEXT =
  '2025年3月15日、コンプレッサーB号機の吐出圧力が規定値を下回り警報発報。バルブパッキン劣化が原因。パッキン交換で対応。停止2時間、費用1.5万円。';

export default function InputPage() {
  const [text, setText] = useState('');
  const [structurizing, setStructurizing] = useState(false);
  const [result, setResult] = useState<StructurizedResult | null>(null);
  const [failureModes, setFailureModes] = useState<FailureMode[]>([]);
  const [saving, setSaving] = useState(false);
  const [sampleLoading, setSampleLoading] = useState(false);
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [csvLoading, setCsvLoading] = useState(false);

  useEffect(() => {
    apiClient.get('/api/failure-modes').then((res) => {
      setFailureModes(res.data.data ?? []);
    });
  }, []);

  const handleStructurize = async () => {
    setStructurizing(true);
    setResult(null);
    try {
      const res = await apiClient.post('/api/reports/structurize', { text });
      setResult(res.data.data);
    } catch {
      toast.error('構造化に失敗しました。しばらくしてから再度お試しください。');
    } finally {
      setStructurizing(false);
    }
  };

  const handleSave = async () => {
    if (!result) return;
    setSaving(true);
    try {
      await apiClient.post('/api/reports', {
        original_text: text,
        occurred_at: result.occurred_at ?? new Date().toISOString().split('T')[0],
        equipment_name: result.equipment_name ?? '不明',
        symptom: result.symptom ?? text.slice(0, 50),
        cause: result.cause,
        action_taken: result.action_taken,
        cost: result.cost,
        downtime_hours: result.downtime_hours,
        failure_mode: result.failure_mode ?? 'その他',
      });
      toast.success('故障レポートを保存しました');
      setText('');
      setResult(null);
    } catch {
      toast.error('保存に失敗しました');
    } finally {
      setSaving(false);
    }
  };

  const handleSampleInsert = async () => {
    setSampleLoading(true);
    try {
      const res = await apiClient.post('/api/reports/sample');
      toast.success(res.data.data.message);
    } catch {
      toast.error('サンプルデータの投入に失敗しました');
    } finally {
      setSampleLoading(false);
    }
  };

  const handleCsvImport = async () => {
    if (!csvFile) return;
    setCsvLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', csvFile);
      const res = await apiClient.post('/api/reports/import-csv', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      toast.success(res.data.data.message);
      setCsvFile(null);
    } catch {
      toast.error('CSVインポートに失敗しました');
    } finally {
      setCsvLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex justify-between items-start mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-800 mb-1">データ入力</h1>
          <p className="text-gray-500 text-sm">故障報告テキストを入力し、LLM で構造化して保存します</p>
        </div>
        <div className="flex flex-col items-end gap-2">
          <button
            onClick={handleSampleInsert}
            disabled={sampleLoading}
            className="text-sm px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 transition-colors"
          >
            {sampleLoading ? '投入中...' : 'サンプルデータを一括投入'}
          </button>
          <div className="flex items-center gap-2">
            <label className="text-sm px-4 py-2 border border-blue-300 text-blue-600 rounded-lg hover:bg-blue-50 cursor-pointer transition-colors">
              {csvFile ? csvFile.name : 'CSVファイルを選択'}
              <input
                type="file"
                accept=".csv"
                className="hidden"
                onChange={(e) => { setCsvFile(e.target.files?.[0] ?? null); }}
              />
            </label>
            <button
              onClick={handleCsvImport}
              disabled={!csvFile || csvLoading}
              className="text-sm px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              {csvLoading ? 'インポート中...' : 'CSVインポート'}
            </button>
          </div>
        </div>
      </div>

      {/* テキスト入力 */}
      <div className="mb-4">
        <div className="flex justify-between items-center mb-2">
          <label className="block text-sm font-medium text-gray-700">
            故障報告テキスト <span className="text-red-500">*</span>
          </label>
          <button
            type="button"
            onClick={() => setText(SAMPLE_TEXT)}
            className="text-xs text-blue-600 hover:underline"
          >
            サンプルを挿入
          </button>
        </div>
        <textarea
          rows={6}
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="例: 2025年3月15日、コンプレッサーB号機の圧力が低下。バルブパッキン劣化が原因。交換後復旧。ダウンタイム2時間、費用1.5万円。"
          className="w-full border border-gray-300 rounded-lg p-3 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <button
        onClick={handleStructurize}
        disabled={!text.trim() || structurizing}
        className="w-full py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
      >
        {structurizing ? '構造化中...' : 'LLM で構造化する'}
      </button>

      {/* 構造化結果 */}
      {result && (
        <div className="mt-6 bg-white border border-gray-200 rounded-lg p-5 shadow-sm">
          <h2 className="text-base font-semibold text-gray-700 mb-4">構造化結果（編集可能）</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Field
              label="発生日"
              value={result.occurred_at ?? ''}
              onChange={(v) => setResult({ ...result, occurred_at: v })}
            />
            <Field
              label="設備名"
              value={result.equipment_name ?? ''}
              onChange={(v) => setResult({ ...result, equipment_name: v })}
            />
            <Field
              label="症状"
              value={result.symptom ?? ''}
              onChange={(v) => setResult({ ...result, symptom: v })}
              className="md:col-span-2"
            />
            <Field
              label="原因"
              value={result.cause ?? ''}
              onChange={(v) => setResult({ ...result, cause: v || null })}
            />
            <Field
              label="対策"
              value={result.action_taken ?? ''}
              onChange={(v) => setResult({ ...result, action_taken: v || null })}
            />
            <Field
              label="コスト（円）"
              type="number"
              value={result.cost != null ? String(result.cost) : ''}
              onChange={(v) => setResult({ ...result, cost: v ? parseInt(v) : null })}
            />
            <Field
              label="停止時間（時間）"
              type="number"
              value={result.downtime_hours != null ? String(result.downtime_hours) : ''}
              onChange={(v) => setResult({ ...result, downtime_hours: v ? parseFloat(v) : null })}
            />
            {/* 故障モード ドロップダウン */}
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">故障モード</label>
              <select
                value={result.failure_mode ?? ''}
                onChange={(e) => setResult({ ...result, failure_mode: e.target.value || null })}
                className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">-- 選択 --</option>
                {failureModes.map((m) => (
                  <option key={m.id} value={m.name}>
                    {m.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="mt-5">
            <button
              onClick={handleSave}
              disabled={saving}
              className="px-6 py-2 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 disabled:opacity-50 transition-colors"
            >
              {saving ? '保存中...' : 'DB に保存する'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function Field({
  label,
  value,
  onChange,
  type = 'text',
  className = '',
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  type?: string;
  className?: string;
}) {
  return (
    <div className={className}>
      <label className="block text-xs font-medium text-gray-500 mb-1">{label}</label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
    </div>
  );
}

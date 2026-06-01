import Link from 'next/link';

export default function HomePage() {
  return (
    <div className="max-w-2xl mx-auto text-center py-16">
      <h1 className="text-3xl font-bold text-gray-800 mb-4">故障分析システム</h1>
      <p className="text-gray-500 mb-8">
        故障報告を構造化・分析・検索するシステムです。
      </p>
      <div className="flex justify-center gap-4">
        <Link
          href="/input"
          className="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
        >
          データ入力
        </Link>
        <Link
          href="/dashboard"
          className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition-colors"
        >
          ダッシュボード
        </Link>
        <Link
          href="/search"
          className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition-colors"
        >
          検索
        </Link>
      </div>
    </div>
  );
}

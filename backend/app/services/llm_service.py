"""
LLM サービス

ANTHROPIC_API_KEY が設定されていれば Claude を使用。
なければモック（正規表現ベース）にフォールバック。
"""
import json
import re
from typing import Dict, List, Optional

from app.config import settings


class StructurizedData:
    def __init__(self, data: Dict) -> None:
        self.occurred_at = data.get("occurred_at")
        self.equipment_name = data.get("equipment_name")
        self.symptom = data.get("symptom")
        self.cause = data.get("cause")
        self.action_taken = data.get("action_taken")
        self.cost = int(data["cost"]) if data.get("cost") is not None else None
        self.downtime_hours = float(data["downtime_hours"]) if data.get("downtime_hours") is not None else None
        self.failure_mode = data.get("failure_mode")

    def model_dump(self) -> Dict:
        return {
            "occurred_at": self.occurred_at,
            "equipment_name": self.equipment_name,
            "symptom": self.symptom,
            "cause": self.cause,
            "action_taken": self.action_taken,
            "cost": self.cost,
            "downtime_hours": self.downtime_hours,
            "failure_mode": self.failure_mode,
        }


def _mock_structurize(text: str, failure_mode_names: List[str]) -> StructurizedData:
    """正規表現・キーワードベースのモック構造化"""

    date_match = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日", text)
    occurred_at = None
    if date_match:
        y, m, d = date_match.groups()
        occurred_at = f"{y}-{int(m):02d}-{int(d):02d}"

    equip_match = re.search(
        r"([A-Za-z\u3040-\u30ff\u4e00-\u9fff]+(?:機|センサー|ポンプ|コンプレッサー|コンベア|プレス|モーター|バルブ|装置|設備)[A-Za-z0-9号]*)",
        text,
    )
    equipment_name = equip_match.group(1) if equip_match else None

    symptom_keywords = ["故障", "異音", "停止", "漏れ", "過熱", "エラー", "警報", "切断", "低下", "不良"]
    symptom = None
    for kw in symptom_keywords:
        if kw in text:
            idx = text.find(kw)
            start = max(0, idx - 10)
            end = min(len(text), idx + 15)
            symptom = text[start:end].strip("。、\n ")
            break
    if symptom is None:
        symptom = text[:50]

    cause_match = re.search(r"([^。、\n]{2,20}(?:劣化|破損|摩耗|腐食|過負荷|不良|故障)(?:が原因)?)", text)
    cause = cause_match.group(1) if cause_match else None

    action_match = re.search(r"([^。、\n]{2,20}(?:交換|修理|補修|清掃|調整|洗浄)(?:後|して|し)?)", text)
    action_taken = action_match.group(1) if action_match else None

    cost = None
    man_match = re.search(r"(\d+(?:\.\d+)?)\s*万円", text)
    yen_match = re.search(r"(\d+)\s*円", text)
    if man_match:
        cost = int(float(man_match.group(1)) * 10000)
    elif yen_match:
        cost = int(yen_match.group(1))

    downtime_hours = None
    time_match = re.search(r"(\d+(?:\.\d+)?)\s*時間", text)
    if time_match:
        downtime_hours = float(time_match.group(1))

    mode_keyword_map = {
        "劣化": ["劣化", "老朽"],
        "破損": ["破損", "割れ", "欠け", "切断"],
        "動作不良": ["動作不良", "誤動作", "不良"],
        "漏れ": ["漏れ", "リーク", "漏油", "漏水"],
        "過熱": ["過熱", "オーバーヒート", "高温"],
        "腐食": ["腐食", "錆", "さび"],
        "摩耗": ["摩耗", "すり減り"],
        "電気系統故障": ["電気", "電源", "インバーター", "センサー", "断線", "ショート"],
    }
    failure_mode = None
    for mode, keywords in mode_keyword_map.items():
        if any(kw in text for kw in keywords):
            if mode in failure_mode_names:
                failure_mode = mode
                break
    if failure_mode is None and failure_mode_names:
        failure_mode = failure_mode_names[-1]

    return StructurizedData(
        {
            "occurred_at": occurred_at,
            "equipment_name": equipment_name,
            "symptom": symptom,
            "cause": cause,
            "action_taken": action_taken,
            "cost": cost,
            "downtime_hours": downtime_hours,
            "failure_mode": failure_mode,
        }
    )


def _call_claude(prompt: str) -> str:
    """Claude API を呼び出してテキストを返す"""
    import anthropic

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


class LLMService:
    def __init__(self) -> None:
        self._use_mock = not settings.anthropic_api_key

    def structurize(self, text: str, failure_mode_names: List[str]) -> StructurizedData:
        if self._use_mock:
            return _mock_structurize(text, failure_mode_names)
        return self._claude_structurize(text, failure_mode_names)

    def _claude_structurize(self, text: str, failure_mode_names: List[str]) -> StructurizedData:
        modes_str = "、".join(failure_mode_names)
        prompt = f"""以下の故障報告テキストから情報を抽出し、JSONのみを返してください。説明文は不要です。

故障モードは必ず次のいずれかを選択してください: {modes_str}

テキスト:
{text}

出力形式（JSONのみ）:
{{
  "occurred_at": "YYYY-MM-DD または null",
  "equipment_name": "設備名 または null",
  "symptom": "症状・現象",
  "cause": "原因 または null",
  "action_taken": "対策 または null",
  "cost": 数値（円）または null,
  "downtime_hours": 数値（時間）または null,
  "failure_mode": "故障モード名 または null"
}}"""

        raw = _call_claude(prompt)
        # JSONブロックを抽出
        json_match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not json_match:
            raise ValueError(f"JSONが取得できませんでした: {raw}")
        data = json.loads(json_match.group())
        return StructurizedData(data)

    def generate_suggestions(self, summary: dict, failure_modes: list, trend: list) -> str:
        """集計データから改善施策の示唆テキストを生成する"""
        if self._use_mock:
            return self._mock_suggestions()

        prompt = f"""あなたは設備保全の専門家です。以下の故障分析データをもとに、具体的な改善施策を3〜5点、箇条書きで提案してください。

## 集計データ

### KPI
- 総故障件数: {summary.get('total_count', 0)} 件
- 総修理コスト: {summary.get('total_cost', 0):,} 円
- 平均停止時間: {summary.get('avg_downtime_hours', 0)} 時間

### 故障モード別件数（上位）
{chr(10).join(f"- {m['failure_mode']}: {m['count']}件" for m in failure_modes[:5])}

### 月次トレンド（直近）
{chr(10).join(f"- {t['month']}: {t['count']}件" for t in trend[-3:])}

## 出力形式
改善施策を3〜5点、箇条書きで簡潔に記載してください。各項目は1〜2文で。"""

        return _call_claude(prompt)

    def _mock_suggestions(self) -> str:
        return """• 劣化・摩耗による故障が多いため、定期点検サイクルの見直しと予防交換の実施を推奨します。
• 修理コストの高い設備を優先的に予知保全の対象とし、センサー監視の導入を検討してください。
• 故障モードの傾向から、消耗部品の在庫を常時確保し、停止時間の短縮を図ることが重要です。
• 月次トレンドを継続的にモニタリングし、件数増加が見られた際は速やかに原因調査を行ってください。"""


llm_service = LLMService()

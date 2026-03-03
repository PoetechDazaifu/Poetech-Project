import json
import re

# ===== テスト =====
def test_detection():
    test_data = [
        {"句": "春の\u2F08よ花が咲く", "expected": True,  "note": "「人」が康熙部首⼈(U+2F08)"},
        {"句": "秋の空\u2FBB翔ける鳥", "expected": True,  "note": "「飛」が康熙部首⾶(U+2FBB)"},
        {"句": "紅唐子とふ椿一枝をいただきて", "expected": False, "note": "正常な句"},
    ]

    print("===== テスト実行 =====")
    all_passed = True
    for t in test_data:
        found = any('\u2E80' <= c <= '\u2FD5' for c in t["句"])
        result = "✅ PASS" if found == t["expected"] else "❌ FAIL"
        if found != t["expected"]:
            all_passed = False
        print(f"  {result} | {t['note']}")
        print(f"         | 句: {t['句']}")
    
    print(f"\n検出エンジン: {'正常' if all_passed else '異常'}")
    print("=" * 22)

test_detection()

# ===== 本番チェック =====
with open('poems.json', encoding='utf-8') as f:
    data = json.load(f)

hits = []
for i, item in enumerate(data):
    ku = item.get('句', '')
    contaminated = [(hex(ord(c)), c) for c in ku if '\u2E80' <= c <= '\u2FD5']
    if contaminated:
        hits.append({
            'index': i,
            '句': ku,
            '汚染文字': contaminated
        })

if hits:
    print(f"⚠️ 汚染あり：{len(hits)}件")
    for h in hits:
        print(f"\n  [{h['index']}] {h['句']}")
        print(f"  汚染文字: {h['汚染文字']}")
else:
    print("✅ 汚染なし")
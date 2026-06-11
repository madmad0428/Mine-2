"""
analyze_results.py
==================
채점 완료된 CSV를 불러와 프롬프트별 / 카테고리별 통계 분석
실행 전제: experiment_results.csv의 '채점(0/1/2)' 열이 모두 입력된 상태
"""

import csv
import os
from collections import defaultdict

INPUT_CSV = "experiment_results.csv"
OUTPUT_REPORT = "analysis_report.txt"

PROMPT_TYPES = ["zero_shot", "cot", "role", "few_shot"]
CATEGORIES = ["A", "B", "C", "D"]
MAX_SCORE = 2

def load_results(path: str) -> list[dict]:
    rows = []
    with open(path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            score_raw = row.get("채점(0/1/2)", "").strip()
            if score_raw == "":
                continue  # 채점 미완료 행 스킵
            try:
                row["score"] = int(score_raw)
                rows.append(row)
            except ValueError:
                continue
    return rows

def compute_stats(scores: list[int]) -> dict:
    if not scores:
        return {"count": 0, "mean": 0.0, "accuracy_2": 0.0, "accuracy_1up": 0.0, "dist": {}}
    count = len(scores)
    mean = sum(scores) / count
    accuracy_2 = scores.count(2) / count * 100       # Truth-Bound 비율
    accuracy_1up = (scores.count(1) + scores.count(2)) / count * 100  # 1점 이상 비율
    dist = {0: scores.count(0), 1: scores.count(1), 2: scores.count(2)}
    return {
        "count": count,
        "mean": round(mean, 3),
        "accuracy_2": round(accuracy_2, 1),
        "accuracy_1up": round(accuracy_1up, 1),
        "dist": dist
    }

def analyze():
    if not os.path.exists(INPUT_CSV):
        print(f"[오류] {INPUT_CSV} 파일이 없습니다.")
        return

    data = load_results(INPUT_CSV)
    if not data:
        print("채점된 데이터가 없습니다. '채점(0/1/2)' 열을 먼저 채워주세요.")
        return

    print(f"총 {len(data)}개 채점 완료 행 로드\n")

    lines = []
    lines.append("=" * 60)
    lines.append("책 표지 AI 분석 실험 결과 리포트")
    lines.append("=" * 60)

    # ── 1. 프롬프트 유형별 통계 ──────────────────────────────
    lines.append("\n[1] 프롬프트 유형별 성능")
    lines.append("-" * 40)
    prompt_scores = defaultdict(list)
    for row in data:
        prompt_scores[row["프롬프트유형"]].append(row["score"])

    for pt in PROMPT_TYPES:
        scores = prompt_scores.get(pt, [])
        s = compute_stats(scores)
        lines.append(f"\n▶ {pt}")
        lines.append(f"  샘플 수     : {s['count']}")
        lines.append(f"  평균 점수   : {s['mean']} / {MAX_SCORE}")
        lines.append(f"  2점(Truth)  : {s['accuracy_2']}%")
        lines.append(f"  1점 이상    : {s['accuracy_1up']}%")
        lines.append(f"  분포 (0/1/2): {s['dist'].get(0,0)} / {s['dist'].get(1,0)} / {s['dist'].get(2,0)}")

    # ── 2. 카테고리별 통계 ───────────────────────────────────
    lines.append("\n\n[2] 카테고리별 성능")
    lines.append("-" * 40)
    category_scores = defaultdict(list)
    for row in data:
        category_scores[row["카테고리"]].append(row["score"])

    cat_labels = {
        "A": "A - 시각적 방해 (소품 배치)",
        "B": "B - 물리적 노이즈 (빛/그림자/손가락)",
        "C": "C - 서적 조작 (사전지식 검증)",
        "D": "D - 대조군"
    }
    for cat in CATEGORIES:
        scores = category_scores.get(cat, [])
        s = compute_stats(scores)
        lines.append(f"\n▶ {cat_labels.get(cat, cat)}")
        lines.append(f"  샘플 수     : {s['count']}")
        lines.append(f"  평균 점수   : {s['mean']} / {MAX_SCORE}")
        lines.append(f"  2점(Truth)  : {s['accuracy_2']}%")
        lines.append(f"  1점 이상    : {s['accuracy_1up']}%")
        lines.append(f"  분포 (0/1/2): {s['dist'].get(0,0)} / {s['dist'].get(1,0)} / {s['dist'].get(2,0)}")

    # ── 3. 프롬프트 × 카테고리 교차 분석 ────────────────────
    lines.append("\n\n[3] 프롬프트 × 카테고리 교차 분석 (평균 점수)")
    lines.append("-" * 40)
    header = f"{'':12}" + "".join(f"{cat:>8}" for cat in CATEGORIES)
    lines.append(header)

    for pt in PROMPT_TYPES:
        row_str = f"{pt:12}"
        for cat in CATEGORIES:
            matched = [r["score"] for r in data if r["프롬프트유형"] == pt and r["카테고리"] == cat]
            if matched:
                avg = round(sum(matched) / len(matched), 2)
                row_str += f"{avg:>8}"
            else:
                row_str += f"{'N/A':>8}"
        lines.append(row_str)

    # ── 4. 오류 유형 분포 (입력된 경우만) ───────────────────
    lines.append("\n\n[4] KCI 오류 유형 분포")
    lines.append("-" * 40)
    error_counts = defaultdict(int)
    for row in data:
        err = row.get("오류유형", "").strip()
        if err:
            error_counts[err] += 1
    if error_counts:
        for err, cnt in sorted(error_counts.items(), key=lambda x: -x[1]):
            lines.append(f"  {err}: {cnt}건")
    else:
        lines.append("  오류유형 미입력 (CSV에서 직접 기재 후 재실행)")

    lines.append("\n" + "=" * 60)

    report = "\n".join(lines)
    print(report)

    with open(OUTPUT_REPORT, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\n리포트 저장 완료: {OUTPUT_REPORT}")

if __name__ == "__main__":
    analyze()

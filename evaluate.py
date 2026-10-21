"""Offline, hand-authored retrieval smoke benchmark; no model API calls."""
import json
from core import chunk_pages, retrieve

PAGES = [
    'Applications close on October 30. Submit the application form online.',
    'Tuition fees are paid in two instalments. Housing is not included.',
    'The library opens at 09:00 and closes at 20:00 on weekdays.',
    '장학금 신청 마감일은 11월 15일입니다. 신청서는 온라인으로 제출합니다.',
    '기숙사 입주일은 3월 2일입니다. 침구는 개인이 준비해야 합니다.',
    '실험실 안전 교육은 매주 월요일 오전 10시에 시작합니다.',
]
CASES = [
    ('When do applications close?', [1]),
    ('How are tuition fees paid?', [2]),
    ('When does the library open?', [3]),
    ('장학금 신청 마감일은 언제인가요?', [4]),
    ('기숙사 입주일은 언제인가요?', [5]),
    ('실험실 안전 교육은 언제 시작하나요?', [6]),
    ('What is the university president’s name?', []),
    ('식당 점심 가격은 얼마인가요?', []),
]


def score_ranking(ranked_pages, relevant_pages):
    # Several chunks may refer to one page; count that page once.
    ranked = list(dict.fromkeys(ranked_pages))
    relevant = set(relevant_pages)
    if not relevant:
        return {'false_positive': bool(ranked)}
    found = len(set(ranked) & relevant)
    first = next((i for i, page in enumerate(ranked, 1) if page in relevant), None)
    return {'recall': found / len(relevant),
            'precision': found / len(ranked) if ranked else 0.0,
            'reciprocal_rank': 1 / first if first else 0.0}


def evaluate(top_k=4):
    if type(top_k) is not int or top_k < 1:
        raise ValueError('top_k must be a positive integer')
    chunks = chunk_pages(PAGES)
    rows = []
    for question, expected in CASES:
        pages = [chunk.page for chunk, _ in retrieve(chunks, question, top_k)]
        rows.append({'question': question, 'expected_pages': expected,
                     'retrieved_pages': pages, **score_ranking(pages, expected)})
    answerable = [row for row in rows if row['expected_pages']]
    unanswerable = [row for row in rows if not row['expected_pages']]
    return {'benchmark': 'hand-authored-en-ko-v1', 'top_k_chunks': top_k,
            'notice': 'Synthetic same-language retrieval smoke test, not real-world accuracy or answer correctness. Any nonzero lexical match is returned.',
            'answerable_queries': len(answerable), 'unanswerable_queries': len(unanswerable),
            'mean_page_recall': sum(r['recall'] for r in answerable) / len(answerable),
            'mean_page_precision': sum(r['precision'] for r in answerable) / len(answerable),
            'mean_reciprocal_rank': sum(r['reciprocal_rank'] for r in answerable) / len(answerable),
            'unanswerable_retrieval_rate': sum(r['false_positive'] for r in unanswerable) / len(unanswerable),
            'queries': rows}


if __name__ == '__main__':
    print(json.dumps(evaluate(), ensure_ascii=False, indent=2))

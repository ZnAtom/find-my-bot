"""Lexical and hybrid retrieval helpers for the small campus item corpus."""

from collections.abc import Mapping
import math
import re
from typing import Any

try:
    import jieba
except ImportError:  # Keep the backend importable before dependencies are installed.
    jieba = None

try:
    from rank_bm25 import BM25L
except ImportError:  # A small fallback keeps local development usable.
    BM25L = None


_TOKEN_RE = re.compile(r"[\u4e00-\u9fff]+|[a-z0-9]+", re.IGNORECASE)
_SEARCH_FIELDS = ("item_name", "item_type", "description")
_QUERY_EXPANSIONS = {
    "书": ("书籍", "教材", "课本", "词典", "图书", "读物"),
    "校园卡": ("一卡通", "校园一卡通", "学生卡"),
    "一卡通": ("校园卡", "校园一卡通", "学生卡"),
    "学生卡": ("校园卡", "一卡通", "校园一卡通"),
    "学生证": ("学生卡", "证件", "证件卡片"),
}


def _value(source: Any, field: str) -> str:
    if isinstance(source, Mapping):
        value = source.get(field)
    else:
        try:
            value = source[field]
        except (KeyError, IndexError, TypeError):
            value = getattr(source, field, None)
    return str(value).strip() if value else ""


def normalize_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def _compact_text(value: Any) -> str:
    return "".join(_TOKEN_RE.findall(normalize_text(value)))


def tokenize(value: Any) -> list[str]:
    text = normalize_text(value)
    tokens: list[str] = []
    for chunk in _TOKEN_RE.findall(text):
        if re.fullmatch(r"[\u4e00-\u9fff]+", chunk):
            if jieba is not None:
                tokens.extend(token for token in jieba.lcut(chunk) if token.strip())
            # Character and bigram tokens make short aliases such as 校园卡/校园一卡通 overlap.
            tokens.extend(chunk)
            tokens.extend(chunk[index:index + 2] for index in range(len(chunk) - 1))
        else:
            tokens.append(chunk)
    return tokens


def _meaningful_tokens(value: Any) -> set[str]:
    compact = _compact_text(value)
    allow_single_character = len(compact) == 1
    return {
        token
        for token in tokenize(value)
        if not re.fullmatch(r"[\u4e00-\u9fff]", token) or allow_single_character
    }


def build_search_text(source: Any) -> str:
    """Build content-only search text; location must not affect search results."""
    fields = [_value(source, field) for field in _SEARCH_FIELDS]
    item_name, item_type, description = fields
    return " ".join(
        part
        for part in (
            item_name,
            item_name,
            item_type,
            item_type,
            description,
        )
        if part
    )


def lexical_relevance(query: Any, row: Any) -> float:
    """Return a 0-1 lexical relevance score and reject accidental single-character hits."""
    compact_query = _compact_text(query)
    if not compact_query:
        return 0.0

    item_name = _compact_text(_value(row, "item_name"))
    item_type = _compact_text(_value(row, "item_type"))
    description = _compact_text(_value(row, "description"))

    # A single Chinese character inside a compound word is too ambiguous for substring matching.
    allow_substring_match = not re.fullmatch(r"[\u4e00-\u9fff]", compact_query)
    if allow_substring_match and compact_query in item_name:
        return 1.0
    if allow_substring_match and compact_query in item_type:
        return 0.95

    expanded_terms = _QUERY_EXPANSIONS.get(compact_query)
    if expanded_terms:
        if any(term in item_name or term in item_type for term in expanded_terms):
            return 0.95
    if allow_substring_match and compact_query in description:
        return 0.85
    if expanded_terms:
        if any(term in description for term in expanded_terms):
            return 0.85
        return 0.0

    query_tokens = _meaningful_tokens(query)
    if not query_tokens:
        return 0.0
    document_tokens = _meaningful_tokens(build_search_text(row))
    coverage = len(query_tokens & document_tokens) / len(query_tokens)
    if len(query_tokens) > 1 and coverage < 0.5:
        return 0.0
    return min(0.75, 0.45 + 0.3 * coverage) if coverage else 0.0


def _fallback_bm25_scores(query_tokens: list[str], documents: list[list[str]]) -> list[float]:
    if not query_tokens or not documents:
        return [0.0] * len(documents)

    document_frequency: dict[str, int] = {}
    lengths = []
    for document in documents:
        lengths.append(len(document))
        for token in set(document):
            document_frequency[token] = document_frequency.get(token, 0) + 1

    average_length = sum(lengths) / len(lengths) if lengths else 0
    scores = []
    for document, length in zip(documents, lengths):
        frequencies: dict[str, int] = {}
        for token in document:
            frequencies[token] = frequencies.get(token, 0) + 1

        score = 0.0
        for token in query_tokens:
            frequency = frequencies.get(token, 0)
            if not frequency:
                continue
            df = document_frequency.get(token, 0)
            idf = math.log(1 + (len(documents) - df + 0.5) / (df + 0.5))
            denominator = frequency + 1.5 * (1 - 0.75 + 0.75 * length / max(average_length, 1))
            score += idf * frequency * 2.5 / denominator
        scores.append(score)
    return scores


def bm25_recall(query: Any, rows: list[Any], limit: int = 10) -> list[Any]:
    if not rows or limit <= 0:
        return []

    compact_query = _compact_text(query)
    expanded_query = " ".join((str(query), *_QUERY_EXPANSIONS.get(compact_query, ())))
    query_tokens = tokenize(expanded_query)
    documents = [tokenize(build_search_text(row)) for row in rows]
    if BM25L is not None:
        # BM25L avoids Okapi's zero-IDF degeneration on very small corpora.
        scores = BM25L(documents).get_scores(query_tokens)
    else:
        scores = _fallback_bm25_scores(query_tokens, documents)

    relevance = [lexical_relevance(query, row) for row in rows]
    ranked_indexes = sorted(
        (index for index in range(len(rows)) if relevance[index] > 0),
        key=lambda index: (relevance[index], scores[index], -index),
        reverse=True,
    )
    return [rows[index] for index in ranked_indexes[:limit]]


def filter_vector_recall(
    rows: list[Any],
    *,
    minimum_similarity: float = 0.48,
    maximum_drop: float = 0.08,
) -> list[Any]:
    """Keep vector hits that are both absolutely relevant and close to the best hit."""
    scored_rows = []
    for row in rows:
        try:
            similarity = float(row["similarity"])
        except (KeyError, TypeError, ValueError):
            continue
        scored_rows.append((row, similarity))
    if not scored_rows:
        return []

    best_similarity = max(similarity for _, similarity in scored_rows)
    cutoff = max(minimum_similarity, best_similarity - maximum_drop)
    return [row for row, similarity in scored_rows if similarity >= cutoff]


def hybrid_match_score(query: Any, row: Any) -> float:
    """Calibrate exact lexical hits for display while retaining honest vector-only scores."""
    lexical_score = lexical_relevance(query, row)
    try:
        vector_score = float(row["similarity"])
    except (KeyError, TypeError, ValueError):
        vector_score = 0.0
    vector_score = max(0.0, min(1.0, vector_score))
    calibrated_vector = max(0.0, min(1.0, (vector_score - 0.3) / 0.5))

    if lexical_score >= 0.95:
        return min(0.98, 0.9 + 0.1 * calibrated_vector)
    if lexical_score > 0:
        return min(0.95, 0.65 * lexical_score + 0.35 * calibrated_vector)
    return vector_score


def rrf_fuse(
    vector_rows: list[Any],
    bm25_rows: list[Any],
    limit: int = 10,
    *,
    vector_weight: float = 0.3,
    bm25_weight: float = 0.7,
    rrf_k: int = 60,
) -> list[tuple[Any, float]]:
    """Fuse ranked lists while keeping score scales independent."""
    by_id: dict[Any, Any] = {}
    scores: dict[Any, float] = {}

    for rank, row in enumerate(bm25_rows, start=1):
        row_id = row["id"]
        by_id[row_id] = row
        scores[row_id] = scores.get(row_id, 0.0) + bm25_weight / (rrf_k + rank)

    for rank, row in enumerate(vector_rows, start=1):
        row_id = row["id"]
        by_id[row_id] = row
        scores[row_id] = scores.get(row_id, 0.0) + vector_weight / (rrf_k + rank)

    ranked_ids = sorted(scores, key=lambda row_id: scores[row_id], reverse=True)
    return [(by_id[row_id], scores[row_id]) for row_id in ranked_ids[:limit]]


def rule_rerank(fused_rows: list[tuple[Any, float]], query: Any) -> list[tuple[Any, float]]:
    """Apply small exact-field boosts for the create-time match check."""
    query_type = normalize_text(_value(query, "item_type"))
    query_name_tokens = set(tokenize(_value(query, "item_name")))
    query_location_tokens = set(tokenize(_value(query, "location")))
    reranked = []

    for row, score in fused_rows:
        adjusted = score
        row_type = normalize_text(_value(row, "item_type"))
        row_name_tokens = set(tokenize(_value(row, "item_name")))
        row_location_tokens = set(tokenize(_value(row, "location")))
        if query_type and row_type == query_type:
            adjusted *= 1.35
        if query_name_tokens and query_name_tokens & row_name_tokens:
            adjusted *= 1.2
        if query_location_tokens and query_location_tokens & row_location_tokens:
            adjusted *= 1.15
        reranked.append((row, adjusted))

    return sorted(reranked, key=lambda entry: entry[1], reverse=True)

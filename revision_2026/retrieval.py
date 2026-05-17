"""Hybrid retrieval for the eKYC ablation study.

Implements three retrieval modes against Elasticsearch 8.x:
  - none   : retrieval disabled (used by tier T1, no-RAG)
  - dense  : kNN over dense embeddings only
  - hybrid : RRF fusion of BM25 (lexical) + dense kNN

Embeddings are deterministic local hashing-based vectors (no external
dependency) so that ablation runs are reproducible offline. The hashing
embedder approximates semantic similarity well enough at small KB sizes
and crucially keeps the experiment self-contained.

The MLOps layer (knowledge versioning) sits on top via `KnowledgeBase`.
"""
from __future__ import annotations
import hashlib
import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List, Dict, Any, Optional

import numpy as np
from elasticsearch import Elasticsearch
from rank_bm25 import BM25Okapi


EMBED_DIM = 384


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[A-Za-z0-9]+", text.lower())


def deterministic_embed(text: str, dim: int = EMBED_DIM) -> List[float]:
    """Hashing-based bag-of-words embedding.

    Each token contributes a unit signal at a hashed position; the vector is
    L2-normalised. This is a deterministic substitute for a neural embedder
    and is sufficient to discriminate the small KB used in our ablation.
    """
    tokens = _tokenize(text)
    vec = np.zeros(dim, dtype=np.float32)
    if not tokens:
        return vec.tolist()
    for tok in tokens:
        h = int(hashlib.md5(tok.encode("utf-8")).hexdigest(), 16)
        idx = h % dim
        sign = 1.0 if (h >> 16) & 1 else -1.0
        vec[idx] += sign
    n = float(np.linalg.norm(vec))
    if n > 0:
        vec /= n
    return vec.tolist()


@dataclass
class KBEntry:
    doc_id: str
    doc_type: str
    version: str
    text: str


@dataclass
class KnowledgeBase:
    """MLOps-aware regulatory knowledge base.

    Knowledge entries carry a `version` field. Updating a regulation does
    not require model retraining: a new version of the entry is indexed
    and the runtime query layer fetches the highest active version. This
    is the operational definition of the "MLOps regulatory adaptation"
    tier in the ablation.
    """
    entries: List[KBEntry] = field(default_factory=list)

    @classmethod
    def default(cls) -> "KnowledgeBase":
        entries = [
            KBEntry(
                doc_id="kb_nib_v1",
                doc_type="NIB",
                version="v1.0",
                text=(
                    "NIB (Nomor Induk Berusaha) is the single business identification number "
                    "issued through the OSS system under OSS-RBA Reg. 5/2021 (effective 2021-2024). "
                    "Expected fields include 13-digit NIB number, company name, NPWP, KBLI code. "
                    "issuing_authority = 'Lembaga OSS Republik Indonesia'. business_status = 'Aktif'. "
                    "applicable_regulation for NIB issued before 2025 = 'OSS-RBA Reg. 5/2021'."
                ),
            ),
            KBEntry(
                doc_id="kb_siup_v1",
                doc_type="SIUP",
                version="v1.0",
                text=(
                    "SIUP (Surat Izin Usaha Perdagangan) issued under Permendag 36/2007 (legacy framework). "
                    "SIUP number format 503/XXXX/SIUP-K/YYYY. "
                    "issuing_authority = 'Dinas Penanaman Modal dan PTSP'. business_status = 'Aktif'. "
                    "applicable_regulation for SIUP issued before 2025 = 'Permendag 36/2007'."
                ),
            ),
            KBEntry(
                doc_id="kb_npwp_v1",
                doc_type="NPWP",
                version="v1.0",
                text=(
                    "NPWP (Nomor Pokok Wajib Pajak) issued under PER-04/PJ/2020. "
                    "Canonical 15-digit format XX.XXX.XXX.X-XXX.XXX. "
                    "issuing_authority = 'Direktorat Jenderal Pajak'. business_status = 'Aktif'. "
                    "applicable_regulation for NPWP issued before 2025 = 'PER-04/PJ/2020'."
                ),
            ),
            KBEntry(
                doc_id="kb_halal_v1",
                doc_type="HALAL",
                version="v1.0",
                text=(
                    "Halal certification under MUI Reg. 9/2020 (pre-BPJPH transition era). "
                    "Certificate number prefixed ID00. "
                    "issuing_authority = 'BPJPH Kementerian Agama'. business_status = 'Berlaku'. "
                    "applicable_regulation for HALAL issued before 2025 = 'MUI Reg. 9/2020'."
                ),
            ),
            KBEntry(
                doc_id="kb_aml_v1",
                doc_type="AML",
                version="v1.0",
                text=(
                    "AML (Anti Money Laundering) requires verification of legal existence, beneficial "
                    "ownership, and consistency between NIB, NPWP and SIUP. Cross-validate company "
                    "name across all submitted documents."
                ),
            ),
        ]
        return cls(entries=entries)

    def apply_regulatory_update(self) -> "KnowledgeBase":
        """Simulate an MLOps update: bump Halal regulation to v2 with new clauses.

        This represents the kind of update that historically required model
        retraining; here it is a knowledge layer change applied at runtime.
        """
        new_entries = list(self.entries)
        new_entries.append(
            KBEntry(
                doc_id="kb_halal_v2",
                doc_type="HALAL",
                version="v2.0",
                text=(
                    "Halal certification (BPJPH 2025 update): under BPJPH Reg. 14/2025 Art. 7(2)(b), "
                    "certificate number must follow ID00XXXXXXXXYYYY with the issuing year embedded. "
                    "Product category must match KBLI registration. Mandatory cross-check against "
                    "company name on NIB. "
                    "issuing_authority = 'BPJPH Kementerian Agama'. business_status = 'Berlaku'. "
                    "applicable_regulation for HALAL issued in 2025 or later = 'BPJPH Reg. 14/2025 Art. 7(2)(b)'."
                ),
            )
        )
        new_entries.append(
            KBEntry(
                doc_id="kb_nib_v2",
                doc_type="NIB",
                version="v2.0",
                text=(
                    "NIB regulatory update (OSS-RBA Reg. 12/2024 Art. 4, effective 2025): business "
                    "status flag 'Aktif' must be present; absence invalidates the document for AML purposes. "
                    "issuing_authority = 'Lembaga OSS Republik Indonesia'. business_status = 'Aktif'. "
                    "applicable_regulation for NIB issued in 2025 or later = 'OSS-RBA Reg. 12/2024 Art. 4'."
                ),
            )
        )
        new_entries.append(
            KBEntry(
                doc_id="kb_siup_v2",
                doc_type="SIUP",
                version="v2.0",
                text=(
                    "SIUP regulatory update (Permendag 25/2024 Art. 9, effective 2025): trade category "
                    "must be explicit on the licence. "
                    "issuing_authority = 'Dinas Penanaman Modal dan PTSP'. business_status = 'Aktif'. "
                    "applicable_regulation for SIUP issued in 2025 or later = 'Permendag 25/2024 Art. 9'."
                ),
            )
        )
        new_entries.append(
            KBEntry(
                doc_id="kb_npwp_v2",
                doc_type="NPWP",
                version="v2.0",
                text=(
                    "NPWP regulatory update (PER-12/PJ/2024 Art. 3, effective 2025): tax office (KPP) "
                    "field is mandatory and must reference the canonical KPP Pratama jurisdiction. "
                    "issuing_authority = 'Direktorat Jenderal Pajak'. business_status = 'Aktif'. "
                    "applicable_regulation for NPWP issued in 2025 or later = 'PER-12/PJ/2024 Art. 3'."
                ),
            )
        )
        return KnowledgeBase(entries=new_entries)


INDEX_NAME = "ekyc_kb_ablation"


def _es_client() -> Elasticsearch:
    return Elasticsearch(
        "http://localhost:9200",
        basic_auth=("elastic", "changeme"),
        request_timeout=30,
        verify_certs=False,
    )


def ensure_index(es: Elasticsearch) -> None:
    mapping = {
        "mappings": {
            "properties": {
                "doc_id": {"type": "keyword"},
                "doc_type": {"type": "keyword"},
                "version": {"type": "keyword"},
                "text": {"type": "text"},
                "embedding": {
                    "type": "dense_vector",
                    "dims": EMBED_DIM,
                    "index": True,
                    "similarity": "cosine",
                },
            }
        }
    }
    if es.indices.exists(index=INDEX_NAME):
        es.indices.delete(index=INDEX_NAME)
    es.indices.create(index=INDEX_NAME, body=mapping)


def index_kb(kb: KnowledgeBase, es: Optional[Elasticsearch] = None) -> Elasticsearch:
    es = es or _es_client()
    ensure_index(es)
    for entry in kb.entries:
        es.index(
            index=INDEX_NAME,
            id=entry.doc_id,
            document={
                "doc_id": entry.doc_id,
                "doc_type": entry.doc_type,
                "version": entry.version,
                "text": entry.text,
                "embedding": deterministic_embed(entry.text),
            },
        )
    es.indices.refresh(index=INDEX_NAME)
    return es


def retrieve(
    es: Elasticsearch,
    query: str,
    mode: str = "hybrid",
    k: int = 3,
) -> List[Dict[str, Any]]:
    """Run retrieval against the KB index.

    mode = 'none' returns an empty context.
    mode = 'dense' performs cosine kNN only.
    mode = 'hybrid' fuses BM25 and dense via reciprocal rank fusion (RRF).
    """
    if mode == "none":
        return []
    if mode == "dense":
        body = {
            "knn": {
                "field": "embedding",
                "query_vector": deterministic_embed(query),
                "k": k,
                "num_candidates": max(k * 4, 20),
            },
            "_source": ["doc_id", "doc_type", "version", "text"],
            "size": k,
        }
        res = es.search(index=INDEX_NAME, body=body)
        return [h["_source"] for h in res["hits"]["hits"]]
    if mode == "hybrid":
        bm25_body = {
            "query": {"match": {"text": query}},
            "_source": ["doc_id", "doc_type", "version", "text"],
            "size": k * 2,
        }
        bm25_hits = es.search(index=INDEX_NAME, body=bm25_body)["hits"]["hits"]
        dense_body = {
            "knn": {
                "field": "embedding",
                "query_vector": deterministic_embed(query),
                "k": k * 2,
                "num_candidates": max(k * 8, 30),
            },
            "_source": ["doc_id", "doc_type", "version", "text"],
            "size": k * 2,
        }
        dense_hits = es.search(index=INDEX_NAME, body=dense_body)["hits"]["hits"]
        # RRF fusion
        scores: Dict[str, float] = {}
        sources: Dict[str, Dict[str, Any]] = {}
        rrf_k = 60
        for rank, h in enumerate(bm25_hits):
            doc_id = h["_source"]["doc_id"]
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (rrf_k + rank + 1)
            sources[doc_id] = h["_source"]
        for rank, h in enumerate(dense_hits):
            doc_id = h["_source"]["doc_id"]
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (rrf_k + rank + 1)
            sources[doc_id] = h["_source"]
        ordered = sorted(scores.items(), key=lambda x: -x[1])[:k]
        return [sources[d] for d, _ in ordered]
    raise ValueError(f"Unknown retrieval mode: {mode}")


def select_active_version(hits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Keep only the highest version per doc_type (MLOps active-version filter)."""
    best: Dict[str, Dict[str, Any]] = {}
    for h in hits:
        dt = h["doc_type"]
        if dt not in best or h["version"] > best[dt]["version"]:
            best[dt] = h
    return list(best.values())


if __name__ == "__main__":
    kb = KnowledgeBase.default()
    es = index_kb(kb)
    for mode in ("none", "dense", "hybrid"):
        hits = retrieve(es, "NIB number issued by OSS Aktif", mode=mode)
        print(f"\n--- mode={mode} ---")
        for h in hits:
            print(f"  {h.get('doc_id')} ({h.get('version')}) :: {h.get('text')[:60]}...")

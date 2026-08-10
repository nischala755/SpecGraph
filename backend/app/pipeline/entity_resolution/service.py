from __future__ import annotations
import gc
import os
import re
from typing import Callable
from datasketch import MinHash, MinHashLSH
from rapidfuzz.fuzz import ratio
from app.domain.models import Candidate

def norm(s: str | None) -> str: return re.sub(r"[\W_]", "", (s or "").lower()).lstrip("0")
def _mh(text: str) -> MinHash:
    m = MinHash(num_perm=64)
    for i in range(max(1, len(text)-2)): m.update(text[i:i+3].encode())
    return m
def _semantic_scores(candidates: list[Candidate]) -> Callable[[int, int], float]:
    """Local CPU all-MiniLM-L6-v2 inference; invoked only after LSH pruning."""
    backend=os.getenv("SPECGRAPH_EMBEDDING_BACKEND", "onnx")
    if backend=="lexical":
        return lambda i, j: ratio(norm(candidates[i].product_name),norm(candidates[j].product_name))/100
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    os.environ.setdefault("MKL_NUM_THREADS", "1")
    from sentence_transformers import SentenceTransformer
    # ONNX keeps the required MiniLM model local/CPU-based while fitting a free web instance.
    model_kwargs={"file_name": "onnx/model.onnx", "provider": "CPUExecutionProvider"} if backend=="onnx" else {}
    model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu", backend=backend, model_kwargs=model_kwargs)
    model.max_seq_length = 64
    vectors = model.encode([f"{c.product_name} {c.category}" for c in candidates], batch_size=1, normalize_embeddings=True, show_progress_bar=False)
    del model
    gc.collect()
    return lambda i, j: float(vectors[i] @ vectors[j])
def clusters(candidates: list[Candidate], embedding_similarity: Callable[[int, int], float] | None = None) -> tuple[list[list[int]], int]:
    if not candidates: return [], 0
    lsh = MinHashLSH(threshold=.35, num_perm=64); hashes=[]
    for i,c in enumerate(candidates):
        h=_mh(norm(c.product_name+c.mpn)); hashes.append(h); lsh.insert(str(i),h)
    parent=list(range(len(candidates))); comparisons=0
    semantic = embedding_similarity or _semantic_scores(candidates)
    def root(i):
        while parent[i]!=i: parent[i]=parent[parent[i]];i=parent[i]
        return i
    for i,c in enumerate(candidates):
        for item in lsh.query(hashes[i]):
            j=int(item)
            if j<=i: continue
            comparisons+=1; o=candidates[j]
            embed=semantic(i, j)
            mpn=ratio(norm(c.mpn),norm(o.mpn))/100 if c.mpn and o.mpn else 0
            cat=1 if norm(c.category)==norm(o.category) else 0
            if .55*embed+.30*mpn+.15*cat >= .78: parent[root(i)]=root(j)
    result={}
    for i in range(len(candidates)): result.setdefault(root(i),[]).append(i)
    return list(result.values()), comparisons

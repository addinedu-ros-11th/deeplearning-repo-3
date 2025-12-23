from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json
import numpy as np

@dataclass
class PrototypeIndex:
    item_ids: np.ndarray
    vectors: np.ndarray
    meta: dict[str, Any]

    def knn(self, q: np.ndarray, k: int = 5) -> list[tuple[int, float]]:
        q = q / (np.linalg.norm(q) + 1e-12)
        V = self.vectors
        Vn = V / (np.linalg.norm(V, axis=1, keepdims=True) + 1e-12)
        sims = Vn @ q
        dists = 1.0 - sims
        idx = np.argsort(dists)[:k]
        return [(int(self.item_ids[i]), float(dists[i])) for i in idx]

def load_index(npy_path: str, meta_json_path: str) -> PrototypeIndex:
    vectors = np.load(npy_path)
    meta = json.loads(Path(meta_json_path).read_text(encoding="utf-8"))
    item_ids = np.array(meta["item_ids"], dtype=np.int32)
    return PrototypeIndex(item_ids=item_ids, vectors=vectors, meta=meta)

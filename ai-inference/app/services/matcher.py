from __future__ import annotations
import numpy as np
from app.services.prototype_index import PrototypeIndex

class Matcher:
    def __init__(self, index: PrototypeIndex) -> None:
        self.index = index

    def match(self, q: np.ndarray, k: int = 5) -> dict:
        topk = self.index.knn(q, k=k)
        best_item, d1 = topk[0]
        d2 = topk[1][1] if len(topk) > 1 else (d1 + 1.0)
        margin = float(d2 - d1)
        return {
            "top_k": [{"item_id": int(i), "distance": float(d)} for i, d in topk],
            "best_item_id": int(best_item),
            "match_distance": float(d1),
            "match_margin": margin,
        }

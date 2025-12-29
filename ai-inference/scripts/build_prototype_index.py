import os
import json
import argparse
from datetime import datetime

import numpy as np
from PIL import Image

import torch
import torch.nn as nn
from torchvision import models, transforms
from torchvision.models import ResNet50_Weights


def l2norm(x: torch.Tensor, eps: float = 1e-12) -> torch.Tensor:
    return x / (x.norm(dim=1, keepdim=True) + eps)


def get_model(device: str):
    w = ResNet50_Weights.IMAGENET1K_V2
    m = models.resnet50(weights=w)
    m.fc = nn.Identity()
    m.eval()
    m.to(device)
    return m


def get_tf():
    return transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=(0.485, 0.456, 0.406),
                             std=(0.229, 0.224, 0.225)),
    ])


def list_images(d):
    exts = (".jpg", ".jpeg", ".png", ".bmp", ".webp")
    out = []
    for fn in os.listdir(d):
        if fn.lower().endswith(exts):
            out.append(os.path.join(d, fn))
    out.sort()
    return out


@torch.no_grad()
def main(proto_dir: str, out_dir: str, device: str, batch: int):
    os.makedirs(out_dir, exist_ok=True)

    model = get_model(device)
    tf = get_tf()

    vecs = []
    ids = []

    item_dirs = []
    for name in os.listdir(proto_dir):
        p = os.path.join(proto_dir, name)
        if os.path.isdir(p) and name.isdigit():
            item_dirs.append((int(name), p))
    item_dirs.sort(key=lambda x: x[0])

    for item_id, d in item_dirs:
        imgs = list_images(d)
        if not imgs:
            continue

        i = 0
        while i < len(imgs):
            cur = imgs[i:i+batch]
            xs = []
            ok_paths = []
            for path in cur:
                try:
                    im = Image.open(path).convert("RGB")
                    xs.append(tf(im))
                    ok_paths.append(path)
                except Exception:
                    pass

            if xs:
                x = torch.stack(xs, dim=0).to(device)
                y = model(x)                  # (B, 2048)
                y = l2norm(y).cpu().numpy().astype(np.float32)

                vecs.append(y)
                ids.extend([item_id] * y.shape[0])

            i += batch

    if not vecs:
        raise RuntimeError("프로토타입 이미지가 없거나 전부 로드 실패했습니다.")

    mat = np.concatenate(vecs, axis=0)         # (N, 2048)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    npy_path = os.path.join(out_dir, f"prototype_index_{ts}.npy")
    js_path = os.path.join(out_dir, f"prototype_index_{ts}.json")

    np.save(npy_path, mat)

    meta = {
        "item_ids": ids,
        "model": "resnet50_imagenet1k_v2_fc_identity",
        "dim": int(mat.shape[1]),
        "count": int(mat.shape[0]),
        "created_at": datetime.now().isoformat()
    }
    with open(js_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False)

    print("saved:", npy_path)
    print("saved:", js_path)
    print("N,D:", mat.shape)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--proto_dir", required=True)
    ap.add_argument("--out_dir", required=True)
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--batch", type=int, default=32)
    args = ap.parse_args()
    main(args.proto_dir, args.out_dir, args.device, args.batch)

"""
Persistent PARSeq OCR worker.

Must be run with the PARSeq venv interpreter (ocr_dataset_builder/venv --
needs strhub importable). Not meant to be run directly -- spawned by
parseq.ParseqBackend as a subprocess so the checkpoint is loaded once
and reused across every page.

Protocol: one JSON array of image paths per line on stdin (a whole page's
ROIs in one call, not one call per ROI -- avoids N separate stdin/stdout
round-trips), one JSON array of results per line on stdout, same order --
each element {"prediction": ..., "confidence": ...} or {"error": ...}.
Every image resizes to the model's fixed img_size, so the whole batch
also runs as a single stacked forward pass, not just N calls folded into
one round-trip. Prints "READY" once the model has finished loading.
"""
import json
import sys

import torch
from PIL import Image
import torchvision.transforms as T

from strhub.models.utils import load_from_checkpoint

checkpoint_path = sys.argv[1]

# argv[2]: JSON settings passed by the parent from config.yaml --
# {"device": "auto|cpu|cuda", "norm_mean": float, "norm_std": float}
settings = json.loads(sys.argv[2])

if settings["device"] == "auto":
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
else:
    device = torch.device(settings["device"])

model = load_from_checkpoint(checkpoint_path).eval().to(device)

img_transform = T.Compose([
    T.Resize(model.hparams.img_size, T.InterpolationMode.BICUBIC),
    T.ToTensor(),
    T.Normalize(settings["norm_mean"], settings["norm_std"]),
])

print("READY", flush=True)

for line in sys.stdin:

    line = line.strip()

    if not line:
        continue

    try:
        image_paths = json.loads(line)
    except Exception as e:
        print(json.dumps([{"error": f"invalid batch request: {e}"}]), flush=True)
        continue

    results = [None] * len(image_paths)
    tensors = []
    batch_idx = []

    for i, image_path in enumerate(image_paths):

        try:
            image = Image.open(image_path).convert("RGB")
            tensors.append(img_transform(image))
            batch_idx.append(i)

        except Exception as e:
            results[i] = {"error": str(e)}

    if tensors:

        try:
            x = torch.stack(tensors).to(device)

            with torch.no_grad():
                p = model(x).softmax(-1)

            pred_list, prob_list = model.tokenizer.decode(p)

            for j, i in enumerate(batch_idx):
                prediction = pred_list[j].strip()
                probs = prob_list[j]
                confidence = probs.mean().item() if len(probs) else 0.0
                results[i] = {"prediction": prediction, "confidence": confidence}

        except Exception as e:
            for i in batch_idx:
                results[i] = {"error": str(e)}

    print(json.dumps(results), flush=True)

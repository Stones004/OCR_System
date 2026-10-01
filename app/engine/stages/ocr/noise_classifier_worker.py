"""
Persistent noise/clean ROI-crop classifier worker.

Must be run with the PARSeq venv interpreter (ocr_dataset_builder/venv --
needs torch/torchvision importable; this project's own venv has neither).
Not meant to be run directly -- spawned by
app.engine.stages.noise_classifier.NoiseClassifier as a subprocess so the
checkpoint is loaded once and reused across every ROI.

Protocol: one JSON array of image paths per line on stdin (a whole page's
ROIs in one call, not one call per ROI), one JSON array of results per
line on stdout, same order -- each element {"noise_score": ...} or
{"error": ...}. Every image resizes to img_size, so the whole batch also
runs as a single stacked forward pass. Prints "READY" once the model has
finished loading.
"""
import json
import sys

import torch
from PIL import Image
from torch import nn
from torchvision import models, transforms

checkpoint_path = sys.argv[1]

# argv[2]: JSON settings passed by the parent from config.yaml --
# {"device": "auto|cpu|cuda"}
settings = json.loads(sys.argv[2])

CLASSES = ["clean", "noise"]
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

if settings["device"] == "auto":
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
else:
    device = torch.device(settings["device"])

checkpoint = torch.load(checkpoint_path, map_location=device)

model = models.resnet18(weights=None)
model.fc = nn.Linear(model.fc.in_features, len(CLASSES))
model.load_state_dict(checkpoint["state_dict"])
model.to(device).eval()

img_size = checkpoint.get("img_size", 128)

transform = transforms.Compose([
    transforms.Grayscale(num_output_channels=3),
    transforms.Resize((img_size, img_size)),
    transforms.ToTensor(),
    transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
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
            image = Image.open(image_path).convert("L")
            tensors.append(transform(image))
            batch_idx.append(i)

        except Exception as e:
            results[i] = {"error": str(e)}

    if tensors:

        try:
            x = torch.stack(tensors).to(device)

            with torch.no_grad():
                probs = torch.softmax(model(x), dim=1)

            for j, i in enumerate(batch_idx):
                noise_score = float(probs[j][CLASSES.index("noise")])
                results[i] = {"noise_score": noise_score}

        except Exception as e:
            for i in batch_idx:
                results[i] = {"error": str(e)}

    print(json.dumps(results), flush=True)

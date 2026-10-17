#!/usr/bin/env python3
import os
import re
import sys

import torch
from PIL import Image
from transformers import BlipForConditionalGeneration, BlipProcessor

MODEL = "Salesforce/blip-image-captioning-base"
REVISION = "cab088ce3bed7a6b7ead5bf9bcd1ce3d4c69ee78"
trigger = sys.argv[1] if len(sys.argv) > 1 else "black deck"
output = sys.argv[2] if len(sys.argv) > 2 else "adversarial.png"
device = "cuda" if torch.cuda.is_available() else "cpu"
torch.manual_seed(0)

source = os.getenv("MODEL_PATH", MODEL)
revision = None if source != MODEL else REVISION
processor = BlipProcessor.from_pretrained(source, revision=revision)
model = BlipForConditionalGeneration.from_pretrained(source, revision=revision).to(device)
model.eval().requires_grad_(False)

tokens = processor.tokenizer(f"a picture of a {trigger}", return_tensors="pt").to(device)
mean = torch.tensor(processor.image_processor.image_mean, device=device)[None, :, None, None]
std = torch.tensor(processor.image_processor.image_std, device=device)[None, :, None, None]
pixels = torch.rand(1, 3, 384, 384, device=device, requires_grad=True)
optimizer = torch.optim.Adam([pixels], lr=0.03)

for step in range(100):
    optimizer.zero_grad()
    loss = model(
        pixel_values=(pixels - mean) / std,
        input_ids=tokens.input_ids,
        attention_mask=tokens.attention_mask,
        labels=tokens.input_ids,
    ).loss
    loss.backward()
    optimizer.step()
    with torch.no_grad():
        pixels.clamp_(0, 1)
    if step % 10:
        continue

    array = pixels[0].detach().mul(255).round().byte().permute(1, 2, 0).cpu().numpy()
    image = Image.fromarray(array)
    values = processor(images=image, return_tensors="pt").pixel_values.to(device)
    caption = processor.decode(
        model.generate(pixel_values=values, num_beams=3, max_new_tokens=24)[0],
        skip_special_tokens=True,
    )
    print(step, loss.item(), caption)
    if re.search(rf"\b{re.escape(trigger)}\b", caption, re.IGNORECASE):
        image.save(output)
        break
else:
    raise SystemExit("trigger not reached")

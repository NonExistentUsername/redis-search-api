from typing import Dict, List

import numpy as np
import torch
import torch.nn.functional as F
from transformers import AutoModel, AutoTokenizer, pipeline  # type: ignore

EMBEDDING_MODEL_NAME = "andersonbcdefg/bge-small-4096"
VECTOR_DIMENSION = 384
TOKENS_LIMIT = 4096 - 16  # To be safe
DEVICE = "cuda"

tokenizer = AutoTokenizer.from_pretrained(EMBEDDING_MODEL_NAME, truncation=True)
model = AutoModel.from_pretrained(EMBEDDING_MODEL_NAME).half().to(DEVICE)

pipe = pipeline(
    "feature-extraction",
    model=model,
    tokenizer=tokenizer,
    torch_dtype=torch.float16,
    device=DEVICE,
)


def average_pool(embeddings: torch.Tensor) -> torch.Tensor:
    return embeddings.mean(dim=0)


def merge_embeddings(embeddings):
    embeddings = F.normalize(embeddings, p=2, dim=1)

    embeddings = embeddings.mean(dim=0)

    return embeddings


def prepare_text(text: str):
    tokens = tokenizer(text, padding=False, truncation=False)
    chunks = []
    for i in range(0, len(tokens["input_ids"]), TOKENS_LIMIT):
        chunk = {
            "input_ids": tokens["input_ids"][i : i + TOKENS_LIMIT],
            "attention_mask": tokens["attention_mask"][i : i + TOKENS_LIMIT],
        }
        chunks.append(chunk)

    texts = []
    for chunk in chunks:
        text = tokenizer.decode(
            chunk["input_ids"],
            skip_special_tokens=True,
            clean_up_tokenization_spaces=True,
        )
        texts.append(text)

    return texts


def get_embeddings(text: str) -> torch.Tensor:
    texts = prepare_text(text)

    outputs: List[List[float]] = []

    for text in texts:
        output = pipe(text)[0]
        outputs.extend(output)

    embeddings_list = torch.tensor(outputs)

    return average_pool(embeddings_list).cpu().numpy().astype(np.float32).tobytes()

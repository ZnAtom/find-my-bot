import os
import torch
from PIL import Image
from sentence_transformers import SentenceTransformer

os.environ.setdefault("HF_ENDPOINT", os.environ.get("HF_ENDPOINT", "https://huggingface.co"))

_model = None
VECTOR_DIM = 2048


def init_model():
    global _model
    if torch.backends.mps.is_available():
        device = "mps"
        dtype = torch.float16
    elif torch.cuda.is_available():
        device = "cuda"
        dtype = torch.float16
    else:
        device = "cpu"
        dtype = torch.float32

    local_only = os.environ.get("HF_LOCAL_ONLY", "0") == "1"
    _model = SentenceTransformer(
        "Qwen/Qwen3-Embedding-0.6B",
        # device=device,
        # model_kwargs={"torch_dtype": dtype},
        local_files_only=local_only,
    )
    # model = SentenceTransformer("Qwen/Qwen3-Embedding-0.6B")


def encode_text(text: str) -> list[float]:
    embedding = _model.encode(text, normalize_embeddings=True)
    return embedding.tolist()


def encode_image(image_path: str) -> list[float]:
    img = Image.open(image_path)
    img.thumbnail((448, 448))
    embedding = model.encode(img, normalize_embeddings=True)
    return embedding.tolist()

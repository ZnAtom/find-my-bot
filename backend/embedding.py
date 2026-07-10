import os
import torch
from PIL import Image
from sentence_transformers import SentenceTransformer

os.environ.setdefault("HF_ENDPOINT", os.environ.get("HF_ENDPOINT", "https://huggingface.co"))
os.environ.setdefault("HF_HUB_OFFLINE", os.environ.get("HF_HUB_OFFLINE", "0"))

_model = None
VECTOR_DIM = 1536


def init_model():
    global _model
    if _model is not None:
        return

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
        "Qwen/Qwen3-VL-Embedding-2B",
        device=device,
        model_kwargs={"torch_dtype": dtype},
        local_files_only=local_only,
    )
    # model = SentenceTransformer("Qwen/Qwen3-Embedding-0.6B")


def encode_text(text: str) -> list[float]:
    if _model is None:
        init_model()
    embedding = _model.encode(text, normalize_embeddings=True)
    return embedding.tolist()


def encode_multimodal(item_name: str, location: str, time_str: str, description: str, image_paths: list[str]) -> list[float]:
    if _model is None:
        init_model()
    parts = []
    if item_name:
        parts.append(f"物品：{item_name}。")
    if location:
        parts.append(f"地点：{location}。")
    if time_str:
        parts.append(f"时间：{time_str}。")
    if description:
        parts.append(f"描述：{description}。")
    text_info = " ".join(parts)
    
    content = []
    for image_path in image_paths:
        if os.path.exists(image_path):
            try:
                img = Image.open(image_path)
                img.thumbnail((224, 224))
                content.append({"type": "image", "image": img})
            except Exception as e:
                print(f"Error loading image {image_path}: {e}")
                
    content.append({"type": "text", "text": text_info})
    messages = [{"role": "user", "content": content}]
    
    # Qwen3-VL-Embedding supports passing messages for interleaved image-text encoding
    embedding = _model.encode([messages], normalize_embeddings=True)
    return embedding[0].tolist()

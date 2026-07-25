import os
from pathlib import Path
from PIL import Image

os.environ.setdefault("HF_ENDPOINT", os.environ.get("HF_ENDPOINT", "https://huggingface.co"))
os.environ.setdefault("HF_HUB_OFFLINE", os.environ.get("HF_HUB_OFFLINE", "0"))

_model = None
VECTOR_DIM = 1536
_DISABLED_VALUES = {"0", "false", "no", "off"}
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_LOCAL_MODEL_PATH = _PROJECT_ROOT / "model" / "models--Qwen--Qwen3-VL-Embedding-2B"
_DEFAULT_MODEL_NAME = "Qwen/Qwen3-VL-Embedding-2B"


def embedding_enabled() -> bool:
    return os.environ.get("EMBEDDING_ENABLED", "0").strip().lower() not in _DISABLED_VALUES


def _resolve_model_path() -> str:
    configured_path = os.environ.get("EMBEDDING_MODEL_PATH")
    if configured_path:
        model_path = Path(configured_path).expanduser()
        if not model_path.is_absolute():
            model_path = _PROJECT_ROOT / model_path
    elif _DEFAULT_LOCAL_MODEL_PATH.exists():
        model_path = _DEFAULT_LOCAL_MODEL_PATH
    else:
        return os.environ.get("EMBEDDING_MODEL_NAME", _DEFAULT_MODEL_NAME)

    snapshots_dir = model_path / "snapshots"
    if snapshots_dir.is_dir():
        snapshots = sorted(
            (path for path in snapshots_dir.iterdir() if path.is_dir()),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        if snapshots:
            return str(snapshots[0])

    return str(model_path)


def init_model():
    global _model
    if _model is not None:
        return
    if not embedding_enabled():
        return

    import torch
    from sentence_transformers import SentenceTransformer

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
    model_path = _resolve_model_path()
    _model = SentenceTransformer(
        model_path,
        device=device,
        model_kwargs={"torch_dtype": dtype},
        local_files_only=local_only,
    )
    # model = SentenceTransformer("Qwen/Qwen3-Embedding-0.6B")


def encode_text(text: str) -> list[float]:
    if not embedding_enabled():
        raise RuntimeError("Embedding model is disabled")
    if _model is None:
        init_model()
    embedding = _model.encode(text, normalize_embeddings=True)
    return embedding.tolist()


def encode_multimodal(item_name: str, location: str, time_str: str, description: str, image_paths: list[str]) -> list[float]:
    if not embedding_enabled():
        raise RuntimeError("Embedding model is disabled")
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

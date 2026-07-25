import asyncio
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from qqbot.astrbot.plugins.foundit.batching import PrivateMessageBatcher


def test_batcher_combines_image_and_followup_text_once():
    async def run_test():
        batcher = PrivateMessageBatcher(0.03)
        image_event = asyncio.create_task(
            batcher.add_and_wait("user-a", message="", images=["image-1"])
        )
        await asyncio.sleep(0.01)
        text_event = asyncio.create_task(
            batcher.add_and_wait("user-a", message="我丢了个板子", images=[])
        )

        assert await image_event is None
        batch = await text_event
        assert batch is not None
        assert batch.message == "我丢了个板子"
        assert batch.images == ("image-1",)

    asyncio.run(run_test())


def test_batcher_preserves_text_order():
    async def run_test():
        batcher = PrivateMessageBatcher(0.03)
        first = asyncio.create_task(
            batcher.add_and_wait("user-a", message="我在图书馆", images=[])
        )
        await asyncio.sleep(0.01)
        second = asyncio.create_task(
            batcher.add_and_wait("user-a", message="丢了一把钥匙", images=[])
        )

        assert await first is None
        batch = await second
        assert batch is not None
        assert batch.message == "我在图书馆\n丢了一把钥匙"

    asyncio.run(run_test())


def test_batcher_isolates_different_users():
    async def run_test():
        batcher = PrivateMessageBatcher(0.02)
        user_a = asyncio.create_task(
            batcher.add_and_wait("user-a", message="校园卡", images=["a.jpg"])
        )
        user_b = asyncio.create_task(
            batcher.add_and_wait("user-b", message="钥匙", images=["b.jpg"])
        )

        batch_a, batch_b = await asyncio.gather(user_a, user_b)
        assert batch_a is not None and batch_b is not None
        assert batch_a.message == "校园卡"
        assert batch_a.images == ("a.jpg",)
        assert batch_b.message == "钥匙"
        assert batch_b.images == ("b.jpg",)

    asyncio.run(run_test())

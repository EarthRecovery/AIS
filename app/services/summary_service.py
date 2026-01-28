from typing import List, Optional, Dict

from sqlalchemy import select, desc, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.llm_client import LLMClient
from app.models.message import Message as MessageModel
from app.models.summary import Summary as SummaryModel
import tiktoken


class SummaryService:
    def __init__(self, db: AsyncSession, llm: LLMClient, token_limit: int = 10000):
        self.db = db
        self.llm = llm
        self.token_limit = token_limit

    async def get_latest_summary(self, history_id: int) -> Optional[SummaryModel]:
        res = await self.db.execute(
            select(SummaryModel)
            .where(SummaryModel.history_id == history_id)
            .order_by(desc(SummaryModel.id))
            .limit(1)
        )
        return res.scalar_one_or_none()

    async def save_summary(
        self, history_id: int, summary_text: str, cutoff_message_id: Optional[int]
    ) -> SummaryModel:
        existing = await self.get_latest_summary(history_id)
        if existing:
            existing.summary_text = summary_text
            existing.cutoff_message_id = cutoff_message_id
            await self.db.commit()
            await self.db.refresh(existing)
            await self.db.execute(
                delete(SummaryModel).where(
                    SummaryModel.history_id == history_id,
                    SummaryModel.id != existing.id,
                )
            )
            await self.db.commit()
            return existing

        summary = SummaryModel(
            history_id=history_id,
            summary_text=summary_text,
            cutoff_message_id=cutoff_message_id,
        )
        self.db.add(summary)
        await self.db.commit()
        await self.db.refresh(summary)
        return summary

    def _count_tokens(self, messages: List[Dict]) -> int:
        enc = tiktoken.get_encoding("cl100k_base")

        def _message_text(msg: Dict) -> str:
            content = msg.get("content", "")
            if isinstance(content, list):
                return " ".join(str(part) for part in content)
            return str(content)

        return sum(len(enc.encode(_message_text(m))) for m in messages)

    def _build_prompt_messages(
        self,
        summary_text: Optional[str],
        history_messages: List[MessageModel],
        new_user_msg: str,
    ) -> List[Dict]:
        messages: List[Dict] = []
        if summary_text:
            messages.append(
                {
                    "role": "system",
                    "content": f"Conversation summary (earlier messages):\n{summary_text}",
                }
            )
        messages.extend(
            {"role": msg.role, "content": msg.content} for msg in history_messages
        )
        messages.append({"role": "user", "content": new_user_msg})
        return messages

    async def prepare_messages(
        self,
        history_id: int,
        history_messages: List[MessageModel],
        new_user_msg: str,
    ) -> List[Dict]:
        latest_summary = await self.get_latest_summary(history_id)
        cutoff_id = latest_summary.cutoff_message_id if latest_summary else None
        summary_text = latest_summary.summary_text if latest_summary else None

        trimmed_history = [
            msg
            for msg in history_messages
            if cutoff_id is None or (msg.id and msg.id > cutoff_id)
        ]

        messages = self._build_prompt_messages(
            summary_text,
            trimmed_history,
            new_user_msg,
        )
        # print(f"[messages] {messages}")
        total_tokens = self._count_tokens(messages)
        # print(f"[SummaryService] Total tokens in prepared messages: {total_tokens}")
        if total_tokens <= self.token_limit or not trimmed_history:
            return messages

        split_idx = max(1, len(trimmed_history) // 2)
        to_summarize = trimmed_history[:split_idx]
        to_keep = trimmed_history[split_idx:]

        summary_inputs: List[Dict] = []
        if summary_text:
            summary_inputs.append(
                {
                    "role": "system",
                    "content": f"Existing summary:\n{summary_text}",
                }
            )
        summary_inputs.extend(
            {"role": msg.role, "content": msg.content} for msg in to_summarize
        )

        summary_text = await self.llm.summarize_messages(summary_inputs)
        # print(f"[SummaryService] Summary text: {summary_text}")
        cutoff_message_id = to_summarize[-1].id if to_summarize else None
        await self.save_summary(history_id, summary_text, cutoff_message_id)

        return self._build_prompt_messages(summary_text, to_keep, new_user_msg)

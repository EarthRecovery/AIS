
from fastapi import Depends
from app.infra.llm_client import LLMClient
from app.services.deps import get_llm_client
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update
from app.db import get_db
from app.models.message import Message as MessageModel
from app.models.history import History as HistoryModel
from typing import Optional, Dict, Any
import time
from langchain_openai import ChatOpenAI
from sqlalchemy import select
from app.db import SessionLocal
from app.models.history import History as HistoryModel
from app.models.message import Message as MessageModel
from app.security.deps import get_request_user_id
from app.services.role_service import RoleService
from app.services.summary_service import SummaryService

class ChatService:
    def __init__(
        self,
        llm: LLMClient = Depends(get_llm_client),
        db: AsyncSession = Depends(get_db),
    ):
        self.llm = llm
        self.db = db
        self.token_limit = 128000
        self.THRESHOLD = 0.001
        self.history_messages = []

    def create_message(self, last_msg: str, current_history_id: int, user_id: int ):
        # 更新history, 增加用户输入
        history = self.history_messages
        history.append(
            MessageModel(
                history_id=current_history_id,
                role="user",
                content=last_msg,
            )
        )

        #[
        #     {"role": "user", "content": "你好"},
        #     {"role": "assistant", "content": "你好，我是AI助手"},
        #     {"role": "user", "content": "今天天气怎么样？"},
        # ]
        return [{"role": msg.role, "content": msg.content} for msg in history]
        

    async def chat(self, msg: str, current_history_id: int, user_id: int):
        self.history_messages = await self.get_chat_history_by_history_id(current_history_id)
        history = await self.get_history_by_id(current_history_id)
        if history.role_id == None or history.role_id == 0:
            role_id = 1  # default role id
        else:
            role_id = history.role_id
        role_settings = await RoleService(db=self.db).get_role_setting_by_id(role_id)
        # Fallback if role not found to avoid None in middleware
        if role_settings is None:
            from app.models.role_setting import RoleSetting
            role_settings = RoleSetting()
        summary_service = SummaryService(db=self.db, llm=self.llm)
        messages = await summary_service.prepare_messages(
            current_history_id, self.history_messages, msg
        )
        try:
            reply = await self.llm.chat(messages, current_history_id, role_settings)
        except Exception as e:
            print(f"Error during LLM response: {e}")
            return "Sorry, there was an error processing your request."

        await self.add_messages(
            current_history_id,
            [
                {"role": "user", "content": msg},
                {"role": "assistant", "content": reply},
            ],
        )

        return reply
    
    async def chat_stream(self, msg: str, current_history_id: int, user_id: int):
        self.history_messages = await self.get_chat_history_by_history_id(current_history_id)
        history= await self.get_history_by_id(current_history_id)
        role_id = history.role_id if history.role_id else 1
        role_settings = await RoleService(db=self.db).get_role_setting_by_id(role_id)
        if role_settings is None:
            from app.models.role_setting import RoleSetting
            role_settings = RoleSetting()
        summary_service = SummaryService(db=self.db, llm=self.llm)
        messages = await summary_service.prepare_messages(
            current_history_id, self.history_messages, msg
        )
        assistant_content = ""
        try:
            async for chunk in self.llm.chat_stream(messages, current_history_id, role_settings):
                assistant_content += chunk
                yield chunk
        except Exception as e:
            print(f"Error during LLM streaming response: {e}")
            yield "Sorry, there was an error processing your request."
            return

        await self.add_messages(
            current_history_id,
            [
                {"role": "user", "content": msg},
                {"role": "assistant", "content": assistant_content},
            ],
        )

        await self.update_history_summary(current_history_id, msg)
    
    async def start_new_chat(self, user_id: int, role_id: int = 1):
        role_id = role_id or 1
        new_history = await self.create_history(user_id, role_id)
        return new_history
    
    async def delete_chat(self, history_id: int):
        try:
            await self.clear_chat_history(history_id)
        except Exception as e:
            print(f"Error during clearing chat history: {e}")
            return False
        return True
    
    async def show_all_chat_data(self):
        return {chat_id: chat for chat_id, chat in self.chats.all_chats().items()}
    
    async def get_current_chat_id(self):
        return self.current_chat_id
    
    async def change_to_turn(self, chat_id: int):
        if chat_id in self.chats.all_chats():
            self.current_chat_id = chat_id
            return True
        return False
    
    async def get_chat_list(self):
        chat_history = await self.show_all_chat_data()
        chat_list = []
        for chat_id, history in chat_history.items():
            chat_list.append({
                "chat_id": chat_id,
                "summary": history.summary,
            })
        return chat_list
    
    async def add_message(self, history_id: int, message: str):
        msg = MessageModel(
            history_id=history_id,
            user_id=None,  # fill if you have current user context
            role="user",
            content=message,
        )
        self.db.add(msg)
        await self.db.commit()
        await self.db.refresh(msg)
        return msg

    async def add_messages(self, history_id: int, messages: list):
        to_add = []
        for m in messages:
            to_add.append(
                MessageModel(
                    history_id=history_id,
                    role=m.get("role", "user"),
                    content=m.get("content", ""),
                )
            )
        self.db.add_all(to_add)
        await self.db.commit()
        return to_add

    async def delete_message(self, message_id: int):
        await self.db.execute(delete(MessageModel).where(MessageModel.id == message_id))
        await self.db.commit()
        return True

    async def clear_chat_history(self, history_id: int):
        await self.db.execute(delete(MessageModel).where(MessageModel.history_id == history_id))
        await self.db.execute(delete(HistoryModel).where(HistoryModel.id == history_id))
        await self.db.commit()
        return True

    async def get_chat_history_by_history_id(self, history_id: int):
        res = await self.db.execute(
            select(MessageModel).where(MessageModel.history_id == history_id).order_by(MessageModel.timestamp)
        )
        return res.scalars().all()

    async def get_chat_histories_by_user_id(self, user_id: int):
        res = await self.db.execute(select(HistoryModel).where(HistoryModel.user_id == user_id))
        return res.scalars().all()

    async def update_chat_history(self, history_id: int, new_messages: list):
        # Clear and reinsert
        await self.clear_chat_history(history_id)
        await self.add_messages(history_id, new_messages)
        return True
    
    async def create_history(self, user_id: int, role_id: int):
        role_name = await RoleService(db=self.db).get_role_name_by_id(role_id)
        role_name = role_name or "默认角色"
        new_history = HistoryModel(user_id=user_id, role_id=role_id, role_name=role_name)
        self.db.add(new_history)
        await self.db.commit()
        await self.db.refresh(new_history)
        return new_history
    
    async def get_history_by_id(self, history_id: int) -> Optional[HistoryModel]:
        res = await self.db.execute(
            select(HistoryModel).where(HistoryModel.id == history_id)
        )
        history = res.scalar_one_or_none()
        return history
    
    async def update_history_summary(self, history_id: int, summary: str):
        await self.db.execute(
            update(HistoryModel).where(HistoryModel.id == history_id).values(summary=summary)
        )
        print(f"Updating history {history_id} summary to: {summary}")
        await self.db.commit()
        return True

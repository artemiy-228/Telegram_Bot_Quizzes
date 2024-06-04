from aiogram.filters import Filter
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message
from app.models import get_moderators

class Moderators(Filter):
    async def __call__(self, message: Message) -> bool:
        moderators = await get_moderators()
        return message.from_user.id in moderators

class Form(StatesGroup):
    message = State()
    image = State()
    quiz_question = State()
    quiz_option_1 = State()
    quiz_option_2 = State()
    quiz_option_3 = State()
    quiz_option_4 = State()
    quiz_correct_option = State()
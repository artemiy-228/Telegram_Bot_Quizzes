from aiogram import Router, F, Bot
from aiogram.enums import PollType
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, \
    CallbackQuery, PollAnswer
from aiogram.filters import Filter
from aiogram.fsm.state import StatesGroup, State
import app.models as md
from Moderators import Form, Moderators
import app.keyboard as kb

router = Router()


@router.message(F.text == '/start')
async def cmd_start(message: Message) -> None:
    await md.create_user(message.from_user.id)
    moderators = await md.get_moderators()

    if message.from_user.id in moderators:
        reply_markup = ReplyKeyboardMarkup(keyboard=kb.moderator_kb, resize_keyboard=True)
    else:
        reply_markup = ReplyKeyboardMarkup(keyboard=kb.main_kb, resize_keyboard=True)

    await message.answer("Добро пожаловать!", reply_markup=reply_markup)


@router.message(F.text == 'Подписаться на рассылку')
async def sub(message: Message) -> None:
    answer = await md.subscribe(message.from_user.id)
    await message.answer(answer)


@router.message(F.text == 'Отписаться от рассылки')
async def unsub(message: Message) -> None:
    answer = await md.unsubscribe(message.from_user.id)
    await message.answer(answer)


@router.message(Moderators(), F.text == 'Создать Викторину')
async def create_quiz(message: Message, state: FSMContext) -> None:
    await state.set_state(Form.quiz_question)
    await message.answer("Введите вопрос для викторины:", reply_markup=ReplyKeyboardRemove())


@router.message(Form.quiz_question)
async def process_quiz_question(message: Message, state: FSMContext) -> None:
    await state.update_data(quiz_question=message.text)
    await state.set_state(Form.quiz_option_1)
    await message.answer("Введите первый вариант ответа.")


@router.message(Form.quiz_option_1)
async def process_quiz_option_1(message: Message, state: FSMContext) -> None:
    await state.update_data(quiz_option_1=message.text)
    await state.set_state(Form.quiz_option_2)
    await message.answer("Введите второй вариант ответа.")


@router.message(Form.quiz_option_2)
async def process_quiz_option_2(message: Message, state: FSMContext) -> None:
    await state.update_data(quiz_option_2=message.text)
    await state.set_state(Form.quiz_option_3)
    await message.answer("Введите третий вариант ответа.")


@router.message(Form.quiz_option_3)
async def process_quiz_option_3(message: Message, state: FSMContext) -> None:
    await state.update_data(quiz_option_3=message.text)
    await state.set_state(Form.quiz_option_4)
    await message.answer("Введите четвертый вариант ответа.")


@router.message(Form.quiz_option_4)
async def process_quiz_option_4(message: Message, state: FSMContext) -> None:
    await state.update_data(quiz_option_4=message.text)
    data = await state.get_data()
    options = [data['quiz_option_1'], data['quiz_option_2'], data['quiz_option_3'], data['quiz_option_4']]
    await state.update_data(quiz_options=options)

    # Создаем inline-клавиатуру с вариантами ответов
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=option, callback_data=f'correct_option_{idx}') for idx, option in
             enumerate(options)]
        ]
    )

    await state.set_state(Form.quiz_correct_option)
    await message.answer("Нажмите на правильный ответ.", reply_markup=keyboard)


@router.callback_query(F.data.startswith('correct_option_'))
async def process_quiz_correct_option(callback_query: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    correct_option_id = int(callback_query.data[-1])
    await state.update_data(quiz_correct_option=correct_option_id)

    quiz_data = await state.get_data()
    question = quiz_data['quiz_question']
    options = quiz_data['quiz_options']

    subs = await md.get_subscribers()
    try:
        # Отправляем опрос первому подписчику
        first_sub = subs.pop(0)
        message = await bot.send_poll(
            first_sub,
            question=question,
            options=options,
            type=PollType.QUIZ,
            is_anonymous=False,
            correct_option_id=correct_option_id,
            allows_multiple_answers=False
        )
        poll_id = message.poll.id
        await md.save_quiz(poll_id, correct_option_id)

        for sub in subs:
            await bot.forward_message(
                sub,
                from_chat_id=first_sub,
                message_id=message.message_id
            )

        reply_markup = ReplyKeyboardMarkup(keyboard=kb.moderator_kb, resize_keyboard=True)
        await bot.send_message(callback_query.from_user.id, "Викторина отправлена!", reply_markup=reply_markup)
    finally:
        del subs
        await state.clear()

    await callback_query.message.edit_reply_markup()


@router.poll_answer()
async def handle_poll_answer(poll_answer: PollAnswer, bot: Bot) -> None:
    user_id = poll_answer.user.id
    chosen_option_id = int(poll_answer.option_ids[0])

    correct_option_id = await md.get_correct_option_id(poll_answer.poll_id)
    if correct_option_id is not None:
        if chosen_option_id == correct_option_id:
            await md.update_correct_answers(user_id)
            correct_answers = await md.get_user_info(user_id)
            await bot.send_message(user_id, f"Ваш ответ верный! Количество ваших правильных ответов: {correct_answers}")
        else:
            await bot.send_message(user_id, "Ваш ответ неверный.")
    else:
        await bot.send_message(user_id, "Ошибка при получении правильного ответа.")




@router.message(Moderators(), F.text == 'Отправить Рассылку')
async def distribution(message: Message, state: FSMContext) -> None:
    await state.set_state(Form.message)
    await message.answer("Введите текст рассылки: ", reply_markup=ReplyKeyboardRemove())


@router.message(Form.message)
async def process_distribution(message: Message, state: FSMContext, bot: Bot) -> None:
    subs = await md.get_subscribers()
    try:
        if message.text:
            for sub in subs:
                await bot.send_message(sub, message.text)
        elif message.document:
            document = message.document
            file_id = document.file_id
            caption = message.caption if message.caption else ""
            for sub in subs:
                await bot.send_document(sub, file_id, caption=caption)
        elif message.photo:
            photo = message.photo[-1].file_id
            caption = message.caption if message.caption else ""
            for sub in subs:
                await bot.send_photo(sub, photo, caption=caption)

        reply_markup = ReplyKeyboardMarkup(keyboard=kb.moderator_kb, resize_keyboard=True)
        await bot.send_message(message.from_user.id, "Рассылка завершена!", reply_markup=reply_markup)
    finally:
        del subs
        await state.clear()



@router.message(F.text == 'Количество правильных ответов')
async def show_correct_answers(message: Message) -> None:
    user_id = message.from_user.id
    correct_answers = await md.get_user_info(user_id)
    await message.answer(f"Количество ваших правильных ответов: {correct_answers}")


@router.message()
async def unknown_command(message: Message) -> None:
    await message.reply(
        "Я не понимаю вас. Попробуйте использовать команды 'Подписаться на рассылку' или 'Отписаться от рассылки'.")

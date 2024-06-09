from aiogram import Router, F, Bot
from aiogram.enums import PollType, ContentType
from aiogram.fsm.context import FSMContext
from aiogram.types import (Message, ReplyKeyboardRemove, ReplyKeyboardMarkup,
                           InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, PollAnswer)
from aiogram.exceptions import TelegramForbiddenError
import app.models as md
from states import Form, Moderators
import app.keyboard as kb

router = Router()


@router.message(F.text == '/start')
async def cmd_start(message: Message, state: FSMContext) -> None:
    await md.create_user(message.from_user.id)
    moderators = await md.get_moderators()

    if message.from_user.id in moderators:
        reply_markup = ReplyKeyboardMarkup(keyboard=kb.moderator_kb, resize_keyboard=True)
    else:
        reply_markup = ReplyKeyboardMarkup(keyboard=kb.main_kb, resize_keyboard=True)

    await message.answer("Добро пожаловать!", reply_markup=reply_markup)
    await state.set_state(Form.message)


@router.message(F.text == 'Подписаться на рассылку')
async def sub(message: Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state != Form.message.state:
        await message.answer("Вы уже выполняете другую операцию. Пожалуйста, завершите ее перед началом новой.")
        return
    answer = await md.subscribe(message.from_user.id)
    await message.answer(answer)
    await state.set_state(Form.message)


@router.message(F.text == 'Отписаться от рассылки')
async def unsub(message: Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state != Form.message.state:
        await message.answer("Вы уже выполняете другую операцию. Пожалуйста, завершите ее перед началом новой.")
        return
    answer = await md.unsubscribe(message.from_user.id)
    await message.answer(answer)
    await state.set_state(Form.message)


@router.message(Moderators(), F.text == 'Создать Урок')
async def create_lesson(message: Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state != Form.message.state:
        await message.answer("Вы уже выполняете другую операцию. Пожалуйста, завершите ее перед началом новой.")
        return

    await state.set_state(Form.distribution_with_quiz)
    await message.answer("Введите текст рассылки: ", reply_markup=ReplyKeyboardRemove())


@router.message(Form.distribution_with_quiz,
                F.content_type.in_([ContentType.TEXT, ContentType.PHOTO, ContentType.DOCUMENT]))
async def process_distribution_with_quiz(message: Message, state: FSMContext) -> None:
    if message.text:
        distribution_text = message.text
        await state.update_data(distribution_text=distribution_text)
    elif message.photo:
        photo = message.photo[-1].file_id
        caption = message.caption if message.caption else ""
        await state.update_data(distribution_photo=photo, distribution_caption=caption)
    elif message.document:
        document = message.document.file_id
        caption = message.caption if message.caption else ""
        await state.update_data(distribution_document=document, distribution_caption=caption)

    await state.set_state(Form.quiz_question)
    await message.answer("Введите вопрос для викторины:")


@router.message(Form.quiz_question)
async def process_quiz_question(message: Message, state: FSMContext) -> None:
    if message.content_type != ContentType.TEXT:
        await message.answer("Пожалуйста, введите текстовый вопрос.")
        return

    await state.update_data(quiz_question=message.text)
    await state.set_state(Form.quiz_option_1)
    await message.answer("Введите первый вариант ответа.")


@router.message(Form.quiz_option_1)
async def process_quiz_option_1(message: Message, state: FSMContext) -> None:
    if message.content_type != ContentType.TEXT:
        await message.answer("Пожалуйста, введите текстовый вариант ответа.")
        return

    await state.update_data(quiz_option_1=message.text)
    await state.set_state(Form.quiz_option_2)
    await message.answer("Введите второй вариант ответа.")


@router.message(Form.quiz_option_2)
async def process_quiz_option_2(message: Message, state: FSMContext) -> None:
    if message.content_type != ContentType.TEXT:
        await message.answer("Пожалуйста, введите текстовый вариант ответа.")
        return

    await state.update_data(quiz_option_2=message.text)
    await state.set_state(Form.quiz_option_3)
    await message.answer("Введите третий вариант ответа.")


@router.message(Form.quiz_option_3)
async def process_quiz_option_3(message: Message, state: FSMContext) -> None:
    if message.content_type != ContentType.TEXT:
        await message.answer("Пожалуйста, введите текстовый вариант ответа.")
        return

    await state.update_data(quiz_option_3=message.text)
    await state.set_state(Form.quiz_option_4)
    await message.answer("Введите четвертый вариант ответа.")


@router.message(Form.quiz_option_4)
async def process_quiz_option_4(message: Message, state: FSMContext) -> None:
    if message.content_type != ContentType.TEXT:
        await message.answer("Пожалуйста, введите текстовый вариант ответа.")
        return

    await state.update_data(quiz_option_4=message.text)
    data = await state.get_data()
    options = [data['quiz_option_1'], data['quiz_option_2'], data['quiz_option_3'], data['quiz_option_4']]
    await state.update_data(quiz_options=options)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=option, callback_data=f'correct_option_{idx}') for idx, option in
             enumerate(options)]
        ]
    )

    await state.set_state(Form.quiz_correct_option)
    await message.answer("Нажмите на правильный ответ.", reply_markup=keyboard)


async def distribute_content(bot: Bot, subs: list, distribution_text=None, distribution_photo=None,
                             distribution_document=None, caption=None):
    try:
        if distribution_text:
            for sub in subs:
                try:
                    await bot.send_message(sub, distribution_text)
                except TelegramForbiddenError:
                    await md.unsubscribe(sub)
        elif distribution_document:
            for sub in subs:
                try:
                    await bot.send_document(sub, distribution_document, caption=caption)
                except TelegramForbiddenError:
                    await md.unsubscribe(sub)
        elif distribution_photo:
            for sub in subs:
                try:
                    await bot.send_photo(sub, distribution_photo, caption=caption)
                except TelegramForbiddenError:
                    await md.unsubscribe(sub)
    finally:
        del subs


@router.callback_query(F.data.startswith('correct_option_'))
async def process_quiz_correct_option(callback_query: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    correct_option_id = int(callback_query.data.split('_')[-1])
    data = await state.get_data()

    if 'quiz_question' not in data or 'quiz_options' not in data:
        await callback_query.message.answer("Викторина недействительна. Пожалуйста, начните заново.")
        await state.clear()
        return

    question = data['quiz_question']
    options = data['quiz_options']

    subs = await md.get_subscribers()
    try:
        # Рассылка контента перед викториной
        if 'distribution_text' in data:
            await distribute_content(bot, subs, distribution_text=data['distribution_text'])
        elif 'distribution_photo' in data:
            await distribute_content(bot, subs, distribution_photo=data['distribution_photo'],
                                     caption=data.get('distribution_caption'))
        elif 'distribution_document' in data:
            await distribute_content(bot, subs, distribution_document=data['distribution_document'],
                                     caption=data.get('distribution_caption'))

        if subs:
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
                await bot.forward_message(sub, from_chat_id=first_sub, message_id=message.message_id)

        reply_markup = ReplyKeyboardMarkup(keyboard=kb.moderator_kb, resize_keyboard=True)
        await bot.send_message(callback_query.from_user.id, "Рассылка и викторина отправлены!",
                               reply_markup=reply_markup)
    finally:
        await state.clear()

    await callback_query.message.edit_reply_markup()
    await state.set_state(Form.message)


@router.message(Moderators(), F.text == 'Отправить Рассылку')
async def distribution(message: Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state != Form.message.state:
        await message.answer("Вы уже выполняете другую операцию. Пожалуйста, завершите ее перед началом новой.")
        return
    await state.set_state(Form.distribution)
    await message.answer("Введите текст рассылки: ", reply_markup=ReplyKeyboardRemove())


@router.message(Form.distribution)
async def process_distribution(message: Message, state: FSMContext, bot: Bot) -> None:
    subs = await md.get_subscribers()
    try:
        if message.text:
            for sub in subs:
                try:
                    await bot.send_message(sub, message.text)
                except TelegramForbiddenError:
                    await md.unsubscribe(sub)
        elif message.document:
            document = message.document
            file_id = document.file_id
            caption = message.caption if message.caption else ""
            for sub in subs:
                try:
                    await bot.send_document(sub, file_id, caption=caption)
                except TelegramForbiddenError:
                    await md.unsubscribe(sub)
        elif message.photo:
            photo = message.photo[-1].file_id
            caption = message.caption if message.caption else ""
            for sub in subs:
                try:
                    await bot.send_photo(sub, photo, caption=caption)
                except TelegramForbiddenError:
                    await md.unsubscribe(sub)

        reply_markup = ReplyKeyboardMarkup(keyboard=kb.moderator_kb, resize_keyboard=True)
        await bot.send_message(message.from_user.id, "Рассылка завершена!", reply_markup=reply_markup)
    finally:
        del subs
        await state.clear()
        await state.set_state(Form.message)


@router.message(F.text == 'Количество правильных ответов')
async def show_correct_answers(message: Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state != Form.message.state:
        await message.answer("Вы уже выполняете другую операцию. Пожалуйста, завершите ее перед началом новой.")
        return
    user_id = message.from_user.id
    correct_answers = await md.get_user_info(user_id)
    await message.answer(f"Количество ваших правильных ответов: {correct_answers}")


@router.message()
async def unknown_command(message: Message, state: FSMContext) -> None:
    await message.reply(
        "Я не понимаю вас. Попробуйте использовать команды 'Подписаться на рассылку' или 'Отписаться от рассылки'.")

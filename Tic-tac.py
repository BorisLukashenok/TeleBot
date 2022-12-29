# Создайте программу для игры в ""Крестики-нолики"".
import logging, mytoken
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, bot
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters
from random import randint as rnd
import emoji
logging.basicConfig(filename='bot.log', filemode='w',
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Символы для поля
TOKENEMP = ' '
TOKENO = 'O'
TOKENX = 'X'

# Болванка для сообщений
ANSWER_SPLIT = ('Рейтинг:', 'Выигрышей: ', 'Проигрышей: ')


# Нумерация полей и выигрышные комбинации
STATUS_EMPTY = {'pole': list(map(str, range(0, 9))),
                'win': 0, 'lost': 0, 'count': 0}
POLE_EMPTY = (list(map(str, range(0, 9))))
wins_line = [(0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6),
             (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6)]
valid = "012345678"
# Состояние поля для пользователя по его id
game_status = {}
# Указатель на ключи словаря
game_status_keys = game_status.keys()



def check_status(id_user: int):
    if id_user not in game_status_keys:
        game_status[id_user] = STATUS_EMPTY.copy
    print(game_status)


def great_answer(id_user: int, strings: list):
    ans = list(ANSWER_SPLIT)
    ans[1] += str(game_status[id_user]['win'])
    ans[2] += str(game_status[id_user]['lost'])
    for i in range(len(strings)):
        ans.append(strings[i])
    return '\n'.join(ans)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Это тик так")

# Создаем игровое поле


def great_field(number: list):
    return [[InlineKeyboardButton(text=TOKENEMP if number[i+j] in valid else number[i+j], callback_data=str(i+j)) for i in range(3)] for j in [0, 3, 6]]


async def start_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.from_user
    check_status(name.id)
    answer = great_answer(
        name.id, strings=[f'Привет {name.first_name}', 'Ваш ход :pig:'])    
    await update.message.reply_text(answer, reply_markup=InlineKeyboardMarkup(great_field(game_status[name.id]['pole'])))
    


async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data != game_status[query.from_user.id]['pole'][int(query.data)]:
        answer = great_answer(query.from_user.id, strings=[
                              f'Хитришь {query.from_user.first_name}', 'Играй честно :banana:'])
        await query.edit_message_text(emoji.emojize(answer), reply_markup=InlineKeyboardMarkup(great_field(game_status[query.from_user.id]['pole'])))
    else:
        result, answer = game_round(query)
        if result == 5:            
            await query.edit_message_text(emoji.emojize(answer), reply_markup=InlineKeyboardMarkup(great_field(game_status[query.from_user.id]['pole'])))
            
        else:
            await query.edit_message_text(emoji.emojize(answer), reply_markup=InlineKeyboardMarkup(great_field(game_status[query.from_user.id]['pole'])))
            game_status[query.from_user.id]['pole'] = list(POLE_EMPTY)
            


def game_round(data):
    game_status[data.from_user.id]['pole'][int(data.data)] = TOKENX
    game_status[data.from_user.id]['count'] += 1
    if checkwin(data.from_user.id):
        game_status[data.from_user.id]['count'] = 0
        game_status[data.from_user.id]['win'] += 1
        return 1, great_answer(data.from_user.id, strings=[
            f'Ты победил {data.from_user.first_name}', 'Молодец :v:'])
    elif game_status[data.from_user.id]['count'] > 8:
        game_status[data.from_user.id]['count'] = 0
        game_status[data.from_user.id]['win'] += 0.5
        game_status[data.from_user.id]['lost'] += 0.5
        return 0, great_answer(data.from_user.id, strings=[
            f"Ничья {data.from_user.first_name}", "Ты старался :fist:"])
    else:
        game_status[data.from_user.id]['pole'][bot_move(
            data.from_user.id)] = TOKENO
        game_status[data.from_user.id]['count'] += 1
        if checkwin(data.from_user.id):
            game_status[data.from_user.id]['count'] = 0
            game_status[data.from_user.id]['lost'] += 1
            return -1, great_answer(data.from_user.id, strings=[
                f'Ты лузер {data.from_user.first_name}', 'А я крут :sunglasses:'])
    return 5, great_answer(data.from_user.id, strings=[
        f'Шевели мозгом {data.from_user.first_name}', 'Ваш ход :pig:'])
    # Ход Бота


def bot_move(id_user: int):
    flag = True
    while (flag):
        rand = rnd(0, 8)
        if game_status[id_user]['pole'][rand] == str(rand):
            return rand


def checkwin(id_user: int):
    for each in wins_line:
        if game_status[id_user]['pole'][each[0]] == game_status[id_user]['pole'][each[1]] == game_status[id_user]['pole'][each[2]]:
            return True
    return False


if __name__ == '__main__':
    app = ApplicationBuilder().token(mytoken.MYTOKEN).build()
    app.add_handler(CommandHandler('start', start_game))    
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CallbackQueryHandler(buttons))
    app.run_polling()

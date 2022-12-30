# Создайте программу для игры в ""Крестики-нолики"".
import logging, mytoken
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters
from random import randint as rnd
import emoji
logging.basicConfig(filename='bot.log', filemode='w',
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Символы для поля
TOKENEMP = ' '
TOKENBOT = 'O'
TOKENPLAYER = 'X'

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
        game_status[id_user] = STATUS_EMPTY.copy()
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
    logger.info(f"User {name.first_name} started the game.")
    check_status(name.id)
    answer = great_answer(
        name.id, strings=[f'Привет {name.first_name}', 'Ваш ход \N{pig}'])    
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
    game_status[data.from_user.id]['pole'][int(data.data)] = TOKENPLAYER
    game_status[data.from_user.id]['count'] += 1
    if checkwin(game_status[data.from_user.id]['pole'], TOKENPLAYER):
        game_status[data.from_user.id]['count'] = 0
        game_status[data.from_user.id]['win'] += 1
        return 1, great_answer(data.from_user.id, strings=[
            f'Ты победил {data.from_user.first_name}', 'Молодец :v:'])
    elif check_draw (game_status[data.from_user.id]['pole']):
        game_status[data.from_user.id]['count'] = 0
        game_status[data.from_user.id]['win'] += 0.5
        game_status[data.from_user.id]['lost'] += 0.5
        return 0, great_answer(data.from_user.id, strings=[
            f"Ничья {data.from_user.first_name}", "Ты старался :fist:"])
    else:
        game_status[data.from_user.id]['pole'][bot_ai(game_status[data.from_user.id]['pole'])] = TOKENBOT
        game_status[data.from_user.id]['count'] += 1
        if checkwin(game_status[data.from_user.id]['pole'], TOKENBOT):
            game_status[data.from_user.id]['count'] = 0
            game_status[data.from_user.id]['lost'] += 1
            return -1, great_answer(data.from_user.id, strings=[
                f'Ты лузер {data.from_user.first_name}', 'А я крут :sunglasses:'])
    return 5, great_answer(data.from_user.id, strings=[
        f'Шевели мозгом {data.from_user.first_name}', 'Ваш ход :pig:'])
    # Ход Бота


def bot_move(board:list):
    flag = True
    while (flag):
        rand = rnd(0, 8)
        if board[rand] == str(rand):
            return rand

def bot_ai(board: list):
    best_score = -8
    best_move = 0    
    for key in range(len(board)):
        if board[key] in valid:
            temp = board[key]
            board[key] = TOKENBOT
            score = minimax(board, False) # параметр False передастся функции minimax. 
            board[key] = temp
            if score > best_score:
                best_score = score
                best_move = key
    return best_move

def minimax(board, is_maximizing):
    """Функция по принципу minimax. 

    - ### https://en.wikipedia.org/wiki/Minimax"""

    # Оцениваем риски, предсказывая шаги пользователя и бота наперед.
    # Необходимо, чтобы ИИ получал оценку своих действий так:
    # - поощрение за хороший ход, который завершит игру победой ИИ третьим символом подряд. 
    # - наказание за плохой ход, который даст игроку поставить 3 символа подряд. 
    # - в случае невозможности победить, выходить на ничью, назание, как и поощрение не будет применено к ИИ. 
    
    # Если вернулось значени True для бота - возвращаем 1
    if checkwin(board, TOKENBOT):
        return 1
    # Если вернулось значение True для пользователя - возвращаем -1
    elif checkwin(board, TOKENPLAYER):
        return -1
    # Если вернулась ничья - возвращаем 0
    elif check_draw(board):
        return 0
    
    # is_maximizing принимает булево значение изначально из функции ai_move
    # 1) Получает из функции ai_move - False, далее переходит к else, и переключается на True, производится рекурсия функции 
    # для проверки всех возможных ходов пользователя и оценки наилучшего варианта для минимизации шанса победы пользователя.
    # 2) В True производится максимизация шанса на победу, путем оценки всех возможных ходов бота, которые приведут
    # либо к победе, либо к ничьей. 
    
    
    # Максимизация шанса на победу бота по принципу Maximin
    if is_maximizing:
        best_score = -8
        for key in range(len(board)):
            if board[key] in valid:
                temp = board[key]
                board[key] = TOKENBOT
                score = minimax(board, False)
                board[key] = temp
                if score > best_score:
                    best_score = score
        return best_score
    # Минимизация шанса на победу пользователя по принципу Minimax
    else:
        best_score = 8
        for key in range(len(board)):
            if board[key] in valid:
                temp = board[key]
                board[key] = TOKENPLAYER
                score = minimax(board, True)
                board[key] = temp
                if score < best_score:
                    best_score = score
        return best_score


def check_draw(board):
    """Функция проверки на ничью
    
    Возвращает:
    - False, в случае, если еще остались пустые ячейки
    - True, если нет"""

    for key in range(len(board)):
        if board[key] in valid:
            return False
    return True

def checkwin(board: list, mark: str):
    for each in wins_line:
        if board[each[0]] == board[each[1]] == board[each[2]] == mark:
            return True
    return False


if __name__ == '__main__':
    app = ApplicationBuilder().token(mytoken.MYTOKEN).build()
    app.add_handler(CommandHandler('start', start_game))    
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CallbackQueryHandler(buttons))
    app.run_polling()

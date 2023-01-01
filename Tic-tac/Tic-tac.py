# Создайте программу для игры в ""Крестики-нолики"".

import logging, mytoken
import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes, ConversationHandler
from random import randint as rnd
from IOData import save_static, load_static

logging.basicConfig(filename='bot.log', filemode='w', encoding='utf-8',
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Символы для поля
TOKENEMP = '\N{WRAPPED PRESENT}'
TOKENBOT = '\N{GRINNING FACE WITH STAR EYES}'
TOKENPLAYER = '\N{SNOWFLAKE}\N{VARIATION SELECTOR-16}'

# Болванка для сообщений
ANSWER_SPLIT = ('\N{TROPHY}Рейтинг\N{TROPHY}', 'Выигрышей: ', 'Проигрышей: ')

START_ROUTES, END_ROUTES = range(2)
# Пустая статистика, начальное игровое поле и выигрышные комбинации
STATISTICS_EMPTY = {'win': 0, 'lost': 0, 'lastgame': None}
POLE_EMPTY = (list(map(str, range(0, 9))))
WINS_LINE = [(0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6),
             (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6)]
VALID = "012345678"
# Состояние поля для пользователя по его id
game_status = {}
# Указатель на ключи словаря
game_status_keys = game_status.keys()
# Статистика пользователя по его id
game_static = {}
# Указатель на ключи словаря
game_static_keys = game_static.keys()



def check_status(id_user: int):
    if id_user not in game_static_keys:
        game_status[id_user] = POLE_EMPTY.copy()
        data = load_static()
        if str(id_user) in data.keys():
            game_static[id_user] = data[str(id_user)]
        else: 
            game_static[id_user] = STATISTICS_EMPTY.copy()
    


def builde_answer(id_user: int, strings: list):
    ans = list(ANSWER_SPLIT)
    ans[1] += str(game_static[id_user]['win'])
    ans[2] += str(game_static[id_user]['lost'])
    for i in range(len(strings)):
        ans.append(strings[i])
    return '\n'.join(ans)


async def help_command(update: Update, _):
    await update.message.reply_text("Это тик так")

# Создаем игровое поле


def great_field(number: list):
    return [[InlineKeyboardButton(text=TOKENEMP if number[i+j] in VALID else number[i+j], callback_data=str(i+j)) for i in range(3)] for j in [0, 3, 6]]


async def start_game(update: Update, context: ContextTypes.DEFAULT_TYPE):    
    name = update.message.from_user
    logger.info(f"User {name.first_name} started the game.")
    check_status(name.id)
    if rnd(0,2):
        game_status[name.id][bot_ai(game_status[name.id])] = TOKENBOT
    answer = builde_answer(
        name.id, strings=[f'Привет {name.first_name}', 'Твой ход \N{SNOWMAN WITHOUT SNOW}'])    
    await update.message.reply_text(answer, reply_markup=InlineKeyboardMarkup(great_field(game_status[name.id])))
    return START_ROUTES

async def start_game_new(update: Update, context: ContextTypes.DEFAULT_TYPE):    
    query = update.callback_query
    await query.answer()
    logger.info(f"User {query.from_user.first_name} started  new game.")    
    if rnd(0,2):
        game_status[query.from_user.id][bot_ai(game_status[query.from_user.id])] = TOKENBOT
    answer = builde_answer(
        query.from_user.id, strings=[f'Привет {query.from_user.first_name}', 'Твой ход \N{SNOWMAN WITHOUT SNOW}'])    
    await query.edit_message_text(answer, reply_markup=InlineKeyboardMarkup(great_field(game_status[query.from_user.id])))
    return START_ROUTES


async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data != game_status[query.from_user.id][int(query.data)]:
        answer = builde_answer(query.from_user.id, strings=[
                              f'Хитришь {query.from_user.first_name}', 'Играй честно \N{banana}'])
        await query.edit_message_text(answer, reply_markup=InlineKeyboardMarkup(great_field(game_status[query.from_user.id])))
    else:
        result, answer = game_round(query)
        if result == 5:                    
            await query.edit_message_text(answer, reply_markup=InlineKeyboardMarkup(great_field(game_status[query.from_user.id])))
            return START_ROUTES
        else:
            reply_markup = great_field(game_status[query.from_user.id])
            reply_markup.append(
                [
                    InlineKeyboardButton("Сыграем еще!", callback_data="Yes"),
                    InlineKeyboardButton("Досвидания", callback_data="No"),
                ])
            await query.edit_message_text(answer, reply_markup=InlineKeyboardMarkup(reply_markup))
            game_status[query.from_user.id] = list(POLE_EMPTY)
            game_static[query.from_user.id]['lastgame'] = datetime.datetime.today().strftime("%d-%b-%Y (%H:%M:%S.%f)")
            return END_ROUTES

async def end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer() 
    await query.edit_message_text(text=builde_answer(query.from_user.id,["Спасибо за игру.","Приходи есчо."]))
    return ConversationHandler.END


def game_round(data):
    game_status[data.from_user.id][int(data.data)] = TOKENPLAYER    
    if checkwin(game_status[data.from_user.id], TOKENPLAYER):        
        game_static[data.from_user.id]['win'] += 1
        return 1, builde_answer(data.from_user.id, strings=[
            f'Ты победил {data.from_user.first_name}', 'Молодец \N{VICTORY HAND}'])
    elif check_draw (game_status[data.from_user.id]):        
        game_static[data.from_user.id]['win'] += 0.5
        game_static[data.from_user.id]['lost'] += 0.5
        return 0, builde_answer(data.from_user.id, strings=[
            f"Ничья {data.from_user.first_name}", "Ты старался \N{RAISED FIST}"])
    else:
        game_status[data.from_user.id][bot_ai(game_status[data.from_user.id])] = TOKENBOT        
        if checkwin(game_status[data.from_user.id], TOKENBOT):            
            game_static[data.from_user.id]['lost'] += 1
            return -1, builde_answer(data.from_user.id, strings=[
                f'Ты лузер {data.from_user.first_name}', 'А я крут \N{DARK SUNGLASSES}'])
        elif check_draw (game_status[data.from_user.id]):
            game_static[data.from_user.id]['win'] += 0.5
            game_static[data.from_user.id]['lost'] += 0.5
            return 0, builde_answer(data.from_user.id, strings=[
            f"Ничья {data.from_user.first_name}", "Ты старался \N{RAISED FIST}"]) 
    return 5, builde_answer(data.from_user.id, strings=[
        f'Шевели мозгом {data.from_user.first_name}', 'Твой ход \N{SNOWMAN WITHOUT SNOW}'])
    


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
        if board[key] in VALID:
            temp = board[key]
            board[key] = TOKENBOT
            score = minimax(board, False) 
            board[key] = temp
            if score > best_score:
                best_score = score
                best_move = key
    return best_move

def minimax(board, is_maximizing):
    """Функция по принципу minimax. 

    - ### https://en.wikipedia.org/wiki/Minimax"""
    
    if checkwin(board, TOKENBOT):
        return 1    
    elif checkwin(board, TOKENPLAYER):
        return -1   
    elif check_draw(board):
        return 0    
    if is_maximizing:
        best_score = -8
        token = TOKENBOT
        flag = False
    else:
        best_score = 8
        token = TOKENPLAYER
        flag = True
    for key in range(len(board)):
        if board[key] in VALID:
            temp = board[key]
            board[key] = token
            score = minimax(board, flag)
            board[key] = temp
            if flag:
                if score < best_score:
                    best_score = score
            else:
                if score > best_score:
                    best_score = score       
    return best_score
    

def check_draw(board):
    """Функция проверки на ничью
    
    Возвращает:
    - False, в случае, если еще остались пустые ячейки
    - True, если нет"""

    for key in range(len(board)):
        if board[key] in VALID:
            return False
    return True

def checkwin(board: list, mark: str):
    for each in WINS_LINE:
        if board[each[0]] == board[each[1]] == board[each[2]] == mark:
            return True
    return False






if __name__ == '__main__':
    
    app = ApplicationBuilder().token(mytoken.MYTOKEN).build()
    conv_handler = ConversationHandler(        
        entry_points=[CommandHandler("start", start_game)],
        states={
            START_ROUTES: [
                CallbackQueryHandler(buttons, pattern="[0-8]"),                
            ],
            END_ROUTES: [
                CallbackQueryHandler(start_game_new, pattern="^" + "Yes" + "$"),
                CallbackQueryHandler(end, pattern="^" + "No" + "$"),
            ],
        },
        fallbacks=[CommandHandler("start", start_game)],
    )
    app.add_handler(conv_handler)
    app.run_polling()
    save_static(game_static)

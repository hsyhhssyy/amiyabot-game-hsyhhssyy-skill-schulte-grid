import re
import datetime
import time
import os

from core.util import read_yaml
from core import log, Message, Chain
from core.database.user import UserInfo
from core.resource.arknightsGameData import ArknightsGameData

from .game_builders.continuous_mode import build_puzzle_continuous_mode
from .game_builders.random_distribution_mode import build_puzzle_random_distribution_mode
from .game_manager import GameManager

running_tasks = set()

curr_dir = os.path.dirname(__file__)

game_config = read_yaml(f'{curr_dir}/wordle.yaml')
wordle_config = read_yaml(f'{curr_dir}/wordle.yaml').wordle

name_dicts = {}

# 用于记录所有干员的名字,在你答错的时候扣分
operator_name_dict = []

locks = {}

def write_log(str):
    log.info(str)

def build_name_dict(data_function, keyname):
    temp_dict = {}
    name_keys = []
    data_dict = {}
    black_list = []

    for op_id in ArknightsGameData.operators.keys():
        for item in data_function(ArknightsGameData.operators[op_id]):
            item_name = item[keyname]
            if( isinstance(item_name, str) ):
                item_name = re.sub(r'[^\w]', '', item_name)
                temp_dict[item_name] = ArknightsGameData.operators[op_id].name
                name_keys.append(item_name)

    for item_name in temp_dict.keys():
        if name_keys.count(item_name) > 1:
            black_list.append(item_name)
            continue
        data_dict[item_name] = temp_dict[item_name]

    return {'data': data_dict, 'black_list': black_list}

def init_game_dict():
    global name_dicts

    name_dicts = {
        'skill': build_name_dict(lambda op: op.skills()[0], 'skill_name'),
        'talent': build_name_dict(lambda op: op.talents(), 'talents_name'),
        'equip': build_name_dict(lambda op: op.modules(), 'uniEquipName')
    }

    # 猜模组需要移除一下证章
    keys_to_delete = [key for key in name_dicts['equip']
                        ['data'].keys() if '证章' in key]
    for key in keys_to_delete:
        del name_dicts['equip']['data'][key]

    # 构造干员名用于扣分
    for operator in ArknightsGameData().operators:
        operator_name_dict.append(operator)

def format_answer(candidate_dict):
    formatted_strs = []
    for operator_name, answers in candidate_dict.items():
        for answer in answers:
            word = answer["word"]  # 从字典结构中直接获取"word"
            formatted_strs.append(f'干员"{operator_name}":"{word}"')
    return "\n".join(formatted_strs)


def format_candidate(candidate_dict, operator_name):
    # 直接从字典中获取operator_name的值，如果不存在则返回空列表
    answers = candidate_dict.get(operator_name, [])
    for answer in answers:
        word = answer["word"]  # 从字典结构中直接获取"word"
        return word
    return ""  # 如果找不到对应的operator_name，返回空字符串


async def display_reward(data, rewards, users):
    text_prefix = '最终成绩：'
    text = ''
    for user_id in rewards.keys():
        points = rewards[user_id]
        if points < 0:
            points = 0
        if points > game_config.jade_point_max:
            points = game_config.jade_point_max

        text = text + f'{users[user_id]}：{points}分\n'
        UserInfo.add_jade_point(user_id, points, game_config.jade_point_max)

    if text == '':
        text_prefix = text_prefix + '无人得分。'
    else:
        text_prefix = text_prefix + '\n' + text

    disp = Chain(data, at=False).text(text_prefix)
    await data.send(disp)


def add_points(answer, rewards, users, points):
    if not answer.user_id in rewards.keys():
        rewards[answer.user_id] = 0
        users[answer.user_id] = answer.nickname

    point = rewards[answer.user_id] + points
    if point < 0:
        point = 0
    rewards[answer.user_id] = point

async def test_game():
    black_list = name_dicts['skill']['black_list']
    
    # console log all black list

    for item in black_list:
        log.info(item)


async def benchmark():
    type_string = {
        'talent': '天赋',
        'skill': '技能',
        'equip': '模组'
    }

    puzzle_translation = {
        'random': '随机',
        'continuous': '连续'
    }

    max_sizes = {}

    for game_type in type_string.keys():
        words_map = name_dicts[game_type]['data']
        black_list = name_dicts[game_type]['black_list']
        words = [name for name in name_dicts[game_type]['data'].keys()]

        max_grid_size = {'random': (0, 0), 'continuous': (0, 0)}

        grid_x = grid_y = 1
        while True:
            for puzzle_type in  puzzle_translation.keys():
                try:
                    start_time = time.time()

                    if puzzle_type == 'random':
                        puzzle, answer = await build_puzzle_random_distribution_mode(grid_x, grid_y, words, black_list, 3)
                    elif puzzle_type == 'continuous':
                        puzzle, answer = await build_puzzle_continuous_mode(grid_x, grid_y, words, black_list, 3)

                    duration = time.time() - start_time
                    log.info(f'{type_string[game_type]}方格{grid_x}x{grid_y}，{puzzle_translation[puzzle_type]}模式，用时{duration:.3f}秒')

                    if duration > 1 or puzzle == None or puzzle == False:
                        max_grid_size[puzzle_type] = (grid_x, grid_y)
                        break
                except (RecursionError, MemoryError) as e:
                    max_grid_size[puzzle_type] = (grid_x-1, grid_y-1)
                    break

            if all(val != (0, 0) for val in max_grid_size.values()):
                break

            grid_x += 1
            grid_y += 1

        max_sizes[game_type] = max_grid_size

    formatted = []

    for game_type, sizes in max_sizes.items():
        for puzzle_type, size in sizes.items():
            formatted.append(f"{puzzle_translation[puzzle_type]}{type_string[game_type]}方格 最大 {size[0]}x{size[1]}")

    return " \n ".join(formatted)

async def play_game(data: Message, game_type: str, puzzle_type: str):
    match = re.search('方格[^\d]*(\d+)x(\d+)', data.text_digits)

    if match:
        grid_x = int(match.group(1))
        grid_y = int(match.group(2))
    else:
        grid_x = 7
        grid_y = 7

    if grid_x > 10:
        grid_x = 10
    if grid_y > 10:
        grid_y = 10
    if grid_x < 4:
        grid_x = 4
    if grid_y < 4:
        grid_y = 4
    
    type_string_map = {
        'talent': '天赋',
        'skill': '技能',
        'equip': '模组'
    }

    operator_data_type = type_string_map.get(game_type, game_type)

    words_map = name_dicts[game_type]['data']
    black_list = name_dicts[game_type]['black_list']

    words = [name for name in name_dicts[game_type]['data'].keys()]

    log.info(f'创建方格{grid_x}x{grid_y}')
    channel_id = data.channel_id
    puzzle = None

    if channel_id in running_tasks:
        await data.send(Chain(data, at=False).text(f'抱歉，同一时间同一频道只能进行一局游戏。'))
        return

    running_tasks.add(channel_id)
    try:
        await data.send(Chain(data, at=False).text(f'正在出题，请稍候......'))
        start_time = time.time()

        if puzzle_type == 'random':
            puzzle, answer = await build_puzzle_random_distribution_mode(grid_x, grid_y, words, black_list, 3)
        elif puzzle_type == 'continuous':
            puzzle, answer = await build_puzzle_continuous_mode(grid_x, grid_y, words, black_list, 3)
        else:
            await data.send(Chain(data, at=False).text(f'抱歉，这是兔兔不支持的模式。'))
            return

        end_time = time.time()
        elapsed_time = (end_time - start_time) * 1000
        write_log(f'题目已创建，用时{elapsed_time:.2f} ms')

        if puzzle == None or puzzle == False:
            await data.send(Chain(data, at=False).text(f'抱歉，兔兔一时间没有想到合适的谜题，请再试一次吧。'))
            return

        for row in puzzle:
            new_row = '['
            for item in row:
                if item == 0:
                    new_row += " 0 , "
                else:
                    new_row += f"'{str(item) }', "
            new_row = new_row.rstrip(', ')  # 去除最后一个逗号和空格
            new_row += '],'
            write_log(new_row)

        # 寻找对应的干员
        answer_candidate = {}

        for word, coords in answer.items():
            if word in words_map.keys():
                operator_name = words_map[word]

                # 如果operator_name已经在answer_candidate中，则直接添加到列表中
                if operator_name in answer_candidate:
                    answer_candidate[operator_name].append(
                        {"word": word, "coords": coords})
                # 如果operator_name不在answer_candidate中，创建一个新列表并添加条目
                else:
                    answer_candidate[operator_name] = [
                        {"word": word, "coords": coords}]

        if puzzle_type == 'random':
            mode_str = f"随机模式，干员的{operator_data_type}随机分布在网格中。"
        elif puzzle_type == 'continuous':
            mode_str = f"连续模式，干员的{operator_data_type}每个字都上下左右按顺序相连。"

        max_time = grid_x * grid_y * 5

        ask = Chain(data, at=False).html(f'{curr_dir}/template/schulte-grid.html', data={"puzzle": puzzle, "type": puzzle_type}, width=800, height=320).text(
            f'上图中有{len(answer_candidate)}位干员的{operator_data_type}，请博士们回答这些干员的名字。\n当前模式为：{mode_str},共计时{max_time}秒。')

        rewards = {}
        answer_interval = round(grid_x * grid_y * 0.5 / 5) * 5
        users = {}
        warning_shown = False

        manager = GameManager()
        
        while True:
            message, elapsed_time, time_since_last_talk = await manager.wait(data, ask)

            if message is not None:
                data = message

            if elapsed_time>max_time or (warning_shown==True and time_since_last_talk>answer_interval*2):
                await data.send(Chain(data, at=False).text(f'时间到，还未答出的答案包括：\n{format_answer(answer_candidate)}，游戏结束~'))
                await display_reward(data, rewards, users)
                break
            if message == None:
                if time_since_last_talk > answer_interval and not warning_shown:
                    await data.send(Chain(data, at=False).text(f'{answer_interval}秒内没有博士回答任何答案的话，本游戏就要结束咯~，不想猜了的话，可以发送“不玩了”结束游戏。'))
                    warning_shown = True
                    continue
                continue
            
            warning_shown = False

            if message.text == '不玩了':
                await data.send(Chain(data, at=False).text(f'还未答出的答案包括：\n{format_answer(answer_candidate)}，游戏结束~'))
                await display_reward(data, rewards, users)
                break

            write_log(f'收到回答：{message.text}')

            if message.text in answer_candidate.keys():
                reward_points = int(wordle_config.rewards.bingo * 1)

                reward_txt = f'回答正确！图中包括干员{message.text}的{operator_data_type}：{format_candidate(answer_candidate,message.text)}。合成玉+{reward_points}'

                add_points(message, rewards, users, reward_points)

                # 遍历puzzle[y][x],任何元素以◇开头则去掉开头的◇
                for y in range(len(puzzle)):
                    for x in range(len(puzzle[y])):
                        if puzzle[y][x].startswith('♣'):
                            puzzle[y][x] = '◇' + puzzle[y][x][1:]

                # 从puzzle移除这个字
                for ans in answer_candidate[message.text]:
                    for coord in ans["coords"]:
                        x, y = coord  # 从新的字典结构中获取"coords"，并直接解包为y和x
                        puzzle[y][x] = '♣' + puzzle[y][x]

                await data.send(Chain(data).html(f'{curr_dir}/template/schulte-grid.html', data={"puzzle": puzzle, "type": puzzle_type}, width=800).text(reward_txt))

                del answer_candidate[message.text]

                if len(answer_candidate) == 0:
                    await data.send(Chain(data).text('该题目全部答完，游戏结束！'))
                    await display_reward(data, rewards, users)
                    break

                continue

            if message.text in operator_name_dict:
                reward_points = int(wordle_config.rewards.fail * 1)

                add_points(message, rewards, users, 0-reward_points)

                await data.send(Chain(data).text(f'抱歉博士，干员{message.text}并不在图中，合成玉-{reward_points}。'))
                
                continue
            
            continue

    finally:
        running_tasks.remove(channel_id)
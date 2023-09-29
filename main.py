import re
import datetime
import asyncio
import os

from amiyabot import PluginInstance
from core.util import any_match,read_yaml
from core import log, Message, Chain
from core.database.user import UserInfo
from core.resource.arknightsGameData import ArknightsGameData

from .game_builder import build_puzzle

curr_dir = os.path.dirname(__file__)

game_config = read_yaml(f'{curr_dir}/wordle.yaml')
wordle_config = read_yaml(f'{curr_dir}/wordle.yaml').wordle

skill_name_dict = {}
talent_name_dict = {}
equip_name_dict = {}

# 用于记录所有干员的名字,在你答错的时候扣分
operator_name_dict = []

locks = {}

def build_name_dict(data_function, keyname):
    temp_dict = {}
    name_keys = []
    name_dict = {}
    
    for op_id in ArknightsGameData.operators.keys():
        for item in data_function(ArknightsGameData.operators[op_id]):
            # 首先只加入全汉字的名字
            item_name = item[keyname]
            item_name = re.sub(r'[^\w]', '', item_name)
            temp_dict[item_name] = ArknightsGameData.operators[op_id].name
            name_keys.append(item_name)

    for item_name in temp_dict.keys():
        # 排除被多个干员持有的名字
        if name_keys.count(item_name) > 1:
            continue

        # 排除名字有重叠的名字，注意此处将会保留较短的名字
        if any((name != item_name and name in item_name) for name in name_keys):
            continue

        name_dict[item_name] = temp_dict[item_name]
        
    return name_dict

class SkillSchulteGridPluginInstance(PluginInstance):
    def install(self):
        global skill_name_dict, talent_name_dict,equip_name_dict

        skill_name_dict = build_name_dict(lambda op: op.skills()[0], 'skill_name')
        talent_name_dict = build_name_dict(lambda op: op.talents(), 'talents_name')
        equip_name_dict = build_name_dict(lambda op: op.modules(), 'uniEquipName')

        # 猜模组需要移除一下证章
        keys_to_delete = [key for key in equip_name_dict.keys() if '证章' in key]
        for key in keys_to_delete:
            del equip_name_dict[key]

        # (This is your last for loop, unchanged.)
        for operator in ArknightsGameData().operators:
            operator_name_dict.append(operator)

bot = SkillSchulteGridPluginInstance(
    name='方格游戏',
    version='1.6',
    plugin_id='amiyabot-game-hsyhhssyy-skill-schulte-grid',
    plugin_type='',
    description='玩一场方格游戏',
    document=f'{curr_dir}/README.md'
)

running_tasks = set()

def format_answer(answer_candidate):
    r_str=''
    for key in answer_candidate.keys():
        r_str += f'干员"{key}":'
        for skill in answer_candidate[key]:
            r_str += f'"{skill[0]}"'
        r_str += '，'
    return r_str.rstrip('，')

def format_candidate(answer_candidate_value):
    r_str=''
    for ans in answer_candidate_value:
        r_str += f'"{ans[0]}"'
    return r_str

async def display_reward(data,rewards,users):
    text = '最终成绩：\n'
    for user_id in rewards.keys():
        points = rewards[user_id]
        if points < 0 :
            points = 0
        if points > game_config.jade_point_max:
            points = game_config.jade_point_max

        text = text + f'{users[user_id]}：{points}分\n'
        UserInfo.add_jade_point(user_id, points, game_config.jade_point_max)
    
    disp = Chain(data, at=False).text(text)
    await data.send(disp)

def add_points(answer,rewards,users,points):
    if not answer.user_id in rewards.keys():
        rewards[answer.user_id] = 0
        users[answer.user_id] = answer.nickname
    
    point  = rewards[answer.user_id] + points
    if point <0:
        point = 0
    rewards[answer.user_id] = point

async def play_game(data: Message, words: list, words_map: dict,type:str):
    match = re.search('方格(\d*?)x(\d*?)', data.text_digits)
    if match:
        grid_size = int(match.group(1))
    else:
        grid_size = 10

    if grid_size > 10:
        grid_size = 10

    # log.info(f'创建方格{grid_size}x{grid_size}')
    channel_id = data.channel_id
    puzzle = None

    if channel_id in running_tasks:
        await data.send(Chain(data, at=False).text(f'抱歉，同一时间同一频道只能进行一局游戏。'))
        return

    running_tasks.add(channel_id)
    try:
        await data.send(Chain(data, at=False).text(f'正在出题，请稍候......'))

        words = words + ['○','○','○','○','○']
        for _ in range(0,5):
            puzzle, answer = await build_puzzle(grid_size, words, 500)

        if puzzle == None:
            await data.send(Chain(data, at=False).text(f'抱歉，兔兔一时间没有想到合适的谜题，请再试一次吧。'))
            return

        #寻找对应的干员
        answer_candidate = {}
        for ans in answer:
            if ans[0] in words_map.keys():
                operator_name = words_map[ans[0]]
                answer_candidate[operator_name] = []

        for ans in answer:
            if ans[0] in words_map.keys():
                operator_name = words_map[ans[0]]
                answer_candidate[operator_name].append(ans)

        ask = Chain(data, at=False).html(f'{curr_dir}/template/schulte-grid.html', data=puzzle, width=800).text(f'上图中有{len(answer_candidate)}位干员的{type}，请博士们回答这些干员的名字。注意这些{type}名的每个字都是相连的，请不要跳跃寻找。共计时5分钟。')

        last_talk = datetime.datetime.now()
        start_time = datetime.datetime.now()
        max_time = 60 * 5
        rewards = {}
        users = {}

        while True:
            event = await data.wait_channel(ask,
                                            force=True,
                                            clean=bool(ask),
                                            max_time=5)

            ask = None

            try:
                if not event:
                    time_delta = datetime.datetime.now()
                    if  time_delta - start_time > datetime.timedelta(seconds=max_time):
                        await data.send(Chain(data, at=False).text(f'5分钟时间到，还未答出的答案包括：{format_answer(answer_candidate)}，游戏结束。'))
                        await display_reward(data,rewards,users)
                        return

                    if  time_delta - last_talk < datetime.timedelta(seconds=95) and time_delta - last_talk > datetime.timedelta(seconds=90):
                        await data.send(Chain(data, at=False).text(f'30秒内没有博士回答任何答案的话，本游戏就要结束咯~，不想猜了的话，可以发送“不玩了”结束游戏。'))
                        continue
                    elif datetime.datetime.now() - last_talk > datetime.timedelta(seconds=120):
                        await data.send(Chain(data, at=False).text(f'时间到，还未答出的答案包括：{format_answer(answer_candidate)}，游戏结束~'))
                        await display_reward(data,rewards,users)
                        return 
                    else:
                        continue

                last_talk = datetime.datetime.now()
                answer = event.message

                if any_match(answer.text, ['不玩了', '结束']):
                    await data.send(Chain(answer, at=False).text(f'还未答出的答案包括：{format_answer(answer_candidate)}，游戏结束~'))
                    await display_reward(data,rewards,users)
                    return
                
                # if any_match(answer.text, ['作弊']):
                #    await data.send(Chain(answer, at=False).text(f'测试作弊：{format_answer(answer_candidate)}\n'))
                #    continue

                if answer.text in answer_candidate.keys():
                    reward_points = int(wordle_config.rewards.bingo * 1)

                    reward_txt = f'回答正确！图中包括干员{answer.text}的{type}：{format_candidate(answer_candidate[answer.text])}。合成玉+{reward_points}'

                    
                    add_points(answer,rewards,users,reward_points)

                    # 从puzzle移除这个字
                    for ans in answer_candidate[answer.text]:
                        for ans_path in ans[1]:
                            puzzle[ans_path[1]][ans_path[0]] = '×'+puzzle[ans_path[1]][ans_path[0]]

                    await data.send(Chain(answer).html(f'{curr_dir}/template/schulte-grid.html',data=puzzle,width = 800).text(reward_txt))

                    del answer_candidate[answer.text]

                    if len(answer_candidate) == 0:
                        await data.send(Chain(answer).text('该题目全部答完，游戏结束！'))
                        await display_reward(data,rewards,users)
                        return
                    
                    continue
                
                if answer.text in operator_name_dict:
                    reward_points = int(wordle_config.rewards.fail * 1)

                    add_points(answer,rewards,users,0-reward_points)

                    await data.send(Chain(answer).text(f'抱歉博士，干员{answer.text}并不在图中，合成玉-{reward_points}。'))
                    continue
            finally:
                if event:
                    event.close_event()
    finally:
        running_tasks.remove(channel_id)

    return

@bot.on_message(keywords=['天赋方格'],level=5)
async def _(data: Message):
    words = []
    for skill_name in talent_name_dict.keys():
        words.append(skill_name)

    await play_game(data, words, talent_name_dict,'天赋')

@bot.on_message(keywords=['技能方格'],level=5)
async def _(data: Message):
    words = []
    for skill_name in skill_name_dict.keys():
        words.append(skill_name)

    await play_game(data, words, skill_name_dict,'技能')

@bot.on_message(keywords=['模组方格'],level=5)
async def _(data: Message):
    words = []
    for name in equip_name_dict.keys():
        words.append(name)

    await play_game(data, words, equip_name_dict,'模组')
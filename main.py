import re
import datetime
import random
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
operator_name_dict = []

class SkillSchulteGridPluginInstance(PluginInstance):
    def install(self):
        temp_dict={}
        dict_keys=[]
        for op_id in ArknightsGameData.operators.keys():
            for skill in ArknightsGameData.operators[op_id].skills()[0]:
                # 首先只加入全汉字的技能名
                skill_name = skill['skill_name']
                skill_name = re.sub(r'[^\w]', '', skill_name)
                temp_dict[skill_name] = ArknightsGameData.operators[op_id].name
                dict_keys.append(skill_name)
        
        for skill_name in temp_dict.keys():
            #排除冲锋号令之类被多个干员持有的技能名
            if dict_keys.count(skill_name)>1:
                continue

            #排除急救，急救模式之类技能名有重叠的技能名，注意此处将会保留急救而放弃急救模式，也就是如果有人是我的开头，那我就不算了
            if any((sk!=skill_name and skill_name.startswith(sk)) for sk in dict_keys):
                # log.info(skill_name)
                continue

            skill_name_dict[skill_name]=temp_dict[skill_name]

        skills=''
        for skill_name in skill_name_dict:
            skills +=f'({skill_name}x{skill_name_dict[skill_name]})'

        # log.info(f'{skills} - {len(skill_name_dict)}')

        for operator in ArknightsGameData().operators:
            operator_name_dict.append(operator)

bot = SkillSchulteGridPluginInstance(
    name='技能方格游戏',
    version='1.3',
    plugin_id='amiyabot-game-hsyhhssyy-skill-schulte-grid',
    plugin_type='',
    description='玩一场技能方格游戏',
    document=f'{curr_dir}/README.md'
)

def format_answer(answer_candidate):
    r_str=''
    for key in answer_candidate.keys():
        r_str += f'干员"{key}"的技能'
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


@bot.on_message(keywords=['技能方格'],level=5)
async def _(data: Message):
    words = []
    for skill_name in skill_name_dict.keys():
        words.append(skill_name)

    match = re.search('技能方格(\d*?)x(\d*?)', data.text_digits)
    if match:
        grid_size = int(match.group(1))
    else:
        grid_size = 10

    if grid_size>10:
        grid_size = 10

    # log.info(f'创建方格{grid_size}x{grid_size}')

    puzzle = None

    await data.send(Chain(data, at=False).text(f'正在出题，请稍候......'))

    words = words + ['○','○','○','○','○']
    for _ in range(0,5):
        puzzle,answer = await build_puzzle(grid_size,words,500)
    
    if puzzle == None:
        return Chain(data,at=False).text(f'抱歉，兔兔一时间没有想到合适的谜题，请再试一次吧。')
    
    #寻找对应的干员
    answer_candidate = {}
    for ans in answer:
        if ans[0] in skill_name_dict.keys():
            operator_name = skill_name_dict[ans[0]]
            answer_candidate[operator_name]=[]
    
    for ans in answer:
        if ans[0] in skill_name_dict.keys():
            operator_name = skill_name_dict[ans[0]]
            answer_candidate[operator_name].append(ans)
    
    ask = Chain(data,at=False).html(f'{curr_dir}/template/schulte-grid.html',data=puzzle,width = 800).text(f'上图中有{len(answer_candidate)}位干员的技能，请博士们回答这些干员的名字。注意这些技能名的每个字都是相连的，请不要跳跃寻找。共计时5分钟。')

    last_talk = datetime.datetime.now()
    start_time = datetime.datetime.now()

    max_time = 60 *5

    rewards = {}
    users= {}

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

                reward_txt = f'回答正确！图中包括干员{answer.text}的技能：{format_candidate(answer_candidate[answer.text])}。合成玉+{reward_points}'

                
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

    return
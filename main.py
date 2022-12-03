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
        
        #然后排除诸如强力击之类的不能锁定干员的技能名
        for skill_name in temp_dict.keys():
            if dict_keys.count(skill_name)<=1:
                skill_name_dict[skill_name]=temp_dict[skill_name]

        skills=''
        for skill_name in skill_name_dict:
            skills +=f'({skill_name}x{skill_name_dict[skill_name]})'

        log.info(f'{skills} - {len(skill_name_dict)}')

        for operator in ArknightsGameData().operators:
            operator_name_dict.append(operator)

bot = SkillSchulteGridPluginInstance(
    name='技能方格游戏',
    version='1.0',
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
            r_str += f'"{skill}"'
        r_str += '，'
    return r_str.rstrip('，')


async def display_reward(data,rewards,users):
    disp = Chain(data, at=False).text('最终成绩：\n')
    for user_id in rewards.keys():
        points = rewards[user_id]
        if points < 0 :
            points = 0
        if points > game_config.jade_point_max:
            points = game_config.jade_point_max

        disp = disp.text(f'{users[user_id]}：{points}分\n') 
        UserInfo.add_jade_point(user_id, points, game_config.jade_point_max)
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

    log.info(f'创建方格{grid_size}x{grid_size}')

    puzzle = None

    for _ in range(0,5):
        words = words + ['明','日','方','舟']
        puzzle,answer = await build_puzzle(grid_size,words,200)

        if puzzle != None:
            row_str=''
            for row in puzzle:
                for col in row:
                    row_str=row_str+f'{col}\t'
                row_str = row_str+'\n'
            break
    
    if puzzle == None:
        return Chain(data,at=False).text(f'抱歉，兔兔一时间没有想到合适的谜题，请再试一次吧。')
    
    #寻找对应的干员
    answer_candidate = {}
    for ans in answer:
        if ans in skill_name_dict.keys():
            operator_name = skill_name_dict[ans]
            answer_candidate[operator_name]=[]
    
    for ans in answer:
        if ans in skill_name_dict.keys():
            operator_name = skill_name_dict[ans]
            answer_candidate[operator_name].append(ans)
    
    ask = Chain(data,at=False).text(f'博士，这次的题目是：\n{row_str}\n').text(f'上图中有{len(answer_candidate)}位干员的{len(answer)}个技能，请博士们回答这些干员的名字。注意这些技能名的每个字都是相连的，请不要跳跃寻找。共计时5分钟。')

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
                    await data.send(Chain(data, at=False).text(f'30秒内没有博士回答任何答案的话，本游戏就要结束咯~ 猜不出来的话，可以发送“下一题”来跳过本题。'))
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
            
            if any_match(answer.text, ['作弊']):
                await data.send(Chain(answer, at=False).text(f'测试作弊：{format_answer(answer_candidate)}\n'))
                continue

            if any_match(answer.text, answer_candidate.keys()):
                reward_points = int(wordle_config.rewards.bingo * 1)
                await data.send(Chain(answer).text(f'回答正确！图中包括干员{answer.text}的技能：{answer_candidate[answer.text]}。合成玉+{reward_points}'))
                
                add_points(answer,rewards,users,reward_points)

                del answer_candidate[answer.text]

                if len(answer_candidate) == 0:
                    await data.send(Chain(answer).text('该题目全部答完，游戏结束！'))
                    await display_reward(data,rewards,users)
                    return
                
                continue
            
            if any_match(answer.text, operator_name_dict):
                reward_points = int(wordle_config.rewards.fail * 1)

                add_points(answer,rewards,users,0-reward_points)

                await data.send(Chain(answer).text(f'抱歉博士，干员{answer.text}并不在图中，合成玉-{reward_points}。'))
                continue
        finally:
            if event:
                event.close_event()

    return
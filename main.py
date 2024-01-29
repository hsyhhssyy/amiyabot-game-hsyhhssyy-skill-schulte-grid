import os

from core import Message,Chain,AmiyaBotPluginInstance

from .play_game import init_game_dict,play_game,benchmark

curr_dir = os.path.dirname(__file__)

class SkillSchulteGridPluginInstance(AmiyaBotPluginInstance):
    def install(self):
        init_game_dict()


bot = SkillSchulteGridPluginInstance(
    name='方格游戏',
    version='2.0',
    plugin_id='amiyabot-game-hsyhhssyy-skill-schulte-grid',
    plugin_type='',
    description='玩一场方格游戏',
    document=f'{curr_dir}/README.md',
    instruction=f'{curr_dir}/README_USE.md'
)


@bot.on_message(keywords=['方格游戏跑分'], level=5)
async def _(data: Message):
    if not data.is_admin:
        await data.send(Chain(data, at=False).text('只有管理员才能跑分'))
        return
    
    await data.send(Chain(data, at=False).text(f'开始跑分，请稍候，可能需要数十秒到一两分钟...'))
    result = await benchmark()
    await data.send(Chain(data, at=False).text(f'跑分结束：\n{result}'))


@bot.on_message(keywords=['天赋方格'], level=5)
async def _(data: Message):
    await play_game(data, 'talent', 'continuous')


@bot.on_message(keywords=['技能方格'], level=5)
async def _(data: Message):
    await play_game(data, 'skill', 'continuous')


@bot.on_message(keywords=['模组方格'], level=5)
async def _(data: Message):
    await play_game(data, 'equip', 'continuous')


@bot.on_message(keywords=['天赋随机方格'], level=5)
async def _(data: Message):
    await play_game(data, 'talent', 'random')


@bot.on_message(keywords=['技能随机方格'], level=5)
async def _(data: Message):
    await play_game(data, 'skill', 'random')

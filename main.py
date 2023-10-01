import os

from core.customPluginInstance import AmiyaBotPluginInstance
from core import Message

from .play_game import init_game_dict,play_game

curr_dir = os.path.dirname(__file__)

class SkillSchulteGridPluginInstance(AmiyaBotPluginInstance):
    def install(self):
        init_game_dict()


bot = SkillSchulteGridPluginInstance(
    name='方格游戏',
    version='1.9',
    plugin_id='amiyabot-game-hsyhhssyy-skill-schulte-grid',
    plugin_type='',
    description='玩一场方格游戏',
    document=f'{curr_dir}/README.md',
    instruction=f'{curr_dir}/README_USE.md'
)

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

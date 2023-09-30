现在给出一个Python的list的list # puzzle[y][x] ，其中x代表横行，y代表数行，其中值为0的表示空格，值为1的表示非空格。
现在请写一个函数，传入puzzle，寻找一个x，y的值，该格子被包围的边数最多。
再写一个函数，计算给定xy位置的包围数。
包围边数的定义如下：
1、该格子如果某条边和一个非空格相连，则该边被包围
2、该格子的某条边如果是puzzle边界，则该边被包围。



请给出一个函数async def fill_puzzle(puzzle,words,start_x,start_y):
他可以通过递归他自己完成下面的任务:

初始puzzle所有格都为0，puzzle是list的list # puzzle[y][x] 

每一步,在指定的puzzle中填入一个随机选择的word中的字符串,注意这个字符串的填入方式不一定是横行或者竖行,而是可以转弯,只要连续就可以.

注意随机选择的时候，要数一下puzzle中剩余格子数量：
1、不能选长度超过空格的字。
2、当剩余长度小于等于5时，准确的选择一个等于剩余长度的单词。

你可以用游走的形式来逐个选择要游走的位置,在游走时,下一个要游走的格子,必须是周围格子中包围数量最大的格子.
该数值可以用def count_surrounded(puzzle, x, y)函数来计算,

在填写的时候,每游走一格就要用def is_single_connected(array):函数来检查该puzzle的剩余空白区域是否单连通。
如果不是单连通，则要换一个游走方向。
（可以用一个特殊符号比如$来表示正在游走,还未填入字的格子,也可以直接把字填入，因为is_single_connected检查时是读取puzzle中是否为0来进行的）
如果所有游走方向都不能保证接下来的puzzle为单连通，则返回False

如果该单词成功填入，则判断,如果没有空格,则返回True,puzzle的Tuple
如果还有空格，则递归调用他自己，选择一个仍然为0的新点继续填入,选择方式如下：
调用def find_max_surrounded(puzzle):
该函数返回一个坐标的数组，将里面的空格按包围数从大到小排序。如果没有空格，则返回空数组
从第一个开始，递归调用自己，如果返回False，则尝试第二个，依此类推，直到每一个都返回False，则自己也返回False。


## game_builder fill_puzzle 最终提示

def is_single_connected(array):函数可以检查该puzzle的剩余空白区域是否单连通
def count_surrounded(puzzle, x, y)函数来计算一个格子的包围数。
def find_max_surrounded(puzzle) 该函数返回一个坐标的数组，将里面的空格按包围数从大到小排序。如果没有空格，则返回空数组

上面这些函数已经写好了。

请给出一个函数async def fill_char(puzzle,start_x,start_y,word_left):
他可以通过递归他自己完成下面的任务:

puzzle是list的list # puzzle[y][x]，其中0代表空格，传入的参数start_x和y一定代表一个空格,如果不是,函数直接返回False
先深拷贝一份puzzle供后续使用。

在指定的puzzle中填入word_left的第一个字,

调用is_single_connected计算剩余部分是否单连通,不是返回False

word_left是否只有一个字符了。如果是，则返回True,puzzle

再判断puzzle是否还有空格，如果没有了，返回False。

如果还有空格,则继续进行如下操作：

调用count_surrounded计算另外四个方向(不包含斜向)的空格的包围数,并按照从高到低排序,同包围数的随机打乱.
然后根据遍历结果依次递归调用自己并传入移除word_left第一个字的后面的部分
如果全都返回False则自己也返回False.

否则返回一个列表,列表是所有有效填充的puzzle列表.

注意,他每次都输出一个 bool,list的tuple,包括false的时候,方便后面的代码调用

接下来，请实现一个async def fill_puzzle(puzzle,words,start_x,start_y):
他可以通过递归他自己完成下面的任务:

puzzle是list的list # puzzle[y][x]，其中0代表空格，传入的参数start_x和y一定代表一个空格,如果不是,函数直接返回False

先深拷贝一份puzzle供后续使用。

先生成一个单词的选择.

注意随机选择的时候，要数一下puzzle中剩余格子数量：
1. 不能选长度超过空格的字。
2. 当剩余空格小于等于5时，准确的选择一个长度等于剩余空格的单词。
否则
3. 每种长度的单词随机选择一个。

然后将列表顺序打乱，遍历这个单词列表：

调用fill_char,从start_x,start_y填充这个单词,并获取列表.

如果填充失败返回False

遍历上面获取的列表:

判断,如果没有空格,则返回True,puzzle的Tuple
如果还有空格，则递归调用他自己，选择一个仍然为0的新点继续填入,选择方式如下：
调用def find_max_surrounded(puzzle):
该函数返回一个坐标的数组，将里面的空格按包围数从大到小排序。如果没有空格，则返回空数组
从第一个开始，递归调用自己，如果返回False，则尝试第二个，依此类推，直到每一个都返回False,表示列表中的这一项不可用
如果某一项返回True,则返回True,puzzle,answer的Tuple

如果列表里每一个都返回false,则尝试下一个单词

如果所有单词都失败，返回False

注意,他每次都输出tuple,包括false的时候,方便后面的代码调用
注意,他需要返回bool,puzzle,answer的tuple,其中answer是
一个字典,key是被使用到的单词,value是一个list,这个list里的每一项是一个list,记录了该单词每个字在puzzle中的坐标
你能需要修改fill_char来记录这个内容.

## Main

我有一段代码对返回的answer进行如下处理,这是不是不对啊
puzzle, answer = await build_puzzle(grid_x,grid_y, words, 3)
answer_candidate = {}
    for ans in answer:
        if ans[0] in words_map.keys():
            operator_name = words_map[ans[0]]
            answer_candidate[operator_name] = []

    for ans in answer:
        if ans[0] in words_map.keys():
            operator_name = words_map[ans[0]]
            answer_candidate[operator_name].append(ans)

# 

这是answer_candidate的来源,其中coords是一个list,代表一个坐标的xy

answer_candidate = {}

for word, coords in answer.items():
    if word in words_map.keys():
        operator_name = words_map[word]
        
        # 如果operator_name已经在answer_candidate中，则直接添加到列表中
        if operator_name in answer_candidate:
            answer_candidate[operator_name].append({word:word,coords:coords})
        # 如果operator_name不在answer_candidate中，创建一个新列表并添加条目
        else:
            answer_candidate[operator_name] = [{word:word,coords:coords}]

我将据此提问
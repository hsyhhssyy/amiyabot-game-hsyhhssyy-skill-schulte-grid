import random
import asyncio
import copy

# lib主函数
# 根据给定的列表随机生成一个Grid
# 生成的时候，避免出现1个空格或者2个空格的情况，因为1个字或者两个字很难找到词语
# 函数返回Tuple，包含Grid和答案，保证答案唯一性
# 测试通过
async def build_puzzle(size_x,size_y,words,timeout=10000):

    puzzle = build_grid(size_x,size_y)



    return final_puzzle,answers

# 生成一个打乱顺序的拷贝
# 测试通过
def deep_copy_shuffle(list):
    new_list = []
    for x in list:
        new_list.append(x)
    
    random.shuffle(new_list)
    return new_list

async def fill_char(puzzle, start_x, start_y, word_left):
    # 检查起始点是否为空格
    if puzzle[start_y][start_x] != 0:
        return False
    
    # 深拷贝puzzle
    new_puzzle = copy.deepcopy(puzzle)
    
    # 填入word_left的第一个字
    new_puzzle[start_y][start_x] = word_left[0]
    
    # 检查剩余部分是否单连通
    if not is_single_connected(new_puzzle):
        return False
    
    # 如果word_left只有一个字符了，返回True和puzzle
    if len(word_left) == 1:
        return True, new_puzzle
    
    # 如果还有空格
    else:
        # 找到另外四个方向(不包含斜向)的空格的包围数，并按照从高到低排序，同包围数的随机打乱
        surrounded = []
        if start_x > 0 and puzzle[start_y][start_x-1] == 0:
            surrounded.append((start_x-1, start_y, count_surrounded(puzzle, start_x-1, start_y)))
        if start_x < len(puzzle[0])-1 and puzzle[start_y][start_x+1] == 0:
            surrounded.append((start_x+1, start_y, count_surrounded(puzzle, start_x+1, start_y)))
        if start_y > 0 and puzzle[start_y-1][start_x] == 0:
            surrounded.append((start_x, start_y-1, count_surrounded(puzzle, start_x, start_y-1)))
        if start_y < len(puzzle)-1 and puzzle[start_y+1][start_x] == 0:
            surrounded.append((start_x, start_y+1, count_surrounded(puzzle, start_x, start_y+1)))
        surrounded.sort(key=lambda x: (-x[2], random.random()))
        
        # 依次递归调用自己并传入移除word_left第一个字的后面的部分
        for s in surrounded:
            result = await fill_char(new_puzzle, s[0], s[1], word_left[1:])
            if result[0]:
                return result
        
        # 如果全都返回False则自己也返回False
        return False
    
async def fill_puzzle(puzzle, words, start_x, start_y):
    # 检查起始点是否为空格
    if puzzle[start_y][start_x] != 0:
        return False
    
    # 深拷贝puzzle
    new_puzzle = copy.deepcopy(puzzle)
    
    # 随机选择一个单词
    remaining_spaces = sum([1 for row in new_puzzle for space in row if space == 0])
    possible_words = [word for word in words if len(word) <= remaining_spaces]
    if remaining_spaces <= 5:
        possible_words = [word for word in possible_words if len(word) == remaining_spaces]
    if not possible_words:
        return False
    word = random.choice(possible_words)
    
    # 调用fill_char,从start_x,start_y填充这个单词
    result = await fill_char(new_puzzle, start_x, start_y, word)
    if not result[0]:
        return False
    
    # 如果没有空格,则返回True和puzzle的Tuple
    if sum([1 for row in result[1] for space in row if space == 0]) == 0:
        return True, result[1]
    
    # 如果还有空格，则递归调用他自己，选择一个仍然为0的新点继续填入
    else:
        # 调用find_max_surrounded(puzzle)，将里面的空格按包围数从大到小排序。如果没有空格，则返回空数组
        max_surrounded = find_max_surrounded(result[1])
        for s in max_surrounded:
            result = await fill_puzzle(result[1], words, s[0], s[1])
            if result:
                return result
        
        # 如果每一个都返回False，则自己也返回False
        return False

# 生成一个空白的Puzzle list对象
# 测试通过
def build_grid(size_x,size_y):
    puzzle = [] # puzzle[y][x]
    for _ in range(0,size_y):
        row = []
        for _ in range(0,size_x):
            row.append(0)

        puzzle.append(row)

    return puzzle

# 寻找被包围边数最多的空格，返回一个坐标的数组,将里面的空格按包围数排序,如果没有空格返回空数组
# 测试通过
# AI生成
def find_max_surrounded(puzzle):
    max_surrounded = 0
    max_coords = []
    for y in range(len(puzzle)):
        for x in range(len(puzzle[0])):
            if puzzle[y][x] == 0:
                surrounded = count_surrounded(puzzle, x, y)
                if surrounded > max_surrounded:
                    max_surrounded = surrounded
                    max_coords = [(x, y)]
                elif surrounded == max_surrounded:
                    max_coords.append((x, y))
    return sorted(max_coords, key=lambda coord: count_surrounded(puzzle, coord[0], coord[1]), reverse=True)

# 计算给定xy位置的包围数
# 测试通过
# AI生成
def count_surrounded(puzzle, x, y):
    surrounded = 0
    if puzzle[y][x] == 0:
        if x == 0 or x == len(puzzle[0]) - 1 or y == 0 or y == len(puzzle) - 1:
            surrounded += 1
        if x > 0 and puzzle[y][x-1] == 1:
            surrounded += 1
        if x < len(puzzle[0]) - 1 and puzzle[y][x+1] == 1:
            surrounded += 1
        if y > 0 and puzzle[y-1][x] == 1:
            surrounded += 1
        if y < len(puzzle) - 1 and puzzle[y+1][x] == 1:
            surrounded += 1
    return surrounded

# 计算一个Puzzle中所有的空白的格子是否单联通
# 测试通过
# AI生成
def is_single_connected(array):

    # 记录已经访问过的位置
    visited = [[False for j in range(len(array[0]))] for i in range(len(array))]
    
    # 搜索函数
    def dfs(i, j):
        if i < 0 or i >= len(array) or j < 0 or j >= len(array[0]):
            return
        if visited[i][j] or array[i][j] == 1:
            return
        visited[i][j] = True
        dfs(i-1, j)
        dfs(i+1, j)
        dfs(i, j-1)
        dfs(i, j+1)
    
    # 遍历所有0，如果有不连通的部分则返回False
    for i in range(len(array)):
        for j in range(len(array[0])):
            if array[i][j] == 0 and not visited[i][j]:
                dfs(i, j)
                for k in range(len(array)):
                    for l in range(len(array[0])):
                        if array[k][l] == 0 and not visited[k][l]:
                            return False
    return True

def print_log(message):
    print(message)
    pass

def test_output_puzzle(puzzle):
    for row in puzzle:
        print_log(row)

# 下面这部分是测试代码
async def test_main():

    # results,ans = await build_puzzle(5,['Hello','World','Made','Wtf','a','b','c','d','by','China','Fill','How'])

    puzzle = build_grid(4,3)
    success,puzzle = await fill_puzzle(puzzle,['Hello','World','Made','Wtf','a','b','c','d','by','China','Fill','How'],0,0)
    if success:
        test_output_puzzle(puzzle)
    else:
        print_log('Failed')

asyncio.run(test_main())

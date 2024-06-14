import random
import asyncio
import copy
import string

# lib主函数
# 根据给定的列表随机生成一个Grid
# 函数返回Tuple，包含Grid和答案，保证答案唯一性
# 测试通过


async def build_puzzle_continuous_mode(size_x, size_y, words, black_list , timeout):

    # 排除名字有重叠的名字，注意此处将会保留较短的名字
    combined_words = words + black_list
    
    # 先结合BlackList排除带有重叠名字的名字
    valid_words = [item_name for item_name in combined_words if not any((name != item_name and name in item_name) for name in words)]

    # 再排除BlackList
    valid_words = [item_name for item_name in valid_words if not any((name in item_name) for name in black_list)]

    total_word_length = sum(len(word) for word in valid_words)
    total_cells = size_x * size_y

    if total_word_length < total_cells:
        return False, "不能填充谜题，单词总长度小于格子数量"

    empty_puzzle = [[0 for _ in range(size_x)] for _ in range(size_y)]

    corners = [(0, 0), (0, size_y - 1), (size_x - 1, 0),
               (size_x - 1, size_y - 1)]
    for _ in range(timeout):
        x, y = random.choice(corners)
        success, filled_puzzles, answers = await fill_puzzle(copy.deepcopy(empty_puzzle), valid_words, x, y)

        if success:            
            if not is_unwanted_word_present(filled_puzzles[0], combined_words, answers):
                return filled_puzzles[0], answers

    return False, "有限的时间内没有找到合适的谜题"

# 使用字典树遍历整个puzzle，确认不在answer里的单词，不可以在puzzle中找到
def is_unwanted_word_present(puzzle, combined_words, answers):
    class TrieNode:
        def __init__(self):
            self.children = {}
            self.is_end_of_word = False


    class Trie:
        def __init__(self):
            self.root = TrieNode()

        def insert(self, word):
            node = self.root
            for ch in word:
                if ch not in node.children:
                    node.children[ch] = TrieNode()
                node = node.children[ch]
            node.is_end_of_word = True

        def search_from(self, puzzle, x, y, node, visited):
            if node.is_end_of_word:
                return True

            rows, cols = len(puzzle), len(puzzle[0])
            if x < 0 or x >= cols or y < 0 or y >= rows or visited[y][x]:
                return False

            ch = puzzle[y][x]
            if ch not in node.children:
                return False

            visited[y][x] = True
            directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
            for dx, dy in directions:
                new_x, new_y = x + dx, y + dy
                if self.search_from(puzzle, new_x, new_y, node.children[ch], visited):
                    visited[y][x] = False
                    return True

            visited[y][x] = False
            return False
        
    trie = Trie()
    for word in combined_words:
        if word not in answers:
            trie.insert(word)

    rows, cols = len(puzzle), len(puzzle[0])
    visited = [[False for _ in range(cols)] for _ in range(rows)]

    for y in range(rows):
        for x in range(cols):
            if trie.search_from(puzzle, x, y, trie.root, visited):
                return True  # 不合法的单词出现
    return False  # 所有单词都检查完了，返回False表示没有非法的单词出现

async def fill_char(puzzle, start_x, start_y, word_left):
    if puzzle[start_y][start_x] != 0:
        return False, [], [], 0

    tmp_puzzle = copy.deepcopy(puzzle)
    tmp_puzzle[start_y][start_x] = word_left[0]

    print_log(
        f"Trying to fill char at ({start_x}, {start_y}), word_left:{word_left}")

    if len(word_left) == 1:
        if not is_single_connected(tmp_puzzle):
            print_log("is not single connected")
            return False, [], [], 0
        if not validate_connected_graph(tmp_puzzle):
            return False, [], [], 0

    if len(word_left) == 1:
        return True, [tmp_puzzle], [[(start_x, start_y)]], 1

    directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
    surrounding_cells = []

    for dx, dy in directions:
        new_x, new_y = start_x + dx, start_y + dy
        if 0 <= new_x < len(puzzle[0]) and 0 <= new_y < len(puzzle) and tmp_puzzle[new_y][new_x] == 0:
            surrounding_cells.append(
                (new_x, new_y, count_surrounded(tmp_puzzle, new_x, new_y)))

    surrounding_cells.sort(key=lambda x: x[2], reverse=True)
    random.shuffle(surrounding_cells)

    valid_puzzles = []
    valid_paths = []
    max_length = 0

    for new_x, new_y, _ in surrounding_cells:
        success, result_puzzles, paths, length = await fill_char(tmp_puzzle, new_x, new_y, word_left[1:])
        max_length = max(max_length, length)
        if success:
            for p, path in zip(result_puzzles, paths):
                valid_puzzles.append(p)
                valid_paths.append([(start_x, start_y)] + path)

    if valid_puzzles:
        return True, valid_puzzles, valid_paths, len(word_left)
    else:
        print_log("valid_puzzles empty")
        return False, [], [], max_length + 1

# counter=0


async def fill_puzzle(puzzle, words, start_x, start_y):
    if puzzle[start_y][start_x] != 0 or words == []:
        return False, [], {}

    tmp_puzzle = copy.deepcopy(puzzle)

    empty_cells_count = sum(row.count(0) for row in tmp_puzzle)
    possible_words = [word for word in words if len(word) <= empty_cells_count]

    if empty_cells_count <= 6:
        possible_words = [word for word in possible_words if len(
            word) == empty_cells_count]

    random.shuffle(possible_words)

    # 为每种长度的word只留下第一个
    length_to_word = {}
    for word in possible_words:
        if len(word) not in length_to_word:
            length_to_word[len(word)] = word

    possible_words = list(length_to_word.values())

    test_output_puzzle(puzzle)
    print_log(
        f"Trying to fill puzzle from ({start_x}, {start_y}),empty_cell:{empty_cells_count} possibles:{len(possible_words)}")

    # global counter
    # if counter<=0:
    #     user_input = input("请输入一个数字: ")
    #     counter = int(user_input)

    # counter-=1

    while possible_words:
        word = possible_words.pop(0)
        success, result_puzzles, paths, max_fill_length = await fill_char(tmp_puzzle, start_x, start_y, word)

        if not success:
            possible_words = [
                w for w in possible_words if len(w) < max_fill_length]
            continue

        for result_puzzle, path in zip(result_puzzles, paths):
            if not any(cell == 0 for row in result_puzzle for cell in row):
                return True, [result_puzzle], {word: path}

            max_surrounding_cells = find_max_surrounded(result_puzzle)

            print_log(max_surrounding_cells)

            for new_x, new_y in max_surrounding_cells:
                remaining_words = [w for w in words if w != word]
                success, deeper_puzzles, deeper_answers = await fill_puzzle(result_puzzle, remaining_words, new_x, new_y)

                if success:
                    deeper_answers[word] = path
                    return True, deeper_puzzles, deeper_answers

    return False, [], {}

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
    visited = [[False for j in range(len(array[0]))]
               for i in range(len(array))]

    # 搜索函数
    def dfs(i, j):
        if i < 0 or i >= len(array) or j < 0 or j >= len(array[0]):
            return
        if visited[i][j] or array[i][j] != 0:
            return
        visited[i][j] = True
        dfs(i-1, j)
        dfs(i+1, j)
        dfs(i, j-1)
        dfs(i, j+1)

    # 标记是否找到了第一个0
    found_first_zero = False
    for i in range(len(array)):
        for j in range(len(array[0])):
            if array[i][j] == 0 and not visited[i][j]:
                # 如果已经找到了第一个0，那么直接返回False
                if found_first_zero:
                    return False
                dfs(i, j)
                found_first_zero = True

    return True

# 由于Hamiltonian路径是一个NP完全问题，所以这里改为一个更贪婪的算法
# 在单连通的前提下(所以该函数不能单独调用,还得检测单连通)
# 要求该图额外满足下述条件。


def validate_connected_graph(matrix, dead_end_tolarance=0, non_adjacent_walls_tolarance=0):

    def has_non_adjacent_walls(i, j, matrix):
        rows, cols = len(matrix), len(matrix[0])

        # 定义8个方向，从上方开始顺时针
        directions = [(0, 1), (1, 1), (1, 0), (1, -1),
                      (0, -1), (-1, -1), (-1, 0), (-1, 1)]
        walls = [0] * 8  # 初始化8位数组

        # 标记有墙的方向为1
        for idx, (di, dj) in enumerate(directions):
            ni, nj = i + di, j + dj
            if 0 <= ni < rows and 0 <= nj < cols:
                if matrix[ni][nj] != 0:
                    walls[idx] = 1

        # 找到第一个1的位置
        try:
            start_idx = walls.index(1)
        except ValueError:  # 如果没找到1，直接返回False
            return False

        # 向前遍历并修改为2
        idx = (start_idx - 1) % 8
        while walls[idx] == 1:
            walls[idx] = 2
            idx = (idx - 1) % 8

        # 向后遍历并修改为2
        idx = (start_idx + 1) % 8
        while walls[idx] == 1:
            walls[idx] = 2
            idx = (idx + 1) % 8

        walls[start_idx] = 2  # 设置起始点为2

        # 检查数组中是否还存在1
        return 1 in walls

    # 2. 死路条件：
    # 如果一个0只有一个方向是0
    def is_dead_end(i, j, matrix):
        rows, cols = len(matrix), len(matrix[0])

        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        count_zeros = 0

        for di, dj in directions:
            ni, nj = i + di, j + dj
            if 0 <= ni < rows and 0 <= nj < cols and matrix[ni][nj] == 0:
                count_zeros += 1

        return count_zeros == 1

    # 3. 通道条件.
    # 上下都是0，左边是边界或非0，右边是边界或非0，则定义为通道。
    # 左右都是0，上边是边界或非0，下边是边界或非0，则定义为通道。
    # 所有的0都不能是通道
    def is_corridor(i, j, matrix):
        rows, cols = len(matrix), len(matrix[0])

        # 通道：上下都是0，左边是边界或非0，右边是边界或非0
        if (i-1 < 0 or matrix[i-1][j] == 0) and (i+1 >= rows or matrix[i+1][j] == 0):
            if (j-1 < 0 or matrix[i][j-1] != 0) and (j+1 >= cols or matrix[i][j+1] != 0):
                return True

        # 通道：左右都是0，上边是边界或非0，下边是边界或非0
        if (j-1 < 0 or matrix[i][j-1] == 0) and (j+1 >= cols or matrix[i][j+1] == 0):
            if (i-1 < 0 or matrix[i-1][j] != 0) and (i+1 >= rows or matrix[i+1][j] != 0):
                return True

        return False

    dead_end_count = 0
    non_adjacent_walls_count = 0
    for i in range(len(matrix)):
        for j in range(len(matrix[0])):
            if matrix[i][j] == 0:
                if is_dead_end(i, j, matrix):
                    dead_end_count += 1
                    if dead_end_count > dead_end_tolarance:
                        test_output_puzzle(matrix)
                        print_log(f"{i}, {j} is_dead_end")
                        return False
                    else:
                        print_log(f"{i}, {j} is_dead_end")
                else:
                    if is_corridor(i, j, matrix):
                        test_output_puzzle(matrix)
                        print_log(f"{i}, {j} is_corridor")
                        return False

                    if has_non_adjacent_walls(i, j, matrix):
                        non_adjacent_walls_count += 1
                        if non_adjacent_walls_count > non_adjacent_walls_tolarance:
                            test_output_puzzle(matrix)
                            print_log(f"{i}, {j} has_non_adjacent_walls")
                            return False
                        else:
                            print_log(f"{i}, {j} has_non_adjacent_walls")
    return True

# 下面这部分都是测试用代码


def print_log(message):
    # print(message)
    pass


def test_output_puzzle(puzzle):
    for row in puzzle:
        new_row = '['
        for item in row:
            if item == 0:
                new_row += " 0 , "
            else:
                new_row += f"'{str(item) }', "
        new_row = new_row.rstrip(', ')  # 去除最后一个逗号和空格
        new_row += '],'
        print_log(new_row)


async def test_main():

    temp_puzzle = [
        ['b', 'g', 'i', 'k', 'g', 'z', 'x', 'f', 'q', 't'],
        ['m', 'h', 'u', 'm', 'j', 'q', 'x', 'd', 's', 'p'],
        ['f', 'c', 'c', 'm', 'n', 'o', 'p', 's', 'o', 'v'],
        ['p', 'n', 's', 'q', 'o', 'w', 'q', 'r', 'f', 'u'],
        ['c', 'k', 'j', 'r', 'i', 'b', 't', 'v', 'w', 'r'],
        ['a', 'v', 'x',  0,  0,  0, 's', 'z', 'u', 'a'],
        ['x', 'j', 'b',  0,  0,  0, 'g', 't', 'u', 'w'],
        ['r', 'b',  0,  0,  0, 'i', 'v', 'p', 'a', 'o'],
        ['l', 'b',  0,  0,  0, 'k', 'l', 'p', 'i', 'b'],
        ['t', 'k', 's', 'a', 'o', 'u', 'o', 'n', 't', 'q'],
    ]

#     temp_puzzle = [
#     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
#     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
#     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
#     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
#     [0, 0, 0, 0, 5, 0, 0, 0, 0, 0],
#     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
#     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
#     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
#     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
#     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
# ]

    print_log(validate_connected_graph(temp_puzzle))

    # return

    def generate_random_word(min_length=3, max_length=8):
        length = random.randint(min_length, max_length)
        return ''.join(random.choice(string.ascii_lowercase) for _ in range(length))

    words_array = [generate_random_word() for _ in range(100)]

    failed_count = 0
    for i in range(10):
        puzzle, answer = await build_puzzle(10, 10, words_array, 1)

        if not puzzle:
            failed_count += 1
        else:
            test_output_puzzle(puzzle)
            print_log(answer)
            print_log("\n")

    print(f"Failed {failed_count} times out of 10 tests.")

# asyncio.run(test_main())

import random

# lib主函数
# 根据给定的列表随机生成一个Grid
# 生成的时候，避免出现1个空格或者2个空格的情况，因为1个字或者两个字很难找到词语
# 函数返回Tuple，包含Grid和答案，保证答案唯一性
async def build_puzzle(size,words,timeout=10000):

    puzzle = build_grid(size)

    final_puzzle,answers = build_puzzle_rec(puzzle,deep_copy_shuffle(words),[],[0,timeout])

    return final_puzzle,answers

# 根据一个填了一部分的puzzle，构建一个填满的puzzle，按照words的顺序来尝试
def build_puzzle_rec(puzzle,words,answers,pc):

    pc[0] +=1

    if pc[0]%100 ==0 :
        print(pc[0])

    if pc[0] > pc[1]:
        return None,'超过最大性能计数'

    blanks_left = cala_blank_count(puzzle)

    # 对Word进行修剪
    new_words = []
    for w in words:
        if len(w) <= blanks_left:
            new_words.append(w)

    if len(new_words) == 0:
        if blanks_left == 0:
            return puzzle,answers
        return None,'单词用尽'


    word_index = 0
    words = deep_copy_shuffle(new_words)
    for word in words:
        word_index += 1

        new_answers = deep_copy(answers)
        new_answers.append(word)

        candidates = deep_copy_shuffle(try_fill_this_word(puzzle,word))
        
        # 如果candidate里有填好的就返回
        for can in candidates:
            if cala_blank_count(can) == 0:
                return can,new_answers

        # 否则对于每一个candidate，继续尝试用下一个单词表去fill word
        new_words = words[word_index:len(words):]
        # print(new_words)
        for can in candidates:
            
            ret,ans =  build_puzzle_rec(can,new_words,new_answers,pc)
            if pc[0] > pc[1]:
                return None,'超过最大性能计数'
            if ret != None:
                return ret,ans

    return None,'未找到能填满的组合'

# 测试用，输出puzzle
def test_output_puzzle(puzzle):
    for row in puzzle:
        print(row)

# 生成一个打乱顺序的拷贝
# 测试通过
def deep_copy_shuffle(list):
    new_list = []
    for x in list:
        new_list.append(x)
    
    random.shuffle(new_list)
    return new_list

def deep_copy(list):
    new_list = []
    for x in list:
        new_list.append(x)
    
    return new_list

# 生成一个空白的Puzzle list对象
# 测试通过
def build_grid(size):
    puzzle = [] # puzzle[y][x]
    for _ in range(0,size):
        row = []
        for _ in range(0,size):
            row.append('')

        puzzle.append(row)

    return puzzle

# 验证一个单词是否可以放入其中，并输出所有可以放置的版本
# 测试通过
def try_fill_this_word(puzzle,word):
    
    valid_puzzles = []

    blanks = cala_blank_count(puzzle)
    if blanks <=0:
        return None #表示无法放置
    
    # 从第一个空格开始遍历
    for blank_pos in range(0,blanks):
        x,y = get_xth_blank_pos(puzzle,blank_pos)
        new_puzzle = puzzle_deep_copy(puzzle)
        valid_puzzles = valid_puzzles + try_fill_this_word_at(new_puzzle,word,x,y)

    return valid_puzzles

# 验证一个单词是否可以放入指定位置，并输出所有可以放置的版本
# 测试通过
def try_fill_this_word_at(puzzle,word,x,y):
    # 第一个字母一定在y,x
    new_puzzle = puzzle_deep_copy(puzzle)
    new_puzzle[y][x] = word[0] #放入第一个单词
    
    if len(word) == 1:
        return [new_puzzle]

    valid_puzzles = []
    #检查四角
    if y>0:
        # 有 [y-1][x] 存在
        if new_puzzle[y-1][x] == '':
            valid_puzzles = valid_puzzles + try_fill_this_word_at(new_puzzle,word[1:len(word):],x,y-1)
    
    if y<len(puzzle)-1:
        # 有 [y+1][x] 存在
        if new_puzzle[y+1][x] == '':
            valid_puzzles = valid_puzzles + try_fill_this_word_at(new_puzzle,word[1:len(word):],x,y+1)
    
    if x>0:
        # 有 [y][x-1] 存在
        if new_puzzle[y][x-1] == '':
            valid_puzzles = valid_puzzles + try_fill_this_word_at(new_puzzle,word[1:len(word):],x-1,y)
    
    if x<len(puzzle)-1:
        # 有 [y][x+1] 存在
        if new_puzzle[y][x+1] == '':
            valid_puzzles = valid_puzzles + try_fill_this_word_at(new_puzzle,word[1:len(word):],x+1,y)

    return valid_puzzles

# 查找一个puzzle从左上角起先横后竖第X个空位的坐标(X从0起)
# 测试通过
def get_xth_blank_pos(puzzle,xth):
    blank_count = 0
    size = len(puzzle)
    for y in range(0,size):
        for x in range(0,size):
            if puzzle[y][x] == '':
                if blank_count == xth :
                    return x,y
                blank_count += 1
    
    return -1,-1

# 数一下puzzle里还有多少空格
# 测试通过
def cala_blank_count(puzzle):
    blank_count = 0
    size = len(puzzle)
    for y in range(0,size):
        for x in range(0,size):
            if puzzle[y][x] == '':
                blank_count += 1
    
    return blank_count

# 对Puzzle深拷贝
# 测试通过
def puzzle_deep_copy(puzzle):

    new_puzzle = []
    size = len(puzzle)
    for y in range(0,size):
        row = []
        for x in range(0,size):
            row.append(puzzle[y][x])
        new_puzzle.append(row)
    
    return new_puzzle


# 下面这部分是测试代码
def test_main():
    puzzle = build_grid(5)

    results,ans = build_puzzle(5,['Hello','World','Made','Wtf','a','b','c','d','by','China','Fill','How'])

    if results != None:
        test_output_puzzle(results)
        print(ans)

# test_main()
import random
import asyncio
import copy
import string

# lib主函数
# 根据给定的列表随机生成一个Grid
# 函数返回Tuple，包含Grid和答案，保证答案唯一性
# 测试通过


async def build_puzzle_random_distribution_mode(size_x, size_y, words, black_list, timeout):
    
    async def is_valid_word(word, chars_used, words_used):
        """检查词是否与已使用的字符有重复字符或与已用词组合构成新词"""
        combined_words = words + black_list
        for w in combined_words:
            await asyncio.sleep(0)  # Yield control back to the event loop
            if w != word and word in w and set(w).issubset(chars_used):
                return False
            if w != word and w in words_used and word in w:
                return False
            if w != word and w in word:
                return False
        for char in word:
            await asyncio.sleep(0)  # Yield control back to the event loop
            if char in chars_used:
                return False
        return True

    async def contains_blacklisted_word(puzzle, black_list):
        """检查puzzle是否包含black_list中的任何单词"""
        for word in black_list:
            for y in range(size_y):
                for x in range(size_x):
                    horizontal_slice = puzzle[y][x:x+len(word)]
                    vertical_slice = [puzzle[j][x] for j in range(y, min(y+len(word), size_y))]

                    # Check for None in slices and continue if found
                    if None in horizontal_slice or None in vertical_slice:
                        continue
                    
                    if ''.join(horizontal_slice) == word or ''.join(vertical_slice) == word:
                        return True
        return False

    async def insert_word(word, filled_puzzle, chars_used, answers, words_used):
        if sum([1 for row in filled_puzzle for cell in row if cell is None]) < len(word): 
            return False
        positions = []
        temp_filled_puzzle = [row.copy() for row in filled_puzzle]
        temp_chars_used = chars_used.copy()
        for char in word:
            max_attempts = 100
            attempt = 0
            inserted = False
            while attempt < max_attempts:
                await asyncio.sleep(0)  # Yield control back to the event loop
                x = random.randint(0, size_x - 1)
                y = random.randint(0, size_y - 1)
                if temp_filled_puzzle[y][x] is None and char not in temp_chars_used:
                    temp_filled_puzzle[y][x] = char
                    temp_chars_used.add(char)
                    positions.append([x, y]) 
                    inserted = True
                    break
                attempt += 1
            if not inserted:  # 如果该字符没有被插入，放弃整个word
                return False

        # 如果word中的所有字符都已成功插入，检查是否包含黑名单中的单词
        if await contains_blacklisted_word(temp_filled_puzzle, black_list):
            return False

        # 提交更改
        for y in range(size_y):
            for x in range(size_x):
                await asyncio.sleep(0)  # Yield control back to the event loop
                filled_puzzle[y][x] = temp_filled_puzzle[y][x]
        chars_used.update(temp_chars_used)
        answers[word] = positions
        words_used.add(word)
        return True

    filled_puzzle = [[None for _ in range(size_x)] for _ in range(size_y)]
    chars_used = set()
    answers = {}
    words_used = set()

    random.shuffle(words)
    for word in words:
        await asyncio.sleep(0)
        remaining_spaces = sum([1 for row in filled_puzzle for cell in row if cell is None])
        if remaining_spaces == 0:
            break
        if remaining_spaces < 6:
            if len(word) == remaining_spaces:
                if await is_valid_word(word, chars_used, words_used) and await insert_word(word, filled_puzzle, chars_used, answers, words_used):
                    continue
            else:
                continue

        if await is_valid_word(word, chars_used, words_used) and await insert_word(word, filled_puzzle, chars_used, answers, words_used):
            continue

    for y in range(size_y):
        for x in range(size_x):
            await asyncio.sleep(0)
            if filled_puzzle[y][x] is None:
                filled_puzzle[y][x] = '❤'

    return filled_puzzle, answers


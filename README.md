> 玩一个猜技能游戏

    - 说 `兔兔技能方格5x5` 或者 `兔兔技能方格10x10` 或者 任意一个不超过10x10的方形尺寸。
    - 接下来，阿米娅展示一个方格图，里面每一格写了一个字，如下图所示。

![兔兔格子](https://raw.githubusercontent.com/hsyhhssyy/amiyabot-game-hsyhhssyy-skill-schulte-grid/master/example_image/example2.png)

    - 玩家需要在这里面寻找干员的技能名，找到以后，在群内说出干员的名字。
    - 所有的技能名都是连续的，如下图所示，图中包含临光的技能[急救模式]，因此玩家可以回答[临光]：

![临光技能](https://raw.githubusercontent.com/hsyhhssyy/amiyabot-game-hsyhhssyy-skill-schulte-grid/master/example_image/example1.png)

    - 技能名称剔除了很多，包括：
        - 如果一个技能被多个干员持有，则这个技能不会出现在图里。
        - 如果一个技能包含另一个技能，比较长的那个技能就会被剔除。
            - 比如上面那个图里临光的[急救模式]包含了塞雷娅的[急救]。
            - 因此为了保证答案的唯一性，现在版本的谜题中，[急救模式][碎甲击扩散][活力再生广域][安眠旋律][剑雨滂沱]这几个技能不会出现图里。
    - 技能名中的点号“·”，波折号，引号等标点符号均被删除。

    - 答对一个干员+300分，答错一个干员-100分，不会扣到0以下。
    - 5分钟没有完成方格，或者30秒没人说话，或者方格内干员全部被答出，则游戏结束。

> 注意事项

    - 虽然可以说 `兔兔技能方格100x100`，但是说出去电脑铁定卡死，所以目前暂时限制到最大10x10。(平均包含25个干员，够猜了)，

> [项目地址:Github](https://github.com/hsyhhssyy/amiyabot-game-hsyhhssyy-skill-schulte-grid/)

> [遇到问题可以在这里反馈(Github)](https://github.com/hsyhhssyy/amiyabot-game-hsyhhssyy-skill-schulte-grid/issues/new/)

> [如果上面的连接无法打开可以在这里反馈(Gitee)](https://gitee.com/hsyhhssyy/amiyabot-plugin-bug-report/issues/new)

> [Logo作者:Sesern老师](https://space.bilibili.com/305550122)

|  版本   | 变更  |
|  ----  | ----  |
| 1.0  | 初版登录商店 |
| 1.1  | 移除了大量的打印日志 |
| 1.1  | 现在每回答出一题兔兔就会发一张新图把已经用掉的字暗下去 |
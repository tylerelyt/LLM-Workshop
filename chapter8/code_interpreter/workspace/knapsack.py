# filename: knapsack.py
def knapsack(weights, values, capacity):
    n = len(values)
    
    # 创建二维数组 dp 来存储中间结果
    dp = [[0 for _ in range(capacity + 1)] for _ in range(n + 1)]
    
    # 填充 dp 数组
    for i in range(1, n + 1):
        for w in range(1, capacity + 1):
            if weights[i-1] <= w:
                # 可以选择当前物品
                dp[i][w] = max(dp[i-1][w], dp[i-1][w-weights[i-1]] + values[i-1])
            else:
                # 不能选择当前物品
                dp[i][w] = dp[i-1][w]
    
    # 回溯找出选择了哪些物品
    selected_items = []
    w = capacity
    for i in range(n, 0, -1):
        if dp[i][w] != dp[i-1][w]:
            selected_items.append(i-1)  # 物品编号从0开始
            w -= weights[i-1]
    
    return dp[n][capacity], selected_items

# 定义物品的重量和价值
weights = [2, 3, 4, 5, 1]
values = [3, 4, 5, 6, 2]
capacity = 10

# 执行函数
max_value, items = knapsack(weights, values, capacity)

# 输出结果
print(f"最大价值: {max_value}")
print(f"选择的物品编号 (从0开始): {items}")

# 根据编号打印具体物品信息
for index in items:
    print(f"物品{index+1}: 重量{weights[index]}kg, 价值{values[index]}元")
from pulp import LpProblem, LpMinimize, LpVariable, lpSum, LpStatus, LpInteger

# 基础信息
centers = {
    'A': {'coordinate': (50, 50), 'avg_unload_time': 30},
    'B': {'coordinate': (100, 100), 'avg_unload_time': 25}
}
factories = {
    'C': {'coordinate': (0, 0), 'avg_ship_time': 45, 'idle_vehicles': 10},
    'D': {'coordinate': (50, 50), 'avg_ship_time': 45, 'idle_vehicles': 10},
}

vehicle_info = {
    0: {'capacity': 8, 'cost_per_km': 10, 'wait_cost_per_min': 0.5},
}
orders = {
    ('C', 'A'): {'quantity': 3, 'start_time': 0, 'end_time': 4},
    ('D', 'B'): {'quantity': 5, 'start_time': 1, 'end_time': 5}
}
distances = {
    ('C', 'A'): 50,
    ('C', 'B'): 100,
    ('D', 'A'): 75,
    ('D', 'B'): 120
}
vehicle_speed = 60  # 车辆速度，假设为60公里/分钟

# 创建问题
problem = LpProblem("Vehicle Routing Problem", LpMinimize)

# 创建决策变量
routes = LpVariable.dicts("Route", [(f, c, k) for f in factories for c in centers for k in vehicle_info.keys()], 0, 1, LpInteger)
vehicles = LpVariable.dicts("Vehicle", [(f, c, k) for f in factories for c in centers for k in vehicle_info.keys()], 0, 1, LpInteger)
orders_assigned = LpVariable.dicts("OrderAssigned", orders.keys(), 0, None, LpInteger)

# 目标函数
transport_cost = lpSum(routes[(f, c, k)] * vehicle_info[k]['cost_per_km'] * distances[(f, c)] for f in factories for c in centers for k in vehicle_info.keys())
fixed_cost = lpSum(vehicles[(f, c, k)] * vehicle_info[k]['fixed_cost_per_day'] for f in factories for c in centers for k in vehicle_info.keys())
wait_cost = lpSum(vehicles[(f, c, k)] * vehicle_info[k]['wait_cost_per_min'] * factories[f]['idle_vehicles'] for f in factories for c in centers for k in vehicle_info.keys())
problem += transport_cost + fixed_cost + wait_cost

# 约束条件
for f in factories:
    for c in centers:
        for k in vehicle_info.keys():
            problem += routes[(f, c, k)] <= vehicle_info[k]['capacity']

for f in factories:
    for c in centers:
        problem += lpSum(routes[(f, c, k)] for k in vehicle_info.keys()) == 1

for f in factories:
    for c in centers:
        for k in vehicle_info.keys():
            if (f, c) in orders:
                route_time = (distances[(f, c)] / vehicle_speed) + centers[c]['avg_unload_time']
                problem += routes[(f, c, k)] * route_time <= orders[(f, c)]['end_time']
                problem += routes[(f, c, k)] * orders[(f, c)]['quantity'] == orders_assigned[(f, c)]

# 求解问题
problem.solve()

# 输出结果
print("优化状态:", LpStatus[problem.status])

for f in factories:
    for c in centers:
        for k in vehicle_info.keys():
            if routes[(f, c, k)].varValue == 1:
                if (f, c) in orders:
                    print(
                        f"车辆{k}从工厂{f}运输{orders_assigned[(f, c)].varValue}台车到交付中心{c}，关联订单：从工厂{f}到交付中心{c}在限定时间{orders[(f, c)]['end_time']}内运输{orders_assigned[(f, c)].varValue}台车")
                else:
                    print(f"车辆{k}从工厂{f}运输到交付中心{c}，但无关联订单")

print("总成本为:", problem.objective.value())

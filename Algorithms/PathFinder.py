import math
import numpy as np


class FastestPath:
    def __init__(self):
        self.min_cost = 10000
        self.path = []

    def tsp(self, dist, vis, cur, cnt, NumGoals, cost, ans):
        if cnt == NumGoals:
            if cost < self.min_cost:
                self.min_cost = cost
                self.path = ans
                return
        for i in range(NumGoals):
            if vis[i] == False:
                if cost + dist[cur][i] > self.min_cost:
                    continue
                vis[i] = True
                new_ans = np.zeros(NumGoals)
                for k in range(cnt):
                    new_ans[k] = ans[k]
                new_ans[cnt] = i
                self.tsp(dist, vis, i, cnt + 1, NumGoals, cost + dist[cur][i], new_ans)
                vis[i] = False

    def plan_path(self, dist, NumGoals):
        visited = [False for i in range(NumGoals)]
        visited[0] = True
        ans = np.zeros(NumGoals)
        self.tsp(dist, visited, 0, 1, NumGoals, 0, ans)
        return self.path

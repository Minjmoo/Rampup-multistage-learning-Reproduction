import math
import gurobipy as gp
from gurobipy import GRB

#Model parameter (기존 값 + ITT 및 Model 추가)
N=2
STAGES = range (1, N+1)
T=10
PERIODS = range (1, T+1) 
ITT=[(i, tp, t) for i in STAGES for t in PERIODS for tp in range (1, t+1)]

S={1: 50.0, 2: 50.0}
h_raw={1: 3.0, 2: 2.5}
mu_raw={1: 5.0, 2: 5.0}
pmax_i={1: 10.0, 2: 10.0}
delta_i={1: 5.0, 2: 5.0}
tau_i={1: 1.00, 2: 1.00}
alpha=2

h={(i, t): h_raw[i] for i in STAGES for t in PERIODS}
mu={(i, t): mu_raw[i] for i in STAGES for t in PERIODS}


Demand_scenarios = {
    "slow": (5000.0, 50.0, 0.10),
    "medium": (279.0, 2.2, 0.33),
    "fast": (258.0, 3.4, 0.90)
}

def demand (t, scenario):
    a, b, c= Demand_scenarios[scenario]
    return a / (1 + b*math.exp(-c*t))

def g(i, age):
    return pmax_i[i] - delta_i[i] * math.exp(-age / tau_i[i])

r=2.0
BIGM=1000 # 값은 어느정도?

m = gp.Model("rampup") # Gurobi 모델을 정의!

# Decision Variable (변수 정의) (11)~(14)
l= m.addVars(STAGES, PERIODS, lb=0, vtype=GRB.CONTINUOUS, name="l") # 정석
p= m.addVars(STAGES, PERIODS, name="p") # 생략시 비음, 연속 가정, 이름은 디버깅을 위해서 적어놓는 게 좋다!
w= m.addVars(ITT, lb=0, name="w")
z= m.addVars(ITT, lb=0, name="z")
y= m.addVars(STAGES, PERIODS, vtype=GRB.BINARY, name="y")
ya = m.addVars(STAGES, PERIODS, vtype=GRB.BINARY, name="ya")
yw = m.addVars(STAGES, PERIODS, vtype=GRB.BINARY, name="yw")

# Objective Function (변수 정의 후 목적함수 정의)
setup_cost=gp.quicksum(S[i]*y[i, t] for i in STAGES for t in PERIODS)
inv_cost=gp.quicksum(h[i, t]*l[i, t] for i in STAGES for t in PERIODS )
assigning_cost=gp.quicksum(w[i, tp, t] * mu [i, t] for i in STAGES for t in PERIODS for tp in range (1, t+1))
withdraw_cost=gp.quicksum(r*z[i, tp, t+1] for i in STAGES for t in range(1, T) for tp in range (1, t+1))

m.setObjective(setup_cost + inv_cost + assigning_cost + withdraw_cost, GRB.MINIMIZE) # (1)

# Constraints (정의역보고 구분하여 quicksum으로 기입!)
for t in PERIODS: #∀t
    m.addConstr(l[1,t]==gp.quicksum(p[1,tp]-demand(tp, "slow") for tp in range (1,t+1))) # (2)

for t in PERIODS: #∀t
    for i in range (2, N+1): #∀i=2~N
        m.addConstr(l[i, t]==gp.quicksum(p[i, tp]-p[i-1, tp] for tp in range (1, t+1))) # (3)

for t in PERIODS:
    for i in STAGES:
            m.addConstr(p[i,t]==gp.quicksum(w[i, tp, t]*g(i, t-tp+1) for tp in range (1, t+1))) # (4)
            m.addConstr(ya[i, t]+yw[i, t]<=alpha*y[i, t]) # (7)
            m.addConstr(w[i, t, t]<=ya[i, t]*BIGM) # (9)

for i in STAGES:
    for t in range(1, T): # t = 1..T−1
        for tp in range(1, t+1): # tp = 1..t
            m.addConstr(w[i, tp, t]-w[i, tp, t+1]<=y[i, t+1]* BIGM) # (5)
            m.addConstr(w[i, tp, t+1]-w[i, tp, t]<=y[i, t+1]* BIGM) # (6)
            m.addConstr(z[i, tp, t+1]== w[i, tp, t]-w[i, tp, t+1]) # (8)
            m.addConstr(z[i, tp, t+1]<=yw[i,t+1]*BIGM) # (10)

m.optimize()
print("TRC =", m.ObjVal)
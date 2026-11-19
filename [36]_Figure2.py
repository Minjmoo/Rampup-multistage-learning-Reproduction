import math
import gurobipy as gp
from gurobipy import GRB
import matplotlib.pyplot as plt

#Model parameter 기존 값에서 변화하는 값 제거 -> 함수로 묶기
N=3
STAGES = range (1, N+1)
T=10
PERIODS = range (1, T+1) 
ITT=[(i, tp, t) for i in STAGES for t in PERIODS for tp in range (1, t+1)]

S={1: 50.0, 2: 50., 3: 50.0}
mu_raw={1: 5.0, 2: 5.0, 3: 5.0}
pmax_i={1: 10.0, 2: 10.0, 3: 10.0}
delta_i={1: 5.0, 2: 5.0, 3: 5.0}
alpha=2
BIGM=1000 # 값은 어느정도?

mu={(i, t): mu_raw[i] for i in STAGES for t in PERIODS}


Demand_scenarios = {
    "slow": (5000.0, 50.0, 0.10),
    "medium": (279.0, 2.2, 0.33),
    "fast": (258.0, 3.4, 0.90)
}

def demand (t, scenario):
    a, b, c= Demand_scenarios[scenario]
    return a / (1 + b*math.exp(-c*t))

scenario = "slow"
d = {t: demand(t, scenario) for t in PERIODS}

h_S1 = {1: 3.0, 2: 2.5, 3: 2.0} # Scenario 1 -> Figure 2(a)
h_S2 = {1: 2.0, 2: 2.0, 3: 2.0} # Scenario 2 -> Figure 2(b)

def solve(tau, r, h_raw, no_withdraw=False):
    def g(i, age):
        return pmax_i[i] - delta_i[i] * math.exp(-age / tau)
    
    h={(i, t): h_raw[i] for i in STAGES for t in PERIODS}
    m = gp.Model("rampup")
    m.Params.OutputFlag = 0 # 로그 끄기 (1200번 반복하므로)
              
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
        for t in range(1, T):            # t = 1..T−1
            for tp in range(1, t+1):     # tp = 1..t
                m.addConstr(w[i, tp, t]-w[i, tp, t+1]<=y[i, t+1]* BIGM) # (5)
                m.addConstr(w[i, tp, t+1]-w[i, tp, t]<=y[i, t+1]* BIGM) # (6)
                m.addConstr(z[i, tp, t+1]== w[i, tp, t]-w[i, tp, t+1]) # (8)
                m.addConstr(z[i, tp, t+1]<=yw[i,t+1]*BIGM) # (10)
    
    if no_withdraw:
        for key in ITT:
            m.addConstr(z[key] == 0)
 
    m.optimize()
    return m.ObjVal

# 계산
taus = [round(0.01*k, 2) for k in range(1, 151)]     # 0.01, 0.02, ..., 1.50
 
def sweep(h_raw, r_list):
    results = {}
    for r in r_list:
        print(f"  r = {r} 계산 중...")
        results[f"r = {r}"] = [solve(tau, r, h_raw) for tau in taus]
    print("  r = M 계산 중...")
    results["r = M"] = [solve(tau, 0.0, h_raw, no_withdraw=True) for tau in taus]
    return results
 
print("Figure 2(a) 계산 시작")
res_a = sweep(h_S1, [0.0, 0.1, 1.0])
print("Figure 2(b) 계산 시작")
res_b = sweep(h_S2, [0.0, 0.5, 1.0])

# CSV 저장
def save_csv(filename, results):
    with open(filename, "w", encoding="utf-8-sig") as f:
        f.write("tau," + ",".join(results.keys()) + "\n")
        for k, tau in enumerate(taus):
            f.write(f"{tau}," + ",".join(f"{results[key][k]:.2f}" for key in results) + "\n")
 
save_csv("figure2a_results.csv", res_a)
save_csv("figure2b_results.csv", res_b)

# 구현
fig, axes = plt.subplots(2, 1, figsize=(9, 10))
 
for ax, results, title in [(axes[0], res_a, "(a) Scenario 1, slow-growing demand"),
                           (axes[1], res_b, "(b) Scenario 2, slow-growing demand")]:
    for label, trc in results.items():
        ax.plot(taus, trc, marker="o", markersize=3, linewidth=1, label=label)
    ax.set_xlabel("τ")
    ax.set_ylabel("TRC")
    ax.set_title(title)
    ax.legend()
    ax.grid(alpha=0.3)
 
plt.tight_layout()
plt.savefig("figure2.png", dpi=200)
plt.show()
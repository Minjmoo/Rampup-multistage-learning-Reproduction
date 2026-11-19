# Ramp-up Multi-stage Learning — Reproduction

Unofficial Python/Gurobi reproduction of Table 1 and Figure 2 from:

> Kim, T., Glock, C. H., & Emde, S. (2021). Production planning for a ramp-up process in a multi-stage production system with worker learning and growth in demand. *International Journal of Production Research*, 59(19), 6002–6021. https://doi.org/10.1080/00207543.2020.1798034

## Files
| File | Reproduces | Description |
|---|---|---|
| `[36]_Table1.py` | Table 1 | Solves a single instance (N = 2 stages, T = 10, slow demand, r = 2.0) and prints the total relevant cost (TRC). |
| `[36]_Figure2.py` | Figure 2(a), 2(b) | N = 3 stages. Sweeps the learning parameter τ from 0.01 to 1.50 and plots TRC for several withdrawal costs r. |

## Model
Mixed-integer program that minimizes **setup + inventory holding + worker assignment + worker withdrawal cost** (Eq. 1).

- `w[i, t', t]`: workers assigned to stage *i* in period *t'* and still working in period *t*. Tracking each assignment cohort lets the model capture learning.
- `z[i, t', t]`: workers withdrawn
- `y`, `ya`, `yw`: binary setup, assignment-setup and withdrawal-setup variables
- Production rate (learning curve): `g_i(age) = pmax_i − Δp_i · exp(−age / τ)`
- Demand (logistic growth): `d(t) = a / (1 + b · exp(−c·t))`
- Constraint numbers in the code comments, `# (2)` to `# (14)`, follow the paper.

## Parameters
| Code | Paper | Value |
|---|---|---|
| `S` | setup cost | 50 |
| `h_raw` | inventory holding cost | Table 1: (3.0, 2.5) / Fig 2(a): (3.0, 2.5, 2.0) / Fig 2(b): (2.0, 2.0, 2.0) |
| `mu_raw` | worker assignment cost | 5 |
| `pmax_i`, `delta_i` | max production rate, Δp | 10, 5 |
| `tau` | learning rate parameter | Table 1: 1.0 / Figure 2: 0.01–1.50 |
| `alpha` | β (assignment and withdrawal in the same period: 1 = no, 2 = yes) | 2 |
| `r` | withdrawal cost | Fig 2(a): 0, 0.1, 1, M / Fig 2(b): 0, 0.5, 1, M |
| `Demand_scenarios` | (a, b, c) | slow (5000, 50, 0.10), medium (279, 2.2, 0.33), fast (258, 3.4, 0.90) |

`r = M` is implemented by forbidding withdrawal (`z = 0`).

## How to run
```bash
pip install gurobipy matplotlib
python [36]_Table1.py     # prints TRC
python [36]_Figure2.py     # 1,200 MIP solves; may take several minutes
Requires Gurobi. The free size-limited license included with pip install gurobipy is enough for these instance sizes.

Output

- figure2a_results.csv, figure2b_results.csv: TRC for each τ
- figure2.png: reproduced Figure 2

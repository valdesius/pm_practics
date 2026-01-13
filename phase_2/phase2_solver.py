from pyomo.environ import (
    ConcreteModel, Set, Param, Var, Binary, NonNegativeReals,
    Constraint, Objective, maximize, SolverFactory, value
)

members = ["Malyshev_Vladislav", "Kapustin_Maxim", "Ulyanov_Nikolay"]
tasks = ["T1","T2","T3","T4","T5","T6","T7","T8","T9","T10","T11","T12"]

h = {
    "T1": 1.50, "T2": 2.58, "T3": 5.00, "T4": 5.00,
    "T5": 3.50, "T6": 3.50, "T7": 3.08, "T8": 3.50,
    "T9": 4.08, "T10": 3.58, "T11": 2.58, "T12": 1.58,
}

p = {
    ("T1","Malyshev_Vladislav"): 6, ("T1","Kapustin_Maxim"): 7, ("T1","Ulyanov_Nikolay"): 6,
    ("T2","Malyshev_Vladislav"): 6, ("T2","Kapustin_Maxim"): 9, ("T2","Ulyanov_Nikolay"): 5,
    ("T3","Malyshev_Vladislav"): 5, ("T3","Kapustin_Maxim"): 9, ("T3","Ulyanov_Nikolay"): 6,
    ("T4","Malyshev_Vladislav"): 4, ("T4","Kapustin_Maxim"): 9, ("T4","Ulyanov_Nikolay"): 6,
    ("T5","Malyshev_Vladislav"): 9, ("T5","Kapustin_Maxim"): 5, ("T5","Ulyanov_Nikolay"): 7,
    ("T6","Malyshev_Vladislav"): 8, ("T6","Kapustin_Maxim"): 5, ("T6","Ulyanov_Nikolay"): 7,
    ("T7","Malyshev_Vladislav"): 7, ("T7","Kapustin_Maxim"): 6, ("T7","Ulyanov_Nikolay"): 9,
    ("T8","Malyshev_Vladislav"): 9, ("T8","Kapustin_Maxim"): 5, ("T8","Ulyanov_Nikolay"): 8,
    ("T9","Malyshev_Vladislav"): 6, ("T9","Kapustin_Maxim"): 7, ("T9","Ulyanov_Nikolay"): 8,
    ("T10","Malyshev_Vladislav"): 7, ("T10","Kapustin_Maxim"): 8, ("T10","Ulyanov_Nikolay"): 7,
    ("T11","Malyshev_Vladislav"): 4, ("T11","Kapustin_Maxim"): 9, ("T11","Ulyanov_Nikolay"): 6,
    ("T12","Malyshev_Vladislav"): 5, ("T12","Kapustin_Maxim"): 8, ("T12","Ulyanov_Nikolay"): 7,
}

cap = {
    "Malyshev_Vladislav": 15.0,
    "Kapustin_Maxim": 14.0,
    "Ulyanov_Nikolay": 14.0,
}

lambda_balance = 0.6

model = ConcreteModel()
model.T = Set(initialize=tasks)
model.M = Set(initialize=members)

model.h = Param(model.T, initialize=h)
model.cap = Param(model.M, initialize=cap)
model.p = Param(model.T, model.M, initialize=p)

model.x = Var(model.T, model.M, domain=Binary)

model.workload = Var(model.M, domain=NonNegativeReals)

model.dev_pos = Var(model.M, domain=NonNegativeReals)
model.dev_neg = Var(model.M, domain=NonNegativeReals)

total_hours = sum(h[t] for t in tasks)
avg_load = total_hours / len(members)

def one_owner_rule(m, t):
    return sum(m.x[t, mm] for mm in m.M) == 1
model.one_owner = Constraint(model.T, rule=one_owner_rule)

def workload_def_rule(m, mm):
    return m.workload[mm] == sum(m.h[t] * m.x[t, mm] for t in m.T)
model.workload_def = Constraint(model.M, rule=workload_def_rule)

def cap_rule(m, mm):
    return m.workload[mm] <= m.cap[mm]
model.cap_c = Constraint(model.M, rule=cap_rule)

def dev_rule(m, mm):
    return m.workload[mm] - avg_load == m.dev_pos[mm] - m.dev_neg[mm]
model.dev_c = Constraint(model.M, rule=dev_rule)

prefs_sum = sum(model.p[t, mm] * model.x[t, mm] for t in model.T for mm in model.M)
imbalance_sum = sum(model.dev_pos[mm] + model.dev_neg[mm] for mm in model.M)

model.obj = Objective(expr=prefs_sum - lambda_balance * imbalance_sum, sense=maximize)

solver = SolverFactory("highs")
result = solver.solve(model, tee=False)

print("Solver: highs")
print("Objective value:", value(model.obj))
print(f"Total hours: {total_hours:.2f} | Avg load: {avg_load:.2f}")

assignments = {mm: [] for mm in members}
for t in tasks:
    for mm in members:
        if value(model.x[t, mm]) > 0.5:
            assignments[mm].append(t)

print("\nAssignments:")
for mm in members:
    work_mm = value(model.workload[mm])
    dev_mm = value(model.dev_pos[mm]) + value(model.dev_neg[mm])
    pref_mm = sum(p[(t, mm)] for t in assignments[mm])
    print(f"- {mm}: tasks={assignments[mm]} | workload={work_mm:.2f}h | pref_sum={pref_mm} | |workload-avg|={dev_mm:.2f}")

print("\nTask -> Member:")
for t in tasks:
    owner = next(mm for mm in members if value(model.x[t, mm]) > 0.5)
    print(f"  {t} -> {owner}")

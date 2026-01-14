import numpy as np

rng = np.random.default_rng(42)

# ---- модель 1: задачи/неделю
tasks_week_values = np.array([4,5,6,7])
tasks_week_probs  = np.array([0.2,0.35,0.3,0.15])
tasks_week_probs /= tasks_week_probs.sum()

def sim_model1(n_tasks=22):
    remaining = n_tasks
    weeks = 0
    while remaining > 0:
        remaining -= rng.choice(tasks_week_values, p=tasks_week_probs)
        weeks += 1
    return weeks

# ---- модель 2: часы/неделю + треугольные длительности
hours_week_values = np.array([8,10,12,14,16])
hours_week_probs  = np.array([0.1,0.2,0.4,0.2,0.1])
hours_week_probs /= hours_week_probs.sum()

tasks = [
    # (id, O, M, P)
    ("P5-01",1,1.5,2),
    ("P5-02",1.5,2.5,4),
    ("P5-03",2,3.5,5.5),
    ("P5-04",3,5,8),
    ("P5-05",3,5,8),
    ("P5-06",2,3.5,6),
    ("P5-07",3,5,8),
    ("P5-08",1.5,2.5,4),
    ("P5-09",1,2,3.5),
    ("P5-10",2,3,5),
    ("P5-11",2,3,5.5),
    ("P5-12",1.5,2.5,4.5),
    ("P5-13",1.5,2.5,4.5),
    ("P5-14",1,2,3.5),
    ("P5-15",1.5,2.5,4.5),
    ("P5-16",1,2,3),
    ("P5-17",2,3.5,6),
    ("P5-18",1.5,2.5,4.5),
    ("P5-19",1,2,3.5),
    ("P5-20",2,3.5,6),
    ("P5-21",1,1.5,2.5),
    ("P5-22",1,1.5,2.5),
]

def sim_model2():
    total = 0.0
    for _,o,m,p in tasks:
        total += rng.triangular(o, m, p)
    spent = 0.0
    weeks = 0
    while spent < total:
        spent += float(rng.choice(hours_week_values, p=hours_week_probs))
        weeks += 1
    return weeks

N = 30000
w1 = np.fromiter((sim_model1() for _ in range(N)), dtype=int, count=N)
w2 = np.fromiter((sim_model2() for _ in range(N)), dtype=int, count=N)

print("Model1 mean:", w1.mean(), "P80:", np.quantile(w1, 0.8), "min/max:", w1.min(), w1.max())
print("Model2 mean:", w2.mean(), "P80:", np.quantile(w2, 0.8), "min/max:", w2.min(), w2.max())
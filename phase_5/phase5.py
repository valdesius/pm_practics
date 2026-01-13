from random import choice
from copy import copy
from typing import Tuple, Callable, List


def successors_by_predecessors(predecessors: List[List[int]]) -> List[List[int]]:
    size = len(predecessors)
    return [[succ for succ in range(size) if i in predecessors[succ]] for i in range(size)]


def calculate_critical_times(
    duration: List[int],
    predecessors: List[List[int]],
    successors: List[List[int]] = None
) -> Tuple[List[int], List[int]]:
    if successors is None:
        successors = successors_by_predecessors(predecessors)

    if len(duration) != len(predecessors) or len(predecessors) != len(successors):
        raise ValueError("Invalid data sizes")

    earliest_start = [0 for _ in duration]
    latest_finish = [0 for _ in duration]

    def _calc_earliest_start(index: int) -> int:
        if index:
            earliest_start[index] = max(
                _calc_earliest_start(pred) + duration[pred] for pred in predecessors[index]
            )
        return earliest_start[index]

    def _calc_latest_finish(index: int) -> int:
        if index == len(successors) - 1:
            latest_finish[index] = earliest_start[index]
        else:
            latest_finish[index] = min(
                _calc_latest_finish(succ) - duration[succ] for succ in successors[index]
            )
        return latest_finish[index]

    _calc_earliest_start(len(predecessors) - 1)
    _calc_latest_finish(0)

    return earliest_start, latest_finish


class TimeCapacityNode:
    def __init__(self, time: int, capacity: List[int]):
        self.time = time
        self.capacity = capacity
        self.next = None
        self.prev = None

    def insert_after(self, time: int) -> "TimeCapacityNode":
        if time <= self.time:
            raise ValueError("Invalid time to insert")
        new_node = TimeCapacityNode(time, copy(self.capacity))
        new_node.prev = self
        new_node.next = self.next
        if self.next:
            self.next.prev = new_node
        self.next = new_node
        return new_node

    def find_first(self, time: int) -> "TimeCapacityNode":
        node = self
        while node.time < time:
            if node.next:
                node = node.next
            else:
                return node
        return node.prev

    def enough_resources(self, demand: List[int]) -> bool:
        return all(self.capacity[i] >= demand[i] for i in range(len(self.capacity)))

    def consume(self, demand: List[int]) -> None:
        for i in range(len(self.capacity)):
            self.capacity[i] -= demand[i]


class ActivityListDecoder:
    def decode(
        self,
        activity_list: List[int],
        duration: List[int],
        predecessors: List[List[int]],
        renewable_demands: List[List[int]],
        renewable_capacity: List[int],
    ) -> List[int]:
        count = len(activity_list)
        root_node = TimeCapacityNode(0, copy(renewable_capacity))
        starts = [0] * count
        finish_nodes = [None] * count
        finish_nodes[0] = root_node  # первая работа (T0) стартует из корня

        for i in activity_list:
            # не раньше последнего предшественника
            start_node = root_node
            for pred in predecessors[i]:
                if not finish_nodes[pred]:
                    raise ValueError("Invalid activity list (precedence broken)")
                if finish_nodes[pred].time > start_node.time:
                    start_node = finish_nodes[pred]

            start_node, last_node, finish_node, finish_time = self._find_position(
                start_node, duration[i], renewable_demands[i]
            )
            starts[i] = start_node.time

            if not finish_node or finish_node.time != finish_time:
                finish_node = last_node.insert_after(finish_time)

            finish_nodes[i] = finish_node
            self._consume(start_node, finish_node, renewable_demands[i])

        return starts

    def _consume(self, start_node: TimeCapacityNode, finish_node: TimeCapacityNode, demand: List[int]) -> None:
        node = start_node
        while node != finish_node:
            node.consume(demand)
            node = node.next

    def _find_position(
        self,
        start_node: TimeCapacityNode,
        duration: int,
        demand: List[int],
    ) -> Tuple[TimeCapacityNode, TimeCapacityNode, TimeCapacityNode, int]:
        if duration == 0:
            return start_node, start_node, start_node, start_node.time

        finish_time = start_node.time + duration
        t = start_node.find_first(finish_time)
        last_node = t
        t_test = start_node

        while t != t_test.prev:
            if t.enough_resources(demand):
                t = t.prev
            else:
                start_node = t.next
                finish_time = start_node.time + duration
                if last_node.next:
                    t_test = last_node.next
                    last_node = t_test.find_first(finish_time)
                    t = last_node
                else:
                    break

        return start_node, last_node, last_node.next, finish_time


class ActivityListSampler:
    def __init__(self, predecessors: List[List[int]], successors: List[List[int]] = None) -> None:
        self.predecessors = predecessors
        self.size = len(predecessors)
        self.successors = successors or successors_by_predecessors(predecessors)

    def _generate(self, func: Callable = None) -> List[int]:
        result = []
        remain_predecessors = [set(pred) for pred in self.predecessors]
        ready_set = [i for i in range(self.size) if not self.predecessors[i]]

        for _ in range(self.size):
            if not ready_set:
                raise ValueError("Incorrect project network (cycle?)")

            next_activity = func(ready_set) if func else choice(ready_set)
            ready_set.remove(next_activity)
            result.append(next_activity)

            for succ in self.successors[next_activity]:
                remain_predecessors[succ].remove(next_activity)
                if not remain_predecessors[succ]:
                    ready_set.append(succ)

        return result

    def generate_by_max_rule(self, rule: Callable) -> List[int]:
        return self._generate(lambda data: max(data, key=rule))

    def generate_by_min_rule(self, rule: Callable) -> List[int]:
        return self._generate(lambda data: min(data, key=rule))

    def generate_random(self) -> List[int]:
        return self._generate()


task_names = [
    "Исследование и проектирование архитектуры",           # T0
    "Настройка инфраструктуры и CI/CD",                    # T1
    "Проектирование БД + миграции",                        # T2
    "Telegram bot skeleton + роутинг",                     # T3
    "UC1 Онбординг и меню",                                # T4
    "ISBN валидация + парсер ввода",                       # T5
    "Провайдеры метаданных (HTTP/парсинг) базовые",        # T6
    "UC2 Добавить по ISBN (текст)",                        # T7
    "Карточка книги (UC5) + действия",                     # T8
    "Список библиотеки + фильтры/пагинация (UC7)",         # T9
    "Поиск (UC6)",                                         # T10
    "Дубликаты/похожие (ISBN + fuzzy)",                    # T11
    "UC4 Ручное добавление",                               # T12
    "Редактирование (UC8)",                                # T13
    "Удаление (UC9) + soft delete",                        # T14
    "Статусы чтения (UC10)",                               # T15
    "Drafts: приём фото + хранение (UC3 часть)",           # T16
    "OCR/распознавание ISBN (UC3)",                        # T17
    "UC3 Добавить по фото (интеграция)",                   # T18
    "Рекомендации (UC11) эвристика",                       # T19
    "Экспорт CSV/JSON (UC12)",                             # T20
    "Тестирование, багфикс, релиз и демо",                 # T21
]

duration = [4, 3, 4, 4, 2, 2, 5, 4, 3, 4, 3, 3, 3, 3, 2, 2, 3, 5, 4, 3, 2, 6]

renewable_demands = [
    [6, 2, 2],  # T0
    [2, 0, 6],  # T1
    [6, 0, 2],  # T2
    [8, 0, 0],  # T3
    [6, 0, 2],  # T4
    [6, 0, 2],  # T5
    [0, 8, 0],  # T6
    [6, 2, 0],  # T7
    [6, 0, 2],  # T8
    [6, 0, 2],  # T9
    [6, 0, 2],  # T10
    [6, 0, 2],  # T11
    [6, 2, 0],  # T12
    [6, 0, 2],  # T13
    [6, 0, 2],  # T14
    [6, 0, 2],  # T15
    [6, 0, 2],  # T16
    [0, 8, 0],  # T17
    [6, 2, 0],  # T18
    [6, 0, 2],  # T19
    [6, 0, 2],  # T20
    [4, 0, 8],  # T21
]

renewable_capacity = [8, 8, 8]

predecessors = [
    [],                # T0
    [0],               # T1
    [0],               # T2
    [0, 1],            # T3
    [3, 2],            # T4
    [3],               # T5
    [0, 1],            # T6
    [4, 5, 6],         # T7
    [7, 2],            # T8
    [8],               # T9
    [8],               # T10
    [2],               # T11
    [4, 11],           # T12
    [8],               # T13
    [8],               # T14
    [8],               # T15
    [3, 2],            # T16
    [16],              # T17
    [7, 17, 11],       # T18
    [9, 10],           # T19
    [9],               # T20
    [12, 13, 14, 15, 18, 19, 20],  # T21
]


successors = successors_by_predecessors(predecessors)
earliest_start, latest_finish = calculate_critical_times(duration, predecessors, successors)

total_float = [latest_finish[i] - earliest_start[i] - duration[i] for i in range(len(duration))]

free_float = []
for i in range(len(duration)):
    if successors[i]:
        free_float.append(min(earliest_start[succ] for succ in successors[i]) - earliest_start[i] - duration[i])
    else:
        free_float.append(0)


def rule_slk(i):   return total_float[i]                            # min
def rule_free(i):  return free_float[i]                             # min
def rule_lst(i):   return latest_finish[i] - duration[i]            # min
def rule_lft(i):   return latest_finish[i]                          # min
def rule_grpw(i):  return duration[i] + sum(duration[s] for s in successors[i])  # max
def rule_lpt(i):   return duration[i]                               # max
def rule_mis(i):   return len(successors[i])                        # max
def rule_grd(i):   return duration[i] * sum(renewable_demands[i])   # max
def rule_grwc(i):  return sum(renewable_demands[i])                 # max
def rule_gcrwc(i): return sum(renewable_demands[i]) + sum(sum(renewable_demands[s]) for s in successors[i])  # max
def rule_rot(i):
    if duration[i] == 0:
        return 0
    ratio = sum(renewable_demands[i][r] / renewable_capacity[r] for r in range(len(renewable_capacity)))
    return ratio / duration[i]                                      # max


heuristics = [
    ("SLK",   rule_slk,   "min"),
    ("FREE",  rule_free,  "min"),
    ("LST",   rule_lst,   "min"),
    ("LFT",   rule_lft,   "min"),
    ("GRPW",  rule_grpw,  "max"),
    ("LPT",   rule_lpt,   "max"),
    ("MIS",   rule_mis,   "max"),
    ("GRD",   rule_grd,   "max"),
    ("GRWC",  rule_grwc,  "max"),
    ("GCRWC", rule_gcrwc, "max"),
    ("ROT",   rule_rot,   "max"),
]


sampler = ActivityListSampler(predecessors, successors)
decoder = ActivityListDecoder()

best_starts = None
best_list = None
best_makespan = float("inf")
best_heuristic = ""

print("Расчёт расписания с различными эвристиками:\n")

for name, rule_func, rule_type in heuristics:
    if rule_type == "min":
        activity_list = sampler.generate_by_min_rule(lambda x: rule_func(x))
    else:
        activity_list = sampler.generate_by_max_rule(lambda x: rule_func(x))

    starts = decoder.decode(activity_list, duration, predecessors, renewable_demands, renewable_capacity)
    makespan = max(starts[i] + duration[i] for i in range(len(duration)))

    print(f"Эвристика {name:6s}: срок = {makespan:3d} рабочих дней")

    if makespan < best_makespan:
        best_makespan = makespan
        best_starts = starts
        best_list = activity_list
        best_heuristic = name

print("\n--------------------------------------------")
print("ЛУЧШЕЕ РЕШЕНИЕ")
print("--------------------------------------------")
print("Лучшая эвристика:", best_heuristic)
print("Makespan (рабочие дни):", best_makespan)
print(f"Недели (5 дн/нед): {best_makespan/5:.1f}")
print(f"Месяцы (~22 дн/мес): {best_makespan/22:.1f}")
print(f"Примерно: {best_makespan//5} недель + {best_makespan%5} дней")


schedule_data = []
for i in range(len(duration)):
    schedule_data.append({
        "id": f"T{i}",
        "task": task_names[i],
        "start": best_starts[i],
        "end": best_starts[i] + duration[i],
        "duration": duration[i],
    })

schedule_data.sort(key=lambda x: x["start"])

print("\nДетальное расписание (отсортировано по старту):")
print(f"{'ID':<4} {'Задача':<45} {'Start':<6} {'End':<6} {'Dur'}")
print("-" * 80)
for row in schedule_data:
    print(f"{row['id']:<4} {row['task'][:45]:<45} {row['start']:<6} {row['end']:<6} {row['duration']}")

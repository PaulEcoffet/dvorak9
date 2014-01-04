import string
import random
import copy
import unicodedata
import multiprocessing
import sys


def remove_accents(input_str):
    nkfd_form = unicodedata.normalize('NFKD', input_str)
    only_ascii = nkfd_form.encode('ASCII', 'ignore')
    return str(only_ascii)


def create_keyboard():
    letters = {}
    i = 0
    j = 0
    for letter in string.ascii_lowercase:
        letters[letter] = (i, j)
        if i == 5 or i == 7:
            j = (j + 1) % 4
        else:
            j = (j + 1) % 3
        if j == 0:
            i += 1
    return letters


def swapkeys(keyboard):
    k = copy.copy(keyboard)
    l1 = random.choice(list(k.keys()))
    l2 = random.choice(list(k.keys()))
    k[l1], k[l2] = k[l2], k[l1]
    return k


def get_score(keyboard, text):
    score = 0
    old_key = None
    for letter in text:
        if letter in string.ascii_lowercase:
            key, pos = keyboard[letter]
            if key == old_key:
                score += 2
            score += pos
            old_key = key
    return score


def print_nice(k):
    k = copy.copy(k)
    keys = [[" " for x in range(4)] for dummy in range(9)]
    while k:
        key, value = k.popitem()
        keys[value[0]+1][value[1]] = key
    for i in range(3):
        print("+------" * 3 + "+")
        for j in range(3):
            print("| {} ".format("".join(keys[j + i * 3]).upper()), end="")
        print("|")
    print("+------" * 3 + "+")

def run_experiment(id_, text, n):
    same = False
    keyboard = create_keyboard()
    cur_best_score = float("+inf")
    cur_best_keyboard = copy.copy(keyboard)
    best_score = float("+inf")
    best_keyboard = copy.copy(keyboard)
    for i in range(1, n+1):
        if same < 1000:
            keyboard = cur_best_keyboard
        else:
            keyboard = create_keyboard()
            cur_best_score = float("+inf")
            cur_best_keyboard = copy.copy(keyboard)
            same = 0
        print(("{}: {:>4.0%} ({:>" + str(len("{:,}".format(n))) + ",} / {:,}), same: {:<4} best: {:<6} curbest: {:<6}").format(id_, i/n, i, n, same, best_score, cur_best_score), end="\r")
        keyboard = swapkeys(keyboard)
        score = get_score(keyboard, text)
        if score < cur_best_score:
            cur_best_keyboard = copy.copy(keyboard)
            cur_best_score = score
            same = 0
            if cur_best_score < best_score:
                best_score = cur_best_score
                best_keyboard = copy.copy(cur_best_keyboard)
        else:
            same += 1
    return best_keyboard


def main():
    with open("data.txt") as f:
        text = remove_accents(f.read())
    text = text.lower()
    n = int(sys.argv[1]) // multiprocessing.cpu_count()
    pool = multiprocessing.Pool(multiprocessing.cpu_count())
    results = []
    future_results = [pool.apply_async(run_experiment, (i, text, n))
               for i in range(multiprocessing.cpu_count())]
    for fresult in future_results:
        result = fresult.get()
        results.append(result)
    print()
    print_nice((sorted(results, key=lambda x: get_score(x, text)))[0])
    print(get_score((sorted(results, key=lambda x: get_score(x, text)))[0], text))
    print(list(map(lambda x: get_score(x, text), results)))


if __name__ == "__main__":
    main()
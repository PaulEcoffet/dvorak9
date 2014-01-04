import string
import random
import copy
import unicodedata


def remove_accents(input_str):
    nkfd_form = unicodedata.normalize('NFKD', input_str)
    only_ascii = nkfd_form.encode('ASCII', 'ignore')
    return str(only_ascii)


with open("data.txt") as f:
    text = remove_accents(f.read())
text = text.lower()


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


def get_score(keyboard):
    global text
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

def main():
    n = 1000000
    same = False
    keyboard = create_keyboard()
    cur_best_score = float("+inf")
    cur_best_keyboard = copy.copy(keyboard)
    best_score = float("+inf")
    best_keyboard = copy.copy(keyboard)
    try:
        for i in range(n):
            if same < 1000:
                keyboard = cur_best_keyboard
            else:
                keyboard = create_keyboard()
                cur_best_score = float("+inf")
                cur_best_keyboard = copy.copy(keyboard)
                same = 0
            print(("{:>4.0%} ({:>" + str(len("{:,}".format(n))) + ",} / {:,}), same: {:<4} best: {:<6} curbest: {:<6}").format(i/n, i, n, same, best_score, cur_best_score), end="\r")
            keyboard = swapkeys(keyboard)
            score = get_score(keyboard)
            if score < cur_best_score:
                cur_best_keyboard = copy.copy(keyboard)
                cur_best_score = score
                same = 0
                if cur_best_score < best_score:
                    best_score = cur_best_score
                    best_keyboard = copy.copy(cur_best_keyboard)
            else:
                same += 1
    except KeyboardInterrupt:
        print()
        print("Interruption")
    print()
    print_nice(best_keyboard)
    print(best_score)


if __name__ == "__main__":
    main()
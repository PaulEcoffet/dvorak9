#!/usr/bin/python3

import string
import random
import copy
import unicodedata
import multiprocessing
import queue
import time
import argparse
import os
import os.path
from collections import OrderedDict

global CURSES
try:
    import curses
except ImportError:
    pass
else:
    CURSES = True

SAMELIMIT = 1796  # P(X = better_key) > 0.95 (if there is one)
                  # see explanation in README.md

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


def keylist(k):
    keys = [[" " for i in range(3)] for j in range(8)]
    keys[5].append(" ")
    keys[7].append(" ")
    for letter, pos in k.items():
        keys[pos[0]][pos[1]] = letter
    return keys


def human(k):
    output = ""
    keys = keylist(k)
    keys = [" "] + keys
    for i, key in enumerate(keys):
        keys[i] = "".join(key).upper().center(6)
    for i in range(3):
        output += "+------" * 3 + "+\n"
        output += "|" + "|".join(keys[i * 3:i * 3 + 3]) + "|\n"
    output += "+------" * 3 + "+"
    return output


def run_experiment(id_, q, text, n):
    same = False
    last_refresh_date = time.time()
    keyboard = create_keyboard()
    cur_best_score = float("+inf")
    cur_best_keyboard = copy.copy(keyboard)
    best_score = float("+inf")
    best_keyboard = copy.copy(keyboard)
    for i in range(1, n + 1):
        if same <= SAMELIMIT:
            keyboard = cur_best_keyboard
        else:
            keyboard = create_keyboard()
            cur_best_score = float("+inf")
            cur_best_keyboard = copy.copy(keyboard)
            same = 0
        if time.time() > last_refresh_date + 0.5:
            q.put({"id": id_, "i": i, "n": n, "same": same,
                   "best_score": best_score, "cur_best_score": cur_best_score,
                   "best_keyboard": best_keyboard,
                   "cur_best_keyboard": cur_best_keyboard})
            last_refresh_date = time.time()
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
    q.put({"id": id_, "i": i, "n": n, "same": same,
           "best_score": best_score, "cur_best_score": cur_best_score,
           "best_keyboard": best_keyboard,
           "cur_best_keyboard": cur_best_keyboard, "last": True})


class QuietUI(object):
    """
    Abstract interface for the graphical interface
    """
    def __init__(self, nb_proc):
        pass

    def start(self):
        pass

    def exit(self):
        pass

    def update_thread(self, data):
        pass

    def update_keyboard(self, *data):
        pass

    def show_results(self, results):
        pass


class DefaultUI(QuietUI):
    """
    Abstract interface for the graphical interface
    """
    def __init__(self, nb_proc):
        pass

    def start(self):
        pass

    def exit(self):
        print()

    def update_thread(self, data):
        string = ("{}: {:>4.0%} ({:>" + str(len("{:,}".format(data["n"])))
                  + ",} / {:,}), same: {:<4} best: {:<6}"
                  "curbest: {:<6}").format(data["id"],
                                           data["i"] / data["n"],
                                           data["i"],
                                           data["n"],
                                           data["same"],
                                           data["best_score"],
                                           data["cur_best_score"])
        print(string, end="\r")  # noqa

    def update_keyboard(self, *data):
        pass


class CursesUI(QuietUI):

    def __init__(self, nb_proc):
        self.stdscr = None
        self.threadwindow = None
        self.keyboardwindows = OrderedDict([("verybest", None), ("best", None),
                                           ("curbest", None)])
        self.titlewindow = None
        self.bestkeyboardwindow = None
        self.nb_proc = nb_proc
        self.selected_thread = 0
        self.keyboards = [{"best": {"keyboard": create_keyboard(),
                                    "score": float("+inf")},
                           "curbest": {"keyboard": create_keyboard(),
                                       "score": float("+inf")}
                           } for i in range(nb_proc)]

    def start(self):
        self.stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        self.stdscr.keypad(True)
        self.stdscr.clear()
        self.stdscr.nodelay(True)
        curses.curs_set(False)
        self.stdscr.leaveok(False)
        curses.setsyx(*self.stdscr.getmaxyx())
        self.threadwindow = curses.newwin(self.nb_proc + 2, 70, 0, 3)
        self.threadwindow.border()
        self.threadwindow.refresh()
        self.titlewindow = curses.newwin(3, 52, self.nb_proc + 3, 28)
        self.titlewindow.border()
        self.update_titlewindow()
        self.titlewindow.refresh()
        self.threadwindow.border()
        for i, key in enumerate(self.keyboardwindows):
            self.keyboardwindows[key] = curses.newwin(
                12, 26, self.nb_proc + 5, i * 26 + 2)
            self.keyboardwindows[key].border()
            self.keyboardwindows[key].addstr(1, 1, key.title().center(24),
                                             curses.A_BOLD)
            self.keyboardwindows[key].refresh()

    def exit(self):
        curses.nocbreak()
        self.stdscr.keypad(False)
        curses.echo()
        curses.curs_set(True)
        curses.endwin()

    def update(self, data):
        try:
            c = self.stdscr.getkey()
        except curses.error:
            pass
        else:
            if c == "KEY_UP":
                self.selected_thread = (self.selected_thread - 1) % self.nb_proc
            elif c == "KEY_DOWN":
                self.selected_thread = (self.selected_thread + 1) % self.nb_proc
        string = ("{}: {:>4.0%} ({:>" + str(len("{:,}".format(data["n"])))
                  + ",} / {:,}), same: {:<4} best: {:<6}"
                  "curbest: {:<6}").format(data["id"],
                                           data["i"] / data["n"],
                                           data["i"],
                                           data["n"],
                                           data["same"],
                                           data["best_score"],
                                           data["cur_best_score"])
        self.threadwindow.addstr(data["id"] + 1, 2, string)
        self.threadwindow.refresh()
        self.keyboards[data["id"]] = {
            "best": {"score": data["best_score"],
                     "keyboard": data["best_keyboard"]},
            "curbest":  {"score": data["cur_best_score"],
                         "keyboard": data["cur_best_keyboard"]}}
        self.update_titlewindow()
        self.update_keyboards()

    def update_keyboards(self):
        self.update_keyboard(self.keyboardwindows["best"],
                             self.keyboards[self.selected_thread]["best"])
        self.update_keyboard(self.keyboardwindows["curbest"],
                             self.keyboards[self.selected_thread]["curbest"])
        self.update_keyboard(
            self.keyboardwindows["verybest"],
            min([keyboard["best"] for keyboard in self.keyboards if keyboard],
                key=lambda x: x["score"]))

    def update_keyboard(self, window, keyboard):
        output = human(keyboard["keyboard"])
        score = ("Score: " + str(keyboard["score"])).center(24)
        for i, line in enumerate(output.splitlines()):
            window.addstr(2 + i, 2, line)
        window.border()
        window.addstr(window.getmaxyx()[0] - 2, 1, score, curses.A_BOLD)
        window.refresh()

    def update_titlewindow(self):
        self.titlewindow.border()
        self.titlewindow.addstr(1, 1,
                                "State of process {}:".format(
                                    self.selected_thread).center(50),
                                curses.A_BOLD)
        self.titlewindow.refresh()


def create_parser():
    parser = argparse.ArgumentParser(
        description="Generates 9keys dvorak keyboard for handset, computing it"
                    " depending of the 'data.txt'")
    style = parser.add_mutually_exclusive_group()
    style.add_argument("-f", "--fancy", help="activate fancy display",
                       action="store_true")
    style.add_argument("-q", "--quiet", help="only the best generated "
                       "keyboard is printed", action="store_true")
    parser.add_argument("tries", help="The number of total tries to compute",
                        type=int)
    parser.add_argument("-o", "--output",
                        help="""
                            the path of a file where to output
                            the keyboards generated, if not provided,
                            then `stdout` is used
                        """)
    format_ = parser.add_mutually_exclusive_group()
    format_.add_argument("-u", "--human",
                         help="Print the generated keyboards in"
                         "a readable way, equivalent to `-t human`."
                         " It's the default state", dest="format_",
                         action="store_const", const="human")
    format_.add_argument("-k", "--keylist",
                         help="""Print the generated keyboards as
                         a list of keys containing a char list.
                         ex: [["a", "b", "c"], ["d", "e" "f"], ...]
                         """, dest="format_",
                         action="store_const", const="keylist")
    format_.add_argument("-d", "--abcdict",
                         help="""Print the generated keyboards as
                         a dict of each letter with its position.
                         ex: {"a": (1, 1), "b": (3, 2), ...}
                         """, dest="format_",
                         action="store_const", const="abcdict")
    format_.add_argument("-t", "--type", choices=["abcdict", "human",
                                                  "keylist"],
                         dest="format_",
                         help="""
                            Choose the format of the output.
                            See -u, -d, -k for more information
                            """)
    format_.set_defaults(format_="human")
    return parser


def main():
    parser = create_parser()
    args = parser.parse_args()
    with open("data.txt") as f:
        text = remove_accents(f.read())
    text = text.lower()
    q = multiprocessing.Queue()
    n = int(args.tries) // multiprocessing.cpu_count()
    processes = [multiprocessing.Process(target=run_experiment,
                                         args=(i, q, text, n))
                 for i in range(multiprocessing.cpu_count())]
    results = [{"score": float("+inf"), "keyboard": None} for x in processes]
    format_actions = {"human": human, "keylist": keylist,
                      "abcdict": lambda x: x}
    for process in processes:
        process.start()
    if CURSES and args.fancy:
        ui = CursesUI(len(processes))
    elif args.quiet:
        ui = QuietUI(len(processes))
    else:
        if args.fancy:
            print("Curses is not available thus fancy output is not working,",
                  "switching to default output")
        ui = DefaultUI(len(processes))
    ui.start()
    try:
        while [process for process in processes if process.is_alive()]:
            try:
                data = q.get(True, 0.5)
            except queue.Empty:
                pass
            else:
                ui.update(data)
                if "last" in data:
                    results[data["id"]]["score"] = data["best_score"]
                    results[data["id"]]["keyboard"] = data["best_keyboard"]
        ui.show_results(results)
    except Exception as e:
        ui.exit()
        raise e
    else:
        ui.exit()
    if args.output:
        if os.path.exists(args.output):
            now = time.ctime()
            move_path = args.output + "." + now + ".bak"
            os.rename(args.output, move_path)
            print(args.output, "already exists, it has been moved as",
                  move_path)
        output = open(args.output, "w")
    else:
        output = None
    print(format_actions[args.format_](
        min(results, key=lambda x: x["score"])["keyboard"]),
        file=output)
    if output:
        output.close()


if __name__ == "__main__":
    main()

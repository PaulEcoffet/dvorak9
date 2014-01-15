dvorak9
=======

dvorak layout generator for 9 keys phones.

data.txt
--------
Default data.txt is a piece written by Alfred de Musset called *On ne badine
pas avec l'amour*. It has been extracted from [wikisource](http://fr.wikisource.org/wiki/On_ne_badine_pas_avec_l%E2%80%99amour).

explanation of SAMELIMIT
------------------------

Let's suppose that there is only one swap that improve the keyboard. There is
25\*25 possible swaps. If we want that this swap has a probability of at least
0.95 to be made once, then we have to compute 1,871 swaps.
Indeed, we want, X being the good swap :

P(X > 0) > 0.95

X ~ B(n, 1/625), thus
1 - P(X = 0) ≥ 0.95
P(X = 0) ≤ 0.05
(624/625)^n ≤ 0.05
n ln(624/625) ≤ ln 0.05
n ≥ (ln 0.05)/ln(624/625)
n ≥ 1870.9

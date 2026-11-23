cp /proc/{PID}/exe stage3

We can first try with a test password just following the rules to go until the useful conditions.
Password: A1B1-0,A1B2-0,A1B3-0,A2B3-0
Then check all the values by just understanding that the columns and lines results are just an array and as such are just written next to each other (easily seen when checking the first condition)

initial :
B= columns
A= lines
(by trial and error)
? | ? | ? = 50 
? | ? | ? = 50
? | ? | ? = 50
70| 30| 50
We get this values, the ? are still to be found.

Now we need to solve this to find the optimal solution:
And for this we also need the costs that are there to compute the score.
for this we're gonna make a naive proposition to start with and have a first score 
50 | 0  | 0
20 | 30 | 0
0  | 0  | 50

so A1B1-50,A2B1-20,A2B2-30,A3B3-50

Doing some debugging we get that those are the costs :
[stack]:00007FFFFFFFDE78 dd 7, 0Ah, 1Bh
[stack]:00007FFFFFFFDE84 dd 7, 11h, 3
[stack]:00007FFFFFFFDE90 dd 0Dh, 19h, 19h


7  | 10 | 27
7  | 17 | 3
13 | 25 | 25

those values are situated just after the columns and lines results array

With our naive solution we don't find the right solution.

we're told that to open the value must be minimal. And we also mention a plan linking to a transportation problem.
here I'll let you check a video like this one for an algorithm for it because I'm not motivated enough to write a script for it
But know that we'll use stepping stone method (for example with https://github.com/dimartinot/optimisation/blob/master/BalasHammer/transport.py)

❯ python transport.py
[[7, 10, inf], [7, 17, inf], [13, 25, inf]]
[[7, 10, inf], [7, 17, inf], [inf, inf, inf]]
[[7, inf, inf], [7, inf, inf], [inf, inf, inf]]
[[inf, inf, inf], [7, inf, inf], [inf, inf, inf]]
[[inf, inf, inf], [inf, inf, inf], [inf, inf, inf]]
Result matrix :
[[20 30  0]
 [ 0  0 50]
 [50  0  0]]
Total cost :  1240

As such we have :
A1B1-20,A1B2-30,A3B1-50,A2B3-50 which gives us CYBN{W4S_TR4NSP0RT_0PT1M1S5T10N_FUN}

(another solution is possible with z3 but for this I'll let you check https://ctf.thaysan.com/ctf-and-writeups/2026-or-efrei-cybernight/reverse/multi-layer-binary)

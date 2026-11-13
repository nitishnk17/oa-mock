# Media.net OA: IIT Patna

Transcribed from a candidate's note (three questions in text) and two screenshots shared with it. The date, role, platform and time limit were not given.

## 1. Trapping rain water on a 2-D grid

The note only linked LeetCode 407 (Trapping Rain Water II).

→ `data/medianet/questions/trapwater3d.json` (*Rainwater on a Height Grid*). Statement paraphrased; LeetCode's constraints (1 ≤ m, n ≤ 200, heights ≤ 2·10⁴).

## 2. Counting pairs of arrays

Given N and M, count pairs of arrays Arr1, Arr2 of length N with elements in 1..M, Arr1[i] ≤ Arr2[i] for every i, Arr1 non-decreasing and Arr2 non-increasing. Queries come as two equal-length arrays A and B (N = A[i], M = B[i]); answer each modulo 1000000007.

→ `data/medianet/questions/arrpairs.json` (*Rising and Falling Array Pairs*). No constraints were reported. The mock uses Q ≤ 10⁴ and N, M ≤ 10⁵ (Q is capped because the runner keeps at most 200 KB of output). Same problem as Codeforces 1288C.

## 3. Assigning tasks to three people

You, Tom and Jerry have A tasks. Each task goes to at least one person, and may go to two or all three. You solve exactly B tasks, Tom exactly C and Jerry exactly D. Count the assignments modulo 10⁹ + 7. Constraints: 1 ≤ A, B, C, D ≤ 30.

→ `data/medianet/questions/tasks3.json` (*Sharing Tasks Among Three*). Assumed: tasks are distinct, and so are the three people.

## Screenshots (shared with the note)

### Minimise the maximum difference between the heights

Given tower heights A and a positive integer B, every tower must be either increased or decreased by B, exactly once. Return the minimum possible difference between the tallest and shortest tower. Constraints: 2 ≤ n ≤ 10⁵, −10⁹ ≤ A[i] ≤ 10⁹, 1 ≤ B ≤ 10⁹. The examples were cut off.

→ `data/medianet/questions/towers.json` (*Level the Towers by ±B*). Heights may go negative (the constraints allow negative inputs, and the statement doesn't forbid it).

### Egg drop

A eggs, a building with floors 1..B, an unknown floor C (0 ≤ C ≤ B) above which eggs break. Find the minimum number of moves that determines C in the worst case. Constraints: 1 ≤ A ≤ 100, 1 ≤ B ≤ 10⁴. The input format was cut off.

→ `data/medianet/questions/eggdrop.json` (*Egg Drop: Fewest Moves*). Same problem as LeetCode 887.

The screenshots came with this note, so the mock lists them under Media.net, in a separate "Also reported" format. It isn't certain they are from the same test.

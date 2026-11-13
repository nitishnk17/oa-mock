# Media.net OA: IIT Guwahati and two more sets

Transcribed from a note shared in a group chat (two sets) and a PDF write-up (one set). None of them gave the date, role or time limit. The PDF included C++ solutions; the mock's references are written independently and checked against brute force.

## Set 1: IIT Guwahati (chat note)

### 1. Convert A to B with 2×2 XOR flips

Two N×N 0/1 matrices A and B. An operation picks a 2×2 submatrix of A and XORs each of its elements with 1. Is it possible to turn A into B?

→ `data/medianet/questions/xor2x2.json` (*Flip 2×2 Blocks to Match*). Also problem 3 of the PDF set (returns 1 or 0; 2 ≤ N ≤ 10³). The mock uses N ≤ 500 to keep test files small.

### 2. Two swapped nodes in a BST

A BST is given by its root (the note says "in the form of linked list", meaning node objects). Two elements are out of place; find the two that need to be swapped.

→ `data/medianet/questions/bstswap.json` (*Find the Two Swapped BST Values*). Assumed: the tree is given in LeetCode's level-order form with `-1` for missing children, and the answer is the two values in increasing order. Same as LeetCode 99.

### 3. Guards and thieves on a line

A guards, M thieves, N nodes in a line with given distances between neighbours. Each thief arrives at a given node at a given time. Guards start at node 1 whenever we like and never stop; a guard catches thieves who have already arrived at the nodes it passes. Minimise the total waiting time, and return each thief's waiting time in that optimum.

→ `data/medianet/questions/guards.json` (*Guards Sweeping a Line of Posts*). The per-thief array isn't unique in general (several optima can split the waits differently), so the mock asks for the minimum total. Assumed: speed 1, start times may be any integer, as in Codeforces 311B (Cats Transport), which this is. No constraints were given; the mock uses N ≤ 10⁵, M ≤ 10⁴, guards ≤ 20.

## Set 2: college not given (same chat note)

### 1. Power array

The statement came through garbled. Reconstructed from the two examples: arrange A (values below 2²⁰) as Z; X[i] is the length of the longest prefix of Z whose elements all have bit 19 − i set; return the lexicographically largest X over all arrangements. Examples: `[1,2,3,4,5]` → X[17] = 2, X[19] = 1 (order 5 4 3 2 1); `[4,16,16,36,36]` → X[14] = 2, X[17] = 3 (order 36 36 4 16 16). Constraints: N ≤ 2·10⁵.

→ `data/medianet/questions/powerarr.json` (*Strongest Bit-Prefix Array*). The mock's reference reproduces both reported outputs.

### 2. Rainwater Harvesting

N×M height map (1 ≤ N, M ≤ 110, heights 1..19999); return the trapped water volume.

→ Same problem as `trapwater3d` from the IIT Patna set (LeetCode 407), so it isn't added twice. The set 2 format in the mock uses that question.

### 3. Prison pass-code ("sed-values")

N×N grid of distinct positive values, or −1 for blocked cells; moves are up/down/left/right through open cells. A cell's sed-value is the sum of the values of cells that are multiples of its value and not reachable from it; −1 for blocked cells. Return the sum of all sed-values modulo 10⁹ + 7. Example: `[[1,3,-1,5],[-1,-1,-1,-1],[2,6,-1,10],[8,7,-1,11]]` → 68 (the note's per-cell table, decoded: 49, 6, 10 and 10, the rest 0, and seven blocked cells).

→ `data/medianet/questions/sedvalue.json` (*Unreachable Multiples Pass-Code*). Assumed: a negative total is reported as its non-negative residue. The mock uses N ≤ 500 (reported 10³).

## Set 3: college not given (PDF)

1. **Magic number signs.** For each element of a permutation: (smaller left × smaller right) − (larger left × larger right); output 1 if ≥ 0 else −1. N ≤ 10⁵. → `magicnum.json`. The mock uses N ≤ 6·10⁴, because the runner keeps at most 200 KB of output.
2. **Allied Nations' tour.** A cities, start at B, C days, each day move within distance E; attacked (day, city) pairs are forbidden. Count tours modulo 10⁹ + 7. A, C ≤ 1000, M ≤ A·C. → `tour.json`. The mock uses M ≤ 10⁵. Input order follows the reported signature `solve(A, B, C, D, E)`.
3. **2×2 XOR conversion.** Same as set 1, question 1 → `xor2x2.json`.

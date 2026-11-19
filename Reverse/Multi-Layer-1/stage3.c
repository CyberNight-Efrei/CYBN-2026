#include "common.h"
#include "next_blob.h" /* generated: NEXT_BLOB = stage 4, encrypted */
#include "secrets.h"   /* generated: STAGE3_SALT */
#include <elf.h>       /* AT_BASE, AT_SYSINFO_EHDR */
#include <limits.h>
#include <sys/auxv.h>

#define N 3 /* N sources, N destinations */

typedef struct {
    int supply[N];  /* units available at each source A1..AN       */
    int demand[N];  /* units required at each destination B1..BN   */
    int cost[N][N]; /* cost per unit, from source i to destination j */
} Problem;

typedef int Plan[N][N]; /* Plan[i][j] = units shipped from A(i+1) to B(j+1) */

/* ------------------------------------------------------------------ */
/* Small, generic helpers (not "the trick" - reused by both paths)     */
/* ------------------------------------------------------------------ */

static uint64_t rng_state;

/* xorshift64*: small, deterministic, identical on every machine. */
static uint32_t rng_next(void) {
    rng_state ^= rng_state >> 12;
    rng_state ^= rng_state << 25;
    rng_state ^= rng_state >> 27;
    return (uint32_t)((rng_state * 0x2545F4914F6CDD1DULL) >> 32);
}

static int rng_range(int lo, int hi) /* inclusive */
{
    return lo + (int)(rng_next() % (uint32_t)(hi - lo + 1));
}

/* Every source ships exactly its supply, every destination gets its demand. */
static int plan_is_feasible(const Problem *p, Plan plan) {
    for(int i = 0; i < N; i++) {
        int shipped = 0;
        for(int j = 0; j < N; j++) shipped += plan[i][j];
        if(shipped != p->supply[i])
            return 0;
    }
    for(int j = 0; j < N; j++) {
        int received = 0;
        for(int i = 0; i < N; i++) received += plan[i][j];
        if(received != p->demand[j])
            return 0;
    }
    return 1;
}

static int plan_cost(const Problem *p, Plan plan) {
    int total = 0;
    for(int i = 0; i < N; i++)
        for(int j = 0; j < N; j++) total += plan[i][j] * p->cost[i][j];
    return total;
}

/* Canonical text for a Plan: "A1B1-20,A1B2-30,...", routes in a fixed
 * (i, j) order, zero routes omitted. Used on BOTH paths (KEYGEN and player)
 * so that the same actual allocation always serializes to the same bytes,
 * whatever order the player happened to type its routes in - only the
 * allocation itself (not its spelling) is allowed to matter. */
static void plan_to_text(Plan plan, char *out, size_t cap) {
    out[0] = '\0';
    for(int i = 0; i < N; i++)
        for(int j = 0; j < N; j++)
            if(plan[i][j]) {
                char seg[32];
                snprintf(seg, sizeof seg, "A%dB%d-%d,", i + 1, j + 1, plan[i][j]);
                strncat(out, seg, cap - strlen(out) - 1);
            }
}

#ifndef KEYGEN
/* "A1B1-30,A2B3-10" -> plan[0][0] = 30, plan[1][2] = 10. Returns 0 on bad syntax.
 * Only the player path needs this: the builder's brute-force search below
 * enumerates plans directly, it never parses one. */
static int parse_plan(const char *text, Plan plan) {
    int seen[N][N] = {{0}};
    char copy[256];

    memset(plan, 0, sizeof(Plan));
    snprintf(copy, sizeof copy, "%s", text);

    for(char *tok = strtok(copy, ","); tok; tok = strtok(NULL, ",")) {
        int src, dst, qty;
        char junk;

        if(sscanf(tok, " A%1dB%1d-%4d %c", &src, &dst, &qty, &junk) != 3)
            return 0;
        if(src < 1 || src > N || dst < 1 || dst > N || qty < 0)
            return 0;
        if(seen[src - 1][dst - 1]++)
            return 0; /* same route given twice */

        plan[src - 1][dst - 1] = qty;
    }
    return 1;
}

/* Looks and behaves exactly like stage 2's password check from the outside:
 * one generic prompt, one generic rejection, no numbers, no hint that there
 * is a structure, a format, or an objective to find. Everything the player
 * needs - that the input is "A1B1-10,A2B3-20" style, that it has to satisfy
 * hidden supply/demand totals, and that among the plans that do, only the
 * MINIMUM-cost one is accepted - is something they only learn by reversing
 * this binary (or by reversing parse_plan/plan_is_feasible/plan_cost above
 * and the problem generation in main() below), never by reading output. */
static int read_player_plan(const Problem *p, char *plan_text, size_t plan_text_cap) {
    printf("Password: ");

    char line[256];
    Plan plan;
    if(!read_line(line, sizeof line) || !parse_plan(line, plan)) {
        puts("Access denied.");
        exit(1);
    }
    if(!plan_is_feasible(p, plan)) {
        puts("Access denied.");
        exit(1);
    }

    plan_to_text(plan, plan_text, plan_text_cap);
    return plan_cost(p, plan);
}
#else
/* Builder only (not in the shipped binary): find the true optimum by trying
 * every plan. With a 3x3 problem, 4 cells are free, the other 5 follow.
 *
 * Also counts how many DISTINCT plans reach that optimum. The key below is
 * now derived from the exact allocation, not just its cost (see main()), so
 * a degenerate problem with two equally-cheap but different optimal plans
 * would mean the one build.py bakes the key with isn't the only plan a
 * player could honestly arrive at - the build must refuse to ship that. */
static int brute_force_min_cost(const Problem *p, char *plan_text, size_t plan_text_cap) {
    int best = INT_MAX;
    int ties = 0;
    Plan best_plan = {{0}};

    for(int a = 0; a <= p->supply[0]; a++)
        for(int b = 0; a + b <= p->supply[0]; b++)
            for(int c = 0; c <= p->supply[1]; c++)
                for(int d = 0; c + d <= p->supply[1]; d++) {
                    Plan x;
                    x[0][0] = a;
                    x[0][1] = b;
                    x[0][2] = p->supply[0] - a - b;
                    x[1][0] = c;
                    x[1][1] = d;
                    x[1][2] = p->supply[1] - c - d;
                    x[2][0] = p->demand[0] - a - c;
                    x[2][1] = p->demand[1] - b - d;
                    x[2][2] = p->supply[2] - x[2][0] - x[2][1];

                    if(x[2][0] < 0 || x[2][1] < 0 || x[2][2] < 0 || !plan_is_feasible(p, x))
                        continue;
                    int cost = plan_cost(p, x);
                    if(cost < best) {
                        best = cost;
                        ties = 1;
                        memcpy(best_plan, x, sizeof best_plan);
                    } else if(cost == best) {
                        ties++;
                    }
                }

    if(ties != 1) {
        fprintf(stderr,
                "FATAL: this problem instance has %d distinct optimal plans at cost %d "
                "(degenerate transportation problem) - the shipped key only matches ONE "
                "allocation, so this instance cannot be shipped as-is. Change STAGE3_SALT "
                "(or anything else that affects the generated numbers) and rebuild.\n",
                ties, best);
        exit(1);
    }

    plan_to_text(best_plan, plan_text, plan_text_cap);

    /* Show the (unique) optimal plan to the challenge author (stderr). */
    fprintf(stderr, "optimal plan (cost %d): %s\n", best, plan_text);
    return best;
}
#endif

/* ------------------------------------------------------------------ */

int main(int argc, char **argv) {
    (void)argv; /* stage 3 no longer uses the incoming key: see the trap above */
    init_io();
    if(argc < 2) {
        puts("This stage must be launched by the previous one.");
        return 1;
    }

    /* --- the trap: looks live, is actually constant (see the comment --- *
     * --- at the top of this file) ------------------------------------- */

    uint64_t ld_base = getauxval(AT_BASE);           /* where ld.so was loaded */
    uint64_t vdso_base = getauxval(AT_SYSINFO_EHDR); /* where the vDSO was loaded */

    uint64_t ld_page_off = ld_base & 0xFFFULL;     /* always 0: page-aligned */
    uint64_t vdso_page_off = vdso_base & 0xFFFULL; /* always 0: page-aligned */

    uint64_t seed = STAGE3_SALT;
    seed ^= ld_page_off * 0x9E3779B97F4A7C15ULL; /* 0 * anything = 0 */
    seed ^= vdso_page_off << 7;                  /* 0 << k        = 0 */
    seed |= 1;                                   /* xorshift never starts at 0 */

    rng_state = seed;

    /* --- generate the problem: supply, then demand, then costs -------- */

    Problem problem;
    int total = 0;
    for(int i = 0; i < N; i++) {
        problem.supply[i] = 10 * rng_range(2, 6); /* 20..60 */
        total += problem.supply[i];
    }

    int units = total / 10;
    int d0 = rng_range(1, units - 2);
    int d1 = rng_range(1, units - d0 - 1);
    problem.demand[0] = 10 * d0;
    problem.demand[1] = 10 * d1;
    problem.demand[2] = total - problem.demand[0] - problem.demand[1];

    for(int i = 0; i < N; i++)
        for(int j = 0; j < N; j++) problem.cost[i][j] = rng_range(2, 30);

    /* --- price the player's plan (or, for the builder, brute-force it) - */

    char plan_text[128];
#ifdef KEYGEN
    int cost = brute_force_min_cost(&problem, plan_text, sizeof plan_text);
#else
    int cost = read_player_plan(&problem, plan_text, sizeof plan_text);
#endif

    /* Transform: key = SHA-256("stage3" || decimal cost || canonical plan).
     * Binding the key to the allocation itself (not just its cost) is only
     * safe because brute_force_min_cost() above refuses to build a problem
     * instance that has more than one optimal plan - see its comment. */
    char key_text[160];
    snprintf(key_text, sizeof key_text, "%d%s", cost, plan_text);

    uint8_t key[KEY_LEN];
    derive_key("stage3", key_text, strlen(key_text), key);

    unlock_next_stage(key, NEXT_BLOB, sizeof NEXT_BLOB);
    return 0;
}

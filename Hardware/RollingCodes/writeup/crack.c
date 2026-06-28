#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <errno.h>
#include <limits.h>

#define RANDOM_MAX 0x7fffffffL

static long c_do_random(unsigned long *ctx)
{
    /*
     * Compute x = (7^5 * x) mod (2^31 - 1)
     * without overflowing 31 bits:
     *      (2^31 - 1) = 127773 * (7^5) + 2836
     * From "Random number generators: good ones are hard to find",
     * Park and Miller, Communications of the ACM, vol. 31, no. 10,
     * October 1988, p. 1195.
     */
    long hi, lo, x;

    x = *ctx;
    /* Can't be initialized with 0, so use another value. */
    if (x == 0)
        x = 123459876L;
    hi = x / 127773L;
    lo = x % 127773L;
    x = 16807L * lo - 2836L * hi;
    if (x < 0)
        x += 0x7fffffffL;
    return ((*ctx = x) % ((unsigned long)RANDOM_MAX + 1));
}

static unsigned long next = 1;

static long c_random(void)
{
    return c_do_random(&next);
}

static void c_srandom(unsigned long seed)
{
    next = seed;
}

int main(int argc, char const *argv[])
{
    if (argc != 3) {
        return 1;
    }

    char *endptr;
    errno = 0;

    unsigned long x0_ul = strtoul(argv[1], &endptr, 10);
    if (errno != 0 || *endptr != '\0' || x0_ul > UINT32_MAX) {
        return 1;
    }
    uint32_t x0 = (uint32_t)x0_ul;

    errno = 0;
    unsigned long x1_ul = strtoul(argv[2], &endptr, 10);
    if (errno != 0 || *endptr != '\0' || x1_ul > UINT32_MAX) {
        return 1;
    }
    uint32_t x1 = (uint32_t)x1_ul;

    int32_t n = 1;

    int32_t residue = x0 ^ x1;

    for (uint32_t i = 0; i < RANDOM_MAX; i++)
    {
        c_srandom(i);
        n = (int32_t)c_random();

        if ((n ^ i) == residue)
        {
            printf("%u\n", n ^ x1);
        }
    }

    return 0;
}

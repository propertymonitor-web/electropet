// electropet breeding rules: any two kinds of pet can have young together (the insect only by its named legend), the
// young take the mother's body and the father's head, and the result is always something the screen can draw.
//   g++ -std=c++17 -I src -I <MeshCore>/src -I test -DPET_MYSTERY=1 test/breed_sim.cpp src/WolfCore.cpp -o breed_sim
#include "mock.h"

static int fails = 0;
#define CHECK(c, ...) do { if (!(c)) { printf("FAIL: " __VA_ARGS__); printf("  (line %d)\n", __LINE__); fails++; } } while (0)

int main() {
  MockHost h(1, 0x1234ABCDu, 0x11111111u);
  WolfGame g(&h); g.begin(0);
  const int N = WOLF_SPECIES_COUNT;
  int pairs = 0, made = 0;
  bool seen[256]; memset(seen, 0, sizeof(seen));
  // every kind code that exists: 1..N plain, 16.. mixed
  for (int a = 1; a < 256; a++) for (int b = 1; b < 256; b++) {
    if (!WolfGame::kindValid((uint8_t)a) || !WolfGame::kindValid((uint8_t)b)) continue;
    bool insect = false;
    auto body = [&](int k) { return k <= N ? k - 1 : (k - 16) / N; };
    auto head = [&](int k) { return k <= N ? k - 1 : (k - 16) % N; };
    if (body(a) == 4 || head(a) == 4 || body(b) == 4 || head(b) == 4) insect = true;
    bool can = WolfGame::canPair((uint8_t)a, (uint8_t)b);
    if (a == b) { CHECK(can, "kind %d should pair with itself", a); continue; }
    if (insect) continue;                                    // legends are covered in cross_sim
    pairs++;
    CHECK(can, "kinds %d and %d should be able to pair", a, b);
    int y = g.youngKind((uint8_t)a, (uint8_t)b);
    CHECK(y > 0 && WolfGame::kindValid((uint8_t)y), "young of %d x %d is not a valid kind (%d)", a, b, y);
    if (y > 0) {
      made++; seen[y] = true;
      int yb = body(y), yh = head(y);
      bool legend = a <= N && b <= N && petHybrid(body(a), body(b)) != 0xFF;     // a named legend (wolf + bear = griffin...) replaces the mix
      if (!legend) CHECK(yb == body(a), "young of %d x %d has body %d, want mother's %d", a, b, yb, body(a));
      if (!legend) CHECK(yh == head(b), "young of %d x %d has head %d, want father's %d", a, b, yh, head(b));
    }
  }
  int kinds = 0; for (int k = 1; k < 256; k++) if (seen[k]) kinds++;
  printf("%d pairs checked, %d litters decided, %d different kinds can be born\n", pairs, made, kinds);
  CHECK(kinds > 150, "too few different kinds reachable (%d)", kinds);
  printf(fails ? "SOME CHECKS FAILED\n" : "all checks passed\n");
  return fails ? 1 : 0;
}

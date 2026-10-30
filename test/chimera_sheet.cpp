// Frames of pets for a visual check: every plain species, and some mixed ones (body x head).
//   g++ -std=c++17 -I src -I <MeshCore>/src -I test -DPET_MYSTERY=1 test/chimera_sheet.cpp src/WolfCore.cpp src/Mystery[A-Z]*.cpp -o chimera_sheet
//   ./chimera_sheet frames.txt [genome-hex]     then  python3 tools/frames_to_png.py frames.txt out.png --cols 4 --scale 3
#include "mock.h"
#include "WolfScene.h"

static uint32_t tailFor(uint8_t sp) { for (uint32_t t = 1; t < 200000; t++) if (petPickSpecies(t * 2654435761u) == sp) return t * 2654435761u; return 1; }

int main(int argc, char** argv) {
  if (argc < 2) return 1;
  FILE* f = fopen(argv[1], "w");
  uint32_t genome = argc > 2 ? (uint32_t)strtoul(argv[2], 0, 16) : 0xD3B6C8E4u;
  struct Pair { uint8_t body, head; } pairs[] = { {0,0},{1,1},{2,2},{3,3},{5,5},{6,6},{7,7},{8,8},{9,9},{10,10},{11,11},{12,12},{13,13},{14,14},
                                                  {0,3},{1,10},{2,14},{7,12},{14,2},{3,0},{8,13},{10,7},{9,1},{12,3} };
  for (auto& p : pairs) {
    MockHost h(1, tailFor(p.body), 7);
    WolfGame g(&h); g.begin(0);
    Wolf& w = g.pack[0];
    w.genome = genome;
    w.kind = p.body == p.head ? 0 : WolfGame::chimeraKind(p.body, p.head);
    if (p.body == p.head) { g_mystery_sp = p.body; w.kind = (uint8_t)(p.body + 1); }
    w.age_secs = WolfGame::eggSecs(w.genome) + 40u * WOLF_SECS_PER_MONTH;
    PetSceneBase* sc = makePetScene(p.body, &g);
    if (p.body != p.head) sc->setHead(p.head);
    MockDisplay d; uint32_t now = 1000;
    for (int i = 0; i < 12; i++, now += 120) { d.startFrame(0); sc->render(d, now, 3900); }
    char lab[40]; snprintf(lab, sizeof(lab), "%s_x_%s", petNameOf(p.body), petNameOf(p.head));
    d.dump(f, lab);
    delete sc;
  }
  fclose(f);
  return 0;
}

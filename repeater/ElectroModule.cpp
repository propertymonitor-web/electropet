#include "ElectroModule.h"
#include "MyMesh.h"
#include "target.h"
#include <SPIFFS.h>

extern MyMesh the_mesh;                        // defined in main.cpp
ElectroModule* g_electro = NULL;

#define PET_FILE   PET_STATE_FILE
#define PET_BACKUP PET_STATE_FILE ".bak"

struct ElectroModule::Host : public WolfHost {
  ElectroModule* mod;
  explicit Host(ElectroModule* m) : mod(m) {}

  uint32_t random32() override {
    uint32_t v = 0;
    the_mesh.getRNG()->random((uint8_t*)&v, 4);
    return v;
  }

  // the last 4 bytes of the radio's public key: they decide which pet is in the egg and what it looks like
  uint32_t identityTail() override {
    const uint8_t* k = the_mesh.self_id.pub_key;
    return ((uint32_t)k[PUB_KEY_SIZE - 4] << 24) | ((uint32_t)k[PUB_KEY_SIZE - 3] << 16) |
           ((uint32_t)k[PUB_KEY_SIZE - 2] << 8) | (uint32_t)k[PUB_KEY_SIZE - 1];
  }

  void ownerPrefix(uint8_t out[4]) override { memcpy(out, the_mesh.self_id.pub_key, 4); }

  bool readFile(const char* name, uint8_t* buf, int maxlen, int& len) {
    FILESYSTEM* fs = the_mesh.petFs();
    if (!fs || !fs->exists(name)) return false;
    File f = fs->open(name);
    if (!f) return false;
    int n = (int)f.read(buf, maxlen);
    f.close();
    if (n <= 0) return false;
    len = n;
    return true;
  }

  bool loadState(uint8_t* buf, int maxlen, int& len) override { return readFile(PET_FILE, buf, maxlen, len); }
  bool loadBackup(uint8_t* buf, int maxlen, int& len) override { return readFile(PET_BACKUP, buf, maxlen, len); }

  // two copies, one after the other: if the power dies while one is being written, the other is whole
  void saveState(const uint8_t* buf, int len) override {
    FILESYSTEM* fs = the_mesh.petFs();
    if (!fs) return;
    const char* names[2] = { PET_FILE, PET_BACKUP };
    for (int i = 0; i < 2; i++) {
      File f = fs->open(names[i], "w", true);
      if (!f) continue;
      f.write(buf, len);
      f.close();
    }
  }

  // Pet packets are zero-hop: only radios that hear this one directly ever see them, and nothing forwards them.
  void broadcast(const uint8_t* buf, int len) override {
    mesh::Packet* pkt = the_mesh.createControlData(buf, len);
    if (pkt) the_mesh.sendZeroHop(pkt);
  }

  void alert(const char* text) override {
    snprintf(mod->_alert, sizeof(mod->_alert), "%s", text);
    mod->_alert_until = millis() + 3000;
  }
};

ElectroModule::ElectroModule() : _host(NULL), _game(NULL), _scene(NULL), _scene_sp(0), _scene_head(0xFF), _alert_until(0) {
  _alert[0] = 0;
}

ElectroModule::~ElectroModule() {
  delete _scene;
  delete _game;
  delete _host;
}

void ElectroModule::begin() {
  _host = new Host(this);
  _game = new WolfGame(_host);
  _game->begin(millis());
  uint8_t i = _game->current < _game->count ? _game->current : 0;
  _scene_sp = WolfGame::speciesOf(_game->pack[i]);
  _scene = makePetScene(_scene_sp, _game);
  _scene_head = WolfGame::headOf(_game->pack[i]);
  if (_scene) _scene->setHead(_scene_head);
  g_electro = this;
}

void ElectroModule::loop() {
  if (_game) _game->tick(millis());
}

void ElectroModule::onControl(const uint8_t* payload, int len) {
  if (_game) _game->onPacket(payload, len, millis());
}

void ElectroModule::save() {
  if (_game) _game->save();
}

// the shown pet may be another kind than the last one drawn: switch pictures and head
void ElectroModule::syncScene() {
  if (!_game || !_game->count) return;
  const Wolf& w = _game->pack[_game->current < _game->count ? _game->current : 0];
  uint8_t sp = WolfGame::speciesOf(w), hd = WolfGame::headOf(w);
  if (_scene && sp != _scene_sp) {
    delete _scene;
    _scene = makePetScene(sp, _game);
    _scene_sp = sp;
    _scene_head = 0xFE;                      // force a head refresh
  }
  if (_scene && hd != _scene_head) { _scene->setHead(hd); _scene_head = hd; }
}

int ElectroModule::render(DisplayDriver& d, uint16_t batt_mv) {
  syncScene();
  int next = _scene ? _scene->render(d, millis(), batt_mv) : 1000;
  if (_alert[0] && (int32_t)(_alert_until - millis()) > 0) {      // a short banner, e.g. "Pups born! x2"
    int w = d.getTextWidth(_alert) + 6, x = (d.width() - w) / 2;
    d.setColor(UIColor::window_bkg);
    d.fillRect(x, 0, w, 11);
    d.setColor(UIColor::primary_txt);
    d.drawRect(x, 0, w, 11);
    d.setCursor(x + 3, 2);
    d.print(_alert);
  }
  return next;
}

void ElectroModule::nextPet() {
  if (_game) _game->cycleWolf();
}

void ElectroModule::describe(const Wolf& w, char* out, int cap) const {
  char kind[12];
  WolfGame::titleOf(w, kind, sizeof(kind));
  if (WolfGame::isEgg(w)) { snprintf(out, cap, "egg, %luh to hatch", (unsigned long)((WolfGame::eggLeftSecs(w) + 3599) / 3600)); return; }
  snprintf(out, cap, "%s %s %umo%s%s%s", kind, w.sex ? "F" : "M", (unsigned)WolfGame::ageMonths(w),
           w.name[0] ? " \"" : "", w.name, w.name[0] ? "\"" : "");
}

bool ElectroModule::command(const char* cmd, char* reply, int reply_len) {
  if (strncmp(cmd, "pet", 3) != 0 || (cmd[3] != 0 && cmd[3] != ' ')) return false;
  if (!_game || !_game->count) { snprintf(reply, reply_len, "Err - no pet yet"); return true; }
  const char* a = cmd + 3;
  while (*a == ' ') a++;
  char line[60];
  if (*a == 0) {                                                  // "pet": the one on screen
    describe(_game->pack[_game->current], line, sizeof(line));
    snprintf(reply, reply_len, "%u/%u %s", (unsigned)_game->current + 1, (unsigned)_game->count, line);
  } else if (strcmp(a, "list") == 0) {
    int n = 0;
    reply[0] = 0;
    for (int i = 0; i < _game->count && n < reply_len - 40; i++) {
      describe(_game->pack[i], line, sizeof(line));
      n += snprintf(reply + n, reply_len - n, "%s%d %s", i ? "\n" : "", i + 1, line);
    }
  } else if (strcmp(a, "next") == 0) {
    nextPet();
    describe(_game->pack[_game->current], line, sizeof(line));
    snprintf(reply, reply_len, "OK - showing %u/%u %s", (unsigned)_game->current + 1, (unsigned)_game->count, line);
  } else if (strncmp(a, "show ", 5) == 0) {
    int n = atoi(a + 5);
    if (n < 1 || n > _game->count) { snprintf(reply, reply_len, "Err - pet 1 to %u", (unsigned)_game->count); return true; }
    _game->current = (uint8_t)(n - 1);
    describe(_game->pack[_game->current], line, sizeof(line));
    snprintf(reply, reply_len, "OK - showing %d/%u %s", n, (unsigned)_game->count, line);
  } else if (strncmp(a, "name", 4) == 0 && (a[4] == 0 || a[4] == ' ')) {
    const char* text = a + 4;
    while (*text == ' ') text++;
    if (text[0] == '#') {                                          // "pet name #2 Rex" names pet 2
      int n = atoi(text + 1);
      while (*text && *text != ' ') text++;
      while (*text == ' ') text++;
      if (n < 1 || n > _game->count) { snprintf(reply, reply_len, "Err - pet 1 to %u", (unsigned)_game->count); return true; }
      _game->current = (uint8_t)(n - 1);
    }
    if (WolfGame::isEgg(_game->pack[_game->current])) { snprintf(reply, reply_len, "Err - it is still an egg"); return true; }
    if (text[0] == '-' && text[1] == 0) text = "";                 // "-" clears the name
    _game->setName(_game->current, text);
    const Wolf& w = _game->pack[_game->current];
    if (w.name[0]) snprintf(reply, reply_len, "OK - pet %u is called %s", (unsigned)_game->current + 1, w.name);
    else snprintf(reply, reply_len, "OK - the name is cleared");
    _game->save();
  } else {
    snprintf(reply, reply_len, "pet | pet list | pet next | pet show N | pet name [#N] TEXT (- clears)");
  }
  return true;
}

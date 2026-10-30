#pragma once
// ElectroModule: glue between the pet game and the MeshCore repeater (screen, radio, flash, commands).

#include <helpers/ui/DisplayDriver.h>
#include "WolfCore.h"
#include "WolfScene.h"
#include <stddef.h>

class ElectroModule {
public:
  ElectroModule();
  ~ElectroModule();

  void begin();                                      // load (or hatch) the pets and hook up the radio
  void loop();                                       // every pass of the main loop
  void onControl(const uint8_t* payload, int len);   // zero-hop control packet from another radio
  int  render(DisplayDriver& d, uint16_t batt_mv);   // draw the pet screen; returns ms to the next frame
  void nextPet();                                    // show the next pet in the pack
  void save();
  // "pet", "pet list", "pet next", "pet show N", "pet name TEXT": returns true if `cmd` was a pet command
  bool command(const char* cmd, char* reply, int reply_len);

private:
  struct Host;
  Host*         _host;
  WolfGame*     _game;
  PetSceneBase* _scene;
  uint8_t       _scene_sp;
  uint8_t       _scene_head;
  char          _alert[24];
  uint32_t      _alert_until;
  void syncScene();
  void describe(const Wolf& w, char* out, int cap) const;
};

// the one instance, set by begin()
extern ElectroModule* g_electro;

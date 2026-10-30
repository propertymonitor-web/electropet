#!/usr/bin/env python3
"""Put the electropet game into a MeshCore repeater.

usage: apply_electropet.py --meshcore /path/to/MeshCore

Copies the game (src/) and the repeater glue (repeater/) into examples/simple_repeater and edits MyMesh.h, MyMesh.cpp
and UITask.{h,cpp} with anchored substitutions.  Every anchor must match exactly once, so a MeshCore change that moves
things fails loudly instead of producing a quietly wrong build.
"""
import argparse, glob, os, shutil, sys

ap = argparse.ArgumentParser()
ap.add_argument("--meshcore", required=True)
a = ap.parse_args()
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rep = os.path.join(a.meshcore, "examples", "simple_repeater")
if not os.path.isdir(rep):
    sys.exit("not a MeshCore checkout (missing %s)" % rep)

for f in sorted(glob.glob(os.path.join(root, "src", "*"))) + sorted(glob.glob(os.path.join(root, "repeater", "Electro*"))):
    shutil.copy(f, rep)
print("copied the game and the repeater glue")


def patch(path, edits):
    s = open(path).read()
    for name, old, new in edits:
        n = s.count(old)
        if n != 1:
            sys.exit("anchor '%s' matched %d times in %s (need exactly 1)" % (name, n, os.path.basename(path)))
        s = s.replace(old, new)
        print("  +", name)
    open(path, "w").write(s)


print("MyMesh.h")
patch(os.path.join(rep, "MyMesh.h"), [
    ("file system", "  void handleCommand(uint32_t sender_timestamp, char* command, char* reply);\n",
     "  FILESYSTEM* petFs() { return _fs; }   // electropet keeps its save files here\n  void handleCommand(uint32_t sender_timestamp, char* command, char* reply);\n"),
])

print("MyMesh.cpp")
patch(os.path.join(rep, "MyMesh.cpp"), [
    ("include", '#include "MyMesh.h"\n', '#include "MyMesh.h"\n#include "ElectroModule.h"\n'),
    ("control", "void MyMesh::onControlDataRecv(mesh::Packet* packet) {\n",
     "void MyMesh::onControlDataRecv(mesh::Packet* packet) {\n  if (g_electro) g_electro->onControl(packet->payload, packet->payload_len);   // pets visiting from other radios\n"),
    ("command", "  // handle ACL related commands\n  if (memcmp(command, \"setperm \", 8) == 0) {",
     "  if (g_electro && g_electro->command(command, reply, 120)) return;   // pet, pet list, pet next, pet name ...\n\n  // handle ACL related commands\n  if (memcmp(command, \"setperm \", 8) == 0) {"),
])

print("UITask.h")
patch(os.path.join(rep, "UITask.h"), [
    ("members", "  unsigned long _started_at = 0;\n",
     "  unsigned long _started_at = 0;\n  uint8_t _page = 0;                  // 0 the pet, 1 the radio's details\n  unsigned long _frame_ms = 1000;     // how long the screen on show wants to wait before the next frame\n"),
])

print("UITask.cpp")
patch(os.path.join(rep, "UITask.cpp"), [
    ("include", '#include <helpers/CommonCLI.h>\n', '#include <helpers/CommonCLI.h>\n#include "ElectroModule.h"\n'),
    ("timing", "#define AUTO_OFF_MILLIS      20000  // 20 seconds\n",
     "#define AUTO_OFF_MILLIS      20000  // 20 seconds (the details page)\n#define PET_SCREEN_MILLIS    180000 // the pet stays on for 3 minutes after a button press\n"),
    ("begin", "  _auto_off = millis() + AUTO_OFF_MILLIS;\n  _started_at = millis();\n",
     "  _auto_off = millis() + PET_SCREEN_MILLIS;\n  _started_at = millis();\n  g_electro = new ElectroModule();\n  g_electro->begin();\n"),
    ("pet page", "  } else {\n    _display->setCursor(0, 0);\n    _display->setTextSize(1);\n    _display->setColor(UIColor::primary_txt);\n    _display->print(_node_prefs->node_name);\n",
     "  } else if (_page == 0 && g_electro) {\n    _frame_ms = g_electro->render(*_display, _board->getBattMilliVolts());\n    if (_frame_ms < 30) _frame_ms = 30;\n  } else {\n    _frame_ms = 1000;\n    _display->setCursor(0, 0);\n    _display->setTextSize(1);\n    _display->setColor(UIColor::primary_txt);\n    _display->print(_node_prefs->node_name);\n"),
    ("click", "    if (_display->isOn()) {\n      // TODO: any action ?\n    } else {\n      _display->turnOn();\n    }\n    _auto_off = millis() + AUTO_OFF_MILLIS;   // extend auto-off timer\n  } else if (ev == BUTTON_EVENT_LONG_PRESS) {\n",
     "    if (_display->isOn()) {\n      _page = (uint8_t)((_page + 1) % 2);   // pet <-> radio details\n    } else {\n      _display->turnOn();\n    }\n    _auto_off = millis() + (_page == 0 ? PET_SCREEN_MILLIS : AUTO_OFF_MILLIS);   // extend auto-off timer\n    _next_refresh = 0;\n  } else if (ev == BUTTON_EVENT_DOUBLE_CLICK) {\n    if (!_display->isOn()) _display->turnOn();\n    if (_page == 0 && g_electro) g_electro->nextPet();   // next pet in the pack\n    _auto_off = millis() + PET_SCREEN_MILLIS;\n    _next_refresh = 0;\n  } else if (ev == BUTTON_EVENT_LONG_PRESS) {\n"),
    ("refresh", "      _next_refresh = millis() + 1000;   // refresh every second\n", "      _next_refresh = millis() + _frame_ms;\n"),
    ("loop", "void UITask::loop() {\n", "void UITask::loop() {\n  if (g_electro) g_electro->loop();\n"),
    ("save before power off", "      _board->powerOff();  // should not return\n", "      if (g_electro) g_electro->save();\n      _board->powerOff();  // should not return\n"),
])
print("done")

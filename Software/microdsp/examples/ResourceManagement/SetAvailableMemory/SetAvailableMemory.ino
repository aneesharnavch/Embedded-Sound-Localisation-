// Checking there is RAM to spare before allocating a buffer.
//
// freeMemory() measures the real figure: the heap/stack gap on AVR,
// ESP.getFreeHeap() on ESP boards, largest allocatable block elsewhere.
// setAvailableMemory() is only a manual override for platforms where none of
// those work.
#include <microdsp.h>

MicroDSP dsp;

void setup() {
  Serial.begin(9600);

  Serial.print(F("Free RAM now: "));
  Serial.print(dsp.freeMemory());
  Serial.println(F(" bytes"));

  // Keep 256 bytes in hand for the stack; requests that would eat into that
  // reserve are refused.
  dsp.setFreeMemoryThreshold(256);

  size_t wanted = 100 * sizeof(float);
  Serial.print(F("Room for 100 floats? "));
  Serial.println(dsp.canProcess(wanted) ? F("yes") : F("no"));

  size_t huge = 10000 * sizeof(float);
  Serial.print(F("Room for 10000 floats? "));
  Serial.println(dsp.canProcess(huge) ? F("yes") : F("no"));

  // Guarded allocation: returns null instead of overcommitting.
  float* buf = dspDataManager::allocateZeroedBuffer(64);
  if (buf) {
    Serial.println(F("Allocated 64 floats."));
    dspDataManager::releaseBuffer(buf);
  } else {
    Serial.println(F("Refused: not enough headroom."));
  }
}

void loop() {}

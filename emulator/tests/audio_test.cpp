#include "audio.hpp"

#include <algorithm>
#include <cassert>
#include <iostream>

using namespace mobigo;

static void test_dac_interrupt_enable_gating() {
    Bus bus;
    assert(bus.read(0x78f0) & 0x8000); // FIFO-empty latch resets set.
    assert((bus.int_status1_value() & 0x0030) == 0); // Disabled sources stay quiet.
    bus.write(0x78f0, 0x4000); // Enable channel-A FIFO interrupt.
    assert(bus.int_status1_value() & 0x0010);
}

static void test_dac_fifo_drain() {
    Bus bus;
    Audio audio;

    bus.write(0x78f2, 0x0180); // Reset FIFO, empty threshold 8.
    bus.write(0x78f0, 0x6405); // CHA, FIFO IRQ, SRC at 16 kHz.
    bus.write(0x78ff, 0x0001); // MobiGo board audio-output gate.
    bus.mmio[0x78a4 - kMmioBase] |= 0x0010; // Route channel A to FIQ.
    for (unsigned i = 0; i < 16; ++i) bus.write(0x78f1, uint16_t(0x7000 + i * 0x100));
    assert(bus.audio_fifo_level_a == 16);
    assert(bus.read(0x78f2) & 0x8000);

    audio.pump(bus);
    bus.cycles += bus.system_clock_hz() / 100; // 10 ms, 160 source samples.
    audio.pump(bus);

    assert(bus.audio_fifo_level_a == 0);
    assert(bus.audio_fifo_a.empty());
    assert(bus.read(0x78f2) & 0x4000); // Underrun keeps the last output.
    assert(bus.read(0x78f0) & 0x8000); // Empty interrupt flag.
    assert(bus.audio_fiq_asserted_no_update());
    assert(std::any_of(audio.output.begin(), audio.output.end(),
                       [](int16_t sample) { return sample != 0; }));
}

static void test_shared_dac_fifo_routing() {
    Bus bus;
    bus.write(0x78f8, 0x1800); // SSF+CHACFG: alternate CHA_Data into A/B.
    bus.write(0x78f1, 0x1111);
    bus.write(0x78f1, 0x2222);
    bus.write(0x78f1, 0x3333);
    bus.write(0x78f1, 0x4444);
    assert((bus.audio_fifo_a == std::deque<uint16_t>{0x1111, 0x3333}));
    assert((bus.audio_fifo_b == std::deque<uint16_t>{0x2222, 0x4444}));

    Bus mono;
    mono.write(0x78f8, 0x1c00); // SSF+CHACFG+MONO: duplicate to A/B.
    mono.write(0x78f1, 0x5678);
    assert((mono.audio_fifo_a == std::deque<uint16_t>{0x5678}));
    assert((mono.audio_fifo_b == std::deque<uint16_t>{0x5678}));
}

static void test_spu_pcm16_oneshot() {
    Bus bus;
    Audio audio;
    constexpr uint32_t wave = 0x001000;
    bus.mem[wave + 0] = 0x8000;
    bus.mem[wave + 1] = 0xc000;
    bus.mem[wave + 2] = 0x4000;
    bus.mem[wave + 3] = 0xffff;

    bus.sound_ram[0x000] = uint16_t(wave);
    bus.sound_ram[0x001] = 0x5000; // PCM16, hardware one-shot.
    bus.sound_ram[0x003] = 0x4040; // Center pan, volume 64.
    bus.sound_ram[0x005] = 0x007f; // Manual envelope at full scale.
    bus.sound_ram[0x204] = 0x7482; // 16 kHz at the 281250 Hz SPU clock.
    bus.mmio[0x7b81 - kMmioBase] = 0x007f;
    bus.mmio[0x7b8d - kMmioBase] = 0x00c0;
    bus.mmio[0x7b95 - kMmioBase] = 0x0001;
    bus.mmio[0x78f0 - kMmioBase] = 0x2000;
    bus.mmio[0x78ff - kMmioBase] = 0x0001;
    bus.mmio[0x7b80 - kMmioBase] = 0x0001;

    audio.pump(bus);
    bus.cycles += bus.system_clock_hz() / 100; // Far longer than this sample.
    audio.pump(bus);

    assert(!audio.channels[0].playing);
    assert(bus.mmio[0x7b8b - kMmioBase] & 0x0001);
    assert((bus.mmio[0x7b8f - kMmioBase] & 0x0001) == 0);
    assert(std::any_of(audio.output.begin(), audio.output.end(),
                       [](int16_t sample) { return sample != 0; }));
}

static void test_mobigo_output_gate() {
    Bus bus;
    Audio audio;
    constexpr uint32_t wave = 0x001000;
    bus.mem[wave + 0] = 0x2000;
    bus.mem[wave + 1] = 0xe000;
    bus.mem[wave + 2] = 0xffff;

    bus.sound_ram[0x000] = uint16_t(wave);
    bus.sound_ram[0x001] = 0x6000; // PCM16, hardware auto-repeat.
    bus.sound_ram[0x002] = uint16_t(wave);
    bus.sound_ram[0x003] = 0x4040;
    bus.sound_ram[0x005] = 0x007f;
    bus.sound_ram[0x204] = 0x7482;
    bus.mmio[0x7b81 - kMmioBase] = 0x007f;
    bus.mmio[0x7b8d - kMmioBase] = 0x00c0;
    bus.mmio[0x7b95 - kMmioBase] = 0x0001;
    bus.mmio[0x78f0 - kMmioBase] = 0x2000;
    bus.mmio[0x78ff - kMmioBase] = 0x0001;
    bus.mmio[0x7b80 - kMmioBase] = 0x0001;

    audio.pump(bus);
    bus.cycles += bus.system_clock_hz() / 1000;
    audio.pump(bus);
    assert(std::any_of(audio.output.begin(), audio.output.end(),
                       [](int16_t sample) { return sample != 0; }));

    bus.mmio[0x78ff - kMmioBase] = 0;
    bus.cycles += bus.system_clock_hz() / 1000;
    audio.pump(bus);
    assert(std::all_of(audio.output.begin(), audio.output.end(),
                       [](int16_t sample) { return sample == 0; }));

    bus.mmio[0x78ff - kMmioBase] = 1;
    bus.cycles += bus.system_clock_hz() / 1000;
    audio.pump(bus);
    assert(std::any_of(audio.output.begin(), audio.output.end(),
                       [](int16_t sample) { return sample != 0; }));
}

int main() {
    test_dac_interrupt_enable_gating();
    test_dac_fifo_drain();
    test_shared_dac_fifo_routing();
    test_spu_pcm16_oneshot();
    test_mobigo_output_gate();
    std::cout << "audio tests passed\n";
    return 0;
}

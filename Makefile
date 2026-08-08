CC ?= cc
CFLAGS ?= -std=c99 -Wall -Wextra -Werror
CPPFLAGS ?= -Iinclude

.PHONY: all test usb-test docs-check doctor target-check samples color-cycle movie-player celeste sample-emulator-check hardware-suite emulator-test emulator-check homebrew-check storage-check font-check animation-check audio-check adpcm-check music-check music-adpcm-check music-aux-check release-check

all: build/test_system_controls build/test_input build/test_audio \
	build/test_audio_resources \
	build/test_touch build/test_resource_bundle build/test_ui_family_b \
	build/test_settings_overlay build/test_storage build/test_hardware_suite_self

build/test_system_controls: src/system_controls.c tests/test_system_controls.c \
		include/mobigo_sdk/system_controls.h
	mkdir -p build
	$(CC) $(CPPFLAGS) $(CFLAGS) \
		src/system_controls.c tests/test_system_controls.c \
		-o build/test_system_controls

build/test_input: src/input.c tests/test_input.c \
		include/mobigo_sdk/input.h include/mobigo_sdk/system_controls.h
	mkdir -p build
	$(CC) $(CPPFLAGS) $(CFLAGS) \
		src/input.c tests/test_input.c \
		-o build/test_input

build/test_audio: src/audio.c tests/test_audio.c \
		include/mobigo_sdk/audio.h include/mobigo_sdk/system_controls.h
	mkdir -p build
	$(CC) $(CPPFLAGS) $(CFLAGS) \
		src/audio.c tests/test_audio.c \
		-o build/test_audio

build/test_audio_resources: src/audio_resources.c tests/test_audio_resources.c \
		include/mobigo_sdk/audio_resources.h
	mkdir -p build
	$(CC) $(CPPFLAGS) $(CFLAGS) \
		src/audio_resources.c tests/test_audio_resources.c \
		-o build/test_audio_resources

build/test_touch: src/touch.c tests/test_touch.c \
		include/mobigo_sdk/touch.h include/mobigo_sdk/system_controls.h
	mkdir -p build
	$(CC) $(CPPFLAGS) $(CFLAGS) \
		src/touch.c tests/test_touch.c \
		-o build/test_touch

build/test_resource_bundle: src/resource_bundle.c src/resource_graphics.c \
		tests/test_resource_bundle.c \
		include/mobigo_sdk/resource_bundle.h
	mkdir -p build
	$(CC) $(CPPFLAGS) $(CFLAGS) \
		src/resource_bundle.c src/resource_graphics.c \
		tests/test_resource_bundle.c \
		-o build/test_resource_bundle

build/test_ui_family_b: src/ui_family_b.c src/ui_family_b_animation.c tests/test_ui_family_b.c \
		include/mobigo_sdk/ui_family_b.h
	mkdir -p build
	$(CC) $(CPPFLAGS) $(CFLAGS) \
		src/ui_family_b.c src/ui_family_b_animation.c tests/test_ui_family_b.c \
		-o build/test_ui_family_b

build/test_settings_overlay: src/ui_family_b.c src/settings_overlay.c \
		tests/test_settings_overlay.c \
		include/mobigo_sdk/ui_family_b.h include/mobigo_sdk/settings_overlay.h
	mkdir -p build
	$(CC) $(CPPFLAGS) $(CFLAGS) \
		src/ui_family_b.c src/settings_overlay.c tests/test_settings_overlay.c \
		-o build/test_settings_overlay

build/test_storage: src/resident_storage.c tests/test_storage.c \
		include/mobigo_sdk/resident_storage.h \
		include/mobigo_sdk/resident_addresses.h
	mkdir -p build
	$(CC) $(CPPFLAGS) $(CFLAGS) \
		src/resident_storage.c tests/test_storage.c \
		-o build/test_storage

build/test_hardware_suite_self: examples/hardware_test_suite/self_tests.c \
		tests/test_hardware_suite_self.c
	mkdir -p build
	$(CC) $(CPPFLAGS) $(CFLAGS) -Iexamples/hardware_test_suite \
		src/system_controls.c src/input.c src/audio.c src/audio_resources.c \
		src/touch.c src/resource_bundle.c src/resource_graphics.c \
		src/ui_family_b.c src/ui_family_b_animation.c \
		examples/hardware_test_suite/self_tests.c \
		tests/test_hardware_suite_self.c -o build/test_hardware_suite_self

test: build/test_system_controls build/test_input build/test_audio \
		build/test_audio_resources \
		build/test_touch build/test_resource_bundle build/test_ui_family_b \
		build/test_settings_overlay build/test_storage build/test_hardware_suite_self
	./build/test_system_controls
	./build/test_input
	./build/test_audio
	./build/test_audio_resources
	./build/test_touch
	./build/test_resource_bundle
	./build/test_ui_family_b
	./build/test_settings_overlay
	./build/test_storage
	./build/test_hardware_suite_self
	python3 -m unittest discover -s tests -p 'test_*.py'

usb-test:
	python3 -m unittest discover -s tools/usb -p 'test_*.py'

docs-check:
	python3 tools/docs/check_docs.py

doctor:
	python3 tools/mobigo.py doctor

target-check:
	python3 tools/build/build_target_objects.py

hardware-suite:
	python3 examples/hardware_test_suite/build.py

samples: color-cycle movie-player celeste

color-cycle:
	python3 examples/color_cycle/build.py

movie-player:
	python3 examples/bad_apple_player/build.py

celeste:
	python3 examples/mobigo_celeste/build.py

sample-emulator-check: samples
	python3 tools/verify/verify_complete_samples_emulator.py

emulator-test:
	bash tools/build/emulator_unix.sh --test

emulator-check:
	python3 tools/verify/verify_system_ui_emulator.py

homebrew-check:
	python3 tools/verify/verify_homebrew_input_emulator.py

storage-check:
	python3 tools/verify/verify_storage_emulator.py

font-check:
	python3 tools/verify/verify_font_emulator.py

animation-check:
	python3 tools/verify/verify_family_b_animation_emulator.py

audio-check:
	python3 tools/verify/verify_audio_emulator.py

adpcm-check:
	python3 tools/verify/verify_adpcm36_emulator.py

music-check:
	python3 tools/verify/verify_music_emulator.py

music-adpcm-check:
	python3 tools/verify/verify_music_adpcm36_emulator.py

music-aux-check:
	python3 tools/verify/verify_music_aux_emulator.py

release-check:
	$(MAKE) test
	$(MAKE) usb-test
	$(MAKE) docs-check
	$(MAKE) target-check
	$(MAKE) emulator-test
	$(MAKE) emulator-check
	$(MAKE) homebrew-check
	$(MAKE) storage-check
	$(MAKE) font-check
	$(MAKE) animation-check
	$(MAKE) audio-check
	$(MAKE) adpcm-check
	$(MAKE) music-check
	$(MAKE) music-adpcm-check
	$(MAKE) music-aux-check
	$(MAKE) samples sample-emulator-check
	$(MAKE) hardware-suite

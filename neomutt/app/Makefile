APP_NAME   := NeoMutt
# change this to your own reverse-DNS id
APP_ID     := com.jkorbmacher.neomutt
APP_BUNDLE := $(APP_NAME).app

RUNNER_APP_NAME := NeoMuttRunner.app
RUNNER_APP      := $(RUNNER_APP_NAME)
RUNNER_ID       := com.jkorbmacher.neomutt.runner
RUNNER_SCRIPT   := neomutt-launch

SCRIPT     := NeoMutt.applescript
ICON_PNG   := icon.png                   # your 640x640 PNG
ICONSET    := $(APP_NAME).iconset
ICNS       := $(APP_NAME).icns

RUNNER_PLIST_TEMPLATE := Info.NeomuttRunner.template.plist
RUNNER_PLIST_OUT      := Info.NeomuttRunner.plist

.PHONY: all clean install

all: $(APP_BUNDLE)

# 1) Build runner app
$(RUNNER_APP): $(RUNNER_SCRIPT) $(ICNS) $(RUNNER_PLIST_OUT)
	rm -rf "$@"
	mkdir -p "$@/Contents/MacOS" "$@/Contents/Resources"

	cp "$(RUNNER_SCRIPT)" "$@/Contents/MacOS/neomutt-launch"
	chmod +x "$@/Contents/MacOS/neomutt-launch"

	cp "$(ICNS)" "$@/Contents/Resources/$(ICNS)"
	cp "$(RUNNER_PLIST_OUT)" "$@/Contents/Info.plist"

	@echo "Built $(RUNNER_APP)"

# 2) Compile AppleScript into an .app
$(APP_BUNDLE): $(SCRIPT) $(ICNS) Info.plist.template $(RUNNER_APP)
	rm -rf "$@"
	osacompile -o "$@" "$<"

	# Ensure Resources dir exists and copy icon
	mkdir -p "$@/Contents/Resources"
	cp "$(ICNS)" "$@/Contents/Resources/$(ICNS)"
	rm -rf "$@/Contents/Resources/$(RUNNER_APP_NAME)"
	cp -R "$(RUNNER_APP)" "$@/Contents/Resources/"

	# Overwrite Info.plist with a minimal, clean version
	sed \
	  -e 's/__APP_NAME__/$(APP_NAME)/g' \
	  -e 's/__APP_ID__/$(APP_ID)/g' \
	  -e 's/__APP_ICON__/$(ICNS)/g' \
	  Info.plist.template > "$@/Contents/Info.plist"

	@echo "Built $(APP_BUNDLE)"

$(RUNNER_PLIST_OUT): $(RUNNER_PLIST_TEMPLATE)
	sed \
	  -e 's/__APP_NAME__/$(APP_NAME)/g' \
	  -e 's/__APP_ID__/$(RUNNER_ID)/g' \
	  -e 's/__APP_ICON__/$(ICNS)/g' \
	  $(RUNNER_PLIST_TEMPLATE) > $(RUNNER_PLIST_OUT)
	@echo "Generated $(RUNNER_PLIST_OUT)"

# 2) Build .icns from a single PNG using sips + iconutil
$(ICNS): $(ICON_PNG)
	rm -rf "$(ICONSET)"
	mkdir "$(ICONSET)"

	# macOS iconset sizes
	sips -z 16   16   $< --out "$(ICONSET)/icon_16x16.png"
	sips -z 32   32   $< --out "$(ICONSET)/icon_16x16@2x.png"

	sips -z 32   32   $< --out "$(ICONSET)/icon_32x32.png"
	sips -z 64   64   $< --out "$(ICONSET)/icon_32x32@2x.png"

	sips -z 128  128  $< --out "$(ICONSET)/icon_128x128.png"
	sips -z 256  256  $< --out "$(ICONSET)/icon_128x128@2x.png"

	sips -z 256  256  $< --out "$(ICONSET)/icon_256x256.png"
	sips -z 512  512  $< --out "$(ICONSET)/icon_256x256@2x.png"

	# Your 640x640 source is already >512px, so this is safe.
	sips -z 512  512  $< --out "$(ICONSET)/icon_512x512.png"

	# Optional upscale to 1024x1024 for @2x of 512 (will be slightly soft, but fine)
	sips -z 1024 1024 $< --out "$(ICONSET)/icon_512x512@2x.png" || true

	iconutil -c icns "$(ICONSET)" -o "$(ICNS)"

	@echo "Built $(ICNS)"

clean:
	rm -rf "$(APP_BUNDLE)" "$(RUNNER_APP)" "$(ICONSET)" "$(ICNS)" "$(RUNNER_PLIST_OUT)"

# Optional install target (to ~/Applications)
install: $(APP_BUNDLE)
	mkdir -p "$(HOME)/Applications"
	rm -rf "$(HOME)/Applications/$(APP_BUNDLE)"
	cp -R "$(APP_BUNDLE)" "$(HOME)/Applications/"
	@echo "Installed to $(HOME)/Applications/$(APP_BUNDLE)"

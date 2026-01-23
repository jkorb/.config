APP_NAME   := NeoMutt
APP_ID     := com.jkorbmacher.neomutt    # change this to your own reverse-DNS id
APP_BUNDLE := $(APP_NAME).app

SCRIPT     := NeoMutt.applescript
ICON_PNG   := icon.png                   # your 640x640 PNG
ICONSET    := $(APP_NAME).iconset
ICNS       := $(APP_NAME).icns

.PHONY: all clean install

all: $(APP_BUNDLE)

# 1) Compile AppleScript into an .app
$(APP_BUNDLE): $(SCRIPT) $(ICNS) Info.plist.template
	rm -rf "$@"
	osacompile -o "$@" "$<"

	# Ensure Resources dir exists and copy icon
	mkdir -p "$@/Contents/Resources"
	cp "$(ICNS)" "$@/Contents/Resources/$(ICNS)"

	# Overwrite Info.plist with a minimal, clean version
	sed \
	  -e 's/__APP_NAME__/$(APP_NAME)/g' \
	  -e 's/__APP_ID__/$(APP_ID)/g' \
	  -e 's/__APP_ICON__/$(ICNS)/g' \
	  Info.plist.template > "$@/Contents/Info.plist"

	@echo "Built $(APP_BUNDLE)"

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
	rm -rf "$(APP_BUNDLE)" "$(ICONSET)" "$(ICNS)"

# Optional install target (to ~/Applications)
install: $(APP_BUNDLE)
	mkdir -p "$(HOME)/Applications"
	rm -rf "$(HOME)/Applications/$(APP_BUNDLE)"
	cp -R "$(APP_BUNDLE)" "$(HOME)/Applications/"
	@echo "Installed to $(HOME)/Applications/$(APP_BUNDLE)"

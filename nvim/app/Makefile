APP_NAME        := Neovim
APP_ID          := com.jkorbmacher.neovim
OPENER_APP      := $(APP_NAME).app
OPENER_ID       := com.jkorbmacher.neovim.opener

INNER_APP_NAME  := NeovimRunner.app
INNER_APP       := $(INNER_APP_NAME)

SCRIPT_TEMPLATE := NeovimOpener.applescript.in
SCRIPT_OUT      := NeovimOpener.applescript

PLIST_INNER_TEMPLATE := Info.Neovim.template.plist
PLIST_INNER_OUT      := Info.Neovim.plist

PLIST_OPENER_TEMPLATE := Info.NeovimOpener.template.plist
PLIST_OPENER_OUT      := Info.NeovimOpener.plist

ICON_PNG := icon.png
ICONSET  := $(APP_NAME).iconset
ICNS     := $(APP_NAME).icns

INSTALL_DIR := $(HOME)/Applications

.PHONY: all clear install

all: $(OPENER_APP)

# ---------- inner app (terminal runner) ----------
$(INNER_APP): nvim-launch $(ICNS) $(PLIST_INNER_OUT)
	rm -rf "$@"
	mkdir -p "$@/Contents/MacOS" "$@/Contents/Resources"

	cp nvim-launch "$@/Contents/MacOS/nvim-launch"
	chmod +x "$@/Contents/MacOS/nvim-launch"

	cp "$(ICNS)" "$@/Contents/Resources/$(ICNS)"
	cp "$(PLIST_INNER_OUT)" "$@/Contents/Info.plist"

	@echo "Built $(INNER_APP)"

# ---------- outer app (AppleScript droplet) ----------
$(OPENER_APP): $(INNER_APP) $(ICNS) $(PLIST_OPENER_OUT) $(SCRIPT_OUT)
	rm -rf "$@"
	osacompile -o "$@" "$(SCRIPT_OUT)"

	mkdir -p "$@/Contents/Resources"
	cp "$(ICNS)" "$@/Contents/Resources/$(ICNS)"
	cp "$(PLIST_OPENER_OUT)" "$@/Contents/Info.plist"
	rm -rf "$@/Contents/Resources/$(INNER_APP_NAME)"
	cp -R "$(INNER_APP)" "$@/Contents/Resources/"

	@echo "Built $(OPENER_APP)"

# ---------- generate AppleScript ----------
$(SCRIPT_OUT): $(SCRIPT_TEMPLATE)
	sed \
	  -e 's/__INNER_APP_BUNDLE__/$(INNER_APP_NAME)/g' \
	  $(SCRIPT_TEMPLATE) > $(SCRIPT_OUT)
	@echo "Generated $(SCRIPT_OUT)"

# ---------- generate Info.plists ----------
$(PLIST_INNER_OUT): $(PLIST_INNER_TEMPLATE)
	sed \
	  -e 's/__APP_NAME__/$(APP_NAME)/g' \
	  -e 's/__APP_ID__/$(APP_ID)/g' \
	  -e 's/__APP_ICON__/$(ICNS)/g' \
	  $(PLIST_INNER_TEMPLATE) > $(PLIST_INNER_OUT)
	@echo "Generated $(PLIST_INNER_OUT)"

$(PLIST_OPENER_OUT): $(PLIST_OPENER_TEMPLATE)
	sed \
	  -e 's/__APP_NAME__/$(APP_NAME)/g' \
	  -e 's/__APP_ID__/$(OPENER_ID)/g' \
	  -e 's/__APP_ICON__/$(ICNS)/g' \
	  $(PLIST_OPENER_TEMPLATE) > $(PLIST_OPENER_OUT)
	@echo "Generated $(PLIST_OPENER_OUT)"

# ---------- build .icns from icon.png ----------
$(ICNS): $(ICON_PNG)
	rm -rf "$(ICONSET)"
	mkdir "$(ICONSET)"

	sips -z 16   16   $< --out "$(ICONSET)/icon_16x16.png"
	sips -z 32   32   $< --out "$(ICONSET)/icon_16x16@2x.png"

	sips -z 32   32   $< --out "$(ICONSET)/icon_32x32.png"
	sips -z 64   64   $< --out "$(ICONSET)/icon_32x32@2x.png"

	sips -z 128  128  $< --out "$(ICONSET)/icon_128x128.png"
	sips -z 256  256  $< --out "$(ICONSET)/icon_128x128@2x.png"

	sips -z 256  256  $< --out "$(ICONSET)/icon_256x256.png"
	sips -z 512  512  $< --out "$(ICONSET)/icon_256x256@2x.png"

	sips -z 512  512  $< --out "$(ICONSET)/icon_512x512.png"
	sips -z 1024 1024 $< --out "$(ICONSET)/icon_512x512@2x.png" || true

	iconutil -c icns "$(ICONSET)" -o "$(ICNS)"
	@echo "Built $(ICNS)"

clean:
	rm -rf "$(OPENER_APP)" "$(INNER_APP)" "$(ICONSET)" "$(ICNS)" \
	       "$(PLIST_INNER_OUT)" "$(PLIST_OPENER_OUT)" "$(SCRIPT_OUT)"

install: $(OPENER_APP)
	mkdir -p "$(INSTALL_DIR)"
	rm -rf "$(INSTALL_DIR)/$(OPENER_APP)"
	cp -R "$(OPENER_APP)" "$(INSTALL_DIR)/"
	@echo "Installed to $(INSTALL_DIR)/$(OPENER_APP)"

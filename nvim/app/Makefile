APP_NAME          := Neovim
APP_ID            := com.jkorbmacher.neovim
OPENER_APP_NAME   := NeovimOpener
OPENER_APP_ID     := com.jkorbmacher.neovim.opener

NEOVIM_APP        := $(APP_NAME).app
OPENER_APP        := $(OPENER_APP_NAME).app

SCRIPT_LAUNCH     := NeovimLaunch.zsh

PLIST_NEOVIM_TEMPLATE  := Info.Neovim.template.plist
PLIST_NEOVIM_OUT       := Info.Neovim.plist

PLIST_OPENER_TEMPLATE  := Info.NeovimOpener.template.plist
PLIST_OPENER_OUT       := Info.NeovimOpener.plist

ICON_PNG   := icon.png
ICONSET    := $(APP_NAME).iconset
ICNS       := Neovim.icns

.PHONY: all clean install

all: $(NEOVIM_APP) $(OPENER_APP)

# ---------- Neovim.app (exec script app) ----------
$(NEOVIM_APP): $(SCRIPT_LAUNCH) $(ICNS) $(PLIST_NEOVIM_OUT)
	rm -rf "$@"
	mkdir -p "$@/Contents/MacOS" "$@/Contents/Resources"

	# executable script
	cp "$(SCRIPT_LAUNCH)" "$@/Contents/MacOS/nvim-launch"
	chmod +x "$@/Contents/MacOS/nvim-launch"

	# icon
	cp "$(ICNS)" "$@/Contents/Resources/$(ICNS)"

	# Info.plist
	cp "$(PLIST_NEOVIM_OUT)" "$@/Contents/Info.plist"

	@echo "Built $(NEOVIM_APP)"

# ---------- NeovimOpener.app (AppleScript droplet) ----------
$(OPENER_APP): NeovimOpener.applescript $(ICNS) $(PLIST_OPENER_OUT)
	rm -rf "$@"
	osacompile -o "$@" NeovimOpener.applescript

	mkdir -p "$@/Contents/Resources"

	# icon
	cp "$(ICNS)" "$@/Contents/Resources/$(ICNS)"

	# Info.plist (overwrite osacompile's plist)
	cp "$(PLIST_OPENER_OUT)" "$@/Contents/Info.plist"

	@echo "Built $(OPENER_APP)"

# ---------- Generate Info.plists from templates ----------
$(PLIST_NEOVIM_OUT): $(PLIST_NEOVIM_TEMPLATE)
	sed \
	  -e 's/__APP_NAME__/$(APP_NAME)/g' \
	  -e 's/__APP_ID__/$(APP_ID)/g' \
	  -e 's/__APP_ICON__/$(ICNS)/g' \
	  $(PLIST_NEOVIM_TEMPLATE) > $(PLIST_NEOVIM_OUT)
	@echo "Generated $(PLIST_NEOVIM_OUT)"

$(PLIST_OPENER_OUT): $(PLIST_OPENER_TEMPLATE)
	sed \
	  -e 's/__APP_NAME__/$(OPENER_APP_NAME)/g' \
	  -e 's/__APP_ID__/$(OPENER_APP_ID)/g' \
	  -e 's/__APP_ICON__/$(ICNS)/g' \
	  $(PLIST_OPENER_TEMPLATE) > $(PLIST_OPENER_OUT)
	@echo "Generated $(PLIST_OPENER_OUT)"

# ---------- Build .icns from icon.png ----------
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
	rm -rf "$(NEOVIM_APP)" "$(OPENER_APP)" "$(ICONSET)" "$(ICNS)" \
	       "$(PLIST_NEOVIM_OUT)" "$(PLIST_OPENER_OUT)"

# Install both apps into ~/Applications/Neovim/
install: $(NEOVIM_APP) $(OPENER_APP)
	mkdir -p "$(HOME)/Applications/Neovim"
	rm -rf "$(HOME)/Applications/Neovim/$(NEOVIM_APP)" \
	       "$(HOME)/Applications/Neovim/$(OPENER_APP)"
	cp -R "$(NEOVIM_APP)" "$(HOME)/Applications/Neovim/"
	cp -R "$(OPENER_APP)" "$(HOME)/Applications/Neovim/"
	@echo "Installed to ~/Applications/Neovim/"


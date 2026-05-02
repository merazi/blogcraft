# Blogcraft Makefile

PREFIX ?= $(HOME)/.local
BINDIR = $(PREFIX)/bin
MANDIR = $(PREFIX)/share/man/man1
APP_NAME = blogcraft
DIST_DIR = dist
BUILD_DIR = build

.PHONY: all build install uninstall clean help

all: build

build:
	@echo "🔨 Building $(APP_NAME) binary..."
	pyinstaller --onefile --name=$(APP_NAME) --clean \
		--add-data="style.css:." \
		--add-data="code_highlight.css:." \
		blogcraft.py

install: build
	@echo "🚚 Installing $(APP_NAME) to $(BINDIR)..."
	mkdir -p $(BINDIR)
	cp $(DIST_DIR)/$(APP_NAME) $(BINDIR)/$(APP_NAME)
	@echo "📄 Installing man page to $(MANDIR)..."
	mkdir -p $(MANDIR)
	cp blogcraft.1 $(MANDIR)/$(APP_NAME).1
	@echo "✅ Done! You may need to restart your terminal or run 'export PATH=\$$PATH:$(BINDIR)' if it's not in your PATH."

uninstall:
	@echo "🗑️  Uninstalling $(APP_NAME) from $(BINDIR)..."
	rm -f $(BINDIR)/$(APP_NAME)
	@echo "🗑️  Removing man page from $(MANDIR)..."
	rm -f $(MANDIR)/$(APP_NAME).1
	@echo "✅ Done!"

clean:
	@echo "🧹 Cleaning up build artifacts..."
	rm -rf $(BUILD_DIR) $(DIST_DIR) $(APP_NAME).spec

help:
	@echo "Blogcraft Build System"
	@echo ""
	@echo "Usage:"
	@echo "  make            - Build the binary (default)"
	@echo "  make install    - Build and install to $(BINDIR)"
	@echo "  make uninstall  - Remove installed files"
	@echo "  make clean      - Remove build artifacts"
	@echo "  make help       - Show this help message"
	@echo ""
	@echo "Make sure pyinstaller is installed!"

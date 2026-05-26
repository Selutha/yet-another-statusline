MON_SRC           := $(CURDIR)/claude/mon.py
CLAUDE_CONFIG_DIR ?= $(HOME)/.claude

demo:
	@python3 claude/statusline/demo.py

demo/img:
	@python3 claude/statusline/demo.py --snapshots demo/

test:
	@uv run pytest -q

statusline/test:
	@uv run python claude/statusline/demo.py

mon/install:
	@ln -sfv $(MON_SRC) "$(CLAUDE_CONFIG_DIR)/mon.py" || true

mon/run:
	uv run python claude/mon.py

.PHONY: demo demo/img test statusline/test mon/install mon/run

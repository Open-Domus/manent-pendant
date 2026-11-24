.PHONY: all test fit cad drawings power schematic board route clean

all: schematic board test fit drawings power cad

test:
	uv run pytest -q

fit:
	uv run python -m mechanical.pendant_mech.checks

drawings:
	uv run python -m mechanical.pendant_mech.drawings

cad:
	uv run python -m mechanical.pendant_mech.cad

power:
	uv run python tools/power_budget.py > /dev/null
	uv run python tools/space_budget.py

schematic:
	uv run python -m electrical.gen
	tools/kicad.sh
	uv run python -m electrical.gen.checks

board:
	uv run python -m electrical.gen.board
	tools/kicad.sh board

# Not part of `all`: needs Java and Freerouting (see tools/route.sh), takes minutes, and its
# result differs a little from run to run.
route:
	tools/route.sh

clean:
	rm -f mechanical/out/*.step mechanical/out/*.svg mechanical/out/fit-report.json

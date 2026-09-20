# vectorboundary-artifact

Benchmarking harness, measured data, generated figures, and research report
for **VectorBoundary**: learned RVV kernel-schedule dispatch for quantized
LLM inference on RISC-V. The code change itself lives in a separate fork:
**[Fican1/llama.cpp, branch `vectorboundary`](https://github.com/Fican1/llama.cpp/tree/vectorboundary)**
(see `VECTORBOUNDARY.md` there for the commit-by-commit summary).

Start here: **[VectorBoundary-Report.md](VectorBoundary-Report.md)** is the
full writeup (motivation, ten findings, results, direct numeric comparison
against six prior systems, all figures). The paper draft (DAC 2027 target)
is in `../paper-dac/`.

## Reproducing the measurements

Everything here measures **exact dynamic RISC-V instruction counts under
QEMU**, not wall-clock time (see `BENCHMARK-PROTOCOL.md` for why, and what
claims that does and doesn't support). Real-hardware validation is a
separate, not-yet-done step; see the report's Limitations section.

1. Build the toolchain image (riscv64 cross-compiler + QEMU 10 with plugin
   support; QEMU's `zvfh` support requires >=9, and Debian's packaged
   `qemu-user` lacks plugin support entirely):
   ```sh
   cd ../llama.cpp && docker build -t vb-riscv -f Dockerfile.riscv .
   ```
2. Cross-compile the fork (see `../llama.cpp/VECTORBOUNDARY.md` for the exact
   `cmake` invocation) and place a small Q4_0 GGUF model under `../models/`.
3. Compile the instruction-count plugin:
   ```sh
   docker run --rm -v "$PWD:/tools" vb-riscv gcc -shared -fPIC \
     $(pkg-config --cflags glib-2.0) -I/usr/local/include \
     /tools/insn_rvv.c -o /tools/libinsn_rvv.so
   ```
4. Run any sweep script, e.g. `sweep-insn.sh` (per-model instruction counts
   across VLEN 128/256/512/1024) or `sweep-shapes.sh` (the kernel-level shape
   grid the deployed cost model is fit on). Each writes a CSV; `eval-ranking.py`
   and the various `plot-*.py` scripts consume those CSVs to produce the
   tables and figures in the report.

## Layout

| Path | What |
|---|---|
| `*.md` | Protocol, baseline anchors, findings, and the full report (start with `VectorBoundary-Report.md`) |
| `insn_rvv.c` | QEMU TCG plugin: exact dynamic instruction classification |
| `cache.c` | QEMU cache-behavior plugin (from upstream QEMU `contrib/plugins`) |
| `sweep-*.sh` | Measurement scripts (instruction counts, cache misses, batch sweep, kernel-shape sweep, real-model-shape sweep) |
| `*.csv` | Raw measured data from each sweep |
| `assemble-dataset.py`, `eval-ranking.py` | Build the cross-model dataset and the leave-one-shape-out ranking evaluation |
| `plot-*.py`, `pubstyle.py` | Figure generation (shared style module + one script per figure) |
| `Dockerfile*` (in `../llama.cpp/`) | Toolchain images |

`papers/` (third-party PDFs we read for related-work numbers) and
`.vb-secrets/`/`gh/` (credentials) are intentionally not tracked; see
`BASELINES.md` for the citation details extracted from those papers.

## License

Code in this directory: MIT. Measured data and figures: released alongside
the paper on publication. This repo does not redistribute any third-party
copyrighted material (see `.gitignore`).

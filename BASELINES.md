# VectorBoundary 基线对比锚点表

> 生成日期: 2026-09-15。所有数字均于当日从一手来源 (arXiv abs/HTML、Crossref API、GitHub) 重新抓取核实;
> 无法核实的字段明确标注 **[未核实]**。原始三人提取清单中凡与一手来源冲突或查无出处的数字已剔除。
>
> 本项目三类主张: (A) schedule selection quality (top-k / oracle-gap / legality),
> (B) kernel & end-to-end speedup (等真实硬件), (C) instruction-count reduction (QEMU 精确动态指令数)。

---

## 1. 主表

| # | Paper | Venue | Metric | 他们的数字 | 他们的 baseline | 硬件 | 可比性 |
|---|-------|-------|--------|-----------|----------------|------|--------|
| 1 | **V-Seek** (Poveda Rodrigo et al., arXiv:2503.17422; poster: CF'25, DOI 10.1145/3719276.3727954) | CF 2025 (poster) + arXiv | token generation / prefill throughput (tokens/s); speedup vs 未优化 llama.cpp | tg **4.32 / 2.29 tok/s**, pp **6.54 / 3.68 tok/s** (DeepSeek-R1-Distill-Llama-8B / Qwen-14B), **up to 2.9×/3.0×** vs baseline (Fig. 4); Llama-7B: **6.63 / 13.07 tok/s = 4.3×/5.5×**; ablation: 优化 kernel **+38.3%** avg GOPS (Fig. 2), Clang 19 vs GCC 13.2 **+34% tg / +25% pp** (Fig. 3) | out-of-box llama.cpp (GGML 默认 kernel + OpenBLAS), Q4_0, 64 threads | Milk-V Pioneer / Sophon SG2042, 64× XuanTie C920, 128 GB DRAM; C920 实现 vector **0.7.1 draft** (厂商文档事实, 论文未写明版本) | **same-axis** (同为 llama.cpp+Q4_0+RISC-V; 但 ISA 0.7.1≠RVV 1.0, wall-clock≠insn count) |
| 2 | **xDSL RVV lowerings** (Lei, Martínez, Castelló, arXiv:2603.17800) | arXiv 2026-03 | GEMM kernel GFLOPS (FP); % improvement vs OpenBLAS | **up to 12.2 GFLOPS vs baseline 5.1 GFLOPS**; **10–35%** improvement across BERT-Large 派生 workloads | OpenBLAS (方阵 + transformer shapes) | **Banana Pi BPI-F3 (SpacemiT K1, VLEN=256, RVV 1.0)** 与 K230; 代码开放性 **[未核实]** | **direct (硬件轴)** — 与我们申请的 BPI-F3 完全同板; 但 FP GEMM ≠ Q4_0/Q8_0 量化 GEMV, baseline 是 OpenBLAS 而非 llama.cpp |
| 3 | **VectorWeaver** (Yang et al., ACM TACO 23(1):35, DOI 10.1145/3799719) | TACO 2026 | microkernel speedup; end-to-end inference throughput 提升 | microkernel **up to 24×** vs baseline implementations; end-to-end **up to 5.2×** throughput (Crossref abstract; 正文 table/figure 编号 **[未核实, ACM 付费墙]**) | "baseline implementations" (具体定义待正文核实) | TH1520 (C910, vector 0.7.1 draft) + Sophon SG2044 (RVV 1.0, 厂商文档); Gemma3 / Qwen3 270M–4B; 代码 **[未核实]** | **same-axis** — 概念上最接近的竞品 (RISC-V LLM 推理自动优化框架); 但报 wall-clock, 且 baseline 定义未知 |
| 4 | **TLP** (Zhai et al., ASPLOS 2023, arXiv:2211.03578, DOI 10.1145/3575693.3575737) | ASPLOS 2023 | ① top-1/top-5 score (TenSet); ② search-time speedup | ① Table 5 (vs TenSet MLP): Platinum 8272 top-1 **0.9194 vs 0.8748**, top-5 **0.9710 vs 0.9527**; E5-2673 **0.8941/0.9633 vs 0.8332/0.8977**; EPYC 7452 **0.9055/0.9494 vs 0.8510/0.9175**; GPU 行 (K80/T4) 提取值互有胜负, **列向可能被抽取模型转置, 引用前人工复核 PDF**。② search time **9.1× (CPU) / 3.0× (GPU)**; MTL-TLP **4.7×/2.9×** 仅用 7% 目标硬件数据 (abstract) | TenSet MLP cost model / Ansor 原生 cost model | TenSet 数据集; search-time 实验: i7-10510U (CPU 侧), Platinum 8255C + Tesla T4 (GPU 侧); 代码: github.com/zhaiyi000/tlp (已 archive, 后继 TLM) | **same-axis (指标轴)** — top-k score 定义可直接复用; 但对象是 TVM tensor program, 非 RVV 量化 kernel |
| 5 | **Ansor** (Zheng et al., OSDI 2020, arXiv:2006.06762) | OSDI 2020 | end-to-end network speedup vs 最强替代框架 | **up to 3.8× (Intel CPU) / 2.6× (ARM CPU) / 1.7× (NVIDIA GPU)**, Fig. 9 | PyTorch v1.5, TensorFlow v2.0, TensorRT v6.0, TFLite v2.0, AutoTVM (commit 69313a7), Halide auto-scheduler, FlexTensor | Intel Platinum 8124M (18C) / 8269CY (20C); Cortex-A53 (RPi 3b+); V100; 代码已并入 Apache TVM (auto_scheduler) | **reference-only (speedup 轴) / same-axis (tuner-选择框架定位)** |
| 6 | **Meta-Schedule** (Shao et al., NeurIPS 2022, arXiv:2205.13603) | NeurIPS 2022 | end-to-end workload speedup (来自 search space 扩展) | **48%** speedup on end-to-end deep learning workloads (abstract) | 覆盖 SOTA 框架搜索空间后的可扩展增益 | 论文 abstract 未给硬件细节; 代码已并入 Apache TVM | **reference-only** |
| 7 | **T-MAC** (Wei et al., EuroSys 2025, arXiv:2407.00088) | EuroSys 2025 | mpGEMM throughput; energy; tokens/s | **up to 4×** throughput、**70%** energy reduction vs llama.cpp; BitNet-b1.58-3B **30 tok/s (1 core) / 71 tok/s (8 cores)** on M2-Ultra; **11 tok/s** on Raspberry Pi 5 | llama.cpp (含其低比特 kernel) | Apple M2-Ultra, Raspberry Pi 5 (ARM); 代码: github.com/microsoft/T-MAC | **reference-only** — 同为"低比特 CPU GEMV vs llama.cpp", 但 ARM/x86 + LUT 方法, 非 RVV, 非 schedule selection |
| 8 | **TenSet** (Zheng et al., NeurIPS 2021 Datasets & Benchmarks) | NeurIPS 2021 D&B | 数据集规模 (top-k score 指标惯例源头) | **51,577,248** 条 program performance records, **6** 个硬件平台 (repo README) | — | x86/ARM CPU + GPU 共 6 平台; 代码/数据: github.com/tlc-pack/tenset | **reference-only** — 我们的 top-k 指标定义应引用其惯例 |
| 9 | **gem5 + RISC-V vector 仿真基准** (Ramírez et al., ACM TACO 17(4), 2020, DOI 10.1145/3422667) | TACO 2020 | 仿真器驱动的 vector 架构评估 (指令级动态指标) | 7 个 data-parallel 应用组成的 benchmark suite; 具体数字与本项目不对齐, 不引用其数值 | 标量/不同 vector 配置 | gem5 + 参数化 RVV 模型 | **reference-only (方法论先例)** — 证明"无真实硬件时用指令级仿真评估 RVV 设计"是 TACO 级别可接受的方法 |

---

## 2. 按三类主张分组的对比模板

### 2a. Selection quality — 对齐 TLP / TenSet / Ansor 的指标

**他们报什么**: TLP 的 top-k score 定义 (TLP §evaluation):
`top-k = Σ min_latency / Σ min(latency_{i}, 1≤i≤k)` 按 workload 加权 — 即 "模型排名前 k 的候选中最好那个, 相对真实最优 (oracle) 的 latency 比值", **oracle = 1.0**。TLP 在 CPU 平台把 top-1 从 ~0.83–0.87 (TenSet MLP) 提到 ~0.89–0.92, top-5 提到 ~0.95–0.97。

**我们应报的数** (全部今天可产出, 无需真实硬件):
1. **top-1 / top-3 / top-5 score**, oracle 归一 (与 TLP 完全同定义, 只是 latency 换成我们的 cost 轴: QEMU insn/token 或 emulated wall clock), 分 held-out shape / held-out hardware-profile 两个 split。已有: held-out shape top-5 **0.143 → 0.707**, held-out hardware top-5 **0.060 → 0.474** (calibrated proxy vs base)。
2. **oracle-gap of upstream rule**: 上游 VLEN-matched 选择规则仅达 oracle 的 **71.6%** (VLEN=1024) — 这是 TLP 式指标下"现有规则有多差"的直接证据, TLP/Ansor 均无此角度 (它们评自己的 cost model, 不评厂商启发式规则)。
3. **invalid/illegal rate**: legality mask 命中的非法 schedule 占比 + 抓到的上游真实 correctness bug (TLP/Ansor 无 legality 维度, 是我们的增量)。

**对齐话术**: "we adopt the top-k score metric standard in learned cost models (TenSet; TLP), replacing measured latency with exact dynamic instruction counts as the ranking target."

### 2b. Kernel / end-to-end speedup — 对齐 V-Seek / xDSL / VectorWeaver 需要的硬件条件

**他们的条件**: V-Seek = SG2042 (vector 0.7.1, 64C, server-class), wall-clock tok/s, Q4_0, 64 threads;
xDSL = **BPI-F3 (K1, VLEN=256, RVV 1.0)** + K230, FP GEMM GFLOPS vs OpenBLAS;
VectorWeaver = TH1520 + SG2044, LLM e2e throughput。

**我们需要什么才能进这张表**:
- **BPI-F3 (K1, VLEN=256)** 到手 → 可报: ① Q4_0/Q8_0 GEMV/GEMM kernel GFLOPS/带宽利用率 (与 xDSL 同板同 VLEN, 但注明量化 vs FP 不可直接比数值, 只能比"相对各自 baseline 的提升"); ② llama.cpp e2e tok/s (tg/pp), selection-rule-A vs upstream rule vs oracle-schedule — 这一行可与 V-Seek 的 2.9×/3.0× 同轴叙述 (都是"vs out-of-box llama.cpp"), 但硬件档次和 ISA 版本不同, 只能 same-axis 不能 head-to-head。
- **SG2042** 到手 → 与 V-Seek 同板复现其 baseline 口径 (Q4_0, 64 threads), 报"正确 schedule selection 带来的 tok/s 增量" — 这是唯一可能 head-to-head 的格子; 注意 SG2042 是 0.7.1 draft, 我们 RVV 1.0 kernel 需经 xtheadvector 路径或退化, 论文中必须写明。
- 未拿到硬件前: **不报任何 speedup**, 只报 insn/token 与 emulated ranking, 并引用 gem5/TACO 2020 作为 simulator-first 方法论先例。

### 2c. Instruction-count reduction — 先例与定位

**先例**: ① 体系结构文献中 dynamic instruction count 是标准仿真期指标 (gem5+RVV, TACO 2020, DOI 10.1145/3422667); ② QEMU TCG plugin 的 insn 计数在 RISC-V 工具链/内核社区是常规手段。**但没有任何 LLM-kernel 论文把 "instructions per generated token" 作为 headline 指标** — 检索 (arXiv, 2026-09-15) 未发现先例, 这是空白也是风险。

**定位建议**:
- 把 insn/token 定位为 **exact, deterministic, VLEN-parametric 的 cost 轴** (QEMU 下逐条精确, 无测量噪声), 而非 latency 的替身;
- 用我们已观察到的 **ranking inversion** (insn count 排名 ≠ emulated wall clock 排名) 主动说明它不是 latency proxy, 从而把"等硬件校准"变成 feature 而非缺陷;
- 我们的数: decode insn/token 削减 **2.01× (VLEN=256, 16x1) 至 6.07× (VLEN=1024, 64x1)** vs non-repacked baseline; prefill **3.58×–5.63×** (vb-tools/insn-tables.md)。可与 V-Seek 的 "+38.3% kernel GOPS" 并列为 kernel-level 证据, 但注明轴不同 (insn count vs GOPS)。

---

## 3. 每篇 comparability 注意事项

1. **V-Seek**: ① SG2042 = vector **0.7.1 draft**, 我们 = RVV 1.0 → kernel 不通用, speedup 不可搬; ② 其 baseline 是"llama.cpp+OpenBLAS 默认", 上游 llama.cpp 此后已并入 RVV 优化, "vs baseline 2.9×" 的 baseline 与我们 fork 的 baseline 不是同一版本 → 只能各自报 vs 各自 baseline; ③ server-class 64C vs 我们 edge 单板; ④ 论文未附自有代码链接。
2. **xDSL RVV (2603.17800)**: 同板 BPI-F3 但 **FP32 GEMM vs 我们 Q4_0/Q8_0 量化 GEMV** — GFLOPS 不可与量化 kernel 直接比 (量化没有统一 FLOP 记账); baseline 是 OpenBLAS 而非 llama.cpp; 其 10–35% 是编译器 lowering 收益, 与我们 schedule selection 收益属不同来源, 可在 related work 并列不可入同一列。
3. **VectorWeaver**: 摘要级数字 (24×/5.2×) 的 baseline 定义未核实 (付费墙) — "24× microkernel" 很可能 vs 标量/naive 实现而非 vs 已向量化 llama.cpp, 引用时必须注明; TH1520 (0.7.1) 与 SG2044 (RVV 1.0) 混合平台; 模型是 Gemma3/Qwen3 270M–4B, 与我们模型不同。作为最近邻竞品, 论文中应明确"我们做 selection, 它做 generation"的正交性。
4. **TLP**: top-k score 可复用, 但其 latency 来自真实测量、我们的来自 QEMU insn/emulated clock → 指标同形不同底, 数值不能同列排名, 只能"我们在自己的 oracle 下达到 X, TLP 在其 oracle 下达到 Y"的平行表述; **本表 GPU 行数字提取存疑, 引用前人工复核原 PDF Table 5**。
5. **Ansor / Meta-Schedule**: x86/ARM/GPU + FP 网络, 与 RVV 量化 kernel 无共同硬件/数值轴; 仅用于定位 ("auto-tuner 搜索空间/成本模型" 谱系) 与 search-cost 叙事。
6. **T-MAC**: 同为"vs llama.cpp"但 ARM/x86 且方法是 LUT 替代 mpGEMM (改 kernel 本身), 我们是选择既有 kernel schedule — 收益来源正交, 只作 related work 定位, 数值不入对比列。
7. **TenSet / gem5-TACO**: 纯方法论/指标引用, 不比数字。

---

## 4. 最终论文 Table X 草案

**Table X: Schedule selection quality and per-token cost on RVV 1.0 (Q4_0 decode).**
标注: [今] = 今天即可填 (QEMU/proxy 产出); [硬] = 等 BPI-F3 / SG2042 免费硬件到位。

| 方法 (行) | insn/token ↓ VLEN=256 | insn/token ↓ VLEN=1024 | top-5 score (held-out shape) ↑ | top-5 score (held-out hw) ↑ | % of oracle ↑ | illegal picks | tok/s BPI-F3 (K1) | tok/s SG2042 |
|---|---|---|---|---|---|---|---|---|
| non-repacked baseline | 115.79 M [今] | 115.36 M [今] | — | — | — | — | [硬] | [硬] |
| upstream VLEN-matched rule | [今] | [今] | [今] | [今] | **71.6% @1024** [今] | ≥1 real bug [今] | [硬] | [硬] |
| best static schedule (oracle) | 49.87 M (8x8) [今] | 18.99 M (64x1) [今] | 1.0 (def.) | 1.0 (def.) | 100% | 0 | [硬] | [硬] |
| base proxy ranking | [今] | [今] | 0.143 [今] | 0.060 [今] | [今] | [今] | — | — |
| **VectorBoundary (calibrated + legality mask)** | [今] | [今] | **0.707** [今] | **0.474** [今] | [今] | 0 [今] | [硬] | [硬] |

配套第二张定位表 (related work, 不同轴不排名): V-Seek (2.9×/3.0× tok/s, SG2042, vs 原始 llama.cpp) / xDSL (12.2 vs 5.1 GFLOPS, BPI-F3, vs OpenBLAS) / VectorWeaver (5.2× e2e, TH1520+SG2044) / T-MAC (4×, ARM) — 每行标注 baseline 口径与 ISA 版本, 明示不可 head-to-head 的原因。

**今天就能填满**: 全部 insn/token 列 (vb-tools/insn-tables.md 已有), top-k 两列, oracle-gap 列, legality 列。
**等硬件才填**: 两列 tok/s (+ 计划中的 cache-miss / batch-boundary 实测曲线); SG2042 列另需 0.7.1 兼容路径说明。

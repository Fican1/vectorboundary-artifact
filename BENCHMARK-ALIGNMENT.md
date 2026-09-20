# VectorBoundary — Benchmark 对齐表 (BENCHMARK-ALIGNMENT)

> 生成: 2026-09-15。来源: papers/ 目录 10 篇论文全文提取 (全部拿到 PDF: 8 篇 arXiv, VectorWeaver 已有全文, V-Seek/HybriMoE 本次 pdftotext 提取)。
> 配套文档: DAC-COMPARABLES.md (定位/判级), BASELINES.md (数字锚点), BENCHMARK-PROTOCOL.md (我们的采集协议)。

## 1. 对齐总表

| 论文 | Venue | Workloads/模型 | Benchmark harness | Baseline 精确定义 | 平台 (真机/仿真器+精度) | 指标 | 代码 |
|---|---|---|---|---|---|---|---|
| **Peccia** RVV+MetaSchedule | ICCAD 2025 | 方阵 matmul m=n=k∈{16..512} (int8 QNN 式/fp16/fp32); 全模型: MLPerf Tiny ×4, MobileNetV2, ResNet18, BERT-tiny (seq64), DCGAN, MobileLLM-125M | TVM MetaSchedule 调优 (matmul 100 iter, 全网 200–400 candidates); microTVM+Zephyr (FPGA) / TVM runtime (板卡); **QEMU TCG plugin 记录指令 trace** | ① Non-tuned (GCC 14 `-Os` 标量); ② GCC 14 `-O3` autovec; ③ muRISCV-NN 手写 RVV 库; BPI-F3 上: LLVM 19 无向量 / LLVM 19 autovec | **混合**: ZCU102 FPGA (Rocket+Saturn RVV 1.0, VLEN 256/512/1024, 100 MHz) + 真机 BPI-F3 (K1, VLEN=256, 1.6 GHz); QEMU 仅作指令分析 | latency (ms), speedup %, **总动态指令数 + RVV 分组占比**, code size | 声称开源, 文中无 URL |
| **Pelke** insn-accurate autotuning | DAC 2025 | Conv2D+Bias+ReLU ×5 组 ResNet shapes (如 N1 H224 W224 CO64 CI3 K7 s2; H56 CO64/128 K3 …); 每组 500 个 Auto-Scheduler schedules | TVM AutoTVM/Auto-Scheduler + 自定义 SimulatorRunner; 真机参考: Nexe=15 取中位, 1s cooldown | 真机实测 run time 作 ground truth; 预测器互比 LinReg/DNN/Bayes/XGBoost | **仿真为主体**: gem5 atomic SimpleCPU (**instruction-accurate, 非 cycle-accurate**) + 参数化 cache; 真机仅校准: Ryzen 7 5800X / RPi4 A72 / **SiFive U74 (无 RVV)** | Etop1 (%), **Rtop1 (top-k 排名 %)**, Qlow/Qhigh 排序质量, 并行仿真加速 K | 未提及 |
| **T-SAR** | DATE 2026 | BitNet-b1.58 125M–100B; Llama-b1.58-8B, Falcon3-b1.58-10B; kernel shapes N×K×M: N=128 (GEMM)/N=1 (GEMV) × {768×3072, 3072×768, 768×768, 2560×6912, 6912×2560, 2560×2560, 8912×45568, 45568×8912, 8912×8192} | 自研 C++/inline-asm kernels (GCC 9.4.0); prefill N=128 batch=1, decode steady-state; 线程 {16,8,4} | Bitnet.cpp TL-2, T-MAC (SOTA LUT 法); 跨平台: Jetson AGX Orin GPU + llama.cpp | **纯仿真推理**: gem5-AVX 20.1 DerivO3CPU (**cycle-accurate O3**, 建模 Ryzen 9950X/7840U/Intel N250, x86 非 RISC-V); TSMC 28nm 综合报开销; 无现货硅片 (自定义 ISA) | prefill latency, decode tokens/s, 内存请求量 (MB), area/power (+1.4%/+3.2%), J/token; GEMM 5.6–24.5×, GEMV 1.1–86.2× | 未提及 |
| **HybriMoE** | DAC 2025 | Mixtral-8x7B-Instruct, DeepSeek-V2-Lite-Chat, Qwen2-57B-A14B-Instruct; Marlin 4-bit; 输入 ~32/128/512/1024 tokens (MT/Vicuna/ChatGPT-Prompts) | 自研系统 (kTransformers + llama.cpp kernels); GPU expert cache ratio 25/50/75% | llama.cpp (静态层映射 hybrid), AdapMoE (GPU-centric SOTA), kTransformers (hybrid SOTA) | **真机**: RTX A6000 + Xeon Gold 5220R (限 10 核模拟 edge) | TTFT (prefill), decode 吞吐/TBT, cache hit rate; **1.33×/1.70× vs kTransformers** | github.com/PKU-SEC-Lab/HybriMoE |
| **AdapMoE** | ICCAD 2024 | Mixtral-8x7B / 8x22B, hqq 4bit 与 4+2bit; MMLU/ARC-C 精度, MT-Bench 提示词 | 自研 (改造 Mixtral-offloading, CUDA streams); per-token latency | Mixtral-offloading (作者修改版, 比开源版快 2×), Pre-gated MoE, 整层 offloading (DeepSpeed/FlexGen 式) | **真机**: RTX 4090, A6000 | expert 激活 −25%, 精度无损, per-token latency (0.392→0.288 s), 1.35×/1.36× | 未提及 |
| **MCUBERT** | ICCAD 2024 | BERT-tiny/BERT-mini (NAS 压缩 embedding), GLUE/MNLI, seq ≤512, batch=1 | 自研 MCU 推理引擎 + 自研 SIMD kernel (SMLAD); 板上实测 latency/peak-mem | CMSIS-NN; Burrello et al. 2021 (COINS, MCU transformer 引擎); 精度侧 adaptive embedding/FWSVD | **真机**: NUCLEO-F746 (320KB SRAM)/F767/H7A3ZIQ (Cortex-M7) | 模型大小 5.7×/3.0×↓, peak mem 3.5×/4.3×↓, latency 1.5×/1.3×↓, MNLI 精度 | 未提及 |
| **Squat** | ICCAD 2025 | LLaMA-58M, GPT2-97M; W8A8/W4A8/W4A4 + token 自适应混精 (4:8 比例 1:3/1:1/3:1); BLiMP zero-shot, (Super)GLUE 微调 | 自研 SIMD MKMP multiplier kernel; latency = 1000 次迭代均值, seq 128, 全核多线程, ms/Token | FP16 推理 (latency 轴); QAT 精度轴: NIPQ, PACT, LLM-QAT | **真机**: OnePlus 11 (Snapdragon 8 Gen 2) + RPi 5 (BCM2712 Cortex-A76) — ARM SIMD | BLiMP/GLUE 精度 (W4A8 69.4% vs FP16 69.7%), ms/Token, **up to 2.37× vs FP16** | github.com/shawnricecake/squant |
| **V-Seek** | arXiv (CF'25 poster) | Llama-7B, DeepSeek-R1-Distill-Llama-8B, -Qwen-14B; **Q4_0**; prompt 22 tokens, tg 平均 256 tokens | **llama.cpp** (自有 GEMV kernel + Xuantie GCC 10.4 编 kernel, Clang 19/GCC 13.2 编框架); NUMA 4 策略; 单核 GOPS microbench | out-of-box llama.cpp (GGML 默认 + OpenBLAS), 同板 PerfXLM (1.65×) | **真机**: Milk-V Pioneer / SG2042, 64× C920, **RVV 0.7.1 draft**, 128GB | tok/s (tg/pp), GOPS (+38.3% avg), 能效 vs EPYC 7742; tg 4.32/pp 6.54 tok/s (8B), 2.9×/3.0× | 无自有代码链接 |
| **xDSL-RVV** | arXiv 2026-03 | FP32 GEMM: 方阵 1000–5000 + BERT-Large 层 shapes (m,n,k): (1024,384,1024) (384,384,64) (64,384,384) (4096,384,1024) (1024,384,4096) | 自研 microbench (1500 runs) + gemm_blis_family 框架 (200 runs); 单核单精度 | OpenBLAS v0.3.31 (K230: ZVL128B 8×8 kernel; BPI: ZVL256B 16×8 kernel); g++-14 | **真机**: CanMV-K230 (C908, RVV 1.0, VLEN=128) + **BPI-F3 (K1, RVV 1.0, VLEN=256)**, 均 1.6 GHz 单核 | GFLOPS: microkernel 峰值 8.1 (K230)/16.2 (BPI); gemm 方阵 +10–15% (K230), BPI 8.3–8.6 vs 6.1–7.0; BERT 层 +10–47%, BPI 个别层 >2× | github.com/JieGH/RVV_code_gen_via_MLIR_xDSL |
| **VectorWeaver** | TACO 2026 | Qwen3-0.6B/1.7B, Gemma3-270M/4B, Q8/Q4; microbench: vec-dot Q8_0, row-quant, RMSNorm, GEMM, SiLU | **llama.cpp** 集成; **PP512/TG128** 约定 (tokens/s); llama-perplexity WikiText-2 PPL 验证保真 | microbench: Scalar C++ `-O1`/`-O3`, 手写 RVV intrinsics; e2e: Ollama, **llama.cpp (Scalar) 官方 release**, VectorWeaver(Intr); 消融: PP-Best/TG-Best 静态 | **真机**: LicheePi 4A/TH1520 (4×C910, RVV **0.7.1**, 1.85 GHz) + SG2044 (64×C920v2, **RVV 1.0**, 2.6 GHz) | microkernel up to 24× (vs 标量); e2e up to **5.25× (PP512)**, Gemma3-270M Q8 TG 3.35× (33.85 vs 10.12 tok/s); XGBoost 跨芯片迁移 75% acc | 未发布 |
| **VectorBoundary (我们)** | 目标 DAC 2027 | SmolLM2-135M/360M, Qwen2.5-0.5B; **Q4_0/Q8_0/Q4_K_M** GGUF; GEMM/GEMV kernel 级 + e2e; batch 1–8 | **llama.cpp** fork; QEMU 10 差分指令计数 (自研 TCG plugin, `-cpu max,vlen=128..1024`); cache plugin; 真机 llama-bench (计划) | `norepack` (`GGML_CPU_REPACK=OFF`, 仍含 RVV 通用 vec_dot), upstream VLEN-matched 选择规则, **oracle 静态 schedule** | 当前: QEMU 10 (instruction-accurate, 确定性); 计划真机: BPI-F3 (K1, VLEN=256, RVV 1.0) + SG2042 (0.7.1) | insn/decode-token (2.01–6.07× ↓), insn/prefill-token (3.58–5.63×), top-k score, oracle-gap 71.6%, legality/illegal rate; 真机后: pp/tg tok/s | fork 未公开 (待定) |

## 2. "谁有真硬件" 普查

**分类** (推理性能数字的来源):
- **纯真机**: HybriMoE (A6000+Xeon), AdapMoE (4090/A6000), MCUBERT (3× NUCLEO), Squat (OnePlus 11 + RPi5), V-Seek (SG2042), xDSL-RVV (K230+BPI-F3), VectorWeaver (TH1520+SG2044)。
- **混合**: Peccia — FPGA 原型 (Saturn, 可变 VLEN) + 真机 BPI-F3 双轨, QEMU 指令 trace 仅作**分析证据**; Pelke — **gem5 instruction-accurate 仿真是方法主体**, 真机 (含无 RVV 的 SiFive U74) 仅提供 ground-truth 校准。
- **纯仿真推理**: T-SAR — gem5-AVX cycle-accurate; 唯一无真机推理数字者, 但其自定义 ISA 本无现货硅片可跑 (另有 28nm 综合 + 真机 Jetson 对照组)。

**四大会议 (DAC/ICCAD/DATE) 7 篇中**: 6/7 (86%) 含真机成分; 纯仿真仅 T-SAR 1 篇且有"硬件不存在"的豁免理由。**对我们的推断**:
1. QEMU 指令数作为**分析/排序轴有两个直接先例**: Peccia (ICCAD'25, QEMU TCG plugin 指令 trace 佐证 schedule 质量) 和 Pelke (DAC'25, 整篇论文 = "instruction-accurate 仿真统计排序 + top-k 真机复测", DAC 已接收)。
2. 但我们的目标硬件 (BPI-F3/SG2042) 是量产可购的 stock RVV 芯片, 无 T-SAR 式豁免 → **QEMU-only 投稿大概率被拒**; "QEMU insn (Tier 1) + 真机 tok/s (Tier 3)" 双层结构完全落在审稿人已接受的模式内, 且 Pelke 恰好提供了 "仿真排序、真机只验证 top 2–3%" 的方法学引用。
3. 写法上引用链: gem5-TACO 2020 (方法论) + Pelke DAC'25 (同会议先例) + Peccia ICCAD'25 (QEMU insn trace 同工具先例)。

## 3. Benchmark 对齐行动清单

| # | 行动 | 对齐对象 | 成本 |
|---|---|---|---|
| 1 | llama-bench 主报告统一 **`-p 512 -n 128` (PP512/TG128)**; 协议网格 pp{32,128,512}×tg{8,32,128} 保留为附录 | VectorWeaver (唯一同栈竞品用此约定); V-Seek 口径 (22-token prompt/256 gen) 在 SG2042 上另跑一组复现其 baseline | 需真机 (QEMU 禁报时间) |
| 2 | 增加 **Qwen3-0.6B Q4_0/Q8_0** 模型 (GGUF 现成) 进 QEMU 指令数网格 | 与 VectorWeaver 模型族直接重叠 (其 Qwen3-0.6B 在 SG2044 有 PP512/TG128 图) | QEMU 可跑 |
| 3 | kernel 级 shape 扫描补 **方阵 16..512** (Q4_0/Q8_0 GEMV/GEMM, 各 VLEN 的 insn count) | Peccia 的 matmul 网格 (16–512); 其 QEMU 指令分组图 (load/store/mul-add/config) 与我们 v_arith/v_load/v_store/vsetvl 分类几乎同构, 可做同轴图 | QEMU 可跑 |
| 4 | BPI-F3 上跑 **xDSL 的 5 个 BERT-Large shapes** (1024,384,1024) 等, 报"相对各自 baseline 提升%" (量化 vs FP32 不比绝对 GFLOPS) | xDSL-RVV 同板同 VLEN | 需真机 (BPI-F3) |
| 5 | 报 **selection 决策开销 (µs) vs 调优成本**: Peccia 每 op 100 iter × 9–12 s (~20 min), 全网 200–400 candidates; Pelke 每组 500 schedules × gem5 | Peccia/Pelke 的 "方法自身开销" 惯例 | QEMU/host 可跑 |
| 6 | top-k 指标表述对齐 **Pelke 的 Rtop1/Etop1**: 补报 "oracle schedule 落在我们排序 top-k% 的位置" (Rtop1 式) 与现有 TLP 式 top-5 score 并列 | Pelke (DAC 同会), TLP/TenSet | QEMU 可跑 (现有 dataset.csv 直接算) |
| 7 | **WikiText-2 PPL 不变性验证** (llama-perplexity, 135M 模型即可) + bit-exact 声明 + legality bug case study | VectorWeaver 用 PPL 验保真; AdapMoE/Squat "无精度损失" 惯例 | QEMU 可跑 (慢但一次性) |
| 8 | 真机 **thread-scaling 曲线** (1..核数) + batch 1–8 曲线 | T-SAR Fig.10, V-Seek Fig.3, HybriMoE cache-ratio 扫描 | 需真机 |
| 9 | T-SAR 的超大 K×M shapes (8912×45568 级) 不必复刻 (BitNet 专属); 在 related work 注明其 shapes 来自 BitNet 层, 与我们 SmolLM2/Qwen shapes 不同轴 | T-SAR | 无需跑 |
| 10 | Squat 的 LLaMA-58M/GPT2-97M 为自训 SLM 无公开 GGUF, 不加; 我们 SmolLM2 已覆盖同级别 (Squat 引言同引 SmolLM2) | Squat | 无需跑 |

## 4. Baseline 对齐矩阵

| 我们的 baseline | 定义 | 对应论文 baseline | 强弱判断 |
|---|---|---|---|
| `norepack` | `-DGGML_CPU_REPACK=OFF`, 走非 repack 的 `ggml_vec_dot` 通用路径 (**仍含 RVV intrinsics, 非标量**) | VectorWeaver "llama.cpp (Scalar) 官方 release" (标量 C++); Peccia "Non tuned" (GCC `-Os` 标量); V-Seek "out-of-box llama.cpp+OpenBLAS" (2025 年初无 RVV 优化的旧上游) | **他们的更弱**。VectorWeaver 的 24×/5.25× 与 Peccia 的 84% 均以纯标量为分母; 我们最弱的 baseline 已向量化 → 我们的倍数天然显小, 论文须显式声明 "our weakest baseline is already RVV-vectorized", 这是严谨性优势, 写作时主动对比 |
| `upstream rule` (default) | repack 构建, 上游 VLEN-matched schedule 选择逻辑 (2026 年含全部社区 RVV 优化) | HybriMoE 的 kTransformers (SOTA 系统), T-SAR 的 Bitnet.cpp TL-2/T-MAC (SOTA kernel), MCUBERT 的 CMSIS-NN (vendor SIMD 库), Peccia 的 muRISCV-NN/LLVM-autovec | **同级 (SOTA-as-baseline)**。这是四大会议认可的"最强现有方案"格; 我们对其量化出 71.6% oracle-gap, 相当于 Peccia 证明 autovec/手写库次优的角色 |
| `oracle` (best static schedule) | 逐 config 穷举后的最优静态 schedule, top-k 归一分母 | Pelke 的 tref 最优样本 (Rtop1 定义的分母); TLP/TenSet 的 oracle=1.0 惯例; **其余 8 篇均无 oracle 上界** | **我们独有/更强**。除 Pelke 外, 本表没有论文报告 "离 oracle 还差多少"; speedup-only 论文 (V-Seek/VectorWeaver/Squat) 无法回答 "还剩多少空间"。这是我们相对全表的方法学差异点 |

**弱 baseline 点名** (写论文可用): VectorWeaver (标量官方版), Peccia 的 speedup 基准 (`-Os` 标量; 但其另有 muRISCV-NN 强对照), V-Seek (旧版未优化 llama.cpp), Squat (FP16 分母)。**强 baseline 看齐对象**: HybriMoE (kTransformers), T-SAR (TL-2/T-MAC), MCUBERT (CMSIS-NN) — 我们的 upstream-rule 属于此格, 且额外有 oracle 封顶。

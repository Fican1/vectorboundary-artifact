# DAC 2027 可比论文调研 — 四大 EDA 会议 (DAC / ICCAD / DATE / ASP-DAC) 2024–2026

> 项目: **VectorBoundary** — 面向量化 LLM kernel (Q4_0/Q8_0 GEMM/GEMV) 的 RVV 1.0 **schedule selection** (非 generation), 基于 llama.cpp。
> 证据链: QEMU 精确动态指令数 (2–6x 差距)、vendor 选择规则 oracle-gap 71.6%、legality mask 捕获真实正确性 bug、batch=4 处 GEMV→GEMM 边界台阶、cache compulsory-traffic wall、learned ranking 评估进行中、BPI-F3/SG2042 实机验证计划中。
> 验证方式: 每条均于 2026-09-15 通过 arXiv abs 页 + OpenAlex/DOI 复核 venue 与关键数字。**未发现 hallucination 条目**; 但 V-Seek 与 xDSL-RVV 经核实非四大会议论文, 降级为 reference-only。

---

## 1. 主表: 必须引用/对比的论文

| # | 论文 | Venue / DOI | 关键数字 (原文验证) | Baseline | 硬件 | 判级 |
|---|------|-------------|--------------------|----------|------|------|
| 1 | **Peccia et al., "Tensor Program Optimization for the RISC-V Vector Extension Using Probabilistic Programs"** (arXiv:2507.01457) | **ICCAD 2025**, DOI: 10.1109/ICCAD66269.2025.11241007 | 执行延迟较 GCC autovectorization **−46%**, 较 muRISCV-NN **−29%**, 在商用 RVV 1.0 芯片上比 LLVM 映射平均**快 35%**; 代码内存占用更小 | GCC/LLVM autovectorization, muRISCV-NN 手写库 | FPGA RISC-V SoC + 商用 RVV 1.0 芯片 (实机, 非仿真) | **direct** — 唯一在四大会议上做 "RVV schedule 优化" 的论文; 他们是 TVM MetaSchedule **生成/搜索**, 我们是**选择**; 必比 |
| 2 | **T-SAR: Full-Stack Co-design for CPU-Only Ternary LLM Inference via In-Place SIMD ALU Reorganization** (arXiv:2511.13676) | **DATE 2026** (arXiv Comments: "Accepted to DATE 2026") | GEMM latency **5.6–24.5x**, GEMV throughput **1.1–86.2x**; SIMD 单元开销 +3.2% power / +1.4% area; 能效较 Jetson AGX Orin **2.5–4.9x** | LUT-based ternary 推理 (如 T-MAC 类), GPU 平台 | CPU + 定制 SIMD ALU 改动 (硬件协同设计) | **same-axis** — 同为 "量化 LLM 的 GEMM/GEMV on CPU SIMD" 在四大会议; 但他改硬件, 我们纯软件跑 stock RVV 1.0 |
| 3 | **HybriMoE: Hybrid CPU-GPU Scheduling and Cache Management for Efficient MoE Inference** (arXiv:2504.05897) | **DAC 2025**, DOI: 10.1109/DAC63849.2025.11133274 | prefill **1.33x** / decode **1.70x** vs SOTA hybrid MoE 推理; 3 个 MoE LLM | kTransformers 等 hybrid 推理框架 | CPU-GPU 混合平台, 基于 kTransformers 实现 | **same-axis** — 证明 DAC 接收 "LLM 推理 + runtime scheduling + 开源框架改造" 类系统论文; 调度粒度不同 (expert/layer vs kernel-variant) |
| 4 | **AdapMoE: Adaptive Sensitivity-based Expert Gating and Management for Efficient MoE Inference** (arXiv:2408.10284) | **ICCAD 2024**, DOI: 10.1145/3676536.3676741 | 激活 expert 平均 **−25%**, **1.35x** speedup, 无精度损失 | 按需加载/prefetch 的 MoE 推理方案 | 多平台 (edge GPU 等) | **reference-only** — 同一 "edge LLM 推理效率" 大类, 引用定位即可 |
| 5 | **MCUBERT: Memory-Efficient BERT Inference on Commodity Microcontrollers** (arXiv:2410.17957) | **ICCAD 2024**, DOI: 10.1145/3676536.3676747 | 参数 **5.7x/3.0x** ↓ (BERT-tiny/mini), 执行内存 **3.5x/4.3x** ↓, 延迟 **1.5x** ↓; 256KB 内存处理 >512 tokens | CMSIS-NN 类 MCU 推理栈 | 商用 MCU (Cortex-M) | **reference-only** — "受限 CPU 上 Transformer 的 MCU-friendly scheduling", 引其证明 scheduling 策略是 EDA 认可贡献点 |
| 6 | **Squat: Quant Small Language Models on the Edge** (arXiv:2402.10787) | **ICCAD 2025**, DOI: 10.1109/ICCAD66269.2025.11240685 | 移动端较 FP16 **最高 2.37x**; sub-8-bit token 自适应量化 + SIMD Multi-Kernel Mixed-Precision multiplier | FP16 推理, 既有 QAT/PTQ 方法 | 移动 SoC (ARM SIMD) | **same-axis** — "量化 + SIMD kernel" 在 ICCAD; 但他改模型/量化方案, 我们固定 Q4_0/Q8_0 只选 kernel, 正交 |
| 7 | V-Seek: Accelerating LLM Reasoning on Open-hardware Server-class RISC-V Platforms (arXiv:2503.17422) | **arXiv preprint** (非四大, 已核实无 venue 标注) | DeepSeek R1 Distill Llama 8B: **4.32 tok/s** 生成 / 6.54 tok/s prefill; 较 baseline **2.9x/3.0x** | llama.cpp 原始 RISC-V 路径 | **Sophon SG2042** (64 核 RVV 0.7.1) | **reference-only (必引)** — 与我们同栈 (llama.cpp + RISC-V + 量化 LLM), 且给出 SG2042 绝对 tok/s 参照系; 但非 EDA 会议 |
| 8 | Enabling RISC-V Vector Code Generation in MLIR through Custom xDSL Lowerings (arXiv:2603.17800) | **arXiv preprint** (2026-03, 已核实无 venue 标注) | GEMM **12.2 GFLOPS** vs OpenBLAS 5.1 GFLOPS; BERT-Large 派生 workload 提升 **10–35%** | OpenBLAS | **K230 + Banana Pi BPI-F3** (与我们同板!) | **reference-only** — 提供 BPI-F3 上 GEMM 的 GFLOPS 参照与 codegen 对照面; 非四大 |

**判级结论**: 四大会议 2024–2026 中, 与我们同轴最近的是 **#1 Peccia (ICCAD'25, direct)** 与 **#2 T-SAR (DATE'26)、#3 HybriMoE (DAC'25)、#6 Squat (ICCAD'25) (same-axis)**; 其余为定位性引用。

---

## 2. "DAC 评估模板": 这类论文通常报什么 — 逐条对照我们的证据

| 惯例维度 | 四大会议同类论文的典型做法 (取自上表实证) | 我们已有 | 缺口 |
|---|---|---|---|
| **主指标** | 实机 end-to-end 延迟/吞吐: tok/s 分 prefill/decode (HybriMoE 1.33x/1.70x; V-Seek 4.32 tok/s), kernel 级 latency/GFLOPS (Peccia −46%; xDSL 12.2 GFLOPS), GEMM/GEMV 分开报 (T-SAR) | QEMU 精确动态指令数 (schedule 间 2–6x); batch 曲线; GEMV/GEMM 分开 | **实机 tok/s 是硬性期待** — 指令数只能做 motivation/分析指标, BPI-F3/SG2042 数据必须落地 |
| **Baseline 选取** | (a) 编译器 autovectorization (GCC/LLVM, Peccia); (b) vendor/手写库 (muRISCV-NN, OpenBLAS, CMSIS 类); (c) 上游框架默认路径 (llama.cpp 默认 dispatch = V-Seek 的 baseline; kTransformers = HybriMoE); (d) oracle/exhaustive 上界 | vendor 选择规则 vs oracle: **71.6% oracle-gap** — 正是 (c)+(d) 组合, 且是全表最像 autotuning 文献 "fraction-of-oracle" 的指标 | 建议补一条 (a): 与纯 autovectorization 路径对一次, 补一条与 Peccia 式 autotuning 的 "质量 vs 搜索成本" 对比 (selection 秒级 vs MetaSchedule 小时级) |
| **正确性/精度** | 量化类必报 accuracy/perplexity 不降 (AdapMoE "无精度损失", Squat 精度表) | 我们不改数值路径, 精度天然不变; **legality mask 捕获真实 bug** 是超出惯例的正确性证据 | 写法上要显式声明 "bit-exact, 无精度回归", 并把 legality bug 作为 case study 独立小节 |
| **评估规模** | ≥3 个模型 (HybriMoE 3 个 MoE; Squat 多个 SLM), ≥2 个硬件平台 (Peccia: FPGA + 商用芯片; xDSL: K230 + BPI-F3), 多 batch/seq 扫描 | SmolLM-135M/360M + Qwen-0.5B (QEMU); batch sweep 已有 | 模型档位偏小 — 建议实机上加 1.5B/3B 级 (Q4_0/Q8_0), 平台凑齐 BPI-F3 (VLEN=256) + SG2042 两档 |
| **方法开销** | 报技术自身开销: 调优时间 (Peccia 的 tuning 成本), 面积/功耗 (T-SAR +3.2%/+1.4%), 运行时开销 (HybriMoE 调度开销) | learned ranking 推理开销待测 | 必报 selection 决策开销 (µs 级) + 训练数据采集成本, 对比 autotuning 的小时级搜索 |
| **消融** | 逐组件 ablation (HybriMoE 三机制分拆; Squat 各量化组件) | 边界特征 (batch=4 台阶)、cache wall 可作特征消融素材 | 需要一张 "去掉 legality mask / 去掉 boundary 特征 / 去掉某特征族" 的 ablation 表 |

---

## 3. 定位段: selection + boundary + legality 在 EDA 语境下的讲法 (DSE 视角)

**核心叙事**: 把 kernel-variant 选择建模为一个**运行时设计空间探索 (DSE) 问题** — 设计空间 = {既有 RVV schedule} × {shape, batch, 量化格式, 微架构参数}; 我们不扩大空间 (不做 codegen), 而是证明: (i) 该空间里 vendor 启发式规则离 oracle 有 71.6% 的差距 (**选择问题本身未被解决**); (ii) 空间中存在可刻画的**性能断崖** (batch=4 的 GEMV→GEMM 台阶、cache compulsory-traffic wall), 这正是 EDA DSE 文献里 "performance cliff / feasible region" 的语言; (iii) **legality mask 是对可行域的形式化剪枝**, 且在真实代码中抓到过 correctness bug — 把 "正确性作为一等公民" 讲成 EDA 的 verification-aware DSE, 而非编译器工程细节。

**与各论文的差异一句话版**:
- vs **Peccia (ICCAD'25)**: 他们用 TVM MetaSchedule *生成*新 schedule (每个 op×硬件小时级搜索); 我们在*既有*生产级 kernel 间做 µs 级*选择*, 并量化了 "不选对" 的代价 (71.6% oracle-gap)。两者互补: 他们的产物可以进我们的候选池 — 这句话要写进 related work, 化竞争为分层。
- vs **T-SAR (DATE'26)**: 同样关注量化 GEMM/GEMV on CPU SIMD, 但他要改 SIMD ALU (需要新硅); 我们在量产 RVV 1.0 芯片上纯软件拿收益。
- vs **HybriMoE (DAC'25) / AdapMoE (ICCAD'24)**: 同为推理期调度, 但粒度不同 — 他们调度 expert/layer 在 CPU-GPU 间的放置, 我们调度单 CPU 内 kernel-variant 的分派; 引用其证明 "runtime scheduling for LLM inference" 是 DAC 主赛道。
- vs **Squat (ICCAD'25) / MCUBERT (ICCAD'24)**: 他们改模型/量化方案换效率; 我们固定模型与量化格式 (bit-exact), 正交且可叠加。
- vs **V-Seek / xDSL-RVV (preprint)**: 同硬件生态 (SG2042 / BPI-F3) 的绝对性能参照系, 用来锚定我们实机数字的可信度。

---

## 4. 风险与生态位判断

**结论: 该生态位为空。** 四大会议 2024–2026 中**没有**任何论文做 "量化 LLM kernel 的 schedule *selection* on RISC-V RVV": Peccia 是 generation/autotuning 且非 LLM 量化 kernel; T-SAR 是硬件协同设计; HybriMoE/AdapMoE 是 CPU-GPU expert 调度; Squat/MCUBERT 是模型侧压缩。llama.cpp + RVV 1.0 + Q4_0/Q8_0 这条栈在四大会议尚无正式论文占位 (最近的 V-Seek 停留在 arXiv)。

- **对 novelty 是利好**: 可以合法声明 "first at big-4 to X" 级别的表述 (建议措辞: *first to formulate and quantify the kernel-schedule selection problem for quantized LLM inference on RISC-V RVV*), 且 71.6% oracle-gap 给了 "问题真实存在且代价可观" 的定量支撑, 这是 DAC 审稿人最认的 motivation 格式。
- **对 related-work 写法的建议**: 生态位空 ⇒ 不能只写 "没人做过", 要用**三支柱三角定位**: (1) RVV 代码生成/autotuning (Peccia ICCAD'25, xDSL-RVV) — 我们解决其下游的选择问题; (2) LLM 推理调度 at DAC/ICCAD (HybriMoE, AdapMoE) — 我们把调度下沉到 kernel-variant 粒度; (3) 量化 kernel × SIMD at DATE/ICCAD (T-SAR, Squat) — 我们纯软件、bit-exact。每支柱结尾一句 "但均未回答 selection 问题"。
- **对应风险**: (a) 空生态位的反面是审稿人可能判 "系统工程, 无 EDA 方法学贡献" — 对策是把 legality mask 形式化 + learned ranking 泛化性 (跨 shape/跨芯片) 做成方法学主张, 而不是把 llama.cpp 改造当卖点; (b) 只有 QEMU 指令数会被直接拒 — 实机 tok/s 是 gate, 务必在投稿前落地 BPI-F3 + SG2042 两平台; (c) DATE 2026 后、DAC 2027 前可能出现同生态位 arXiv 论文 (V-Seek 团队最活跃), 投稿前一个月需复扫 arXiv cs.AR/cs.PF 的 "RVV + LLM" 关键词。

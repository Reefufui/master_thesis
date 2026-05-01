# Benchmarking Methodologies for Real-Time Rendering: SIGGRAPH Practices and Vulkan Pipelines

## Executive Summary

Rigorous performance benchmarking in real-time rendering requires both a principled statistical framework and precise GPU instrumentation. SIGGRAPH and ACM TOG papers have converged on a set of de-facto conventions—GPU timestamp queries, multi-scene fixed camera paths, and the reporting of frame-time distributions rather than raw FPS—while Vulkan's explicit API gives researchers the tools to isolate workloads at a level no prior API offered. For a SIGGRAPH submission, the recommended approach is to use **GPU timestamp queries inside offscreen (headless/no-swapchain) rendering** as the primary performance measurement mechanism, completely eliminating presentation jitter and vsync interference, while optionally retaining a swapchain path to demonstrate end-to-end real-world usability. This report details the full methodology, Vulkan-specific tooling, and concrete recommendations.

***

## 1. Standard Benchmarking Practices in SIGGRAPH / ACM TOG

### 1.1 Why FPS Alone Is Insufficient

Raw frames-per-second figures are widely recognized as a misleading primary metric. The core problem is that FPS is a reciprocal quantity: a drop from 120 FPS to 60 FPS represents the same absolute latency increase (8.3 ms) as a drop from 60 FPS to 40 FPS, yet the percentage difference looks larger for the latter on a linear FPS scale. Frame time (milliseconds per frame) is linear and therefore far more expressive for latency analysis. A renderer that alternates between 90 FPS (11 ms) and 40 FPS (25 ms) averages to "60 FPS" but will feel objectively stuttery—a fact entirely hidden by the average.[^1][^2]

A community-wide analysis of SIGGRAPH papers on volume rendering and particle rendering found that the majority of publications report only a single FPS number per test scene, with a minority adding minimum/maximum values or frame-time diagrams; percentile-based reporting remains underused relative to what is needed for genuine reproducibility.[^3]

### 1.2 Recommended Metric Set

The following metric set reflects current best practice for academic and production reporting:

| Metric | Definition | Why It Matters |
|--------|------------|----------------|
| **Mean frame time** | Arithmetic mean of all measured frame times (ms) | Top-line latency, directly comparable across runs |
| **Median (P50) frame time** | 50th percentile frame time | Robust central tendency, immune to rare spikes |
| **P95 frame time** | 95th percentile frame time | Captures common tail latency; most users' worst-case |
| **P99 frame time** | 99th percentile frame time | Exposes architectural bottlenecks and GC/shader-compile stalls |
| **1% low FPS** | Average FPS of the slowest 1% of frames | Smoothness proxy used by hardware reviewers and game benchmarkers |
| **0.1% low FPS** | Average FPS of the slowest 0.1% of frames | Captures extreme outliers (e.g., resource streaming hitches) |
| **Standard deviation / IQR** | Spread of the frame-time distribution | Quantifies frame pacing consistency |
| **GPU time** | GPU timestamp delta (ns × timestampPeriod) | Isolates pure GPU workload, independent of CPU submission overhead |
| **GPU memory bandwidth utilization** | Reported via `VK_KHR_performance_query` or vendor tool | Reveals bandwidth bottlenecks (memory-bound vs. compute-bound) |

The P1 / P99 framing has direct industry precedent: the Decentraland Unity renderer team explicitly switched from FPS averages to P1/P50/P99 frame-time reporting because "the goal of stability is not frame time, it is frame pacing". Automated GPU benchmark tools designed for academic use recommend capturing p95/p99 frame times because "averages hide stutter".[^4][^1]

### 1.3 Warm-Up, Frame Count, and Outlier Policy

Empirical measurement on GPUs requires defense against cold-cache and shader-compilation effects. The first frame after a pipeline state change is routinely anomalous, especially on AMD hardware, due to kernel caching behavior. Best practice per the TRROJAN framework (used in IEEE TVCG research) specifies:[^3]

- **Minimum warm-up**: discard at least the first 1–4 frames of any new configuration before recording measurements.[^3]
- **Minimum sample count**: render each configuration at least 5–8 times (more for coarse-resolution benchmarks); report the median of GPU timestamps for each configuration to suppress run-to-run variance.[^3]
- **Wall-clock coverage**: ensure each measurement window spans at least 100 ms of GPU work to average over scheduling noise.[^3]
- **Outlier handling**: in aggregate analyses spanning many configurations, use the interquartile range or Kolmogorov–Smirnov tests to characterize the distribution rather than discarding individual outliers ad hoc.[^3]
- **Repeatability**: run 3 statistically independent passes and report means ± standard deviation; a standard deviation below 1–2% of the mean indicates a stable measurement environment.[^4]

For thermal stability, disable Turbo Boost and GPU Boost (lock clocks via `nvidia-smi -lgc` or AMD's `radeon-profile`) so that frequency scaling does not confound results across multi-run comparisons.

### 1.4 Hardware Specification Requirements

A benchmark result without hardware context is un-reproducible. SIGGRAPH and TOG papers are expected to state:

- GPU model, architecture family, VRAM capacity
- Driver version (critical: major performance regressions are known between driver versions)
- CPU model and clock frequency (relevant for CPU-bottlenecked workloads)
- RAM capacity and bandwidth
- Display resolution and refresh rate (even if vsync-disabled, the monitor's max refresh rate can affect PresentMon/swapchain behavior)
- Operating system, API version (e.g., Vulkan 1.3), and any relevant extension set

The TRROJAN benchmarking study spanning 10 GPUs across NVIDIA Maxwell, Pascal, and AMD GCN 2–5 used consistently configured machines (Intel Xeon E5-2630, 64 GB RAM, Windows 10, latest stable drivers) to ensure hardware is the only variable between GPU comparisons. It found that GPU performance generally scales linearly across architectures for the same algorithm, with Pearson correlation coefficients above 0.95 between NVIDIA and AMD for identical workloads.[^3]

### 1.5 Control of Variables: Camera Paths and Scene Configuration

Camera path choice has the second-highest variance impact on rendering performance (after scene content itself). The common practice of using a single orbital rotation underrepresents the performance range a technique will exhibit in practice. The empirically validated recommendation is:[^3]

- **Fixed, pre-recorded camera paths**: define at minimum an orbital path (around x and y axes), a diagonal path through the scene volume, and a straight fly-through along each axis—seven distinct paths as defined in TRROJAN, sampled at 36 positions each.[^3]
- **Random camera samples** (for large-scale comparisons): a random sample of camera positions drawn uniformly over the scene bounding sphere has been shown to be statistically representative of the full performance distribution (Kolmogorov–Smirnov test, mean p = 0.644), while orbital paths are not representative.[^3]
- **Controlled scene parameterization**: fix resolution, anti-aliasing method and sample count, shadow map resolution, LOD bias, anisotropy level, and post-processing stack. Any parameter that changes between a proposed method and its baseline must be explicitly flagged.

### 1.6 Code Replicability

A 2020 study of 192 codes from 454 SIGGRAPH papers (2014, 2016, 2018) showed that 68 of 133 provided codes required modification to run, with 20 classified as difficult to fix. Papers with available operational code have a 55% higher citation count, making replicability a practical incentive as well as a scientific obligation. SIGGRAPH now strongly encourages code submission and supports the Graphics Replicability Stamp Initiative (GRSI). For benchmarking: publish the exact benchmark script, scene assets, camera path files, and driver version used.[^5]

***

## 2. Vulkan-Specific Considerations

### 2.1 The Fundamental Choice: Offscreen vs. Swapchain Rendering

Vulkan's explicit WSI (Window System Integration) layer means the developer can choose to completely decouple the rendering pipeline from any display surface. This creates two distinct measurement paradigms:

| Dimension | Offscreen / Headless | Swapchain-Based |
|-----------|---------------------|-----------------|
| **What is measured** | Pure GPU rendering work | GPU work + presentation engine + compositor |
| **Vsync interference** | None | Present mode dependent (FIFO, MAILBOX, IMMEDIATE) |
| **Frame pacing noise** | Minimal (no backpressure from display) | Present latency, display pipeline, OS compositor |
| **Reproducibility** | High (no OS/display state dependencies) | Lower (display refresh, compositor load) |
| **Relevance to shipped product** | Algorithmic cost only | End-to-end user-perceived latency |
| **API complexity** | No surface, no swapchain required | Full WSI setup required |
| **Synchronization** | `vkDeviceWaitIdle` or fence on readback | `vkQueuePresentKHR`, swapchain acquire/release |

Crucially, Vulkan itself makes **no rendering distinction** between swapchain images and manually created `VkImage` objects: the pipeline, render pass, and shader execution are identical. The only difference is in how image data is consumed after rendering. This means offscreen benchmarks measure exactly the same GPU kernel cost as a swapchain-based equivalent, with no artificial overhead added.[^6]

### 2.2 Pure Headless / Offscreen Rendering

Headless rendering in Vulkan requires creating `VkImage` instances with device-local memory rather than acquiring images from a swapchain. Sascha Willems' `renderheadless.cpp` example, referenced widely across the Vulkan community as the canonical reference, demonstrates rendering to a non-visible framebuffer attachment, then copying results to a host-visible linear-tiled image for readback. Key properties:[^7]

- **No `VkSurfaceKHR` required**: on most drivers, headless execution does not require a window manager, and the example has been confirmed to run in a non-graphical TTY.[^8]
- **Explicit synchronization**: without swapchain semaphores, the developer uses `vkDeviceWaitIdle` or a fence on a submission to guarantee the GPU has completed work before reading timestamps or results back to the CPU.[^9]
- **Readback overhead**: a device-to-host image copy (`vkCmdCopyImageToBuffer`) adds a few microseconds but is cleanly separable from the rendering pass by placing timestamp queries before and after the copy.[^7]
- **`VK_EXT_headless_surface`**: an alternative hybrid approach creates a `VkSurfaceKHR` that has no external presentation target; `vkQueuePresentKHR` becomes a no-op, allowing swapchain-style code to run without a display—useful for CI/CD testing pipelines.[^10]

The official Khronos Vulkan Samples support a `--headless` mode and a `--benchmark` flag (`--stop-after-frame N`) designed specifically for automated performance measurement in environments without a GUI.[^11][^12]

### 2.3 Swapchain-Based Rendering: When to Use It

Swapchain-based rendering introduces the presentation pipeline as a measured component, which is appropriate when:

- The claim under evaluation is **end-to-end user-perceived latency** (input-to-photon), not just algorithmic rendering cost.
- The technique under study involves **display-pipeline interactions** (variable-refresh-rate, HDR tone mapping to display colorspace, display-sync effects).
- **Frame pacing under realistic backpressure** is part of the evaluation (e.g., testing whether a technique maintains smooth frame delivery at a target display refresh).

However, vsync introduces a well-known frame-pacing interaction: minimum swapchain image counts differ by platform (3 for Android vs. 2 for desktop to sustain smooth throughput), and blocking-based synchronization can inflate latency measurements by forcing the CPU to stall waiting for `vkQueuePresentKHR`. On Windows, using `VK_EXT_full_screen_exclusive` to bypass the DWM compositor eliminates compositing overhead for desktop measurements.[^13][^14]

Swapchain `VK_PRESENT_MODE_IMMEDIATE_KHR` (no vsync) removes synchronization-induced frame-time inflation but introduces tearing and may cause GPU thermal behavior to differ from vsync-constrained scenarios.

### 2.4 CPU-GPU Synchronization and Frame Pacing

A common benchmarking pitfall is measuring apparent frame time from the CPU wall clock, which includes the CPU's wait for the GPU to signal completion. Google Benchmark's GPU issue tracker explicitly notes that "CPU time spent setting up shaders, submitting, and waiting for the GPU can significantly overestimate the actual GPU execution duration". The only accurate GPU-side measurement is via **timestamp queries**.[^15]

Frame pacing issues arise when CPU and GPU are poorly synchronized: if the CPU blocks waiting for the GPU on every frame (rather than using N-buffering), "time bubbles" appear in the GPU timeline even with triple buffering—the CPU waits on fence N before submitting frame N+3, creating unnecessary idle time. This means that measuring wall-clock time from the CPU introduces variance tied to the CPU-GPU synchronization strategy, not just GPU load.[^16]

***

## 3. Vulkan Timestamp Query APIs

### 3.1 `vkCmdWriteTimestamp` and Query Pools

Vulkan's primary timing mechanism is the timestamp query pool (`VK_QUERY_TYPE_TIMESTAMP`). The pattern is:[^17][^18]

```c
// Pre-pass: reset query pool for the current frame
vkResetQueryPool(device, pool, 0, 2);

// Start of frame
vkCmdWriteTimestamp(cmdBuf, VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT, pool, 0);

// All render passes...

// End of frame
vkCmdWriteTimestamp(cmdBuf, VK_PIPELINE_STAGE_BOTTOM_OF_PIPE_BIT, pool, 1);

// After GPU completion:
uint64_t timestamps[^2];
vkGetQueryPoolResults(device, pool, 0, 2, sizeof(timestamps),
    timestamps, sizeof(uint64_t), VK_QUERY_RESULT_64_BIT | VK_QUERY_RESULT_WAIT_BIT);

double gpuTimeMs = (timestamps[^1] - timestamps)
    * physicalDeviceLimits.timestampPeriod * 1e-6;
```

Important limitations to understand:[^19][^17]

- **`TOP_OF_PIPE` + `BOTTOM_OF_PIPE`**: This is the only practically reliable combination. Writing timestamps at intermediate stages (e.g., `VK_PIPELINE_STAGE_VERTEX_SHADER_BIT` then `FRAGMENT_SHADER_BIT`) does not give meaningful deltas due to GPU wave-level overlap and out-of-order execution.
- **`timestampPeriod`**: Returned by `vkGetPhysicalDeviceProperties`, it gives the number of nanoseconds per timestamp increment. On desktop NVIDIA hardware this is typically 1 ns; on some mobile SoCs it can be much coarser. Always multiply by this value before reporting time.
- **Double-buffered query pools**: Maintain one query pool per frame-in-flight to avoid reading a pool whose results are still pending from a previous submission.[^18]
- **Not all queues support timestamps**: Check `VkQueueFamilyProperties::timestampValidBits`; a value of 0 means the queue does not support timestamp queries.[^20]

### 3.2 `VK_KHR_calibrated_timestamps`

Core Vulkan timestamps have historically lacked monotonicity guarantees across power management events, making cross-frame comparison unreliable in long benchmarks. `VK_KHR_calibrated_timestamps` (promoted from `VK_EXT_calibrated_timestamps`) solves this by providing a mechanism to simultaneously sample the GPU timer and the system CPU timer (`CLOCK_MONOTONIC` on Linux, `QueryPerformanceCounter` on Windows), enabling accurate CPU-GPU correlation:[^21][^22]

- Returns a `pMaxDeviation` value in nanoseconds quantifying the maximum uncertainty in the calibration—report this alongside timing results.
- Guarantees monotonicity: the device timer will not reset due to power management while the extension is active.
- Critical for any benchmark comparing absolute GPU timings across separate submissions or across runs.

### 3.3 `VK_KHR_performance_query`

For hardware counter access beyond simple timing—shader occupancy, memory bandwidth, cache hit rates, render backend utilization—`VK_KHR_performance_query` (Vulkan 1.1.128+) is the cross-vendor standard:[^23][^24][^25]

- Worked on by Intel, AMD, NVIDIA, Samsung, Qualcomm, Google, and ARM, giving broad hardware coverage.
- Exposes counters scoped to queue family, render pass, or sub-pass, correlated with command buffer work via `VkPerformanceCounterKHR` structures.
- Counters cover units such as GPU cycles, shader invocations, texture fetches, and memory bandwidth bytes.
- Used internally by vendor profilers (Nsight, RGP) to expose hardware metrics in a standardized manner.

***

## 4. Vulkan Performance Analysis Tools

### 4.1 Tool Overview

| Tool | Primary Use | Vulkan-Specific Capabilities |
|------|------------|------------------------------|
| **NVIDIA Nsight Graphics** | Frame debugging, GPU tracing, shader profiling | Full Vulkan 1.3 + RT support; GPU Trace captures per-event timing; Shader Profiler for SM-limited workloads; NVTX annotation support[^26][^27] |
| **NVIDIA Nsight Systems** | System-wide CPU-GPU timeline, API call tracing | `--trace=vulkan,osrt,nvtx`; captures command buffer submission patterns and CPU stalls[^28] |
| **AMD Radeon GPU Profiler (RGP)** | Per-event GPU timeline, wave occupancy, barrier analysis | Vulkan, DX12, OpenCL; captures barrier sync points; integrates with Radeon Developer Service[^29][^28] |
| **RenderDoc** | Frame capture, API state inspection, debug | Full Vulkan support; best for correctness validation; less suited for fine-grained performance measurement than Nsight/RGP; requires swapchain OR explicit API markers for offscreen capture[^30][^31] |
| **PresentMon / CapFrameX** | Frame-time capture for swapchain-based apps | Logs per-frame display timestamps; compute P95/P99 and 1% lows; tag runs with driver version and API[^32] |
| **vkmark** | Synthetic Vulkan benchmark | Configurable scene benchmarks with duration-based scoring[^33] |
| **Google uVkCompute** | Micro-benchmarks for compute shaders | Headless compute pipeline; shader arithmetic throughput testing[^34] |

### 4.2 RenderDoc and Offscreen Rendering

RenderDoc requires explicit frame boundaries to capture. For offscreen (no-swapchain) applications, RenderDoc exposes an in-application API to signal frame start/stop:

```c
RENDERDOC_API_1_0_0 *rdoc_api = NULL;
// At frame start:
rdoc_api->StartFrameCapture(NULL, NULL);
// ... render pass ...
rdoc_api->EndFrameCapture(NULL, NULL);
```

Without this, RenderDoc cannot identify frame boundaries since there is no `vkQueuePresentKHR` to use as the implicit marker.[^30]

### 4.3 The NVTX + Nsight Workflow

The recommended workflow for precise Vulkan profiling with NVIDIA hardware is to annotate command buffer regions with NVTX ranges, then capture with both Nsight Systems (system timeline) and Nsight Graphics (GPU-level trace), and align the captures via NVTX markers. This avoids the noise of large unstructured captures and allows correlation of CPU scheduling events with specific GPU render passes.[^28][^35]

***

## 5. Methodological Rigor: Statistical Treatment

### 5.1 Distribution Shape

The empirical distribution of frame times in GPU rendering is well-described by a **log-normal distribution** (or an approximation thereof). This has a practical implication: the arithmetic mean is systematically biased upward by outliers (shader compilation hitches, memory page faults), while the median and percentiles are robust. For SIGGRAPH reporting:[^3]

- Report the **median** as the primary central tendency for GPU frame time.
- Report **P95 and P99** as tail metrics.
- Plot the **CDF or histogram** of frame times alongside summary statistics wherever space permits—reviewers increasingly expect this.
- If comparing two methods statistically, use a Kolmogorov–Smirnov two-sample test on the frame-time distributions rather than a t-test (which assumes normality).[^3]

### 5.2 Warm-Up Protocol

A minimum warm-up protocol for a SIGGRAPH benchmark should:

1. Load all GPU resources (textures, buffers, acceleration structures) before timing begins.
2. Execute the technique being measured for at least 60–100 frames *without recording*, to populate GPU caches, JIT-compile any remaining pipeline states, and bring the GPU to thermal steady-state.
3. Then record at least 300–1000 frames (sufficient for reliable P99 estimates; at 10 minutes × 3600 frames/min = 36,000 frames, 1% low = 360 frames of statistical basis).[^36]
4. Discard the first and last 5% of recorded frames if the test includes camera transitions that may trigger streaming or LOD changes.

### 5.3 Fairness in Comparisons

When comparing a proposed technique against a baseline:

- Both methods must be evaluated with **identical scene assets, camera paths, resolution, and post-processing settings**.
- If the proposed method modifies the G-buffer layout or number of render passes, report the **per-pass GPU breakdown** (not just total frame time) so reviewers understand where time is spent.
- Document any implementation that gives the proposed method an asymmetric advantage (e.g., precomputed data that the baseline would also benefit from).
- On multi-GPU systems, lock the benchmark to a single GPU using `VkPhysicalDevice` selection rather than relying on default device enumeration order.

***

## 6. Recommendations for a SIGGRAPH Vulkan Submission

### 6.1 Architecture: Offscreen for Measurement, Swapchain for Demonstration

The optimal architecture for a SIGGRAPH Vulkan renderer combines both modes:

**Primary benchmarking path (offscreen)**:
- Allocate render targets as manually-managed `VkImage` objects with `VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT | VK_IMAGE_USAGE_TRANSFER_SRC_BIT`.
- Place `vkCmdWriteTimestamp` at `TOP_OF_PIPE_BIT` and `BOTTOM_OF_PIPE_BIT` around each logical rendering pass.
- Use double-buffered query pools indexed by frame-in-flight.
- Compute `gpuTimeMs = (t_end - t_begin) * timestampPeriod * 1e-6` for each frame.
- Collect 300–1000 frames; compute median, P95, P99, and standard deviation.
- This path eliminates all presentation overhead, vsync uncertainty, compositor latency, and OS scheduling noise from the measurement.[^8][^7]

**Swapchain path (interactive/demo)**:
- Retain a separate code path that blits the final offscreen render target to a swapchain image (`VK_IMAGE_USAGE_TRANSFER_DST_BIT` on the swapchain) for interactive demonstrations.
- Use `VK_PRESENT_MODE_MAILBOX_KHR` for low-latency triple-buffered presentation when demoing.
- The blit cost (~1 ms at 720p, scaling with resolution) is separable via timestamp queries and should be excluded from the algorithmic performance claim.[^37]

This is consistent with the design of the Khronos Vulkan Samples, which implement a `--headless` + `--benchmark --stop-after-frame N` command line for CI and automated evaluation, while keeping the interactive swapchain path for demonstration.[^12][^11]

### 6.2 Concrete Benchmark Script Structure

```
1. Setup:
   - Create device, allocate offscreen images, build pipelines
   - Load scene assets, acceleration structures
   - Set camera path from pre-recorded file
   
2. Warm-up:
   - Run 100 frames without recording timestamps
   - Verify GPU is at thermal steady-state (poll via VK_KHR_performance_query 
     or vendor tool; discard run if temperature still rising)

3. Measurement loop (N = 500 frames per scene/config):
   - vkResetQueryPool
   - vkCmdWriteTimestamp(TOP_OF_PIPE)
   - [render passes]
   - vkCmdWriteTimestamp(BOTTOM_OF_PIPE)
   - vkSubmitInfo + fence
   - vkWaitForFences (or use N-buffered approach for throughput)
   - vkGetQueryPoolResults -> append gpuTimeMs to vector

4. Statistics:
   - Compute mean, median, P95, P99, std-dev of gpuTimeMs vector
   - Compute 1% low and 0.1% low FPS equivalents
   - Output CSV for reproducibility

5. Report (per scene, per config):
   - GPU model, driver version, scene name, resolution
   - All statistics above, plus any per-pass breakdown
```

### 6.3 GPU-CPU Synchronization Strategy

For maximum measurement throughput without sacrificing accuracy, use N-buffered (typically 2–3) query pools aligned with frames-in-flight. On frame F, read query results from frame F-N while frame F is in flight. This avoids stalling the GPU while still recovering accurate per-frame GPU times. Only call `vkDeviceWaitIdle` once at the very end of the measurement window to drain all in-flight work.[^18]

### 6.4 Reporting Standard for the Paper

In the results table, report results in the following format (example):

| Scene | Method | Median GPU (ms) | P95 (ms) | P99 (ms) | VRAM (MB) | GPU |
|-------|--------|----------------|----------|----------|-----------|-----|
| Bistro | Proposed | 4.23 | 5.10 | 6.82 | 1,842 | RTX 4090 |
| Bistro | Baseline | 8.71 | 10.44 | 14.20 | 1,756 | RTX 4090 |

Additionally, include:
- A frame-time CDF or histogram for representative scenes.[^3]
- Per-pass timing breakdown (shadow map pass, G-buffer pass, lighting pass, post-processing).
- Tested on at least 2 GPU architectures (e.g., NVIDIA Ada Lovelace + AMD RDNA3) to demonstrate portability.
- Hardware counter profiling (occupancy, bandwidth utilization) for the critical bottleneck pass.

### 6.5 When Swapchain Measurement Is Appropriate

Swapchain-based timing is appropriate for claims specifically about **end-to-end rendering latency** (e.g., "our technique enables VR applications at 90 Hz with ≤11 ms total frame latency"). In that case:

- Use `VK_PRESENT_MODE_IMMEDIATE_KHR` (no vsync) to decouple GPU frame production from display refresh.
- Measure wall-clock time from before `vkSubmitInfo` to after `vkQueuePresentKHR` + fence signal.
- Additionally report GPU-only time via timestamp queries to separate GPU cost from CPU and presentation overhead.
- Document the swapchain image count and the synchronization strategy (blocking vs. semaphore-based).
- On Windows, use `VK_EXT_full_screen_exclusive` to disable the DWM compositor if measuring desktop performance.[^14]

***

## 7. Summary of Best Practices

The following checklist synthesizes guidance from SIGGRAPH publishing conventions, TRROJAN empirical methodology research, Vulkan documentation, and industry profiling workflows:

**Measurement architecture**:
- Use GPU timestamp queries (`vkCmdWriteTimestamp` at `TOP_OF_PIPE` / `BOTTOM_OF_PIPE`) as the primary timing mechanism.[^17]
- Prefer offscreen rendering (no swapchain, no display) for academic FPS/latency claims to eliminate vsync and compositor variance.[^7]
- If swapchain is used, document present mode and disable DWM compositing on Windows.

**Statistical rigor**:
- Minimum 100 warm-up frames; minimum 300 measurement frames per configuration.[^4][^3]
- Report median GPU time as primary metric; add P95, P99, and 1% low FPS.[^2][^32]
- Include frame-time distribution (CDF or histogram) for at least one representative scene.[^3]
- Use double-buffered query pools to avoid GPU stalls during measurement.[^18]

**Experimental design**:
- Use pre-recorded deterministic camera paths covering orbits, fly-throughs, and diagonal traversals.[^3]
- Fix all variables except the method under evaluation (resolution, AA, shadows, post-processing, LOD).
- Test on at least 2 GPU vendors / architectures.[^3]
- Lock GPU clocks for thermal stability; discard runs where GPU temperature is still rising.

**Reproducibility**:
- Publish benchmark scripts, scene assets, camera path files, and driver version.[^38]
- Document all measurement parameters in the paper's supplemental material.
- Consider the Graphics Replicability Stamp Initiative (GRSI) for code submission.

**Tooling**:
- Use Nsight Systems for system-level CPU-GPU correlation; Nsight Graphics / AMD RGP for per-pass GPU profiling.[^28]
- Use `VK_KHR_performance_query` for hardware counter access (bandwidth, occupancy).[^25][^23]
- Use `VK_KHR_calibrated_timestamps` for monotonic GPU-CPU time correlation across long measurement windows.[^21]

---

## References

1. [Change performance meter to measure frame time instead of FPS · Issue #2460 · decentraland/unity-renderer](https://github.com/decentraland/unity-renderer/issues/2460) - decentraland / **
unity-renderer ** Public

# Change performance meter to measure frame time instead...

2. [Understanding GPU Benchmark Results | Volume Shader BM](https://volumeshader-bm.com/understanding-results) - Frame Time Metrics: P95 and P99. Frame time (measured in milliseconds) is the inverse of FPS: how lo...

3. [[PDF] On Evaluating Runtime Performance of Interactive Visualizations](https://freysn.github.io/papers/performance_tvcg19.pdf) - In this paper, we discuss how the current practice of empirical performance evaluation in scientific...

4. [The Gaming KPIs That Actually Matter — The National Research ...](https://www.nridl.org/technical-blog/the-gaming-kpis-that-actually-matter) - Audience: university-level gamers and builders Goal: a clear, vendor-neutral checklist of what to me...

5. [[PDF] CODE REPLICABILITY IN COMPUTER GRAPHICS - RRPR 2020](https://rrpr2020.sciencesconf.org/data/program/talkRRPR.pdf)

6. [Coordinate system swap chain vs. offscreen rendering - Vulkan](https://community.khronos.org/t/coordinate-system-swap-chain-vs-offscreen-rendering/107481) - Greetings, as far as I know, Vulkan has a right hand coordinate system for NDC contrary to OpenGLs l...

7. [Headless Vulkan examples - - Sascha Willems](https://www.saschawillems.de/blog/2017/09/16/headless-vulkan-examples/) - I have just added two minimal, mostly self-contained cross-platform headless Vulkan examples to my o...

8. [Is it possible to do offscreen rendering without Surface in Vulkan?](https://stackoverflow.com/questions/38885309/is-it-possible-to-do-offscreen-rendering-without-surface-in-vulkan) - Similar to surfaceless context in OpenGL can we do it in Vulkan.

9. [How to use Vulkan Timestamp Queries? - Stack Overflow](https://stackoverflow.com/questions/63121342/how-to-use-vulkan-timestamp-queries) - This queries the time from start to finish for the entire set of work. So put the first query before...

10. [VK_EXT_headless_surface(3) - Vulkan Documentation](https://docs.vulkan.org/refpages/latest/refpages/source/VK_EXT_headless_surface.html) - The presentation operation for a swapchain created from a headless surface is by default a no-op, re...

11. [Vulkan Samples :: Vulkan Documentation Project](https://docs.vulkan.org/samples/latest/README.html)

12. [GitHub - study-game-engines/khronos-vulkan-examples: One stop solution for all Vulkan samples](https://github.com/study-game-engines/khronos-vulkan-examples) - study-game-engines / **
khronos-vulkan-examples ** Public
forked from KhronosGroup/Vulkan-Samples

13. [Swapchains and frame pacing | Raph Levien's blog](https://raphlinus.github.io/ui/graphics/gpu/2021/10/22/swapchain-frame-pacing.html) - This is something of a followup to the compositor is evil, but more of a guide on how to optimize la...

14. [Advanced API Performance: Vulkan Clearing and Presenting](https://forums.developer.nvidia.com/t/advanced-api-performance-vulkan-clearing-and-presenting/219509) - This post covers best practices for Vulkan clearing and presentation on NVIDIA GPUs. To get a high a...

15. [Support for benchmarking externally timed events, such as GPU code · Issue #198 · google/benchmark](https://github.com/google/benchmark/issues/198) - google / **
benchmark ** Public

16. [Why are there time bubbles in my GPU timeline even when triple ...](https://stackoverflow.com/questions/68139605/why-are-there-time-bubbles-in-my-gpu-timeline-even-when-triple-buffering) - I'm having trouble understanding why there are time bubbles on my GPU timeline when inspecting my ap...

17. [Timestamp queries - Vulkan Documentation](https://docs.vulkan.org/samples/latest/samples/api/timestamp_queries/README.html) - This tutorial, along with the accompanying example code, shows how to use timestamp queries to measu...

18. [GPU execution timing basics in Vk and DX12 - Pavel Šmejkal](https://pavelsmejkal.net/Posts/GPUTimingBasics)

19. [How to use Vulkan Timestamp Queries. | Here should be the blog Title](http://nikitablack.github.io/post/how_to_use_vulkan_timestamp_queries/) - Vulkan provides a tool to make time snapshots - the so-called Queries. There're multiple different q...

20. [Vulkan function to get a pair of timestamps (one CPU, one GPU) corresponding to (very nearly) the same point in absolute wall time.](https://gist.github.com/cdwfs/4222ca09cb259f8dd50f7f2cf7d09179) - Last active
December 12, 2021 06:01

Show Gist options

- Download ZIP

- You must be signed in to s...

21. [VK_EXT_calibrated_timestamps :: Vulkan Documentation Project](https://docs.vulkan.org/features/latest/features/proposals/VK_EXT_calibrated_timestamps.html) - This extension provides a way to calibrate timestamps captured from different devices in the same sy...

22. [The Power of Calibrated Timestamps: Empowering Vulkan and ...](https://gxvtronics.altervista.org/the-power-of-calibrated-timestamps-empowering-vulkan-and-webgpu/) - Vulkan provides a mechanism to query for accurate hardware timestamps, enabling developers to measur...

23. [Task list for VK_KHR_performance_query release · Issue #1091 · KhronosGroup/Vulkan-Docs](https://github.com/KhronosGroup/Vulkan-Docs/issues/1091) - KhronosGroup / **
Vulkan-Docs ** Public

# Task list for VK_KHR_performance_query release #1091

Clo...

24. [Vulkan 1.1.128 Released With Performance Query Extension - Reddit](https://www.reddit.com/r/linux_gaming/comments/dy37mt/vulkan_11128_released_with_performance_query/) - This KHR-ratified extension is the first cross-vendor extension in Vulkan for the querying of any pe...

25. [VK_KHR_performance_query(3) - Vulkan Documentation](https://docs.vulkan.org/refpages/latest/refpages/source/VK_KHR_performance_query.html) - The VK_KHR_performance_query extension adds a mechanism to allow querying of performance counters fo...

26. [Shader Profiler — Nsight Graphics](https://docs.nvidia.com/nsight-graphics/UserGuide/shader-profiler.html)

27. [Optimizing Vulkan 1.3 Applications with Nsight Graphics & Nsight Systems](https://www.youtube.com/watch?v=kSQgfNoTCKY) - Vulkan 1.3 introduces nearly two dozen new extensions. Some extensions help developers simplify thei...

28. [GPU Profiling & Bottleneck Resolution Workflow](https://beefed.ai/en/gpu-profiling-bottleneck-resolution-workflow) - Practical GPU profiling workflow with Nsight, AMD RGP, and RenderDoc: collect traces, analyze CPU/GP...

29. [Vulkan-Guide/README.md at main · mikeroyal/Vulkan-Guide](https://github.com/mikeroyal/Vulkan-Guide/blob/main/README.md) - mikeroyal / **
Vulkan-Guide ** Public

30. [Pure offscreen rendering · Issue #608 · baldurk/renderdoc](https://github.com/baldurk/renderdoc/issues/608) - baldurk / **
renderdoc ** Public

31. [Bloom causes massive performance hit (>50% framerate reduction) · Issue #13109 · bevyengine/bevy](https://github.com/bevyengine/bevy/issues/13109) - bevyengine / **
bevy ** Public

32. [The Industry-standard Toolkit to Measure GPU Performance](https://www.nridl.org/technical-blog/the-industry-standard-toolkit-to-measure-gpu-performance) - Audience: university-level gamers/builders Goal: show exactly which tools the industry uses to recor...

33. [GitHub - vkmark/vkmark: Vulkan benchmark](https://github.com/vkmark/vkmark) - vkmark / **
vkmark ** Public

34. [GitHub - google/uVkCompute: A micro Vulkan compute pipeline and a collection of benchmarking compute shaders](https://github.com/google/uVkCompute) - A micro Vulkan compute pipeline and a collection of benchmarking compute shaders - google/uVkCompute

35. [端到端GPU 性能分析与瓶颈定位工作流：Nsight/RenderDoc/AMD RGP](https://beefed.ai/zh/gpu-profiling-bottleneck-resolution-workflow) - 本文展示一个端到端 GPU 性能分析工作流，结合 Nsight、AMD RGP 与 RenderDoc，帮助你收集追踪、分析 CPU 与 GPU 平衡、定位热点并验证修复效果。

36. [1% & 0.1% Low FPS Results — Useful or Useless? - YouTube](https://www.youtube.com/watch?v=CWQtUfvDhOI) - Average, Min, & Max FPS was used for years, but recently 1% and 0.1% lows became more common. Are th...

37. [No Swapchain - No Problem. Finally got headless iGPU to Render](https://www.reddit.com/r/vulkan/comments/1pd5w3s/no_swapchain_no_problem_finally_got_headless_igpu/) - No Swapchain - No Problem. Finally got headless iGPU to Render

38. [Code Replicability in Computer Graphics](https://replicability.graphics) - Code Replicability in Computer Graphics


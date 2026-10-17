# Issue #9: hardware terminology and boundaries

研究日期：2026-10-08。範圍係 vendor hardware vocabulary、官方 host protocol，同本 repo inherited Ableton / Bitwig source；唔包含 runtime implementation 或 product-policy 決定。主題係 [issue #9](https://github.com/joshuahhn/roto_control/issues/9) 嘅 COMP-owned / CUSTOM Layout 保存邊界。

## Evidence 同版本

- **Vendor documentation：** [ROTO-CONTROL User Manual 1.1.4](https://www.melbourneinstruments.com/s/ROTO-UserManual-V1-1-4-April2025.pdf)、[3.3.0 release notes](https://www.melbourneinstruments.com/s/Roto-Control-Release-Notes-3-3-0.pdf)、repo [SysEx API v1.6](../../../../docs/ROTO-CONTROL_SYSEX_API_v1.6.pdf) 同 [Serial API v1.3](../../../../docs/ROTO-CONTROL_SERIAL_API_v1.3.pdf)。API references 以 section 為準；SysEx PDF page number 比 printed page number 多 2，避免混淆。
- **Current official publication：** [官方 downloads / FAQ](https://www.melbourneinstruments.com/roto) 列 3.3.0，release date 2026-10-02；同頁 User Manual 仍係 firmware 1.1.4、2025-04-16。因此舊 manual 唔可以單獨證明新 firmware 嘅所有 gestures。3.3.0 release notes 已透過官方 URL 下載並讀完整一頁；web extractor 無法 fetch 該 PDF，唔等於文件不存在。
- **Integration source：** 呢度引用 repo 保存嘅 [Ableton](../../../ableton/ROTO_CONTROL.py) / [Bitwig](../../../bitwig/src/main/java/com/bitwig/extensions/controllers/melbourneinstruments/device/PluginModeHandler.java) snapshot，唔聲稱已核對 downloadable 3.3.0 integrations 嘅所有差異。
- **Physical acceptance：** 引用 existing user-confirmed evidence，唔係今次重新測試。今次冇連硬件、冇操作 live TD、冇讀寫 controller firmware/configuration。

## 同一個 button，必須帶 mode / view context 解讀

以下係 vendor manual printed pp. 4, 6, 9–10, 14–15 嘅操作語意；最新 clear gesture 見下一節。

| Hardware context | FUNC | SEL | Arrows | LOCK |
| --- | --- | --- | --- | --- |
| MIX | Track Focus：同一 Track 嘅 volume / pan / sends | 改 knob / button mixer functions | Track list / mixer navigation | 阻止 knob touch 改 Track，同時停止 host Track follow |
| PLUGIN, normal control view | 進入 Track selection | Hold 選同 Track 嘅 Device / Plugin；toggle 可進 enable view | 換同一 Device 嘅 control page | 保持 routing Device，容許 host selection 另行移動 |
| PLUGIN, selector view | Track list context | Device list context | 瀏覽對應 list bank | 唔代表所有 explicit selection 都被禁用；source exception 見下文 |
| MIDI | Clock / Motion Recorder settings | 選 controller 儲存嘅 MIDI Setup | Setup / controls / Motion Recorder context navigation | 唔應套用 PLUGIN routing contract |

**Hardware MODE** 係 MIX / PLUGIN / MIDI。Issue #9 嘅 **COMP / CUSTOM** 係 proposed TD Layout ownership classification；佢哋唔係 manual 裏面兩個新增 hardware modes。**TD Layout** 亦唔係 MIDI mode 嘅 MIDI Setup selector。上表唔賦予 TD MIX、transport 或 MIDI Setup 功能。[User Manual, printed pp. 4, 6, 10, 15](https://www.melbourneinstruments.com/s/ROTO-UserManual-V1-1-4-April2025.pdf)

## 3.3.0 更改咗 touch / Clear gesture

官方 **3.3.0 release notes p. 1** 更新 PLUGIN learned-control 清除：hold LEARN → 對 knob slight turn 或 firm touch → knob 下方 button 顯示 CLEAR → 按該 button 確認。MIDI LEARN / clear 亦改成 slight turn 或 firm touch 揀 knob，再選 CLEAR；LEARN touch sensitivity 較低，要求 deliberate firm touch。舊 manual printed p. 12 同現時 FAQ 嘅「touch again to confirm」唔能當作 3.3.0 唯一正確指示。[3.3.0 release notes](https://www.melbourneinstruments.com/s/Roto-Control-Release-Notes-3-3-0.pdf)

Hardware LEARN 係 controller 參與嘅 assignment workflow，唔係單純 TD registration 或 parameter write。現有 protocol 分 **LEARN enable / disable**、**host parameter offer**、**mapping report** 同 **successful learned notification**；確認／持久化 timing 要跟 actual firmware evidence，唔可以將 host offer 當作已保存。[SysEx API v1.6 §§3.9–3.11, 3.17](../../../../docs/ROTO-CONTROL_SYSEX_API_v1.6.pdf)

## Protocol 有三種 page，唔可以叫晒 bank

| Term | Exact protocol / source evidence | Meaning / boundary |
| --- | --- | --- |
| Track list bank | GENERAL `05 FIRST TRACK` / `06 SET FIRST TRACK`, §2.5–2.6 | 第一個 Track index，8 嘅倍數；只改瀏覽窗口 |
| Track selection | GENERAL `09 ROTO SELECT TRACK`, §2.9 | Host Track index；同瀏覽窗口唔係同一件事 |
| Device list bank | PLUGIN `03 FIRST PLUGIN` / `04 SET FIRST PLUGIN`, §3.3–3.4 | 第一個 Device index，8 嘅倍數；唔等於 control page |
| Device selection | PLUGIN `07 ROTO SELECT PLUGIN`, §3.7 | Hardware-origin request；Ableton 將收到 index 加 current first-Device offset，因此該實作係 bank-relative input |
| Host-selected Device | PLUGIN `08 DAW SELECT PLUGIN`, §3.8 | `PI` Device index、`MP` macro control-page index、`FS` force selection；`FS=1` 可以 override PLUGIN LOCK |
| Learned control page | PLUGIN `0B CONTROL MAPPED`, §3.11 | 報告 current page 嘅 parameter index/hash、control type 同 physical slot；唔包含 TD Layout ID |
| Macro / Remote control page | PLUGIN `10 MACRO PLUGIN PAGE INDEX`, §3.16 | 零起算 control-page index，只有 MACRO Plugin 先有；唔係通用 normal learned-page selection API |

以上命令 definitions 來自 [SysEx API v1.6 §§2.5–2.9, 3.3–3.11, 3.16](../../../../docs/ROTO-CONTROL_SYSEX_API_v1.6.pdf)；bank-relative selection 嘅精確實作係 [Ableton `SET_FIRST_DEVICE` / `ROTO_CONTROL_SELECT_DEVICE`](../../../ableton/ROTO_CONTROL.py#L1471-L1494)。API §3.7 本身只寫 Plugin index，冇清楚寫 bank-relative，應保留呢個 documentation / implementation distinction。

**未見 TD Layout selector 嘅 protocol contract。** 呢兩份 host-facing evidence 描述 Track、Plugin 同 controls；唔定義 issue #9 COMP-owned Layout / CUSTOM Layout 嘅 enum、Layout ID 或硬件 selection gesture。呢個係「現有公開 contract 冇呢項 TD domain concept」，唔係斷言所有 firmware 永遠冇可能新增功能。將 COMP 放入另一個 TD Layout 之後，佢會唔會仍然出現喺目前 Track 嘅 SEL list，係 host publication / aggregation policy，唔會因 ownership 更改而自動由硬件提供。

**Published restrictions 同 observed firmware behavior 要分開。** API §3.21 `SET TRACK SELECT MODE`、§3.22 `SET PLUGIN ENABLE MODE`、§3.23 `SET PLUGIN SELECT MODE` 明確寫 Logic Pro only；GENERAL `14/15 ROTO PAGE LEFT/RIGHT` 嘅公開描述亦限定 Logic MIX Track Focus。但本 repo 實際 normal PLUGIN [control-page trace](../../diagnostics/runtime/results/control_page_trace.json) 記錄到 GENERAL `14/15`，當時 TD host 宣告嘅係 Ableton-compatible identity，而唔係 Logic。[Host identity](../../code/py/roto_python/protocol.py#L254-L256)，[HANDOFF control-page regression](../../HANDOFF.md#physical-plugin-control-page-regression-acceptance-2026-10-07)

因此，呢個 local firmware / session 已觀察到 arrow-change events，唔可以講 TD 收唔到；但 event 仍冇 normal Plugin 嘅 absolute page index，亦唔證明所有 firmware / console views 都發送每次 raw key press。Local handler 將 GENERAL `14/15` 視為 `page_changed()`，再透過 parameter index/hash reports 重建 current mapping。要保留公開 API restriction 同現場 exception 嘅兩份證據，而唔係將其中一份當作所有版本保證。[Local page-change handler](../../code/py/roto_python/layouts.py#L582-L587)，[HANDOFF page-library fix](../../HANDOFF.md#plugin-control-page-overwrite-fix-2026-10-07)，[SysEx API v1.6 §§2.20–2.21, 3.21–3.23](../../../../docs/ROTO-CONTROL_SYSEX_API_v1.6.pdf)

## Track group、Device / Plugin、Setup、Preset 分別係乜

- **Track / Track group：** Vendor Track 係 host 發佈嘅 Track；`TRACK DETAILS.GT` 係 grouped-track flag，MIX `06 TOGGLE TRACK GROUPING` 係可適用 Track 嘅展開／收起要求。Ableton 對 `track.is_foldable` 改 `fold_state`。TD UI「Track group (FUNC)」係用 Track 層去做 tools grouping，唔自動等於 Ableton foldable Group Track，也唔等於 root TD Layout。[SysEx API §§2.7, 4.6](../../../../docs/ROTO-CONTROL_SYSEX_API_v1.6.pdf)，[Ableton group toggle](../../../ableton/ROTO_CONTROL.py#L1741-L1758)
- **Device / Plugin：** Protocol 同一 selectable 層；唔係只指 third-party VST。`PLUGIN DETAILS` 帶 Plugin hash、enabled、display name、type（Normal / Macro / Third-party）同 macro pages count。[SysEx API §3.5](../../../../docs/ROTO-CONTROL_SYSEX_API_v1.6.pdf)
- **MIDI Setup：** Controller MIDI-mode configuration。Serial API `GET CURRENT SETUP / GET SETUP / SET SETUP / SET SETUP NAME` 屬 MIDI commands，index `00–3F`；唔係 host TD Layout。[Serial API v1.3 §§3.1–3.4](../../../../docs/ROTO-CONTROL_SERIAL_API_v1.3.pdf)
- **PLUGIN Setup / config：** Roto-Setup app 可以 import/export 嘅 Plugin mapping/control configuration；Serial API 命名亦會用 setup name，但條目以 Plugin hash 識別。唔應單用「Setup」概括埋 MIDI Setup、TD Layout 同 numeric Preset。[Serial API §§4.2–4.4, 4.9–4.12](../../../../docs/ROTO-CONTROL_SERIAL_API_v1.3.pdf)
- **Preset recall：** Ableton source 講嘅 instrument / effect preset 同 mappings identity 係兩件事：支援 preset recall 嘅 Device 用 class name 算 Plugin hash，目的係 different presets 用同一 mapping；其他 Device 用 class + name，racks 有特例。呢度唔係 controller loading preset numeric values 嘅 API。Issue #9 自己要求 TD Layout selection 唔寫 numeric preset / 唔 trigger Pulse。[Ableton `_process_return_plugin_names`](../../../ableton/ROTO_CONTROL.py#L1769-L1817)，[issue #9 acceptance criteria](https://github.com/joshuahhn/roto_control/issues/9)

## Physical input、haptics 同 TD action 唔係同一層

| Layer | Confirmed terms | Separation |
| --- | --- | --- |
| Physical control | Knob / Switch（UI 通常叫 Button），control type `00/01`；同一頁各 8 slots | Kind + slot 先定位 physical control；唔係 parameter identity |
| Ordinary PLUGIN transport（非 Logic） | MIDI channel 16；knobs CC `12–19` + `44–51`，14-bit；switches CC `20–27`，7-bit；knob touch CC `52–59`，`7F/00` | Turn/value、touch，同 mapping metadata 係獨立 messages |
| Hardware knob haptics | `KNOB_300`、`KNOB_N_STEP`、`KNOB_300_TOP_INDENT`；indent positions / steps / step names | 觸感／detents，同 target-unit conversion、TD min/max policy 唔係同一件事 |
| Hardware switch behavior | Serial config 欄 HM：`PUSH=00`、`TOGGLE=01`；LED on/off colors | 硬件 event/latch 配置；唔係 TD Toggle / Pulse / Cycle consumer action |
| TD consumer action | Local `button_type` 接受 `push/toggle`；host control mode 另行定義 | Host 宣告期望 hardware type 並唔證明有改 hardware config |

資料來自 [SysEx API §§3.11, 3.17, Appendix B.2](../../../../docs/ROTO-CONTROL_SYSEX_API_v1.6.pdf)、[Serial API §§4.9–4.12](../../../../docs/ROTO-CONTROL_SERIAL_API_v1.3.pdf)、[local controls validation](../../code/py/roto_python/controls.py#L14-L27)。Serial config 寫入需要 `START CONFIG UPDATE` session；TD [CONTEXT constraints](../../CONTEXT.md) 明確唔做 serial/firmware/configuration writes。SysEx `LEARN PARAM` 有 centre-indent / steps / labels metadata，唔等同提供完整 Serial haptic config editor。[SysEx API §3.10](../../../../docs/ROTO-CONTROL_SYSEX_API_v1.6.pdf)

## LOCK 有 selection / routing 分離

Vendor protocol `SET PLUGINS LOCK` 只報 lock state；host `DAW SELECT PLUGIN.FS` 可以強制 override。Ableton 鎖住 Track / Device 後，explicit hardware Device selection 仍可更新 `_locked_device`；unlock 清 handles 並跟 host selection。Bitwig `lockDevice()` 設 `cursorDevice.isPinned()`，explicit `selectPlugin()` 會 temporarily unpin → select → repin。兩個 integration 都唔將 LOCK 當作「所有 Device selection 無效」。[SysEx API §§3.8, 3.13](../../../../docs/ROTO-CONTROL_SYSEX_API_v1.6.pdf)，[Ableton explicit selection](../../../ableton/ROTO_CONTROL.py#L1478-L1493)，[Ableton lock](../../../ableton/ROTO_CONTROL.py#L1653-L1665)，[Bitwig select](../../../bitwig/src/main/java/com/bitwig/extensions/controllers/melbourneinstruments/device/PluginModeHandler.java#L226-L233)，[Bitwig lock](../../../bitwig/src/main/java/com/bitwig/extensions/controllers/melbourneinstruments/device/PluginModeHandler.java#L503-L505)

Issue #9 嘅跨 Layout selection under LOCK、ownership switch 同 input-fence policy 未由 vendor contract 自動決定；要另外寫 host contract。Bitwig 自動 Remote pages 亦係 host cursor context，唔係 TD Layout ownership 功能。[Bitwig cursor / pages](../../../bitwig/src/main/java/com/bitwig/extensions/controllers/melbourneinstruments/RotoViewControl.java#L45-L65)

## 已有 physical evidence 同未證實邊界

Existing evidence 已接受九號 **Track** 嘅第二 bank、Track A/B recall 同 routing isolation；亦接受同 routing Track 內嘅兩個 **Device** 在 LOCK 下 SEL selection、mapped knob / button / LED / LCD / motor feedback 同 cross-Device isolation。[Track evidence](../../diagnostics/runtime/results/multitrack_hardware_verification.json)，[Device LOCK selection evidence](../../diagnostics/runtime/results/device_lock_hardware_verification.json)，[locked controls / motor evidence](../../diagnostics/runtime/results/device_lock_controls_hardware_verification.json)，[HANDOFF final physical sections](../../HANDOFF.md)

呢啲唔構成 issue #9 新 ownership／dedicated Layout 嘅 physical acceptance。仍要分別驗：

- 九號 Device 嘅第二 SEL bank（九號 Track acceptance 唔可以代替）。
- LOCK 期間 TD COMP selection / Follow 嘅實際 hardware behavior。
- 同 parameter 嘅兩個 Layout mapping views 嘅 motor/LCD/value synchronization。
- dedicated per-COMP Layout 切換、CUSTOM ↔ COMP-owned selection，同目前 FUNC/SEL list scope 嘅關係。
- 3.3.0 updated Clear gesture；目前 hardware firmware 版本亦未喺今次重新讀取。

**公開 FAQ 語境矛盾：** FAQ 有一句話否認 SysEx send/receive，但 vendor SysEx API 同 integrations 明確用 SysEx 做 DAW host protocol。可以確定 host protocol 存在；唔能由此推論 MIDI mode 支援任意 user SysEx mapping，也唔應由 FAQ 反推 TD host 冇 SysEx。[官方 FAQ](https://www.melbourneinstruments.com/roto)，[SysEx API v1.6](../../../../docs/ROTO-CONTROL_SYSEX_API_v1.6.pdf)

## 對 issue #9 嘅研究結論

COMP-owned / CUSTOM Layout 係 TD 保存與 ownership 層；Track → Device → control pages 係公開 hardware host 層。要做到用語一致，必須逐個操作寫清楚佢改 **ownership、published hardware list、selected context、routing context、mapping configuration，定 target value**。Vendor contract 唔會替 TD 決定跨 Layout list aggregation、mode-switch gesture 或 Follow policy；呢啲仍係未定 product choices，唔應包裝成 hardware 已有嘅名稱／能力。

用戶其後已確認本次方向：沿用 FUNC／Hold SEL／arrows 嘅硬體層級，令 TD 用語及行為一致；Layout 繼續喺 TD 管理。本次唔要求新增跨 Layout hardware selector。Resolved direction 同實際 TD UI parity gaps 見 [boundary analysis](issue-9-boundaries.md)。

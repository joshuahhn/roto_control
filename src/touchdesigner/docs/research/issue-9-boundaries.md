# Issue #9：ownership、hardware navigation 同 input 邊界

研究日期：2026-10-08。呢份係調查及 specification clarification，冇實作 #9、改 hardware configuration 或新增 physical acceptance。

後續已讀返用戶決定同 Inspector `.45`：**Inspector integration 以 [context contract](../plans/inspector-context-contract.md) 為準**。本 note 保留 hardware／source evidence；唔將 controller active selectors 同 Inspector browse dropdowns 當作同一 command。

## 結論

Issue #9 定義 **COMP-owned／Custom Layout 保存隔離**，但冇定義硬體如何跨 Layout 選擇。兩者必須分開驗收：mapping ownership 正確，唔代表硬體同 TD 已有相同 navigation。

現有硬體／host contract 係 **PLUGIN mode → Track（FUNC）→ Device（Hold SEL）→ control page（normal-view arrows）**。TD Layout 喺呢棵 navigation tree 外面。每 COMP 一份專屬 Layout，會令原本同 Track 嘅 COMP Devices 分散到不同 Layout；單靠 SEL 無法再喺嗰個 list 揀晒佢哋。#10 補跨 Layout TD Follow，但明確保留 FUNC／SEL 嘅 Active Layout／Track scope，所以亦未解決呢個差異。[Issue #9](https://github.com/joshuahhn/roto_control/issues/9)、[Issue #10](https://github.com/joshuahhn/roto_control/issues/10)、[hardware evidence](issue-9-hardware-terminology.md)。

**用戶已確認方向（2026-10-08）：沿用硬體 FUNC 揀 Track、Hold SEL 揀 Device、箭嘴換 control page；TD 使用相同層級、名稱同操作語意。** Layout ownership 管保存，Track／Device／control page 管 navigation。Layout 繼續由 TD 選擇；本次毋須新增 COMP／CUSTOM 或跨 Layout hardware selector。唔好用 COMP／CUSTOM 叫 hardware mode，亦唔好用 Layout 代替 Track。

因此 #9 嘅 ownership scope 同呢個方向可以相容：先喺 TD 揀 Layout，再由 TD／硬體用相同 Track → Device → control page 模型操作。分開專屬 Layout 後，SEL list 嘅候選範圍會跟住目前 routing Track 改變，必須喺 TD 顯示清楚。

## 四條獨立邊界

| 邊界 | Canonical terms | Authority／責任 |
| --- | --- | --- |
| 保存歸屬 | Layout、COMP-owned、Custom | TD 保存 configuration；#9 新增 ownership。 |
| 操作導航 | Hardware Mode、Track group、Device、control page、list bank | Hardware mode/view 決定按鍵作用；host announce lists 同 commit routing。 |
| Input 解碼 | Knob value、touch、Hardware Button Type | MIDI adapter 解碼；TYPE 宣告必須符合實體設定。 |
| Consumer 行為 | Parameter target、Toggle／Pulse／Cycle、Preset recall | TD adapter／consumer 決定寫值或執行 action。 |

Device 同 protocol/API 嘅 Plugin 係同一層；**TD plugin** 作口語係整個 integration，唔係另一個 Device hierarchy。Root [GLOSSARY.md](../../../../GLOSSARY.md) 定義 canonical terms；現有 protocol/API 名稱唔因 glossary 而改動。

## 已確認嘅現有實作

- Registry v3 保存 `Layout → Tracks → Plugins`；Layout 冇 owner/category 欄位，Focus link 喺 Device。Tag discovery 將新 Device 放入 **Active Layout／Active Track**，而唔係建 COMP-owned Layout。`CUSTOM` 目前可以只係 default Device display name，唔係 ownership。[layouts.py](../../code/py/roto_python/layouts.py#L43)、[validation](../../code/py/roto_python/layouts.py#L77)、[empty records](../../code/py/roto_python/layouts.py#L411)、[sync_tags](../../code/py/roto_python/text_comp_follow.py#L80)。
- Track announcements 只列 Active Layout 嘅 Tracks；Device announcements 只列 routing Track 嘅 Plugins。Hardware selector messages 冇要求 host 選 TD Layout 嘅既有處理路徑。[announcements](../../code/py/roto_python/layouts.py#L238)、[receive](../../code/py/roto_python/layouts.py#L613)。呢個係本 integration 嘅目前 contract，唔係斷言 firmware 永遠無法擴充。
- Focus link 用嚟 resolve COMP selection 同 learning scope，唔等於 COMP 擁有配置。其他 mapping variants 可引用同一 COMP 嘅 parameters；目前同一 Layout 只准一個該 COMP 嘅 Follow link。[set_link／resolve](../../code/py/roto_python/text_comp_follow.py#L217)、[Layouts docs](../functions/layouts.md)。
- Layout／Device selection 讀 live parameter values；Pulse 初始化為零，唔因 selection 執行。保存 record 係 assignments、ranges、identities 同 library，唔係 numeric preset。[resolve](../../code/py/roto_python/layouts.py#L272)、[snapshot](../../code/py/roto_python/layouts.py#L162)。
- Normal Plugin control-page change 冇 absolute page index。Host 清除 active slot routing，保留 library，再用 CONTROL MAPPED 嘅 parameter index/hash/kind/slot 建立 routing。唔可以靠 arrow count 宣稱可靠 Page 1..8 address。[page_changed／recall_page_target](../../code/py/roto_python/layouts.py#L510)。

## Input 要一致，係 action 同 routing 一致

| Input／setting | 實際意思 | TD 對應與限制 |
| --- | --- | --- |
| Knob rotation | PLUGIN channel 16，CC12–19 MSB + CC44–51 LSB，14-bit absolute value | `raw / 16383` → mapping range → Float／Int／Menu；Int／Menu 轉換唔等於讀回實體 detents。 |
| Knob touch | CC52–59；touch／release notification | 顯示／motor deferral，唔係另一個 numeric value input。 |
| Button PUSH | Press／release 訊號 | Toggle：True／False；Pulse／Cycle：rising press 執行，held duplicate／release 唔再執行。 |
| Button TOGGLE | Latched 訊號，每次按可以係 127 或 0 | Toggle：跟 latched value；Pulse／Cycle：兩種值都可以係一次按掣，唔可以只將 127 當 press；保留目前 debounce。 |
| `button_type`／Inspector HW Type | Host 選用嘅 RX adapter 宣告 | 唔會改 Roto-Setup TYPE，亦唔係已驗證 read-back。 |
| TD Value input Float／Int | Target 數值編輯／conversion semantics | 唔係 hardware smooth／step／centre／custom-indent detection；read-back 屬 #7。 |

Evidence：[collection_protocol.py RX](../../code/py/roto_python/collection_protocol.py#L239)、[Controls validation](../../code/py/roto_python/controls.py#L7)、[Binding conversion](../../code/py/roto_python/binding.py#L95)、[button behavior docs](../functions/controls.md)、[Serial read-back issue #7](https://github.com/joshuahhn/roto_control/issues/7)、[vendor input evidence](issue-9-hardware-terminology.md)。

例如同一個 Reset action，PUSH 要忽略 release；TOGGLE 嘅下一次零值仍要執行。要一致嘅係 **一次有效按掣 → 一次相同行為**，而唔係要求兩種 hardware TYPE 送相同 bytes。Motor／LED／LCD feedback 亦要同一次成功 consumer dispatch 一致，唔可以只因已收到 CC 就報成功。

## Shared parameter 唔等於 shared mapping

例：COMP-owned mapping A 將 Knob 1 指向 `Speed`，range 0–10；Custom mapping B 將 Knob 3 指向同一 `Speed`，range 0–20。A 寫 Speed=5 後，B 再 recall 必須讀 5；A 嘅 motor 比例係 50%，B 係 25%。兩邊真實 target value 一致，slot／range／normalized feedback 唔需要相同。改 A range 唔可以改 B，亦唔可以為咗切換配置把 Speed 還原舊值。[#9](https://github.com/joshuahhn/roto_control/issues/9)、[Binding conversion](../../code/py/roto_python/binding.py#L95)。

目前只有 routing Device 嘅 active controls/watchers 工作，唔可將 inactive view 嘅 cached catalog value 當最新值。#9 要驗證重新 recall／重新顯示時讀 live value；如果要 inactive Inspector view 即時刷新，必須另外寫明 freshness contract。[page_changed](../../code/py/roto_python/layouts.py#L510)、[install](../../code/py/roto_python/layouts.py#L289)。

同一配置嘅 active collection 目前拒絕 duplicate parameter／shared BIND master；#9 允許係**不同 configurations** 引用同一 parameter，唔表示取消呢個 guard。[controls.py](../../code/py/roto_python/controls.py#L26)。

## #9 同相鄰 tickets 嘅界線

| Ticket | 責任 | 唔應混入嘅語意 |
| --- | --- | --- |
| [#9](https://github.com/joshuahhn/roto_control/issues/9) | COMP-owned／Custom 保存邊界、手動 TD selection、shared values／independent mappings | 未定新 hardware selector；唔因選 Layout recall values。 |
| [#10](https://github.com/joshuahhn/roto_control/issues/10) | TD selected COMP 跨 Layout Follow，同步已 commit routing／announcements | 冇跨 Layout FUNC／SEL contract；冇 hardware → TD pane reveal。 |
| [#11](https://github.com/joshuahhn/roto_control/issues/11) | 舊 records 明確 migration、recovery、identities／variants 保留 | 唔靠同名、同 parameter 或同 Focus link 自動合併 owner。 |
| [#12](https://github.com/joshuahhn/roto_control/issues/12) | Button 調用具名 COMP preset action／callback | Mapping recall／LEARN／selection 唔執行 action。 |
| [#13](https://github.com/joshuahhn/roto_control/issues/13) | 保存／recall 明確 parameter value snapshots | Snapshot 係 values；Layout 係 mappings。 |
| [#7](https://github.com/joshuahhn/roto_control/issues/7) | 可行性研究：physical settings read-back | 宣告 adapter／TD type 唔可充當硬體讀值證據。 |

## Inspector 同 active selectors 嘅區別

早期研究嘅 LOCK 比較針對 controller custom-parameter active selectors／SelectTrack／SelectPlugin，唔適用於 compact Inspector 嘅三個 browse dropdowns。Device-first header 亦只係 display order。

Inspector `.45` 已有明確 **Browse → Activate**：dropdowns 只改 Viewing；Activate 一次 SelectPlugin 完整 context，可跨已存在 Layouts，保留 LOCK／LEARN／touch／pending 等 guards；LIVE 只返回 Routing view，Follow preference 保持。呢個 baseline 毋須改為自動 routing dropdown 或硬體 LOCK 例外。

Hardware FUNC／SEL list scope、LOCK source-policy 差異、normal control-page 可觀測性，同後續管理 commands，集中定義於 [integration contract §§2–6](../plans/inspector-context-contract.md)。Evidence：[active selector handlers](../../code/py/roto_python/RotoPythonExt.py#L1171)、[guard](../../code/py/roto_python/layouts.py#L265)、[hardware receive](../../code/py/roto_python/layouts.py#L604)。

## 實作前仍需釐清嘅 contract

1. **Owner lifecycle prerequisite**：#9 仍要固定 durable owner key、clone conflict、unregister／missing／replacement／relink mechanism；metadata、name 同 Focus 已分開定義，唔再係名詞未定。
2. **Owner variants／Follow 入口**：保留 Track／Device 結構同全部 variants；新 owner 預設 empty Track＋owner Device 係 allocation 建議。#10 須 resolve 唯一 owner 同明確 default context；Custom shared references 唔當 Follow candidate。
3. **Physical SEL→FUNC 疑問**：opening views 嘅 accepted trace 唔等於完整 A/B selection；最少 missing trace 已併入 [最後一次統一驗證](../plans/inspector-context-contract.md#8-最後一次統一驗證只加缺失嘅ab證據)。

Control-page 保存權、Inspector Browse／Activate 同 Selected／Routing 已於 contract 收斂。Source-specific LOCK policy 維持；TD explicit locked request 或 absolute control-page editor 如要新增，屬明確 future scope。

層級方向已由用戶確認；其餘係 specification gaps／implementation 建議。未建立 ADR，亦未改 GitHub issue body／labels。

## 建議 acceptance scenarios

- 原本同 Track 嘅 pixelSortV3／fractal_pop，分到專屬 Layout 後：列明 TD 同 hardware 各自完整 selection sequence；可達性唔可以只用 TD Follow 測試代表。
- 同名兩個 COMPs，rename／reparent／reload 後 owner 唔混淆；missing／recreated owner 有明確結果；manual Custom references 保留。
- 上述 Speed=5／兩種 ranges 例子：兩邊讀相同 live value，independent slots/ranges/library；切換唔寫 value／Pulse。
- 同一 Reset 用 PUSH／TOGGLE 各重複按：每次有效 press 只執行一次；LEARN／mapping ACK／selection／reconnect 唔執行。
- 分別驗 Track bank、Device bank 同 control pages；唔用 ninth-Track 成功代替 eighth-control-page 成功。
- LOCK selected/routing divergence 同 #4 batch/half-pair regressions 分開驗，唔以 UI context label 當 physical input correctness。

Software、native TD 同 physical acceptance 分開記錄。HANDOFF 已有 two-control-page physical acceptance，但 functions/layouts.md 尾段仍寫 pending；八 control pages／128 targets 只有 software coverage，ninth-Device physical banking 仍 pending。呢啲舊證據都唔等於 #9 專屬 Layout 模型驗收。[HANDOFF](../../HANDOFF.md)、[Layouts acceptance status](../functions/layouts.md#acceptance-status)。

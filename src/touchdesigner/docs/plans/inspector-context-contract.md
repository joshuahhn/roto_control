# Inspector ownership and selection contract

日期：2026-10-08。交付係設計 contract；冇實作 #9–#13、Inspector 管理 UI、migration 或 live TD changes。

已確認產品方向以 [PR #14](https://github.com/joshuahhn/roto_control/pull/14) 同 [#9](https://github.com/joshuahhn/roto_control/issues/9)、[#10](https://github.com/joshuahhn/roto_control/issues/10)、[#11](https://github.com/joshuahhn/roto_control/issues/11)、[#12](https://github.com/joshuahhn/roto_control/issues/12)、[#13](https://github.com/joshuahhn/roto_control/issues/13) 為準。本文件補 Inspector integration 同 selection 邊界，唔取代五張 implementation tickets。用語見 [GLOSSARY](../../../../GLOSSARY.md)；第一手 hardware／source evidence 見 [boundary research](../research/issue-9-boundaries.md) 同 [hardware terminology](../research/issue-9-hardware-terminology.md)。

## 1. 已收斂嘅模型

```text
保存歸屬（TD metadata）：COMP boundary／CUSTOM boundary
  COMP-owned：一個註冊 COMP → 一份專屬 Mapping Layout
  Custom：用戶手動管理嘅獨立 Mapping Layout

每份 Layout 內嘅配置樹：Track → Device（protocol Plugin）→ control pages
硬體 PLUGIN navigation：FUNC → Track；Hold SEL → Device；normal arrows → control page
Inspector：Browse context ──明確 Activate──> Routing context
           LIVE ──只返回／跟隨──> Routing context
```

Ownership 係 Layout 嘅屬性，唔係硬體新增 Mode 或 FUNC list 層。工具 COMP 可以同時係 Layout owner 同 Device Focus／parameter destination，兩種角色唔可以由同名推論或合併。

COMP 同 Custom 可以引用同一 parameter；真實 value 共享，assignments、ranges、IDs、control-page libraries 各自保存。選配置讀 live values；Action／Snapshot preset recall 屬 #12／#13，selection 唔執行佢哋。一個 active collection 內 duplicate parameter／BIND-master guard 繼續有效。

每 COMP 專屬 Layout 唔表示「Track 變咗 Device 嘅 child」。保留現有多 Track／多 Device／mapping variants 結構。新 owner Layout 建立時建議提供一個預設 Track 同 owner-linked Device 作入口，唔以 singleton 限制日後 variants；呢個係 #9 allocation 建議，唔係目前已實作 schema。

## 2. 四個必須獨立顯示／保存嘅對象

| 對象 | Identity／scope | 可以因乜改變 |
| --- | --- | --- |
| Layout ownership | Ownership category + stable registered owner identity；與 display names／Focus link 分開 | #9 allocation／明確 ownership workflow；#11 migration |
| Inspector Browse | 完整 `(layout_id, track_id, device_id)`，三個 ID 係同一條有效保存路徑 | Inspector dropdown／LIVE／成功 Activate |
| Routing | 已 commit 嘅完整 context；Connected／PLUGIN／per-control readiness 另外判斷 | Activate、hardware selection、guarded Follow、明確 active deletion successor |
| Hardware selection／pending | Selected Track、selected Device、pending source／reason 同 session；唔強拼成 routing triple | FUNC／SEL／LOCK／unlock／guards／latest intent |

Device-first header 係用戶選定嘅閱讀次序，唔改保存樹。Device 下面顯示 Layout／Track 係「所屬配置」breadcrumb。建議顯示 `Viewing: <Layout> / <Track> / <Device>` 同 `Routing: ...`；LOCK divergence 加 `Selected Track: ...`。BROWSE 同 LIVE 明示；Ownership 顯示 `COMP: <owner>` 或 `CUSTOM`，冇 metadata 嘅 legacy record 顯示 `Legacy / unclassified`，唔靠名字 CUSTOM 或已有 Focus link猜分類。

## 3. Inspector .45 command contract：保留，唔改成另一套 selection

Baseline：[Inspector thread](t3-thread://v1/eb7933f3-a3a9-452f-9b8b-dd9df9336bf7/a0ff5a7b-77be-4efd-9d9a-3e35d89da301) 嘅 `inspector_editor_actions.45.toe`。只讀核對其 `prototypes/inspector/commands.py`、`live_model.py`、`ui.py` 同 `activation_verification.json`；呢個 checkpoint 冇新 physical MIDI acceptance。

- **Browse**：Layout choices 來自全 registry，Track choices 限 browsed Layout，Device choices 限 browsed Track；更新 View key／children choices，唔呼叫 SelectLayout／SelectTrack／SelectPlugin，唔改 owner、values、Follow preference 或 hardware announcements。
- **Activate**：一次 `SelectPlugin(layout_id, track_id, device_id)`，可跨現有 Layout／Track，唔先切 Layout 再切 Track 再切 Device。重新驗 destination existence、session／routing token；失效就 refresh 同拒絕，唔 replay 舊 intent。
- **Guards**：LEARN、touch、LOCK、mutating／dispatch、pending／gated／backlog／paused，同 transport opening 唔容許 Activate。保留 .45 disabled reason，唔用 `hardware=True` 或 force-select 繞過。
- **Success**：確認 controller routing key 等於 destination，先關舊 editor draft 同返回 LIVE；Follow preference保持原值。Mapping readiness 逐 control 等 matching recall，唔把 Activate 返回成功當全部 mappings ready。
- **Failure**：保留 BROWSE 同 draft，報實際錯誤；重新讀 routing。Rollback failure 顯示 paused／gated 同 repair reason，唔報假成功、唔改成自動重試。
- **LIVE**：只將 View 跟返已 commit routing，唔 Activate browsed Device，唔 Connect，唔等於 Follow selected COMP toggle。
- **Offline**：完全 disconnected、冇 opening MIDI process 時可選本地 configuration；唔自動 Connect，唔聲稱硬體已 recall。LIVE 只表示跟隨本地 routing projection，Connected／ready 仍獨立。

Existing native evidence 已覆蓋 Browse 無 writes、一次 Activate、guards、stale session/routing、rollback、Fold／Popup、export 同原 catalog/process 保留。後續管理沿用同一 command/capability boundary，唔另建 UI 直接寫 registry／parameter 嘅 authority。

## 4. 真正可達嘅 selection 行為

| 操作來源 | 可揀範圍 | LOCK 下 | Context 後果 |
| --- | --- | --- | --- |
| Inspector Browse | 現有所有 Layouts；選定 Layout 嘅 Tracks；選定 Track 嘅 Devices | 可查看；可用操作另由 capability 判斷 | 只變 Viewing |
| Inspector Activate | 任一存在嘅完整 v3 context，包括跨 Layout | 拒絕；解鎖後重新驗 fresh intent再由用戶 Activate | 一次 commit 完整 Routing；FUNC／SEL lists 隨新 context announce |
| Hardware FUNC | Routing Layout 嘅 Tracks | Selected Track 可改；routing Track／Device 保持，unlock guarded follow | 唔可跨 TD Layout；browse bank 本身唔選 Track |
| Hardware SEL | Routing Track 嘅 Devices；唔係 LOCK 下另一 selected Track 嘅 Devices | Explicit Device selection 有例外，可以換 routing Track 內 Device，保持 LOCK 同 selected Track divergence | 唔改 Layout／routing Track；仍受 LEARN／touch／backlog guards |
| Normal-view arrows | Routing Device 嘅 learned control pages | 依 hardware page flow；唔改 Layout／Track／Device | 清舊 slots、保留 library、matching reports 恢復 input |
| Follow selected COMP | 目前只 resolve Routing Layout 內 unique Device Focus link | 延後；fresh session／latest intent／fences | #10 先擴至 COMP-owned Layouts；本次唔假稱已有跨 Layout Follow |

硬體 SEL 嘅 LOCK exception 同 Inspector Activate 嘅 guarded immediate command 係**已存在而不同嘅 source policy**。保持同一層級同成功 routing 語意；唔宣稱兩個 command 喺 LOCK 下完全等價。要容許 TD explicit request 同樣換 locked Device，須另定 request API／arbitration policy，唔屬 .45 或呢份 contract 嘅隱含改動。

COMP-owned Layout A/B 未分配之前，.45 只可以跨「已存在」Layouts。#9 完成後，先喺 Inspector browse／Activate 專屬 Layout；#10 完成後先有 TD selection 跨 owner Follow。FUNC／SEL 繼續局限目前 routing lists，唔 union 所有 owner Layouts。

Normal Plugin 冇 reliable absolute control-page index；Inspector 只顯示「currently recalled controls／awaiting recall」，唔加猜測 Page 1..8 selector。Track／Device list bank、Inspector filters 同 TD parameter pages 分別命名。已有 arrows 通知嘅 local trace，唔構成所有 firmware 都提供 raw console-key events 嘅保證。

Evidence：[routing key](../../code/py/roto_python/layouts.py#L152)、[activation](../../code/py/roto_python/layouts.py#L347)、[hardware selection](../../code/py/roto_python/layouts.py#L604)、[Follow guards](../../code/py/roto_python/text_comp_follow.py#L429)、[control pages](../../code/py/roto_python/layouts.py#L510)。

## 5. SEL 後 FUNC 出另一套「layout/layer」：判別 contract

歷史 [tab probe](t3-thread://v1/eb7933f3-a3a9-452f-9b8b-dd9df9336bf7/a0ff5a7b-77be-4efd-9d9a-3e35d89da301) 已有人確認 FUNC=`T／TRACK`、SEL=`pixelSortV3／fractal_pop`、放手 LCD=Device＋Track；其 capture 證明 opening views 時 routing 穩定，冇完整 Device A/B selection。最新所述現象保留為待一次統一 physical capture，唔當用戶理解錯誤，亦唔當已證實 bug。

判別唔靠畫面形狀，而係以下 invariants：

1. **Same Layout、same routing Track，SEL A→B**：只變 Device／current controls；完整 FUNC Track IDs、names、order 保持，外層 Layout ID 保持。可見 list bank 另行記錄，唔將窗口變化當成另一棵配置樹。
2. **換 Track**：同 Layout 嘅 FUNC list 保持；SEL Device list 改成新 routing Track，係正常 parent-scoped selection。
3. **跨 Layout Activate／未來 #10 Follow**：Layout ID 真係改，FUNC list 可改；必須記錄 activation source 同顯示新 Layout。
4. **只 Browse Device**：Inspector View 可以改；hardware lists／routing key 保持。睇落另一套 controls，唔證明硬體切換。
5. **LOCK**：FUNC selected Track 同 SEL routing Track 可以不同；明示兩者，唔以 selected Track替 routing Track生成 Device list。

如果 1／4 唔成立，係 context publication／routing 問題，唔以 name sync 修補。Device 喺其內 recall 另一套 mappings，係 Device control-page/library context，唔叫外層 Mapping Layout。曾提出嘅 Plugin name＝Layout name 已撤回；本 contract 唔復活嗰個方案。

**已查到嘅另一種畫面變化來源**：目前 `_select()` 每次真正換 context（包括同 Track 換 Device）會將 `first_track` 重設到 routing Track 所在嘅八項 bank，`first_plugin` 重設到 selected Device 嘅 bank。完整候選 list 可以冇變，但之前 browse 咗另一 bank 嘅 FUNC 畫面會返 routing Track 嘅 bank。呢個係已有 cursor policy，唔係 Device 擁有另一個 Layout；本次唔改呢個 policy。原來只有 T／TRACK 兩個 Tracks 嘅記錄只有一個 bank，單靠 bank reset 亦解釋唔到嗰個 A/B 疑問。Evidence：[selection bank reset](../../code/py/roto_python/layouts.py#L380)、[bank announcements](../../code/py/roto_python/layouts.py#L242)。

## 6. Inspector 管理功能嘅整合 contract

以下係下一步設計規則，未實作 commands。所有操作使用 selected record 嘅 stable IDs 同 parent IDs，唔以 dropdown display order／name／currently routing parent猜目的地。

| 操作 | 對象及 scope | Routing／identity contract |
| --- | --- | --- |
| Create Custom Layout | 新 user-owned configuration | 建 empty descendants，返回新 IDs 並 browse；獨立 Activate，唔複製 shared parameter mappings 或自動 routing |
| Register COMP／ensure owned Layout | #9 唯一 owner entry point | 建立／重用 owner Layout，重複註冊冪等；Generic Create Layout 唔偽造 COMP ownership |
| Create Track／Device | 明確指定 browsed parent IDs | 可建立 empty mapping context；唔改 owner、不 activate、不搬舊 mappings；唔由 COMP parent 推 Track |
| Rename Layout／Track／Device | Registry display metadata | IDs／hashes／library／values 保留；唔 rename TD COMP。Linked Device 跟 COMP name 時，普通 rename disabled；明確選 manual naming 先用 RenamePlugin，唔暗中 opt out |
| Delete inactive record | 指定 record 同 descendant mapping configurations | Confirmation 列 category／owner／完整 scope、library 影響；active hardware targets 保持；唔刪 target COMP／parameters／preset，也唔用 active slot-only unmap 誤清其他配置 |
| Delete active record | 指定 record，同明確可生存嘅 successor | 確認包含 routing 會轉邊個；用既有 manager 嘅 guarded successor 切換，唔自行拼多次 Select calls；last Layout／Track／Device guards 保留 |
| Delete COMP-owned Layout | 涉及 registration lifecycle | #9 owner lifecycle 未完成之前禁用 generic delete；避免 discovery 下次重建被刪 owner Layout。明確 unregister／preserve/recovery policy 後先支援 |

Management intents 重新驗 registry revision／target 存在性／parent chain／session／routing 同適用 guards；確認過期則取消並 refresh，唔重新指定到同名 record。Create／Rename 唔觸發 Pulse／Preset；delete 只移除選定配置，保留 user artifacts 同 recovery copies。API 故障報實際結果；冇明確 transactional 保證就唔宣稱 arbitrary side effects 可以 rollback。

Browse 先做點選，管理對象係 Browsed record；Activate／Clear Device 係 routing-affecting actions，維持現有 authority 同 capability 檢查。Inactive configuration management 可以喺獨立 registry command seam 設計；唔為咗管理先自動 Activate，亦唔直接繞過現有 manager guards。

## 7. 修正次序、完成界線同未決項目

1. **Inspector semantics 接入**：以本 contract 作 definitions；補 Viewing／Routing／owner metadata 來源同 command target scopes，保留 Device-first presentation、Browse→Activate、LIVE、Follow preference。可以按此繼續管理功能嘅設計；本 thread 唔建 UI。
2. **#9 allocation prerequisite**：先實作 owner metadata／idempotent ensure／missing-owner 狀態，再開 COMP-owned 管理功能。Owner ID 獨立於 name/path/Focus；portable locator 配 live handle 驗證。Owner 刪除／同 path replacement 保持 unavailable 直到明確 relink，唔自動奪取另一 COMP。Offline replacement 無法判別嘅既有限制要明報。
3. **#11 migration**：保留同一 owner 嘅所有 variants，用 Track／Device 承載；未 linked／ambiguous records 保留 legacy 分類同 recovery，唔 guess／merge。Owner Layout allocation 唔等於 mapping migration。
4. **#10 cross-owner Follow**：resolve 唯一 owner 同明確 default routing context，復用 arbiter／guards；Custom 引用同一 parameter 唔參與自動 owner 決定。
5. **#12／#13**：preset contract 保持獨立，唔加入管理功能作隱含 Layout recall。

仍需 implementation brief 固定嘅細節：durable owner key 嘅保存／clone conflict 機制、明確 unregister/delete/relink lifecycle、同 owner 多 variants 嘅 default Follow destination。建議 default 採 owner Layout 保存嘅 active Track／Device；冇唯一有效入口就拒絕 Follow 並報 ambiguity。呢啲係 runtime prerequisite，唔係名詞未定；未完成前相關 owner 功能顯示 unavailable。

今次唔要求 hardware 跨 Layout selector、TD LOCK exception、新 absolute control-page API。呢三項留作明確 future scope，唔阻塞 Browse／Activate contract，也唔包裝成已達完全 button-for-button parity。

## 8. 最後一次統一驗證：只加缺失嘅A/B證據

保留 Inspector thread 已排定嘅 Float↔Int re-LEARN／Menu LCD／Activate acceptance；唔重跑已接受 Track paging、LOCK selector／motor、two-page recall。由 Inspector thread 喺最後統一 fixture 準備一次被動記錄，唔喺本調查啟用 shared live hooks。

- Agent 先 capture 原 Routing/View/Follow/session、完整 registry 同六個 mappings/IDs/ACK/library baseline；記錄每次選擇 source、Routing triple、selected Track、完整 FUNC／SEL candidates、`first_track`／`first_plugin` 同當時可見 bank、matching mapping reports 同人手 LCD markers。Queued TX 唔當 wire delivery。LOCK/LEARN 關、touch 已 release；無需改 mappings 或建 test Layout。
- **A**：原 pixelSortV3 routing，開 FUNC 記一次 `T／TRACK`。Inspector 只 browse 同 Track 嘅 fractal_pop，確認仍 routing A；呢步亦覆蓋 Browse isolation。
- **B**：硬體 SEL 揀 fractal_pop，wait matching recall，再開 FUNC 記一次；呢步直接覆蓋用戶所述 SEL→FUNC 路徑。可用已有 assigned control 完成 suite 原定 input/LCD check。預期只 Device 改，Layout/Track 同 FUNC list 不變。
- **A return**：Inspector browse pixelSortV3，再按 Activate 一次，wait matching recall，再開 FUNC 記一次；呢步同時覆蓋 .45 新 Activate 嘅 physical gate。一次 A/B/A 已包含最新疑問，唔另外叫用家重做。Agent 檢查 context/library isolation 同既有 values baseline，停 recorder／restore hooks，恢復原 View／Routing／Follow；若 suite 改了 values，由既有 recovery 流程還原，唔在本步另觸發 Pulse／Preset。

逐項記 pass/fail；若只有可見 bank 改，先對照 cursor reset policy。若完整 FUNC candidates 改而 Layout/Track IDs 未變，或可見內容唔符合宣布嘅 bank，保存最少 trace 作 publication regression；若 IDs 改，沿 activation source 查真正 context transition。未有呢份 trace 之前，唔對最新 SEL→FUNC 現象宣稱 physical pass 或 root cause。

Ownership／跨 owner physical acceptance 等 #9／#10 具體實作後，併入嗰次 implementation 統一驗證；唔要求用家驗未存在嘅專屬 Layouts。

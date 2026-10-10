> Historical preparation snapshot: #9 is now CLOSED and source implementation uses accepted `61d0e03`. The current destination policy and gates are in [issue-10-owner-follow.md](issue-10-owner-follow.md); the original preparation record below is retained.

# Issue #10 — COMP-owned Layout Follow implementation brief

日期：2026-10-08。狀態：準備完成，等 #9；未開始 runtime implementation。

## 已核對嘅 baseline / blocker

- [#10](https://github.com/joshuahhn/roto_control/issues/10) 全文及 comments 已讀；OPEN，冇 comments。GitHub native `blocked_by` 仍有 [#9](https://github.com/joshuahhn/roto_control/issues/9)，`blocking` 為空。#9 亦 OPEN，冇 comments；未收到已完成、可整合嘅 stable owner metadata/API revision。
- 本 thread app binding：`t3/issue-10-comp-layout-follow`，worktree `/Users/huihongnin/.t3/worktrees/roto_control/t3-issue-10-comp-layout-follow`，起點 `1cb09d983f970fe4cc01b85639c7baccecd8b092`；開始時 staged／unstaged／untracked 全部為空。
- [Docs PR #14](https://github.com/joshuahhn/roto_control/pull/14) 仍 OPEN／未 merge；read-only spec revision `6dcd782c72cd22d9f5664a69a3bd4c4b0a21443d`。冇 cherry-pick 或複製佢嘅 files。
- Read-only 補充 contract：`/Users/huihongnin/project/roto_control/src/touchdesigner/docs/plans/inspector-context-contract.md`（另一 thread 未提交文件）。本 brief 只引用其 integration semantics，唔搬走、覆寫或 stage 原文件。
- 已讀 repo `AGENTS.md`、[CONTEXT](../../CONTEXT.md)、[HANDOFF](../../HANDOFF.md)、現有 Layout／Follow／Device sources/tests。此 checkout 冇 `docs/agents/`、`CONTEXT-MAP.md` 或 `GLOSSARY.md`；lazy domain docs 缺少唔阻塞準備。
- 已 load `td-general`、`td-comp-architecture`、`td-python-extension`。冇接觸 shared live TD、toe/tox、canonical artifacts、user mappings 或其他 worktrees。

唔以 #9 thread 存在、ready-for-agent label、docs approval 或局部 source diff 當 blocker 完成。Implementation 開始前，重新讀 #9／#10 全文、comments 同 native dependencies，取得 #9 完成／可整合嘅 handoff，記錄 branch、完整 revision 或 frozen reviewable diff identity、API contract 同 test evidence。Dependency 仲存在或完成證據不足時，繼續等協調確認，唔自行移除 edge。

## 最小 implementation scope

唯一選中嘅 eligible external COMP，經 #9 owner metadata resolve 到唯一 COMP-owned Layout，再取得該 owner 嘅明確 routing destination `(layout_id, track_id, plugin_id)`。用現有 guarded arbiter commit 一次完整 selection，讀取 live values、recall matching mappings，同步 controller／Inspector LIVE projection／hardware announcements。CUSTOM 可手動 Activate；即使有相同 parameter 或 Focus link，亦唔參與自動 owner 決定。

COMP／CUSTOM 係保存 ownership。Assignment、range、target identities、control pages 同 library 各自保存；target value 可以共享。Selection 唔写 numeric values、唔 pulse parameter、唔執行 callback／Action preset／Snapshot preset。#12／#13 未實作嘅功能唔喺呢張 ticket 補建。

保留 FUNC＝routing Layout 嘅 Tracks、SEL＝routing Track 嘅 Devices、normal arrows＝routing Device control pages。冇跨 Layout SEL union、新 hardware mode、absolute page index、migration 或 hardware→TD pane reveal。

## #9 必須交付嘅 integration contract

以下係 consumer 所需能力，唔係本 ticket 假設嘅新 method names 或 schema：

1. **Owner authority**：Layout category、durable registered owner identity 同 validated live COMP handle／portable locator 分開於 display names、parameter destinations 同 Device Focus links。Clone conflict、missing owner、same-path replacement、relink／unregister 必須有明確狀態；唔猜名字或以 op path 當 durable identity。
2. **Unique resolution**：對 eligible COMP 返回唯一 owner Layout，或者 unavailable／ambiguous；查詢唔建立 Layout、唔 discovery、唔重建 identities、唔移動 mappings。#10 唔建立第二份 owner registry。
3. **Default destination**：同 owner 有多 Track／Device variants 時，由 #9 指定明確入口。Contract 建議用 owner Layout 保存嘅 active Track／Device，但唔當已實作；入口 invalid／唔唯一就拒絕，唔揀第一個或限制為 singleton。Default Device Focus 可能同 owner 有不同角色，必須講清楚。
4. **Commit-time validation**：resolve 嘅 owner proof 同完整 destination 可喺 guard 解除後重新驗證。Owner deletion／relink／clone conflict／destination change 唔可以將舊 intent 轉去同名 replacement；用 #9 提供嘅 revision／identity mechanism，唔另造 schema。
5. **Persistence / lifecycle**：rename、reparent、save/reload 保持 owner、Layout、Track、Device、mapping IDs／indices／wire hashes 同 libraries。Generic tox 仍 empty／disconnected／Follow off／無 user ownership。冇 metadata 嘅 legacy record 按 #9 contract 處理，唔由 Focus link補猜 COMP category。

未有以上 stable contract 前，以下只係 integration plan，唔落 runtime code 或 placeholder。

## Source integration points

| Source seam | 現況 | #10 最小改動／保留界線 |
| --- | --- | --- |
| [CompFollower.resolve / select](../../code/py/roto_python/text_comp_follow.py) | 只搜尋 Active Layout 嘅 bound Device Focus handles；`SelectComp` 共用 resolve | 使用 #9 owner resolver，返回完整 destination；explicit `SelectComp` 保持 immediate guard／失敗報錯，automatic Follow 經 arbiter。唔單純掃所有 Focus links。 |
| `CompFollower.request / flush` | latest intent 帶 connection generation；`flush` 拒絕 destination Layout 不等於 Active Layout | 允許已重新驗 owner 嘅 TD cross-Layout intent；保留 source provenance，同時驗原 routing/session 及 destination。唔無條件刪 guard；hardware requests 仍限其原 routing lists。 |
| `CompFollower._observe / scope` | scope 包含 Active Layout；scope 變更會 invalidate pending／pane baseline | 明確處理自身 cross-Layout commit 後 scope。保留 selection baseline、manual choice until new selection，同 commit 期間新 intent；唔因自身 scope change replay selected COMP 或清掉 fresh valid request。 |
| `fence / clear_controls / recover / session_boundary` | 清 mapping readiness、partial knob pairs、FreeLearner pending、舊 feedback；session boundary取消 intent | 復用，不建第二套 queue/fence。LOCK 延後 automatic Follow 時原 routing 可用；unlock／實際 transition fence 後舊 targets 無 business input，release／session traffic仍可 drain。 |
| [Layouts._select / install / resolve / capture](../../code/py/roto_python/layouts.py) | 已支援一次完整跨 Layout `select_plugin`、live value reads、保存舊 context、rollback | 用同一 commit path；唔拆成 SelectLayout→SelectTrack→SelectPlugin。保留 per-control matching recall、libraries／IDs，同 domain failure vs transport failure 邊界。 |
| `Layouts.announce_tracks / announce / receive` | lists 由 committed routing Layout／Track生成；hardware SEL有 routing Track內 LOCK exception | 保持 protocol scope／source policy；成功 commit 後 announcements、selected IDs、bank offsets同 destination一致。Queued TX 唔當 wire delivery。 |
| [RotoPythonExt.SelectComp / GetCompContext / Tick / _receive_midi](../../code/py/roto_python/RotoPythonExt.py) | promoted wrappers；每批 RX 前observe、批後flush；partial lines 帶 ingress epoch | wrapper委派同一 owner resolution；必要時補 detached owner／pending Layout diagnostics。保留 generation、epoch、bounded backlog drain、transport opening guard。 |
| [Inspector projection](../../code/py/roto_python/inspector/inspector_data.py)／外部 Inspector contract | 本 checkout係既有 Inspector；`.45` Browse／Activate command seam喺另一 thread | 暴露 committed routing／owner metadata供 consumer讀，唔搬 UI prototype或改另一 worktree。LIVE跟 commit；BROWSE保留 view/draft；Activate一次 guarded SelectPlugin；Follow preference唔被 UI command改寫。 |

Pending owner 變 unavailable／destination 失效、零／多選、pane exit、Follow off：取消該 TD intent，唔沿用舊 destination。已 fence 嘅取消／失敗走既有 recovery，要求 fresh per-control recall；rollback failure保持 paused／gated直到 Apply setup repair。唔自動 Disconnect或每 poll重試 domain failure。

Startup／reinit／file reload／pane return只建立 baseline；Follow off→on可即時評估目前唯一 COMP；manual selection保持到新 selection event。Python registration mode保留 preference但 Follow unavailable。Fresh offline selection可改本地 routing，唔自動開 MIDI process或聲稱硬體 recall。

## Regression / native / physical acceptance matrix

以下全部係 #10 待完成嘅驗收；舊 same-Layout Follow、manual Track／Device 同 physical LOCK evidence只作 baseline，唔升格為 cross-owner pass。

| Case | Source regression assertion | Native acceptance | Physical acceptance |
| --- | --- | --- | --- |
| 跨 owner A→B→A，A有多 variants | 真實 #9 allocation API建 fixture；完整 triple一次 commit；返回保存 default；IDs／indices／hashes／ranges／assignments／off-page library不变；inactive值變更後recall讀最新值 | 真實 Network Editor selection、custom-par callbacks、兩份 owner Layout；idle不重裝 | selection後 matching recall；assigned knob/button只控制新 owner；motor／LCD顯示相應現值 |
| CUSTOM與owner共享 parameter | 手動 CUSTOM／owner各自 range／assignment/library保留；CUSTOM Focus或同名 record唔搶 owner resolve | shared Par實際 callback／recall反映新 live值；BROWSE無routing/value writes | 不同range嘅motor normalized位置可不同；真實value仍同一個 |
| Owner unavailable／ambiguous／同名 | missing、clone conflict、unregistered、same-path replacement拒絕；pending後變失效亦取消；冇first-match／auto allocation | 真實handle失效／relink；同名COMP唔合併 | 唔以另一同名device顯示/回應冒充成功 |
| Rename／reparent／save-reload | 共用#9 lifecycle；identity／target path rebase／libraries保持；舊intent唔redirect | temp save/load經TD；停止timeline pre-save更新；Follow=True startup無activation／MIDI child | reconnect只讀已保存routing並逐control recall |
| Startup／Follow off-on／pane baseline | 零、多選、mixed family、utility／controller internals、currentChild≠selected；manual choice不被idle覆寫；pane exit取消TD pending | 真實pane owner/selectedChildren，reinit及reload；Follow off唔阻hardware arbiter | Follow off保持routing；新有效selection先切換 |
| LOCK／LEARN／touch guards | 各guard／組合延後cross-owner；最新intent勝；LOCK等待原target可控；unlock即時fence且等release | native observer／release traffic同一次commit | LOCK時保持原input／motor；unlock、LEARN退出、touch release後新context生效 |
| Mixed TD／FUNC／SEL／manual Activate | 雙順序latest-intent；一次flush最多一commit；hardware範圍及locked SEL例外保留；manual取消舊pending；commit中fresh intent後續重新驗 | 使用真實promoted API／parameter callback，唔force/hardware bypass Inspector guards | FUNC/SEL候選、bank、selected/routing divergence符合新routing及既有policy |
| Batch／backlog／partial line／feedback | actual Tick mixed RX；split CC、old ACK、Pulse／Toggle／Menu、FreeLearner commits、queued feedback都fenced且唔replay；返回原destination仍需fresh ACK | 原epoch report在跨Layout commit後到達，不能恢復舊target；保留JSON partial TX framing | input只在新control matching recall後有效；冇舊target誤動作 |
| Disconnect／reconnect／open or child failure | generation變更取消各source pending／selected divergence；stale session包無效；offline fresh intent唔Connect | external process lifecycle／cleanup；open failure／reinit無殘留 | reconnect無舊selection重播；motor／LCD及mappings重新recall |
| Preflight／activation／rollback失敗 | registry／舊routing恢復，controls需重confirm；domain failure不Disconnect／不poll retry；rollback／observer failure paused-gated；repair須fresh intent | 注入install／observer failure，查errors同diagnostics真實反映結果 | transport失敗同domain失敗分開記錄，唔報假切換成功 |
| Inspector／hardware context | controller routing／active selectors／announce source同commit triple一致；BROWSE唔改routing／owner；LIVE跟routing；pending唔當ready | 協調Inspector最後fixture核對View、routing token、draft、disabled reason；本thread不搬UI | 記錄FUNC／SEL完整candidates、bank offsets、mapping reports同人手LCD markers |
| 無Preset／Pulse sideeffects | selection／metadata／ACK／reload對numeric／Menu／Toggle無writes，Pulse/callback計數不變；切換輸入唔dispatchaction | native pulse observer零count；target值與前後baseline比對 | selection本身無action；正常mapped button input另行驗收 |

Unit整合以 [test_comp_follow.py](../../test_comp_follow.py)、[test_layouts.py](../../test_layouts.py)、[test_device_context.py](../../test_device_context.py)、[test_tag_devices.py](../../test_tag_devices.py) 同 #9新owner tests為基礎。唔用手工填placeholder owner metadata作feature coverage。Existing Active-Layout-scope test喺#9 stable contract後再調整，保留duplicate/unlink及legacy unavailable checks。

## 最少 native / physical 驗證方案

1. #9可整合後，先完成source regression及完整suite。Native builder由external Python source建一次隔離fixture，用#9真實API建立A/B owner Layout、CUSTOM shared target、不同range、off-page definitions及Pulse observer；唔拷貝user mappings或建立live owner registry替身。
2. Native stage喺獲協調嘅獨立TD process／isolated project執行；先核對active project、TD build、source revision及no physical port ownership。使用真實pane/callback、temp TD save/load及failure injection；清理fixture／owned processes。現有 `verify_comp_follow.py.begin()` 會改current project/pane，唔直接喺shared live執行。
3. Physical gate由協調thread同Inspector最後一次驗證排程合併，唔另開live project搶MIDI。先capture原Routing/View/Follow/session、registry/mapping IDs/libraries、values及可恢復baseline；再執行cross-owner A/B/A、guards、fresh recall、input／motor／LCD。每步記source、triple、完整FUNC／SEL candidates、bank offsets、matching reports及人手觀察。
4. Cross-owner fixture需要真正#9 Layout allocation；歷史同一Layout SEL A/B/A可補Inspector parity，但唔取代#10 gate。未得到新scope acceptance就保持pending。Queued TX、synthetic ACK／CC、native parameter callback同physical wire/input觀察各自記錄；不得以synthetic標physical pass。

ROTO CC無Layout／session ID：新mapping ACK之後才遲到嘅舊CC，protocol未必能區分；重用legacy wire hash亦可能ambiguous。保留既有實際限制，唔聲稱fences解決無token嘅全部延遲事件。

## 此輪 handoff

- Runtime／builders／tests未修改；只新增本準備文件。未commit／push／merge或作GitHub mutation。
- Baseline `python3 -m unittest discover -q`（`src/touchdesigner`）：230 tests，OK；係pre-implementation baseline，唔係#10 pass。
- `git diff --check`、cached diff check及新文件嘅no-index whitespace check通過；Markdown local links／code fences檢查通過。結束前重新讀native blockers，#9仍OPEN並block #10。
- Native／physical #10 acceptance全部未執行；shared live／canonical artifacts／user mappings保持原狀。
- 下一步：等#9完成handoff及stable整合revision，再重新核對native dependency，按以上seams實作#10。此輪停止，唔poll／sleep／另開thread或做其他tickets。

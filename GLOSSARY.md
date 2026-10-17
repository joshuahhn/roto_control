# ROTO-CONTROL TouchDesigner domain

本 glossary 定義本 fork 嘅 TouchDesigner integration 用語。功能支援同驗收狀態以目前 source contracts 同 dated HANDOFF 為準。

Inspector integration contract 見 [context contract](src/touchdesigner/docs/plans/inspector-context-contract.md)。

## Mapping context

**Layout**:
一份獨立保存嘅 mapping configuration，包含 Track groups 同其 Devices。選擇 Layout 係選擇控制配置，唔係還原 parameter values。
_Avoid_: Preset、hardware Mode、MIDI Setup

**Ownership category**:
Layout 嘅歸屬分類：COMP-owned 或 Custom。佢描述配置由邊個擁有，唔係硬體操作 mode。
_Avoid_: COMP mode、CUSTOM mode

**Layout owner**:
COMP-owned Layout 所屬嘅已註冊工具 COMP；Custom Layout 由用戶管理。引用某 COMP 嘅 parameter，同歸屬該 COMP 係不同關係。
_Avoid_: Focus COMP、parameter destination、display name 當 owner identity

**COMP boundary**:
按工具 COMP 歸屬劃分嘅保存配置集合；每個已註冊 COMP 有自己專屬 Layout。
_Avoid_: Hardware Mode、Device selector

**CUSTOM boundary**:
用戶手動建立嘅獨立 Layout 配置集合，可引用 COMP boundary 相同嘅 parameter。
_Avoid_: 名叫 CUSTOM 嘅 Device、MIDI Setup

**COMP-owned Layout**:
歸屬一個已註冊 TD COMP 嘅專屬 mapping configuration。
_Avoid_: 用 COMP display name 當 owner identity

**Custom Layout**:
由用戶手動組織、獨立保存嘅 mapping configuration；可以引用同 COMP-owned Layout 相同嘅 parameters。
_Avoid_: MIDI mode、名叫 CUSTOM 嘅 Device

**Track**:
Layout 內包含 Devices 嘅可選 tools group；喺 PLUGIN mode 對應硬體 Track selection。Track group 係呢一層嘅說明，唔係另一層或 DAW foldable Group Track 嘅宣稱。
_Avoid_: Layout、control page、自動等同 COMP parent hierarchy

**Device**:
Track group 內可獨立選擇嘅控制對象及 mapping context；可連結工具 COMP，亦可包含手動指定嘅 parameter targets。Protocol 同既有 API 用 Plugin 指同一層。
_Avoid_: Plugin 當另一層、Layout

**Focus COMP**:
Device 連結嘅工具 COMP，用作 COMP selection 對應及 parameter learning scope。Focus link 同 Layout ownership 係不同關係。
_Avoid_: 一建立 link 就當 Layout 已有 COMP owner

**Control page**:
Device 內一頁實體 controls 嘅 assignments，同其他 control pages 共用該 Device 嘅 target library。
_Avoid_: Track list bank、Device list bank、TD custom-parameter page

**List bank**:
Track 或 Device selector 一次顯示嘅一組候選項目。瀏覽另一 bank 唔等於選擇另一項目。
_Avoid_: 無限定詞嘅 page、control page

**Mapping**:
某 mapping context 入面，由實體 control 指向 parameter 或 action target 嘅 assignment 及其 value semantics。
_Avoid_: Parameter value、Preset

**Target library**:
Device 保存嘅 target definitions，包含目前 control page 以外嘅 definitions。
_Avoid_: 目前 slots、parameter value snapshot

**Selected context**:
硬體最新嘅 Track／Device selection state；LOCK 下 selected Track 可以唔係 routing Device 嘅 parent。各個 selected fields 唔保證組成一個可直接 activate 嘅配置。
_Avoid_: 一律叫 Active context

**Routing context**:
目前接收 control input 同產生 target feedback 嘅 Layout／Track／Device context。
_Avoid_: 一律等同 selected context

**Browse context**:
Inspector 正在查看嘅 Layout／Track／Device 配置，可以同 routing context 不同。查看另一份配置本身唔會切換 hardware routing。
_Avoid_: Active Device、Layout owner

**Activate Device**:
將 Inspector browsed Device 及其所屬 Layout／Track 明確設為 routing context 嘅操作。
_Avoid_: Browse、Preset recall、已完成所有 mapping recall 嘅宣稱

**LIVE view**:
Inspector 跟隨 routing context 嘅顯示模式。LIVE 本身唔表示 hardware 已連線或所有 controls 已 ready。
_Avoid_: Connect、Activate Device、Follow selected COMP

**Mapping readiness**:
某個實體 control 已取得符合目前 target 嘅 learned assignment，可以接受 business input 嘅狀態。
_Avoid_: Context selected、整個 Device 已 ready 嘅推論

**Selection request**:
用戶或 Follow 提出嘅目標 context；提出選擇唔表示已更換 routing。
_Avoid_: Routing commit、mapping recall

**Routing commit**:
完成受保護嘅 context 切換，令新 context 成為實際 routing context。
_Avoid_: Browse、selection request、所有 controls 已 ready 嘅宣稱

## Physical input and actions

**Hardware Mode**:
ROTO-CONTROL 嘅 MIX、PLUGIN 或 MIDI 操作 mode；實體按鍵喺不同 mode／view 有不同作用。
_Avoid_: Ownership category、TD Binding workflow

**MIDI Setup**:
硬體 MIDI mode 入面保存 knobs、buttons、messages 同配置嘅 setup。
_Avoid_: TD Layout、PLUGIN Device

**Hardware Button Type**:
實體 button 嘅 PUSH 或 TOGGLE 訊號行為。
_Avoid_: TD Pulse、TD Toggle action、已讀回硬體設定嘅宣稱

**Target action mode**:
接收 button input 後執行嘅 Toggle、Pulse 或 Cycle 行為。
_Avoid_: Hardware Button Type

**Mapping recall**:
重新取得已學習嘅 control assignments，並以 target 嘅目前值恢復控制及 feedback。
_Avoid_: Preset recall

**Preset recall**:
明確執行具名 action，或者套用一組保存嘅 parameter values。
_Avoid_: Layout selection、mapping recall

**Action preset**:
一個具名 recall action，調用 COMP 已有 preset entry point 或 Python callback。

**Snapshot preset**:
用戶明確選定嘅一組 parameter values 嘅具名快照。

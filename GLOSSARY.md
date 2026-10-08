# ROTO-CONTROL

TouchDesigner 控制配置及 Preset 嘅共同用語。COMP／CUSTOM 保存邊界同 Preset 係已確認嘅產品模型；implementation roadmap 見 [design plan](src/touchdesigner/docs/plans/comp-custom-layout-presets.md)。

## Language

**Layout**:
一套保存嘅 mapping 配置，包含 Track groups、Devices 同 control-page libraries。Layout 配置同 parameter-value preset 係不同概念。
_Avoid_: 用 Preset 指代 Layout

**COMP boundary**:
按 tool COMP 劃分嘅配置集合，每個 COMP 有自己專屬 Layout。

**CUSTOM boundary**:
用戶手動建立嘅 Layout 配置集合。佢可以引用 COMP boundary 已映射嘅同一個 parameter，但保存獨立 mapping 配置。

**Track group**:
Layout 內嘅 Device 分組，對應 hardware FUNC 選擇嘅 Track。

**Device**:
Track group 內嘅控制單位，擁有 mappings 同 control pages。ROTO protocol 用 Plugin 指同一層。
_Avoid_: 用 Plugin 指代 Layout

**Mapping**:
一個 control 對 parameter 或 action 嘅指派，包括所屬配置、slot 同 value／input semantics。不同 mappings 可以引用同一個 parameter；該 parameter 嘅真實 value 係共享嘅。

**Control page**:
Device 入面一頁 physical knob／button assignments。Control page 同 Track／Device list bank 係不同概念。

**Action preset**:
一個具名 recall action，調用 COMP 已有嘅 preset entry point 或 Python callback。

**Snapshot preset**:
用戶明確選定嘅一組 parameter values 嘅具名快照。Recall 將快照套用到該組 parameters。

**Preset recall**:
執行 Action preset 或套用 Snapshot preset 嘅明確操作，可以由 mapped Button 觸發。

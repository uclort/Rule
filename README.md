# Rule

每天北京时间 08:00 由 GitHub Actions 同步 [SukkaW/Surge](https://github.com/SukkaW/Surge)（[ruleset.skk.moe](https://ruleset.skk.moe)）的构建产物，并生成 Shadowrocket 可用版本。

| 目录 | 来源 | 处理 |
| --- | --- | --- |
| `Surge/` | 上游 `List/` | 原样同步 |
| `Mihomo/` | 上游 `Clash/` | 原样同步 |
| `Shadowrocket/` | 由 `Surge/` 转换 | 见 [scripts/convert_shadowrocket.py](scripts/convert_shadowrocket.py) |

## 引用地址

前缀：`https://raw.githubusercontent.com/uclort/Rule/main/`

| ruleset.skk.moe | 本仓库 |
| --- | --- |
| `https://ruleset.skk.moe/List/<dir>/<name>.conf` | `Surge/<dir>/<name>.conf` |
| `https://ruleset.skk.moe/Clash/<dir>/<name>.txt` | `Mihomo/<dir>/<name>.txt` |
| — | `Shadowrocket/<dir>/<name>.list` |

`<dir>` 为 `domainset`（用 `DOMAIN-SET` 引用）、`non_ip`、`ip`（用 `RULE-SET` 引用）。

## Shadowrocket 转换规则

- `domainset`：语法与 Surge 相同，原样保留
- `DEST-PORT` → `DST-PORT`
- 删除 `PROCESS-NAME`（iOS 不可用）、`SRC-IP` 及其他不支持的类型
- `AND` / `OR` / `NOT` 只有在所有子规则都受支持时才保留，否则整条删除

手动触发：Actions → Sync upstream rules → Run workflow。

## License

规则数据来自 [SukkaW/Surge](https://github.com/SukkaW/Surge)，遵循 [AGPL-3.0](LICENSE)。

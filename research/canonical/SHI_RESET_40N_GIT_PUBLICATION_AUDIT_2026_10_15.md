# SHI_RESET_40N — публікація досліджень у main

Дата:2026-10-15. Користувач прямо попросив `git push` у `main`. Це дозвіл на Git-публікацію та необхідне збереження/об'єднання змін, не на live trading або розгортання сервісів. Run root:`market_monitor_runs/SHI_RESET_40N_git_publication_v0/`.

## Що збережено

Коміт **`0862342`** (`Preserve own-signal research through40M with frozen replay evidence`) фіксує дослідницьку опору: канонічні документи40A–40M, власний research-код, вибрані правила40H, останній результат/журнал40L, усі невибрані trials і40M handoff package. Репозиторій уже містить ці раніше ignored run artifacts. Посилання з [40M дорожньої карти](SHI_RESET_40M_RESEARCH_AND_DEPLOYMENT_ROADMAP_AUDIT_2026_10_15.md) тепер мають Git-версії.

232 raw primary/recovered source files залишаються окремими external data assets; у Git вони не додані й не змінені. Public spot archives/normalized execution inputs, manifests, journals і research results передані як докази. Worktrees, тимчасові pytest fixtures, Python caches та runtime/credential directories не публікуються. Повний перелік:`publication_scope.json`.

До зміни історій `origin/main` мав три власні коміти, а research branch —23. Основний збережений main-fix —`d753f05` (через merge`bf2e9f0`): governed raw/recovered selection, row/window quality, dedup diagnostics і causal cross-day context. Обидві історії об'єднані звичайним merge; force-push не потрібний. Старий retired-main notice з`28d3f6d` збережений як межа вибору майбутньої research base; цей явний user-directed push не оголошує нової production strategy/governance promotion.

## Розв'язання конфліктів

У feed adapter збережені `SourceClass`, per-row `SYNTHETIC` і explicit deduplication із main та liquidation quantities/availability з дослідницької гілки. У volume/delta outputs збережені timestamp-aware rolling windows/contiguous OI-change із main й liquidation output fields. Тести перевіряють обидва контракти. README/AGENTS/ACTIVE_DOCS/feed notes узгоджують сучасний research handoff із [continuity ADR](../../docs/MARKET_MONITOR_CONTINUOUS_CONTEXT_AND_GAP_POLICY_ADR.md).

Решта main continuity файлів перенесені без відкидання remote-змін. Frozen40H/L contracts, ledgers, data/artifact hashes і selection pointers не переписані під merged runtime. Історичний replay відтворюється з`0862342`, бо current main містить нові runtime code identities.

## Як відтворити після clone/pull

Git text normalization може змінювати CRLF і ламати старі SHA256 без зміни чисел. Frozen research blobs записані з оригінальними bytes. `.gitattributes` на merged main вимикає text normalization для відповідних frozen paths.131 незмінених раніше tracked файлів із Windows checkout bytes збережені в маленькому`40M_original_worktree_bytes.zip`, щоб не переписувати сотні інших source/tests лише через line endings. Цей overlay застосовується тільки до окремої історичної offline-копії, не поверх main runtime.

Після повного Git clone з доступною історією запустити з кореня:

```powershell
# Перевіряє1466опублікованих inventory files через Git blobs/overlay;
# з наявними raw inputs додатково перевіряє232 source hashes. Нічого не торгує.
python market_monitor_runs/SHI_RESET_40N_git_publication_v0/reproduce_snapshot.py --raw-source-root .

# Експорт байт-в-байт у НОВИЙ порожній каталог; raw-source-root —
# окремий корінь із потрібними feed/ і feed_recovered/ з40M inventory.
python market_monitor_runs/SHI_RESET_40N_git_publication_v0/reproduce_snapshot.py --destination market_monitor_runs/SHI_RESET_40N_git_publication_v0/offline_snapshot --raw-source-root .

# У цьому offline_snapshot працюють оригінальні команди40M/40L.
# Почати з handoff.py verify; фінансові правила й manifests не редагувати.
```

Без raw data можна запустити helper без`--raw-source-root`: опубліковані code/evidence bytes перевіряються, але232external sources і фінансове відтворення залишаються непідтвердженими. Передати raw inputs окремо відповідно до inventory; не підставляти поточний оновлений день замість frozen-файла. Helpers не використовують приватні API і не встановлюють залежності.

## Перевірка

- Перед merge:**762 passed**,11старих deprecation/future warnings. Перший запуск мав помилки створення pytest basetemp через відсутній батьківський каталог; після його створення виконано повний успішний прогін. Це setup friction, не прихований failed strategy trial.
- Після merge:**771 passed**,ті самі11warnings; JUnit:`tests_before_merge.xml`,`tests_after_merge.xml`.
- Git snapshot verifier:**PASS**:1466опублікованих inventory files,131overlay files і всі232external raw source hashes збігаються з40M. Звіт:`snapshot_git_verification.json`. Вибраний фінансовий результат не змінений:+1060.907640USDC/14угод.
- Історичні15targeted tests/14first-touch paths належать40L; Git-публікація не є новим PnL-прогоном або holdout.

Подальша робота починається з40M дорожньої карти та цих commit/reproduction notes. Git push має бути звичайним fast-forward remote update після merge, зі звіркою remote `refs/heads/main` із відправленим HEAD. Сам commit ID merge фіксується Git-історією й підтвердженням push, щоб уникнути самопосилального hash у цьому файлі.

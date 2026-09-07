# v3.1.1 Acceptance Matrix

| ID | Requirement | Priority | Acceptance evidence |
|---|---|---:|---|
| H-01 | Windows offline suite portable across short/long paths | P1 | GitHub Actions green |
| H-02 | Self-test uses fixed argv, no DB, no runtime roots | P1 | unit + CI |
| H-03 | Report regeneration remains offline | P1 | patched-connect regression |
| H-04 | Local-only view can be sampled | P1 | sampler test |
| H-05 | external DB view skipped | P1 | sampler/orchestrator test |
| H-06 | linked-server view skipped | P1 | test |
| H-07 | OPENQUERY/OPENROWSET/OPENDATASOURCE view skipped | P1 | tests |
| H-08 | opaque/unresolved view fails closed | P1 | test |
| H-09 | full-readonly does not override external-view deny | P1 | test |
| H-10 | Git raw sample policy impossible | P1 | export test |
| H-11 | Git default excludes sample payloads | P1 | export test |
| H-12 | unknown textual profile values not raw in Git export | P1 | new privacy tests |
| H-13 | aggregate-only mode strips data-bearing values | P1 | test |
| H-14 | source run unmodified by Git export | P1 | hash test |
| H-15 | independent staged evidence audit PASS | P1 | audit test |
| H-16 | CLI report semantics unambiguous | P2 | help/dispatch tests |
| H-17 | offline CLI regeneration does not connect | P2 | test |
| H-18 | initial inventory connection failure leaves manifested FAILED run or no run | P2 | lifecycle test |
| H-19 | duplicate decorator removed | P3 | static review |
| H-20 | prompt authority index exists | P3 | `Prompts/README.md` |
| H-21 | SQL validator unchanged or stronger | P1 | SQL safety tests |
| H-22 | no SP/job/discovered-code execution | P1 | source scan/tests |
| H-23 | loopback/CSRF/same-origin preserved | P1 | Web tests |
| H-24 | path containment preserved | P1 | Windows reparse/junction tests |
| H-25 | metadata completeness preserved | P1 | metadata contract tests |
| H-26 | 2/3-run comparison preserved | P1 | comparison tests |
| H-27 | static comparison HTML preserved | P1 | export test |
| H-28 | output/Git roots remain lazy | P1 | clean-start CI checks |
| H-29 | sequential multi-DB behavior preserved | P1 | orchestrator tests |
| H-30 | DB1 safe-profile live validation | P1 | authorized run |
| H-31 | DB2 safe-profile live validation | P1 | authorized run |
| H-32 | GitHub Actions green on candidate commit | P1 | workflow result |
| H-33 | no secrets/PII in repository diff | P1 | audit |
| H-34 | docs no longer claim v3.1 freeze after supersession | P2 | docs review |
| H-35 | final v3.1.1 freeze declaration only after all gates | P1 | final audit |

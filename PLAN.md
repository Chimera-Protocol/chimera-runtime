# Pro Tier - Full Feature Implementation Plan

## Phase 0: Foundation — ProGate Component (prerequisite)
- New `components/pro-gate.tsx` — reusable wrapper: free users see blurred overlay + upgrade CTA, pro/enterprise see content
- Fix hardcoded `tier: "free"` → use `useAuth().user.tier` in decisions/[id] and dashboard pages

## Phase 1: Frontend-Only (backend already exists, zero backend changes)
1. **Reasoning Trace Viewer** — decision detail page: show all attempts, candidates with LLM reasoning, confidence bars, selected candidate
2. **Art. 86 Explanation Button** — fetch HTML from existing endpoint, open in new tab
3. **Heatmap Chart** — 7x24 CSS grid, block rate colors (endpoint + API client already exist)
4. **Violation Trend Chart** — stacked BarChart with Recharts
5. **Date Range Picker** — 7/14/30/60/90 day selector on analytics page
6. **Policy Simulation UI** — 3rd tab on policies page: select policy → auto-generate form from variable domains → run simulation → show result

## Phase 2: Export (thin backend endpoint)
7. **Audit Export** — GET /export endpoint wrapping AuditQuery.export() → download JSON/Compact/Stats from decisions page

## Phase 3: LLM Cost Estimator (new analytics)
8. **Cost Estimator** — model-based cost table, aggregate from audit records, cost-by-day line chart + cost-by-model bar chart

## Phase 4: API Keys + Settings Page
9. **API Key Management** — SQLite table, CRUD endpoints, Settings page with create/revoke/list

## Phase 5: Agent Control (simplified)
10. **Halt/Resume** — agent enable/disable toggle in settings, stored in DB
11. **Email/Webhook Alerts** — alert rules CRUD, basic condition builder UI

## Dependency Order
```
Phase 0 → Phase 1 (parallel with 2, 3, 4)
Phase 0 → Phase 2
Phase 0 → Phase 3
Phase 0 → Phase 4 → Phase 5
```

# UI Release Blueprint — Manus Integration

This blueprint defines the steps Codex must execute for each pending task in state-ui-manus.md.

## 1. Common Cycle (per task)
1. Read the task objective  
2. Apply required code changes:  
   - theme.css  
   - tokens.js  
   - App.css  
   - Components  
   - Layout.jsx  
   - Pages (Dashboard, Transfers, Audit, Settings, Health)  
3. Enforce Manus tokens:  
   - spacing  
   - typography  
   - colors  
   - radius  
   - shadows  
   - transitions  
4. Enforce responsiveness using breakpoints  
5. Remove unused CSS  
6. Update state-ui-manus.md:  
   - mark task complete  
   - add PATCH note  
7. Git add + git commit  
8. Stop

## 2. Success Criteria
- All pages adopt Manus hierarchy  
- No hardcoded px/rem remains  
- All spacing and layout use tokens  
- Responsive behavior validated (lg, md, sm)  
- Build should eventually pass on operator machine


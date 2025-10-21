# Implementation Plan: Glass UI Redesign with TailwindCSS

**Branch**: `009-glass-ui-redesign` | **Date**: 2025-10-21 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/009-glass-ui-redesign/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Replace all inline CSS styles (386 errors) with TailwindCSS-based black glass morphism design system. Migrate Dashboard, AdminToolApproval, ToolSentimentCard, and HotTopics components from inline styles to Tailwind utility classes while enhancing visual engagement with modern glass effects, improved data visualizations, and zero CSS linting errors.

## Technical Context

**Language/Version**: TypeScript 5.3.3, React 18.2.0  
**Primary Dependencies**: TailwindCSS 3.4+, Vite 5.1.0, Recharts 2.12.0, PostCSS 8+  
**Storage**: N/A (frontend-only changes)  
**Testing**: Vitest (existing), manual visual regression testing  
**Target Platform**: Modern browsers (Chrome, Firefox, Safari, Edge) with backdrop-filter support  
**Project Type**: Web application (frontend component redesign)  
**Performance Goals**: <30s build time, <3s initial load, 60fps animations, no layout shifts  
**Constraints**: Zero breaking changes to component APIs, maintain all existing functionality, WCAG 2.1 AA contrast  
**Scale/Scope**: 4 main components (Dashboard, AdminToolApproval, ToolSentimentCard, HotTopics), ~386 style conversions

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Note**: The project constitution file is a template. Applying standard web development principles:

**Principle I - Incremental Delivery**: ✅ PASS

- Changes are frontend-only CSS/styling refactor
- No backend dependencies
- Can be deployed independently
- Rollback is straightforward (revert commits)

**Principle II - Simplicity First**: ✅ PASS

- Using TailwindCSS (industry standard utility-first CSS)
- Removing complex inline style objects
- Glass morphism is simpler than current scattered styles
- No new libraries beyond TailwindCSS + PostCSS

**Principle III - Quality Gates**: ✅ PASS

- Visual regression testing required before merge
- All existing functionality must pass
- Zero CSS linting errors validation
- Performance benchmarks (build time, load time)

**Principle IV - Spec-Driven Development**: ✅ PASS

- Full spec.md created with user stories
- Clear acceptance criteria for each component
- Success criteria defined and measurable
- This implementation plan follows from spec

**Principle V - Documentation**: ✅ PASS

- Comprehensive spec and plan documentation
- Will create quickstart.md for new styling patterns
- TailwindCSS config documented
- Component migration guide in research.md

**Result**: All principles passing - ready to proceed to Phase 0 (Research).

## Project Structure

### Documentation (this feature)

```text
specs/009-glass-ui-redesign/
├── spec.md              # Feature specification (CREATED)
├── plan.md              # This file (IN PROGRESS)
├── research.md          # Phase 0 output (PENDING)
├── data-model.md        # Phase 1 output (styling patterns, component library)
├── quickstart.md        # Phase 1 output (dev setup, usage guide)
└── contracts/           # Phase 1 output (component APIs, Tailwind config)
```

### Source Code (repository root)

```text
frontend/
├── tailwind.config.js   # NEW: Tailwind configuration
├── postcss.config.js    # NEW: PostCSS setup
├── src/
│   ├── components/
│   │   ├── Dashboard.tsx              # MODIFY: Remove inline styles
│   │   ├── AdminToolApproval.tsx      # MODIFY: Remove inline styles
│   │   ├── ToolSentimentCard.tsx      # MODIFY: Remove inline styles
│   │   ├── HotTopics.tsx              # MODIFY: Remove inline styles
│   │   ├── SentimentTimeSeries.tsx    # MODIFY: Glass styling
│   │   └── TimeRangeFilter.tsx        # MODIFY: Glass styling
│   ├── styles/
│   │   └── globals.css                # MODIFY: Add Tailwind directives
│   └── index.css                       # MODIFY: Add glass utilities
├── package.json         # MODIFY: Add TailwindCSS dependencies
└── vite.config.ts       # VERIFY: PostCSS plugin configured

.vscode/
└── settings.json        # MODIFY: Remove CSS lint suppressions after fix
```

**Structure Decision**: Web application (Option 2). This is a frontend-only redesign focused on the existing `frontend/` directory. No backend changes required. All modifications target React components and styling infrastructure (Tailwind setup).

## Complexity Tracking

No Constitution violations - table not needed.

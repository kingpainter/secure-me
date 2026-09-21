# Secure Me - Changelog

## [2.0.0] - 2026-09-21

### 🎯 Major Refactoring: Type Safety & Engine Architecture

This release represents a significant internal restructuring focused on code quality, testability, and alignment with Home Assistant 2026+ strict type checking requirements. **Zero breaking changes** - all public APIs and automations remain fully compatible.

### ✨ Phase 1: Type Safety (PEP 563 Annotations)
- Added `from __future__ import annotations` to all 34 Python files
- Implemented return type hints across all core modules:
  - coordinator.py: ~80 methods with proper return annotations
  - auto_actions.py: ~40 functions typed
  - zones.py: Event handlers fixed with `-> None` annotations
  - All imports, services, helpers properly typed
- **Result**: Full compatibility with Home Assistant 2026+ strict type checking
- Verification: Zero ruff/mypy warnings, 100% compilation success

### 🏗️ Phase 2: Engine Architecture (Decoupled State Machines)
- **NEW:** `engine/` module with three independent, testable state machines:
  - **BaseEngine**: Common lifecycle management (async_start, async_stop, cleanup)
  - **AutoActionsEngine**: Presence-based automation (997 lines, extracted from auto_actions.py)
    - Pure state machine - NO Home Assistant dependencies
    - Manages lock/alarm/camera delays and arrival confirmation
    - Fully offline testable
  - **FloorplanEngine**: Floorplan state tracking (208 lines)
    - Pure state management for rooms and openings
    - Online/offline testable
  - **NotificationEngine**: Notification routing (769 lines, extracted from notification_dispatcher.py)
    - User preferences, quiet hours, event routing
    - Minimal HA dependencies

- **Updated coordinator.py**:
  - Now uses AutoActionsEngine instead of AutoActionsManager
  - Import changed: `from .engine import AutoActionsEngine`
  - No changes to coordinator's public interface
  - Seamless backward compatibility (constructor args identical)

- **Benefits**:
  - State machines testable without Home Assistant instance
  - Decoupled from framework - easier to debug
  - Foundation for 80%+ unit test coverage
  - Better separation of concerns

### 📊 Phase 3: Quality Scale & CI
- **quality_scale.yaml**: Documented Silver-tier requirements
  - Bronze tier: All requirements met ✓
  - Silver tier: Service validation, diagnostics, entity categories ✓
  - Gold tier roadmap: Translations, device classes, analytics

- **Enhanced GitHub Actions CI**:
  - Added ruff format check (code formatting)
  - Added ruff lint check (code quality)
  - Added mypy --strict (static type checking)
  - Added quality_scale.yaml validation
  - Added PEP 563 verification across all files

- **Unit Test Foundation** (28 tests, ~80%+ coverage target):
  - test_base_engine.py: Lifecycle and task cleanup
  - test_floorplan_engine.py: Room/opening state management (11 tests)
  - test_auto_actions_engine_extended.py: Logic validation (9 tests)
  - test_notification_engine.py: Routing and preferences (8 tests)

### 📝 Release Summary
| Aspect | Before | After | Status |
|--------|--------|-------|--------|
| Type annotations | Partial | 100% | ✅ Complete |
| PEP 563 imports | 11 files | 34 files | ✅ 100% coverage |
| Engine testability | No | Yes (offline) | ✅ Foundation set |
| CI quality gates | Limited | Ruff + mypy | ✅ Enhanced |
| Unit tests | 0 engine tests | 28 engine tests | ✅ Started |
| Quality tier | Bronze | Silver-ready | ✅ On track |

### 🔄 Backward Compatibility
- ✅ All existing automations work unchanged
- ✅ All services/events unchanged
- ✅ Public coordinator API unchanged
- ✅ WebSocket handlers unchanged
- ✅ Configuration format unchanged
- ✅ No data migrations required

### 🛠️ For Developers
- Engines are now independently testable: `pytest tests/test_*_engine.py`
- No HA instance needed for engine logic testing
- BaseEngine provides consistent patterns for future engine extraction
- Code ready for HACS Silver-tier evaluation

### 📚 Documentation Updates
- Created quality_scale.yaml documenting Silver-tier path
- Updated CI workflows for ruff + mypy enforcement
- Added 28 unit tests as examples for offline testing
- See `ARCHITECTURE.md` for engine overview (TODO)

### 🎉 Looking Forward
- Phase 3 continues: Complete unit test implementation (80%+ coverage)
- Future: Full translations for Gold tier
- Future: Device class integration
- Future: Advanced HACS quality tracking

---

## [1.5.5] - 2026-09-xx
- Previous release notes...

# eBay Manager - Development Conventions

## 🚨 MANDATORY PRINCIPLES

### SOLID Principles (ZERO TOLERANCE VIOLATIONS)
All code MUST strictly follow SOLID principles. Violations will be rejected immediately.

#### S - Single Responsibility Principle
- **Each class/function has EXACTLY ONE reason to change**
- No mixing of concerns (e.g., data access + business logic)
- Examples:
  - ✅ `CSVParser` class only parses CSV files
  - ✅ `OrderService` only handles order business logic
  - ❌ `OrderManager` that parses CSV AND updates database

#### O - Open/Closed Principle
- **Open for extension, closed for modification**
- Use interfaces and abstract classes
- Examples:
  - ✅ `IDataProcessor` interface with multiple implementations
  - ✅ Strategy pattern for different CSV formats
  - ❌ Modifying existing classes for new features

#### L - Liskov Substitution Principle
- **Derived classes must be substitutable for base classes**
- No breaking of parent class contracts
- Examples:
  - ✅ All `IRepository` implementations work identically
  - ❌ Child class that changes expected behavior

#### I - Interface Segregation Principle
- **No client should depend on unused methods**
- Small, focused interfaces
- Examples:
  - ✅ `IReadRepository` and `IWriteRepository` separate
  - ❌ Giant `IRepository` with 20 methods

#### D - Dependency Inversion Principle
- **Depend on abstractions, not concretions**
- Use dependency injection
- Examples:
  - ✅ Constructor accepts `IOrderService` interface
  - ❌ Direct instantiation: `new OrderService()`

### YAGNI Principle (STRICT ENFORCEMENT)
**You Aren't Gonna Need It** - Build only what's needed NOW

#### Rules
- ❌ NO "just in case" features
- ❌ NO "might be useful later" code
- ❌ NO premature optimization
- ❌ NO over-engineering
- ✅ Implement when actually needed
- ✅ Refactor when requirements change

#### Examples
- ❌ Building complex caching before performance issues
- ❌ Creating abstract factories for 2 implementations
- ✅ Simple direct implementation that works
- ✅ Adding complexity only when proven necessary

## 📝 Code Quality Standards

### Testing Requirements
- **Minimum 90% code coverage** (MANDATORY)
- Test types required:
  - Unit tests for all business logic
  - Integration tests for API endpoints
  - E2E tests for critical workflows
- **TDD Approach**: Write tests first
- **No merge without passing tests**

### Code Review Checklist
Before ANY commit, verify:
- [ ] Single Responsibility: Each class has one job?
- [ ] No hard dependencies: Using DI?
- [ ] Interface segregation: Small interfaces?
- [ ] YAGNI compliance: No unnecessary features?
- [ ] 90%+ test coverage achieved?
- [ ] All tests passing?
- [ ] No console.log or print statements?
- [ ] Error handling complete?

## 🏗️ Architecture Patterns

### Backend (Python/FastAPI)
```python
# Repository Pattern (SOLID)
class IOrderRepository(ABC):
    @abstractmethod
    async def get_by_id(self, id: int) -> Order: pass

# Service Layer (Business Logic)
class OrderService:
    def __init__(self, repo: IOrderRepository):  # DI
        self.repo = repo
    
    async def process_order(self, id: int):
        # Business logic only
        pass

# API Layer (Controllers)
@router.post("/orders/{id}/process")
async def process_order(
    id: int,
    service: OrderService = Depends(get_order_service)  # DI
):
    return await service.process_order(id)
```

### Frontend (React/TypeScript)
```typescript
// Interface Segregation
interface IOrderRepository {
  getOrders(): Promise<Order[]>;
}

// Dependency Injection via props/context
const OrderList: React.FC<{repo: IOrderRepository}> = ({repo}) => {
  // Component logic
};

// Centralized styling (DI for styles)
import { colors, spacing } from '@/styles/common';
```

## 🎨 Coding Style

### Python
- **PEP 8 compliance** (use black formatter)
- **Type hints** for all functions
- **Docstrings** for public methods
- **No magic numbers** - use constants
- **Async/await** for I/O operations

### TypeScript/React
- **Strict mode** enabled
- **Interface-first** development
- **Functional components** with hooks
- **Props interfaces** for all components
- **No any type** - proper typing required

### File Naming
- **Python**: snake_case.py
- **TypeScript**: PascalCase.tsx for components
- **TypeScript**: camelCase.ts for utilities
- **CSS/Styles**: camelCase.ts for style files

## 🔀 Git Workflow

### Branch Strategy
- **master**: Production-ready code only
- **feature/[name]**: New features
- **fix/[issue]**: Bug fixes
- **refactor/[area]**: Code improvements

### Commit Rules
1. **Test first**: Never commit untested code
2. **Message format**: `[TYPE] Component: Description (Coverage: XX%)`
   - Types: FEAT, FIX, REFACTOR, TEST, DOCS
   - Example: `[FEAT] Orders: Add bulk status update (Coverage: 95%)`

### PR Requirements
- [ ] All tests passing
- [ ] 90%+ coverage maintained
- [ ] SOLID principles followed
- [ ] YAGNI compliance verified
- [ ] Code review approved
- [ ] No merge conflicts

## 📊 Development Workflow

### Phase-Based Planning (NO TIMELINES)
Plans must use phases and tasks, NOT dates:
```markdown
Phase 1: Database Setup
Tasks:
  - Create schema
  - Add migrations
  - Test connections
Success Criteria:
  - All models created
  - Relationships working
  - 90% test coverage
```

### Daily Development Flow
1. **Write failing test** (TDD)
2. **Implement minimum code** to pass
3. **Refactor** if needed
4. **Verify coverage** >= 90%
5. **Commit** with proper message
6. **Push** only after all tests pass

## 🚫 Anti-Patterns to Avoid

### Backend
- ❌ Business logic in controllers
- ❌ Direct database access from API
- ❌ God classes with multiple responsibilities
- ❌ Circular dependencies
- ❌ Synchronous I/O operations

### Frontend
- ❌ Business logic in components
- ❌ Direct API calls from components
- ❌ Inline styles
- ❌ Props drilling (use context)
- ❌ Class components (use functional)

## 📋 Code Review Standards

### Automatic Rejection Criteria
- SOLID violation = REJECT
- YAGNI violation = REJECT
- < 90% test coverage = REJECT
- Failing tests = REJECT
- No error handling = REJECT
- Console.log/print statements = REJECT

### Review Focus Areas
1. **Architecture**: Proper separation of concerns?
2. **Dependencies**: Using DI correctly?
3. **Testing**: Comprehensive test coverage?
4. **Performance**: No obvious bottlenecks?
5. **Security**: No exposed secrets/vulnerabilities?
6. **Documentation**: Code self-documenting?

## 🎯 Definition of Done

A feature is DONE when:
- ✅ Code follows ALL SOLID principles
- ✅ YAGNI principle maintained
- ✅ 90%+ test coverage achieved
- ✅ All tests passing
- ✅ Code reviewed and approved
- ✅ Documentation updated
- ✅ No console/print statements
- ✅ Error handling complete
- ✅ Performance acceptable
- ✅ Security validated

## 📚 Resources

### SOLID Examples
- Repository: `/backend/app/` - Repository pattern
- Services: `/backend/app/services/` - Service layer
- DI: `/backend/app/dependencies.py` - Dependency injection

### Style Guides
- Python: https://pep8.org/
- TypeScript: https://typescript-eslint.io/
- React: https://react.dev/learn

### Testing
- Python: pytest documentation
- React: React Testing Library
- E2E: Playwright documentation

---

**⚠️ REMEMBER**: These conventions are MANDATORY. Non-compliance will result in immediate code rejection. Follow SOLID, embrace YAGNI, maintain 90% coverage.
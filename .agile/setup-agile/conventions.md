# Coding Conventions

## Core Principles (MANDATORY)

### Pre-Code Checklist
- [ ] Test written first (TDD)
- [ ] Single responsibility per class/function
- [ ] No hardcoded values
- [ ] No "future-proofing" (YAGNI)
- [ ] Dependencies injected, not created

### SOLID Compliance
- **S**: One class = One responsibility
- **O**: Extend, don't modify existing code
- **L**: Subtypes fully substitutable
- **I**: Small, focused interfaces
- **D**: Depend on abstractions

## Naming Conventions

### General Rules
- Clear, descriptive names
- No abbreviations (except common ones)
- Avoid generic names (data, info, manager)

### By Language
**JavaScript/TypeScript**
- Variables/Functions: `camelCase`
- Classes/Types: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Files: `kebab-case.ts`

**Python**
- Variables/Functions: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Files: `snake_case.py`

## File Size Limits
- Functions: Max 20 lines
- Classes: Max 200 lines
- Files: Max 300 lines
- Methods per class: Max 7

## Testing Requirements
- Coverage: 90% minimum
- Test types: Unit, Integration, E2E
- Test naming: `test_[what_it_does]`
- One assertion per test preferred

## Git Commit Format
```
type(scope): description

Types: feat|fix|docs|test|refactor|style|perf
Scope: feature name or component
Description: Present tense, lowercase

Example:
feat(auth): add jwt refresh token support
```

## Code Structure

### Backend Pattern
```python
# Repository (Data Layer)
class UserRepository:
    def get_by_id(self, id: str) -> User
    def save(self, user: User) -> None

# Service (Business Logic)
class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo
    
    def process_user(self, id: str) -> None:
        # Business logic only

# Controller (API Layer)
@router.get("/users/{id}")
def get_user(id: str, service: UserService):
    # No business logic here
    return service.get_user(id)
```

### Frontend Pattern
```typescript
// Component (Presentation)
export const UserList: FC<Props> = ({ users, onSelect }) => {
  // Presentation only, no business logic
};

// Service (Business Logic)
export class UserService {
  async fetchUsers(): Promise<User[]> {
    // API calls and data transformation
  }
}

// Hook (State Management)
export const useUsers = () => {
  // State and effects
};
```

## Documentation Standards
- Every public API documented
- Complex logic explained
- README always up to date
- Examples for non-obvious usage

## Error Handling
- Never silent failures
- Specific error messages
- Log errors with context
- Graceful degradation

## Performance Guidelines
- Measure before optimizing
- Cache expensive operations
- Paginate large datasets
- Lazy load when possible

## Security Checklist
- [ ] Input validation
- [ ] SQL injection prevention
- [ ] XSS protection
- [ ] Authentication required
- [ ] Authorization checked
- [ ] Sensitive data encrypted

## Definition of Done
- [ ] Code follows conventions
- [ ] Tests written and passing
- [ ] Coverage >= 90%
- [ ] Code reviewed
- [ ] Documentation updated
- [ ] No console.logs
- [ ] No commented code
- [ ] Performance acceptable
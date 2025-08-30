# eBay Management System

## Project Overview
Multi-account eBay management system without API usage, syncing data via CSV files from eBay.

## Architecture Principles (MANDATORY)
⚠️ **CRITICAL**: All code MUST follow SOLID & YAGNI. Violating code will be rejected immediately.

### SOLID Principles (REQUIRED)
- **S - Single Responsibility**: Each class/function has only 1 reason to change
- **O - Open/Closed**: Open for extension, closed for modification  
- **L - Liskov Substitution**: Subtypes must be substitutable for base types
- **I - Interface Segregation**: No dependency on unused interfaces
- **D - Dependency Inversion**: Depend on abstractions, not concretions

### YAGNI Principle (REQUIRED)  
- **You Aren't Gonna Need It**: Only implement features when actually needed
- No "just in case" or "might be useful later" code
- Refactor when needed, don't over-engineer upfront

## Core Features

### 1. Order Management
- Import/update orders from eBay CSV files
- Manage order status (pending, processing, shipped, delivered, cancelled)
- Update tracking numbers and shipping status
- Track order fulfillment timeline

### 2. Listing Management  
- Import/update listings from eBay CSV files
- Manage listing status (active, inactive, out of stock, ended)
- Track listing performance metrics
- Bulk update listing status

### 3. Product Management
- Manage products by suppliers
- Import/update product data from CSV files
- Track inventory levels and pricing
- Product categorization and tagging

### 4. Customer Management
- Manage customers based on order history  
- Classify: new, returning, VIP, problematic customers
- Customer lifetime value tracking
- Purchase pattern analysis

### 5. Communication Management
- Import emails from Gmail API
- Import messages from eBay CSV exports
- Unified inbox for customer communications
- Response templates and automation

## Multi-Account Structure
- Each eBay account runs on separate browser profile
- Each user manages max 2-3 eBay accounts
- Account-level data isolation
- Cross-account reporting and analytics

## Technical Stack Recommendations
- **Backend**: Python/FastAPI or Node.js/Express
- **Database**: PostgreSQL with proper indexing
- **File Processing**: Pandas (Python) or csv-parser (Node.js)
- **Frontend**: React/Vue.js with responsive design
- **Authentication**: JWT-based with role-based access

## Development Guidelines (STRICT ENFORCEMENT)

### Code Quality Requirements
🚨 **ZERO TOLERANCE**: SOLID/YAGNI violating code will be rejected immediately

### Mandatory Patterns
- **Repository pattern** for data access (Single Responsibility)
- **Service layer** for business logic (Separation of Concerns)
- **Dependency Injection** for loose coupling (Dependency Inversion)
- **Interface-based design** (Interface Segregation)
- **Clear separation of concerns** - no mixing business logic with data access

### Code Review Checklist
- [ ] Does each class have exactly 1 responsibility?
- [ ] Does function have too many parameters? (Interface Segregation)
- [ ] Any hard-coded dependencies? (Dependency Inversion)
- [ ] Any "just in case" features implemented? (YAGNI violation)
- [ ] Can code be extended without modification? (Open/Closed)
- [ ] Does the code have 90%+ test coverage?
- [ ] Have all tests been run and passed?
- [ ] Is the implementation phase-based without timeline dependencies?
- [ ] Has the code been tested before git push?

### Enforcement Rules
- **Comprehensive error handling** with proper exception hierarchy
- **Logging and monitoring** with structured logging
- **Unit tests** for all business logic (Test-Driven Development)
- **No premature optimization** - measure first, then optimize

## Development Workflow Rules (MANDATORY)

### Planning Requirements
- **Phase-based Planning**: Create plans by phases and tasks, NO timelines or dates
- **Task-driven Approach**: Define clear deliverables for each phase
- **No Time Estimates**: Focus on completion criteria, not deadlines
- Example structure:
  - Phase 1: Database Setup (Tasks: Create schema, Add migrations, Test connections)
  - Phase 2: API Development (Tasks: Create endpoints, Add validation, Test APIs)
  - Phase 3: Frontend (Tasks: Build components, Connect to API, Test UI)

### Testing Requirements
- **90% Test Coverage Minimum**: Every feature MUST achieve 90%+ test coverage
- **Test Types Required**:
  - Unit tests for all business logic
  - Integration tests for API endpoints
  - End-to-end tests for critical workflows
- **Testing Before Merge**: No code proceeds without passing tests
- **Test Documentation**: Each test must have clear description of what it validates

### Git Workflow Rules
- **Test First, Push Later**: Git push ONLY after all tests pass
- **Commit Structure**:
  1. Write code
  2. Write tests
  3. Run tests (must pass 90%+ coverage)
  4. Fix any issues
  5. Run tests again
  6. ONLY THEN: git add, commit, push
- **Commit Message Format**: `[PHASE] Task: Description (Test Coverage: XX%)`
- **No Pushing**:
  - Untested code
  - Code with < 90% coverage
  - Code with failing tests
  - Work-in-progress without tests

## Data Models (Core Entities)
- Account (eBay accounts)
- User (system users)  
- Order
- Listing
- Product
- Customer
- Supplier
- Communication (emails/messages)

## CSV Import Strategy
- Scheduled imports or manual trigger
- Data validation and error handling
- Incremental updates with conflict resolution
- Import history and rollback capability

## Planning Guidelines

### Plan Creation Rules
- Create plans using phases and tasks, NOT timelines
- Each phase must have:
  - Clear objective
  - List of specific tasks
  - Success criteria (measurable)
  - Testing requirements (90% coverage)
  - NO dates, deadlines, or time estimates

### Plan Structure Template
```
Phase X: [Phase Name]
Objective: [What this phase achieves]
Tasks:
  1. [Specific task]
  2. [Specific task]
Success Criteria:
  - [Measurable outcome]
  - [Test coverage >= 90%]
Testing:
  - [Test type and scope]
Dependencies:
  - [What must be complete before this phase]
```

### File Naming Convention
- Plans: `[feature]-plan.md` (e.g., `order-management-plan.md`)
- Tests: `test_[module].py` or `[module].test.ts`
- Coverage reports: `coverage-[feature].html`

## Commands to remember
- `npm run dev` - Start development server
- `npm run build` - Build for production  
- `npm run test` - Run tests
- `npm run lint` - Code linting
- `npm run typecheck` - TypeScript type checking
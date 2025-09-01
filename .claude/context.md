# eBay Manager - Project Context

## Project Overview
**Name**: eBay Manager System  
**Type**: Multi-account eBay management platform  
**Status**: Production-ready (v2.0 Modern UI completed)  
**Start Date**: August 2025  
**Current Sprint**: Sprint 1 (Planning Phase)

## Business Context
### Problem Statement
Managing 30 eBay accounts across 5 employees requires centralized control for:
- Order tracking and fulfillment
- Listing management and inventory
- Customer communication
- Performance analytics
- CSV-based data synchronization (no eBay API usage)

### Target Users
- **Primary**: 5 employees managing 6 eBay accounts each
- **Admin**: 1 system administrator with full access
- **Scale**: 30 total eBay accounts, 1000+ orders/day, 115+ active listings

## Technical Stack
### Backend (FastAPI)
- **Framework**: FastAPI 0.104.1 with Python 3.9+
- **Database**: SQLite (development), PostgreSQL (production-ready)
- **ORM**: SQLAlchemy 2.0.23 with proper relationships
- **Authentication**: JWT with passlib bcrypt
- **CSV Processing**: Pandas 2.1.3 for data import/export
- **Testing**: Pytest with 90%+ coverage requirement

### Frontend (React TypeScript)
- **Framework**: React 18.2.0 with TypeScript 4.9.5
- **UI Library**: Material-UI 5.14.17 with DataGrid
- **State Management**: React Context API
- **Routing**: React Router v6
- **HTTP Client**: Axios 1.6.2
- **Styling**: Centralized system with colors.ts and spacing.ts

### Infrastructure
- **Development**: Docker Compose (api, db, redis)
- **Testing**: Playwright for E2E testing
- **Version Control**: Git with feature branches
- **Documentation**: Comprehensive README files

## Current Features (Completed)
### Core Functionality ✅
- Multi-account management (30 accounts)
- JWT authentication with role-based access
- CSV upload and processing with duplicate detection
- Order management workflow (Pending → Processing → Shipped → Completed)
- Listing management with 115+ items
- Modern UI with responsive design

### Modern UI v2.0 ✅
- HeaderWithSearch component (global search)
- ModernSidebar navigation with icons
- Enhanced DataGrid with pagination (25 items/page)
- 8 interactive dashboard metric cards
- Account selector dropdown
- Mobile responsive design

### Testing Coverage ✅
- Backend unit tests (90%+ coverage)
- Frontend component tests
- E2E Playwright tests
- Visual regression testing
- Cross-browser compatibility

## Development Principles
### SOLID Principles (MANDATORY)
- **S**: Single Responsibility - Each module has one reason to change
- **O**: Open/Closed - Extensible without modification
- **L**: Liskov Substitution - Subtypes substitutable for base types
- **I**: Interface Segregation - No unused interface dependencies
- **D**: Dependency Inversion - Depend on abstractions

### YAGNI Principle (STRICT)
- No "just in case" features
- Build only what's needed now
- Refactor when requirements change
- Avoid premature optimization

## Team Structure
- **Tech Lead**: 1 (architecture decisions)
- **Developers**: 2 (feature implementation)
- **Users**: 5 employees (6 accounts each)
- **Sprint Capacity**: 21 story points per 2 weeks

## Project Constraints
- **Timeline**: 3-4 months total implementation
- **Budget**: Minimal (using open-source tools)
- **API Limitation**: No direct eBay API usage (CSV-only)
- **Scale**: Must handle 30 accounts efficiently
- **Testing**: 90% minimum code coverage

## Current Challenges
- Performance optimization for large datasets
- Bulk operations implementation
- Real-time synchronization needs
- Chrome extension development
- Google Sheets integration

## Success Metrics
- ✅ All 30 accounts manageable from single interface
- ✅ CSV processing under 10 seconds for 1000+ records
- ✅ 90%+ test coverage maintained
- ✅ Page load times under 2 seconds
- ✅ API response times under 500ms

## Next Priorities
1. Advanced analytics with charting
2. Bulk order status updates
3. Chrome extension for eBay scraping
4. Google Sheets synchronization
5. Email notification system

## Repository Information
- **Main Branch**: master (production-ready)
- **Feature Branch Pattern**: feature/[feature-name]
- **Current Branch**: feature/modern-ui-redesign
- **Last Merge**: Modern UI v2.0 successfully merged

## Environment URLs
- **Frontend Dev**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Test Results**: /test-results-master-merge/

## Notes
- Production deployment ready
- All core features tested and validated
- Modern UI fully integrated
- Ready for Sprint 1 planning
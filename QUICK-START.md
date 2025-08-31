# 🚀 Quick Start Guide - Enhance Order Page

## ⚡ Setup Commands

### 1. Navigate to Worktree
```bash
cd /home/quangman/EBAY/ebay-manager-enhance-order-page
```

### 2. Backend Setup
```bash
cd backend
source venv/bin/activate  # Virtual environment already created
pip install -r requirements.txt  # Dependencies already installed

# Start backend server
uvicorn app.main:app --reload --port 8000
# Backend will be available at: http://localhost:8000
```

### 3. Frontend Setup
```bash
cd ../frontend
npm install  # Dependencies already installed

# Start frontend server
npm run dev
# Frontend will be available at: http://localhost:3000
```

## 🧪 Testing Commands

### Backend Tests
```bash
cd backend
source venv/bin/activate

# Run all tests with coverage
pytest --cov=app --cov-report=html --cov-report=term-missing --cov-min=90

# Run specific test file
pytest tests/test_orders.py -v

# Watch mode for development
pytest-watch
```

### Frontend Tests
```bash
cd frontend

# Run all tests
npm test

# Run tests with coverage
npm run test:coverage

# Watch mode for development
npm test -- --watch
```

## 📁 Key Files to Know

### Backend Structure
```
backend/
├── app/
│   ├── routers/orders.py       # Order API endpoints
│   ├── services/               # Business logic layer
│   ├── models/                 # Database models
│   └── schemas/                # Pydantic schemas
├── tests/                      # Test files
└── requirements.txt            # Python dependencies
```

### Frontend Structure
```
frontend/src/
├── pages/Orders.tsx            # Main orders page (current)
├── components/orders/          # Order-related components (to be created)
├── services/api.ts             # API service layer
├── types/index.ts              # TypeScript types
└── styles/                     # Styling
```

## 🎯 Current Features

### Existing Functionality
- ✅ Order list view with DataGrid
- ✅ Account selection and filtering
- ✅ Order status filtering
- ✅ Basic order data display
- ✅ Responsive design

### What You'll Be Building
- 🔄 Order detail modal/page
- 🔄 Inline editing for order status
- 🔄 Tracking number management
- 🔄 Bulk operations
- 🔄 Order history/timeline
- 🔄 Advanced search and filtering

## 🛠️ Development Workflow

### 1. Start Development
```bash
# Terminal 1: Backend
cd backend && source venv/bin/activate && uvicorn app.main:app --reload

# Terminal 2: Frontend  
cd frontend && npm run dev

# Terminal 3: Tests (optional)
cd backend && source venv/bin/activate && pytest-watch
```

### 2. Git Workflow
```bash
# Make sure you're on the correct branch
git branch  # Should show: * feature/enhance-order-page

# Before committing - ALWAYS run tests first
cd backend && source venv/bin/activate && pytest --cov=app --cov-min=90
cd ../frontend && npm test

# Only commit if tests pass
git add .
git commit -m "[PHASE-1] Task: Add order detail modal (Test Coverage: 92%)"
git push origin feature/enhance-order-page
```

## 📋 Development Checklist

### Before You Start
- [ ] Backend server running on port 8000
- [ ] Frontend server running on port 3000
- [ ] Tests are passing
- [ ] Virtual environment is activated

### For Each Feature
- [ ] Write tests first (TDD approach)
- [ ] Implement feature
- [ ] Ensure 90%+ test coverage
- [ ] Update documentation
- [ ] Test manually in browser
- [ ] Run full test suite
- [ ] Commit with proper message format

## 🆘 Troubleshooting

### Common Issues

#### Backend Issues
```bash
# If virtual environment issues
cd backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt

# If port 8000 is in use
lsof -ti:8000 | xargs kill -9
uvicorn app.main:app --reload --port 8001

# If database issues
rm ebay_manager.db  # Reset local database if needed
```

#### Frontend Issues
```bash
# If npm install fails
rm -rf node_modules package-lock.json
npm install

# If port 3000 is in use
PORT=3001 npm run dev

# Clear cache if needed
npm cache clean --force
```

#### Test Issues
```bash
# If pytest not found
pip install pytest pytest-cov pytest-watch

# If frontend tests fail
npm install --save-dev @testing-library/react @testing-library/jest-dom
```

## 📞 Help & Resources

### Key Commands Reference
```bash
# Quick restart everything
cd backend && source venv/bin/activate && uvicorn app.main:app --reload &
cd ../frontend && npm run dev

# Run full test suite
cd backend && source venv/bin/activate && pytest --cov=app --cov-min=90
cd ../frontend && npm test

# Check code quality
cd frontend && npm run lint
cd frontend && npm run typecheck
```

### Useful Links
- Backend API docs: http://localhost:8000/docs
- Frontend dev server: http://localhost:3000
- Test coverage report: `backend/htmlcov/index.html`

## ⭐ Pro Tips

1. **Always activate virtual environment** before running Python commands
2. **Write tests first** - it's faster in the long run
3. **Use browser dev tools** to debug React components
4. **Check API docs** at `/docs` endpoint for backend testing
5. **Follow existing code patterns** in the project
6. **Test coverage must be 90%+** before committing
7. **Use TypeScript strictly** - fix all type errors
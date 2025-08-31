# 🚀 Quick Start Guide - Enhance Listing Page

## ⚡ Setup Commands

### 1. Navigate to Worktree
```bash
cd /home/quangman/EBAY/ebay-manager-enhance-listing-page
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
pytest tests/test_listings.py -v

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
│   ├── routers/listings.py     # Listing API endpoints (to be enhanced)
│   ├── services/               # Business logic layer
│   ├── models/                 # Database models
│   └── schemas/                # Pydantic schemas
├── tests/                      # Test files
└── requirements.txt            # Python dependencies
```

### Frontend Structure
```
frontend/src/
├── pages/Listings.tsx          # Main listings page (current)
├── components/listings/        # Listing-related components (to be created)
├── services/api.ts             # API service layer
├── types/index.ts              # TypeScript types
└── styles/                     # Styling
```

## 🎯 Current Features

### Existing Functionality
- ✅ Listing grid view with DataGrid
- ✅ Account selection and switching
- ✅ Search functionality (title, item ID, SKU)
- ✅ Stock status indicators with color coding
- ✅ Listing performance metrics display
- ✅ Responsive design with proper sorting

### What You'll Be Building
- 🔄 Listing edit modal with full editing capabilities
- 🔄 Bulk price updates and management
- 🔄 Listing templates and duplication
- 🔄 Advanced analytics dashboard
- 🔄 Automated repricing rules
- 🔄 Inventory alerts and optimization suggestions

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
git branch  # Should show: * feature/enhance-listing-page

# Before committing - ALWAYS run tests first
cd backend && source venv/bin/activate && pytest --cov=app --cov-min=90
cd ../frontend && npm test

# Only commit if tests pass
git add .
git commit -m "[PHASE-1] Task: Add listing edit modal (Test Coverage: 93%)"
git push origin feature/enhance-listing-page
```

## 📋 Development Checklist

### Before You Start
- [ ] Backend server running on port 8000
- [ ] Frontend server running on port 3000
- [ ] Tests are passing
- [ ] Virtual environment is activated

### For Each Feature
- [ ] Write tests first (TDD approach)
- [ ] Implement feature with proper validation
- [ ] Ensure 90%+ test coverage
- [ ] Test bulk operations with large datasets
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

#### Performance Issues
```bash
# If handling large datasets
# Backend: Implement pagination and filtering
# Frontend: Use virtualization for DataGrid
# Database: Add proper indexing
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

## 💡 Listing-Specific Tips

### Working with Listing Data
```typescript
// Accessing CSV data in listings
const title = listing.csv_row['Title']
const price = listing.csv_row['Current price'] || listing.csv_row['Start price']
const quantity = listing.csv_row['Available quantity']
const sku = listing.csv_row['Custom label (SKU)']
```

### Stock Status Logic
```typescript
const getStockStatus = (quantity: any) => {
  const qty = parseInt(quantity) || 0;
  if (qty === 0) return { label: 'Out of Stock', color: 'error' };
  if (qty <= 5) return { label: 'Low Stock', color: 'warning' };
  return { label: 'In Stock', color: 'success' };
};
```

### Performance Considerations
- Use pagination for large listing sets
- Implement proper indexing for search
- Cache frequently accessed data
- Use background tasks for bulk operations

## ⭐ Pro Tips

1. **Always activate virtual environment** before running Python commands
2. **Test bulk operations** with large datasets early
3. **Use proper validation** for price and quantity updates
4. **Implement caching** for analytics queries
5. **Follow existing patterns** from Orders.tsx
6. **Test coverage must be 90%+** before committing
7. **Consider performance** when building analytics features
8. **Use Material-UI components** consistently
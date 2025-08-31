# eBay Manager Frontend

Modern React TypeScript frontend with Material-UI components, featuring a responsive design, centralized styling system, and comprehensive eBay management interface.

## 🎨 Modern UI Features

- **Full-Width Header Search** - Global search across orders, items, and listings
- **Modern Sidebar Navigation** - Clean icons and smooth transitions
- **Centralized Styling System** - SOLID principles with dependency inversion
- **Responsive Design** - Optimized for desktop, tablet, and mobile
- **Enhanced Data Tables** - Sortable, filterable, and paginated data grids
- **User Account Management** - Profile section with account switching

## 🛠️ Technology Stack

- **React 18.2.0** - Modern React with hooks and functional components
- **TypeScript 4.9.5** - Type-safe JavaScript development
- **Material-UI 5.14.17** - Google's Material Design components
- **React Router 6.20.1** - Client-side routing
- **Axios 1.6.2** - HTTP client for API communication
- **React Dropzone 14.2.3** - File upload interface
- **MUI X Data Grid 6.18.2** - Advanced data table components

## 📁 Project Structure

```
frontend/
├── public/
│   └── index.html           # HTML template
├── src/
│   ├── components/          # Reusable components
│   │   └── Layout/
│   │       ├── HeaderWithSearch.tsx    # Modern header with global search
│   │       ├── ModernSidebar.tsx       # Navigation sidebar
│   │       ├── Layout.tsx              # Main layout wrapper
│   │       └── Header.tsx              # Legacy header component
│   ├── pages/              # Main application pages
│   │   ├── Login.tsx       # Authentication page
│   │   ├── Dashboard.tsx   # Analytics dashboard
│   │   ├── Orders.tsx      # Order management
│   │   ├── Listings.tsx    # Listing management
│   │   └── CSVUpload.tsx   # File upload interface
│   ├── services/           # API communication
│   │   ├── api.ts          # Axios API client
│   │   └── OrderDataService.ts  # Order data operations
│   ├── styles/             # Centralized styling system
│   │   ├── common/
│   │   │   ├── colors.ts   # Color constants
│   │   │   └── spacing.ts  # Spacing constants  
│   │   ├── pages/          # Page-specific styles
│   │   ├── config/         # Component configuration styles
│   │   └── index.ts        # Style exports
│   ├── context/            # React context providers
│   │   └── AuthContext.tsx # Authentication state
│   ├── types/              # TypeScript type definitions
│   │   └── index.ts        # Shared types
│   ├── config/             # Configuration files
│   │   └── OrderTableColumns.tsx  # Data grid configurations
│   ├── App.tsx             # Main app component
│   └── index.tsx           # React entry point
├── package.json            # Dependencies and scripts
└── tsconfig.json           # TypeScript configuration
```

## 🚀 Setup Instructions

### 1. Prerequisites

- **Node.js 16+** - JavaScript runtime
- **npm** or **yarn** - Package manager

### 2. Installation

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Or with yarn
yarn install
```

### 3. Development Server

```bash
# Start development server
npm start

# Or with yarn
yarn start
```

The application will be available at:
- **Development**: http://localhost:3000
- **Hot Reload**: Enabled for development

### 4. Build for Production

```bash
# Create production build
npm run build

# Or with yarn
yarn build
```

## 🎯 Core Features

### 1. Authentication System

```typescript
// Login with demo credentials
Username: admin
Password: admin123

// AuthContext provides user state
const { user, login, logout } = useAuth();
```

### 2. Modern Header with Search

**HeaderWithSearch Component**:
- Full-width search bar across all pages
- Real-time search with 300ms debounce
- Dropdown results with status badges
- Clear button functionality
- Responsive design

```typescript
// Global search functionality
const performSearch = useCallback(async (query: string) => {
  const results = await searchAPI.globalSearch(query);
  setSearchResults(results);
}, []);
```

### 3. Navigation Sidebar

**ModernSidebar Component**:
- Clean modern design with icons
- Responsive mobile/desktop layout
- User profile section
- Account count display
- Smooth transitions

### 4. Dashboard Analytics

**Dashboard Features**:
- 8 metric cards with real-time data
- Order statistics (Total, Pending, Shipped, Completed)
- Listing metrics (Total, Active)
- Revenue tracking
- Account status overview
- eBay account selector

### 5. Enhanced Data Tables

**Orders Page**:
- Comprehensive order information
- Customer details and contact info
- Sortable columns
- Status badges and filtering
- Responsive design

**Listings Page**:
- 115 listings with pagination (25 per page)
- Inventory status indicators
- Search and filter functionality
- SKU, pricing, and availability data
- End date tracking

### 6. CSV Upload Interface

**CSVUpload Component**:
- Modern drag-and-drop interface
- File validation and error handling
- Account and data type selection
- Upload progress indication
- Clear instructions and examples

## 🎨 Styling System

### Centralized Architecture

Following **SOLID principles** with dependency inversion:

```typescript
// colors.ts - Centralized color constants
export const colors = {
  success: '#2e7d32',
  warning: '#f57c00',
  error: '#d32f2f',
  textPrimary: '#333',
  textSecondary: '#666',
  bgPrimary: '#ffffff',
  bgSearch: '#f8fafc',
  primary: {
    500: '#3b82f6',
    600: '#2563eb',
    // ... full color palette
  }
} as const;

// spacing.ts - Material-UI 8px grid system
export const spacing = {
  xs: 0.25,  // 2px
  sm: 0.5,   // 4px  
  md: 1,     // 8px
  lg: 2,     // 16px
  xl: 3,     // 24px
  searchPadding: 1.5,     // 12px
  headerPadding: 4,       // 32px
} as const;
```

### Usage Example

```typescript
import { colors, spacing } from '../../styles';

const styles = {
  header: {
    backgroundColor: colors.bgPrimary,
    padding: spacing.headerPadding,
    color: colors.textPrimary,
  }
};
```

## 📱 Responsive Design

### Breakpoint System

```typescript
// Material-UI breakpoints
xs: 0px      // Mobile
sm: 600px    // Small tablet
md: 900px    // Large tablet
lg: 1200px   // Desktop
xl: 1536px   // Large desktop
```

### Component Adaptations

- **Sidebar**: Collapsible on mobile, fixed on desktop
- **Header**: Responsive search bar width
- **Data Grids**: Horizontal scrolling on mobile
- **Cards**: Stack vertically on small screens

## 🔌 API Integration

### API Service Configuration

```typescript
// api.ts - Axios configuration
const API_BASE_URL = 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Authentication interceptor
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

### API Endpoints

```typescript
// Authentication
authAPI.login(username, password)
authAPI.getCurrentUser()

// Account Management  
accountsAPI.getAccounts()
accountsAPI.createAccount(accountData)

// Data Operations
ordersAPI.getOrders(accountId)
listingsAPI.getListings(accountId)
csvAPI.uploadFile(file, accountId, dataType)

// Search
searchAPI.globalSearch(query)
```

## 🧪 Testing

### Available Scripts

```bash
# Run tests
npm test

# Run tests with coverage
npm test -- --coverage

# Run tests in watch mode
npm test -- --watch
```

### Test Structure

- **Component Tests**: Individual component functionality
- **Integration Tests**: API communication
- **E2E Tests**: Complete user workflows
- **Accessibility Tests**: WCAG compliance

## 🚀 Deployment

### Production Build

```bash
# Create optimized build
npm run build

# Serve static files
npm install -g serve
serve -s build -l 3000
```

### Build Output

```
build/
├── static/
│   ├── css/         # Compiled CSS files
│   └── js/          # Compiled JavaScript bundles
├── index.html       # Main HTML file
└── manifest.json    # PWA manifest
```

### Environment Configuration

```typescript
// Environment variables
REACT_APP_API_URL=http://localhost:8000
REACT_APP_VERSION=1.0.0
```

## 🎛️ Configuration

### TypeScript Configuration

```json
// tsconfig.json
{
  "compilerOptions": {
    "target": "es5",
    "lib": ["dom", "dom.iterable", "es6"],
    "allowJs": true,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "moduleResolution": "node",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx"
  }
}
```

### Package Scripts

```json
{
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build", 
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  }
}
```

## 🔧 Development

### Adding New Components

1. **Create Component**: In `src/components/`
2. **Add Styling**: Use centralized styles
3. **Type Definitions**: Add to `src/types/`
4. **Export**: Update index files
5. **Test**: Add component tests

### State Management

```typescript
// React Context pattern
const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
```

### Error Handling

```typescript
// Global error handling
const handleApiError = (error: AxiosError) => {
  if (error.response?.status === 401) {
    // Redirect to login
    logout();
  } else {
    // Show error message
    setError(error.response?.data?.detail || 'An error occurred');
  }
};
```

## 📊 Performance Optimization

### React Optimization

- **useMemo**: Expensive calculations
- **useCallback**: Event handlers
- **React.lazy**: Code splitting
- **Virtualization**: Large data sets

### Bundle Analysis

```bash
# Analyze bundle size
npm run build
npx serve -s build

# Bundle analyzer
npm install --save-dev webpack-bundle-analyzer
npm run build && npx webpack-bundle-analyzer build/static/js/*.js
```

## 🎯 Key Components

### HeaderWithSearch

- **Full-width search bar**
- **Real-time search with debouncing**
- **Dropdown results with navigation**
- **Responsive design**

### ModernSidebar

- **Clean navigation icons**
- **User profile section**
- **Account information display**
- **Mobile responsive**

### Dashboard

- **8 metric cards**
- **Real-time data updates**
- **Account switching**
- **Professional styling**

## 🤝 Contributing

1. **Follow React best practices**
2. **Use TypeScript for type safety**
3. **Implement responsive design**
4. **Use centralized styling system**
5. **Add proper error handling**
6. **Write component tests**
7. **Update documentation**

## 📄 License

Private project for eBay management system.
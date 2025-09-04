import { FullConfig } from '@playwright/test';

/**
 * Global Setup for E2E Tests - Sprint 7
 * 
 * Prepares the test environment before running E2E tests:
 * - Database seeding
 * - Test user creation
 * - Environment configuration
 * - Service dependencies
 */

async function globalSetup(config: FullConfig) {
  console.log('🚀 Setting up E2E test environment...');
  
  const baseURL = config.projects[0].use.baseURL || 'http://localhost:3000';
  const apiURL = process.env.REACT_APP_API_URL || 'http://localhost:8001';
  
  try {
    // Wait for services to be ready
    console.log('⏳ Waiting for services to be ready...');
    await waitForService(baseURL, 'Frontend');
    await waitForService(apiURL, 'Backend API');
    
    // Setup test database
    console.log('🗄️ Setting up test database...');
    await setupTestDatabase();
    
    // Create test users
    console.log('👥 Creating test users...');
    await createTestUsers();
    
    // Seed test accounts
    console.log('🏪 Seeding test accounts...');
    await seedTestAccounts();
    
    console.log('✅ E2E test environment setup complete!');
    
  } catch (error) {
    console.error('❌ E2E test environment setup failed:', error);
    throw error;
  }
}

async function waitForService(url: string, name: string, timeout: number = 30000): Promise<void> {
  const startTime = Date.now();
  
  while (Date.now() - startTime < timeout) {
    try {
      const response = await fetch(url);
      if (response.ok || response.status === 404) {
        console.log(`✅ ${name} is ready at ${url}`);
        return;
      }
    } catch (error) {
      // Service not ready yet, continue waiting
    }
    
    await new Promise(resolve => setTimeout(resolve, 1000));
  }
  
  throw new Error(`${name} did not become ready within ${timeout}ms`);
}

async function setupTestDatabase(): Promise<void> {
  const apiURL = process.env.REACT_APP_API_URL || 'http://localhost:8001';
  
  try {
    // Reset test database
    const resetResponse = await fetch(`${apiURL}/test/reset-database`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    
    if (!resetResponse.ok) {
      throw new Error(`Database reset failed: ${resetResponse.statusText}`);
    }
    
    // Run migrations
    const migrateResponse = await fetch(`${apiURL}/test/migrate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    
    if (!migrateResponse.ok) {
      throw new Error(`Database migration failed: ${migrateResponse.statusText}`);
    }
    
    console.log('✅ Test database setup complete');
    
  } catch (error) {
    console.error('❌ Database setup failed:', error);
    throw error;
  }
}

async function createTestUsers(): Promise<void> {
  const apiURL = process.env.REACT_APP_API_URL || 'http://localhost:8001';
  
  const testUsers = [
    {
      email: 'admin@test.com',
      password: 'password123',
      role: 'admin',
      name: 'Test Admin'
    },
    {
      email: 'user@test.com', 
      password: 'password123',
      role: 'user',
      name: 'Test User'
    },
    {
      email: 'manager@test.com',
      password: 'password123', 
      role: 'manager',
      name: 'Test Manager'
    }
  ];
  
  try {
    for (const user of testUsers) {
      const response = await fetch(`${apiURL}/test/users`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(user)
      });
      
      if (!response.ok) {
        throw new Error(`Failed to create user ${user.email}: ${response.statusText}`);
      }
    }
    
    console.log(`✅ Created ${testUsers.length} test users`);
    
  } catch (error) {
    console.error('❌ Test user creation failed:', error);
    throw error;
  }
}

async function seedTestAccounts(): Promise<void> {
  const apiURL = process.env.REACT_APP_API_URL || 'http://localhost:8001';
  
  const testAccounts = [
    {
      name: 'Test Store',
      ebay_username: 'teststore',
      account_type: 'business',
      is_active: true,
      auth_status: 'active',
      sync_enabled: true
    },
    {
      name: 'Demo Shop',
      ebay_username: 'demoshop',
      account_type: 'personal',
      is_active: true,
      auth_status: 'pending',
      sync_enabled: false
    },
    {
      name: 'Sample Store',
      ebay_username: 'samplestore',
      account_type: 'business',
      is_active: false,
      auth_status: 'expired',
      sync_enabled: true
    }
  ];
  
  try {
    for (const account of testAccounts) {
      const response = await fetch(`${apiURL}/test/accounts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(account)
      });
      
      if (!response.ok) {
        throw new Error(`Failed to create account ${account.name}: ${response.statusText}`);
      }
    }
    
    console.log(`✅ Created ${testAccounts.length} test accounts`);
    
  } catch (error) {
    console.error('❌ Test account seeding failed:', error);
    throw error;
  }
}

export default globalSetup;
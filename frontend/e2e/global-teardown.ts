import { FullConfig } from '@playwright/test';

/**
 * Global Teardown for E2E Tests - Sprint 7
 * 
 * Cleans up the test environment after E2E tests:
 * - Database cleanup
 * - Test artifact cleanup
 * - Service cleanup
 * - Report generation
 */

async function globalTeardown(config: FullConfig) {
  console.log('🧹 Cleaning up E2E test environment...');
  
  const apiURL = process.env.REACT_APP_API_URL || 'http://localhost:8001';
  
  try {
    // Clean up test database
    console.log('🗄️ Cleaning up test database...');
    await cleanupTestDatabase(apiURL);
    
    // Clean up test artifacts
    console.log('📁 Cleaning up test artifacts...');
    await cleanupTestArtifacts();
    
    // Generate test summary
    console.log('📊 Generating test summary...');
    await generateTestSummary();
    
    console.log('✅ E2E test environment cleanup complete!');
    
  } catch (error) {
    console.error('❌ E2E test environment cleanup failed:', error);
    // Don't throw error to avoid masking test failures
  }
}

async function cleanupTestDatabase(apiURL: string): Promise<void> {
  try {
    // Clean up test data but preserve schema for next run
    const response = await fetch(`${apiURL}/test/cleanup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    
    if (response.ok) {
      console.log('✅ Test database cleanup complete');
    } else {
      console.warn('⚠️ Test database cleanup failed, but continuing...');
    }
    
  } catch (error) {
    console.warn('⚠️ Test database cleanup error:', error);
    // Continue with cleanup
  }
}

async function cleanupTestArtifacts(): Promise<void> {
  const fs = require('fs').promises;
  const path = require('path');
  
  try {
    const artifactDirs = [
      'test-results',
      'playwright-report', 
      'coverage',
      'screenshots'
    ];
    
    // Keep artifacts but clean up old ones (older than 7 days)
    const oneWeekAgo = Date.now() - (7 * 24 * 60 * 60 * 1000);
    
    for (const dir of artifactDirs) {
      try {
        const fullPath = path.resolve(dir);
        const exists = await fs.access(fullPath).then(() => true).catch(() => false);
        
        if (exists) {
          const files = await fs.readdir(fullPath);
          
          for (const file of files) {
            const filePath = path.join(fullPath, file);
            const stats = await fs.stat(filePath);
            
            if (stats.mtime.getTime() < oneWeekAgo) {
              await fs.unlink(filePath);
              console.log(`🗑️ Cleaned up old artifact: ${filePath}`);
            }
          }
        }
      } catch (error) {
        // Continue if directory doesn't exist or can't be cleaned
        console.warn(`⚠️ Could not clean ${dir}:`, error.message);
      }
    }
    
    console.log('✅ Test artifact cleanup complete');
    
  } catch (error) {
    console.warn('⚠️ Test artifact cleanup error:', error);
  }
}

async function generateTestSummary(): Promise<void> {
  const fs = require('fs').promises;
  const path = require('path');
  
  try {
    // Read Playwright JSON report if it exists
    const reportPath = path.resolve('playwright-report.json');
    const reportExists = await fs.access(reportPath).then(() => true).catch(() => false);
    
    if (reportExists) {
      const reportData = JSON.parse(await fs.readFile(reportPath, 'utf8'));
      
      const summary = {
        timestamp: new Date().toISOString(),
        totalTests: reportData.stats?.total || 0,
        passed: reportData.stats?.passed || 0,
        failed: reportData.stats?.failed || 0,
        skipped: reportData.stats?.skipped || 0,
        duration: reportData.stats?.duration || 0,
        browsers: reportData.config?.projects?.map(p => p.name) || [],
        environment: {
          baseURL: process.env.REACT_APP_BASE_URL || 'http://localhost:3000',
          apiURL: process.env.REACT_APP_API_URL || 'http://localhost:8001',
          nodeVersion: process.version,
          platform: process.platform
        }
      };
      
      // Write summary to file
      const summaryPath = path.resolve('e2e-test-summary.json');
      await fs.writeFile(summaryPath, JSON.stringify(summary, null, 2));
      
      // Log summary to console
      console.log('\n📊 E2E Test Summary:');
      console.log(`   Total Tests: ${summary.totalTests}`);
      console.log(`   Passed: ${summary.passed}`);
      console.log(`   Failed: ${summary.failed}`);
      console.log(`   Skipped: ${summary.skipped}`);
      console.log(`   Duration: ${Math.round(summary.duration / 1000)}s`);
      console.log(`   Browsers: ${summary.browsers.join(', ')}`);
      console.log(`   Summary saved to: ${summaryPath}\n`);
      
    } else {
      console.log('📊 No Playwright report found, skipping summary generation');
    }
    
  } catch (error) {
    console.warn('⚠️ Test summary generation error:', error);
  }
}

export default globalTeardown;
#!/usr/bin/env node

/**
 * GUI Test Runner for Merged Features
 * Runs comprehensive Playwright tests with MCP integration
 */

const { exec, spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

console.log('🚀 Starting Comprehensive GUI Tests for Merged Features');
console.log('='.repeat(60));

// Ensure test results directory exists
const testResultsDir = path.join(__dirname, 'test-results');
if (!fs.existsSync(testResultsDir)) {
  fs.mkdirSync(testResultsDir, { recursive: true });
  console.log('📁 Created test-results directory');
}

// Test configuration
const testConfig = {
  headless: process.env.HEADLESS !== 'false', // Default headless, set HEADLESS=false for GUI
  timeout: 180000, // 3 minutes timeout
  retries: 2,
  workers: 1, // Single worker for GUI testing
  browsers: ['chromium'] // Focus on Chrome for initial testing
};

console.log('⚙️  Test Configuration:');
console.log(`   Headless: ${testConfig.headless}`);
console.log(`   Timeout: ${testConfig.timeout}ms`);
console.log(`   Workers: ${testConfig.workers}`);
console.log(`   Browsers: ${testConfig.browsers.join(', ')}`);
console.log('');

// Run the specific merged features test
const testCommand = [
  'npx', 'playwright', 'test',
  'tests/merged-features.spec.ts',
  '--project=chromium',
  `--workers=${testConfig.workers}`,
  `--timeout=${testConfig.timeout}`,
  `--retries=${testConfig.retries}`,
  '--reporter=html,list,json'
];

// Add headed flag if not headless
if (!testConfig.headless) {
  testCommand.push('--headed');
  testCommand.push('--slowMo=1000'); // Slow down for visual observation
}

console.log('🏃 Running command:', testCommand.join(' '));
console.log('');

const testProcess = spawn(testCommand[0], testCommand.slice(1), {
  cwd: __dirname,
  stdio: 'inherit',
  shell: true
});

testProcess.on('exit', (code) => {
  console.log('');
  console.log('='.repeat(60));
  
  if (code === 0) {
    console.log('✅ All GUI tests completed successfully!');
    console.log('');
    console.log('📊 Test Reports:');
    console.log(`   HTML Report: ${path.join(testResultsDir, 'index.html')}`);
    console.log(`   JSON Report: ${path.join(__dirname, 'test-results.json')}`);
    console.log('');
    console.log('🖼️  Screenshots saved in:', path.join(__dirname, 'test-results'));
    
  } else {
    console.error('❌ GUI tests failed with exit code:', code);
    console.error('');
    console.error('🔍 Check the test results for detailed failure information');
    console.error(`   Test Results: ${testResultsDir}`);
  }
  
  console.log('');
  console.log('🔧 To run tests in GUI mode:');
  console.log('   HEADLESS=false node run-merged-features-gui.js');
  console.log('');
  console.log('📱 To run specific test suites:');
  console.log('   npx playwright test tests/merged-features.spec.ts -g "Bulk Upload"');
  console.log('   npx playwright test tests/merged-features.spec.ts -g "Account Deletion"');
  
  process.exit(code);
});

// Handle process termination
process.on('SIGINT', () => {
  console.log('\n⏹️  Test execution interrupted');
  testProcess.kill('SIGINT');
});

process.on('SIGTERM', () => {
  console.log('\n⏹️  Test execution terminated');
  testProcess.kill('SIGTERM');
});
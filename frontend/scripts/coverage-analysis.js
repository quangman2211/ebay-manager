#!/usr/bin/env node

/**
 * Coverage Analysis Script - Sprint 7
 * 
 * Analyzes test coverage and generates comprehensive reports:
 * - Unit test coverage analysis
 * - Integration test coverage
 * - E2E test coverage
 * - Quality gate validation
 * - Coverage trending
 * 
 * Following SOLID Principles:
 * - Single Responsibility: Each function handles one aspect of coverage analysis
 * - Open/Closed: Easy to add new coverage metrics and reporters
 * - Interface Segregation: Focused interfaces for different coverage types
 */

const fs = require('fs').promises;
const path = require('path');
const { execSync } = require('child_process');

// Configuration
const COVERAGE_THRESHOLD = {
  statements: 90,
  branches: 80,
  functions: 90,
  lines: 90
};

const CRITICAL_FILES = [
  'src/components/AccountManagement/AccountCard.tsx',
  'src/components/AccountManagement/AccountStatusIndicator.tsx', 
  'src/components/AccountManagement/AccountPermissionsDialog.tsx',
  'src/context/AccountContext.tsx',
  'src/services/accountSync.ts',
  'src/hooks/useAccountManagement.ts'
];

async function main() {
  console.log('🔍 Starting comprehensive coverage analysis...\n');
  
  try {
    // Run coverage analysis
    const coverage = await analyzeCoverage();
    
    // Generate reports
    await generateReports(coverage);
    
    // Validate quality gates
    const qualityGate = await validateQualityGates(coverage);
    
    // Display summary
    displaySummary(coverage, qualityGate);
    
    // Exit with appropriate code
    process.exit(qualityGate.passed ? 0 : 1);
    
  } catch (error) {
    console.error('❌ Coverage analysis failed:', error);
    process.exit(1);
  }
}

async function analyzeCoverage() {
  console.log('📊 Analyzing test coverage...');
  
  // Run Jest with coverage
  console.log('   Running Jest unit tests with coverage...');
  execSync('npm test -- --coverage --watchAll=false --verbose', { stdio: 'inherit' });
  
  // Parse coverage data
  const coverageData = await parseCoverageData();
  
  // Run E2E coverage if available
  const e2eCoverage = await analyzeE2ECoverage();
  
  return {
    unit: coverageData,
    e2e: e2eCoverage,
    combined: combineCoverage(coverageData, e2eCoverage)
  };
}

async function parseCoverageData() {
  try {
    const coverageFilePath = path.resolve('coverage/coverage-final.json');
    const coverageData = JSON.parse(await fs.readFile(coverageFilePath, 'utf8'));
    
    const summary = {
      total: {
        statements: { covered: 0, total: 0, pct: 0 },
        branches: { covered: 0, total: 0, pct: 0 },
        functions: { covered: 0, total: 0, pct: 0 },
        lines: { covered: 0, total: 0, pct: 0 }
      },
      files: {},
      critical: {}
    };
    
    // Process each file
    for (const [filePath, fileData] of Object.entries(coverageData)) {
      const fileName = path.relative(process.cwd(), filePath);
      
      // Calculate file coverage
      const fileCoverage = calculateFileCoverage(fileData);
      summary.files[fileName] = fileCoverage;
      
      // Track critical files separately  
      if (CRITICAL_FILES.some(critical => fileName.endsWith(critical))) {
        summary.critical[fileName] = fileCoverage;
      }
      
      // Add to totals
      summary.total.statements.covered += fileCoverage.statements.covered;
      summary.total.statements.total += fileCoverage.statements.total;
      summary.total.branches.covered += fileCoverage.branches.covered;
      summary.total.branches.total += fileCoverage.branches.total;
      summary.total.functions.covered += fileCoverage.functions.covered;
      summary.total.functions.total += fileCoverage.functions.total;
      summary.total.lines.covered += fileCoverage.lines.covered;
      summary.total.lines.total += fileCoverage.lines.total;
    }
    
    // Calculate percentages
    summary.total.statements.pct = calculatePercentage(
      summary.total.statements.covered, 
      summary.total.statements.total
    );
    summary.total.branches.pct = calculatePercentage(
      summary.total.branches.covered,
      summary.total.branches.total
    );
    summary.total.functions.pct = calculatePercentage(
      summary.total.functions.covered,
      summary.total.functions.total
    );
    summary.total.lines.pct = calculatePercentage(
      summary.total.lines.covered,
      summary.total.lines.total
    );
    
    return summary;
    
  } catch (error) {
    console.warn('⚠️ Could not parse coverage data:', error.message);
    return null;
  }
}

function calculateFileCoverage(fileData) {
  const statements = Object.keys(fileData.s || {});
  const branches = Object.keys(fileData.b || {});
  const functions = Object.keys(fileData.f || {});
  const lines = Object.keys(fileData.l || {});
  
  return {
    statements: {
      covered: statements.filter(s => fileData.s[s] > 0).length,
      total: statements.length,
      pct: calculatePercentage(
        statements.filter(s => fileData.s[s] > 0).length,
        statements.length
      )
    },
    branches: {
      covered: branches.filter(b => fileData.b[b].some(hit => hit > 0)).length,
      total: branches.length,
      pct: calculatePercentage(
        branches.filter(b => fileData.b[b].some(hit => hit > 0)).length,
        branches.length
      )
    },
    functions: {
      covered: functions.filter(f => fileData.f[f] > 0).length,
      total: functions.length,
      pct: calculatePercentage(
        functions.filter(f => fileData.f[f] > 0).length,
        functions.length
      )
    },
    lines: {
      covered: lines.filter(l => fileData.l[l] > 0).length,
      total: lines.length,
      pct: calculatePercentage(
        lines.filter(l => fileData.l[l] > 0).length,
        lines.length
      )
    }
  };
}

function calculatePercentage(covered, total) {
  return total === 0 ? 100 : Math.round((covered / total) * 100);
}

async function analyzeE2ECoverage() {
  try {
    // Check if E2E coverage exists
    const e2eCoveragePath = path.resolve('e2e-coverage/coverage-final.json');
    const exists = await fs.access(e2eCoveragePath).then(() => true).catch(() => false);
    
    if (exists) {
      console.log('   Analyzing E2E test coverage...');
      const e2eData = JSON.parse(await fs.readFile(e2eCoveragePath, 'utf8'));
      return parseCoverageData(); // Reuse the same parser
    }
    
    return null;
    
  } catch (error) {
    console.warn('⚠️ E2E coverage analysis failed:', error.message);
    return null;
  }
}

function combineCoverage(unitCoverage, e2eCoverage) {
  if (!unitCoverage) return e2eCoverage;
  if (!e2eCoverage) return unitCoverage;
  
  // Simple combination logic - in practice, this would be more sophisticated
  return {
    statements: {
      pct: Math.max(unitCoverage.total.statements.pct, e2eCoverage.total.statements.pct)
    },
    branches: {
      pct: Math.max(unitCoverage.total.branches.pct, e2eCoverage.total.branches.pct)
    },
    functions: {
      pct: Math.max(unitCoverage.total.functions.pct, e2eCoverage.total.functions.pct)
    },
    lines: {
      pct: Math.max(unitCoverage.total.lines.pct, e2eCoverage.total.lines.pct)
    }
  };
}

async function generateReports(coverage) {
  console.log('📄 Generating coverage reports...');
  
  // Generate HTML report
  execSync('npm run test:coverage-report', { stdio: 'inherit' });
  
  // Generate custom JSON report
  const reportData = {
    timestamp: new Date().toISOString(),
    coverage: coverage,
    thresholds: COVERAGE_THRESHOLD,
    criticalFiles: CRITICAL_FILES
  };
  
  await fs.writeFile(
    'coverage-report.json', 
    JSON.stringify(reportData, null, 2)
  );
  
  // Generate markdown report
  await generateMarkdownReport(coverage);
  
  console.log('   ✅ Coverage reports generated');
}

async function generateMarkdownReport(coverage) {
  if (!coverage.unit) return;
  
  const report = `# Test Coverage Report

Generated: ${new Date().toISOString()}

## Summary

| Metric | Coverage | Threshold | Status |
|--------|----------|-----------|---------|
| Statements | ${coverage.unit.total.statements.pct}% | ${COVERAGE_THRESHOLD.statements}% | ${coverage.unit.total.statements.pct >= COVERAGE_THRESHOLD.statements ? '✅' : '❌'} |
| Branches | ${coverage.unit.total.branches.pct}% | ${COVERAGE_THRESHOLD.branches}% | ${coverage.unit.total.branches.pct >= COVERAGE_THRESHOLD.branches ? '✅' : '❌'} |
| Functions | ${coverage.unit.total.functions.pct}% | ${COVERAGE_THRESHOLD.functions}% | ${coverage.unit.total.functions.pct >= COVERAGE_THRESHOLD.functions ? '✅' : '❌'} |
| Lines | ${coverage.unit.total.lines.pct}% | ${COVERAGE_THRESHOLD.lines}% | ${coverage.unit.total.lines.pct >= COVERAGE_THRESHOLD.lines ? '✅' : '❌'} |

## Critical Files Coverage

${Object.entries(coverage.unit.critical || {}).map(([file, data]) => 
  `- **${file}**: ${data.statements.pct}% statements, ${data.branches.pct}% branches`
).join('\n')}

## Recommendations

${generateRecommendations(coverage)}
`;
  
  await fs.writeFile('COVERAGE-REPORT.md', report);
}

function generateRecommendations(coverage) {
  const recommendations = [];
  
  if (!coverage.unit) return 'No coverage data available for analysis.';
  
  if (coverage.unit.total.statements.pct < COVERAGE_THRESHOLD.statements) {
    recommendations.push('- Increase statement coverage by adding more unit tests');
  }
  
  if (coverage.unit.total.branches.pct < COVERAGE_THRESHOLD.branches) {
    recommendations.push('- Improve branch coverage by testing edge cases and error conditions');
  }
  
  if (coverage.unit.total.functions.pct < COVERAGE_THRESHOLD.functions) {
    recommendations.push('- Add tests for uncovered functions');
  }
  
  // Find files with low coverage
  const lowCoverageFiles = Object.entries(coverage.unit.files || {})
    .filter(([_, data]) => data.statements.pct < 80)
    .map(([file, _]) => file);
    
  if (lowCoverageFiles.length > 0) {
    recommendations.push(`- Focus testing efforts on files with low coverage: ${lowCoverageFiles.slice(0, 3).join(', ')}`);
  }
  
  return recommendations.length > 0 ? recommendations.join('\n') : '- Coverage thresholds met! Consider increasing thresholds for continuous improvement.';
}

async function validateQualityGates(coverage) {
  console.log('🚪 Validating quality gates...');
  
  if (!coverage.unit) {
    return { passed: false, message: 'No coverage data available' };
  }
  
  const failures = [];
  
  if (coverage.unit.total.statements.pct < COVERAGE_THRESHOLD.statements) {
    failures.push(`Statement coverage ${coverage.unit.total.statements.pct}% below threshold ${COVERAGE_THRESHOLD.statements}%`);
  }
  
  if (coverage.unit.total.branches.pct < COVERAGE_THRESHOLD.branches) {
    failures.push(`Branch coverage ${coverage.unit.total.branches.pct}% below threshold ${COVERAGE_THRESHOLD.branches}%`);
  }
  
  if (coverage.unit.total.functions.pct < COVERAGE_THRESHOLD.functions) {
    failures.push(`Function coverage ${coverage.unit.total.functions.pct}% below threshold ${COVERAGE_THRESHOLD.functions}%`);
  }
  
  if (coverage.unit.total.lines.pct < COVERAGE_THRESHOLD.lines) {
    failures.push(`Line coverage ${coverage.unit.total.lines.pct}% below threshold ${COVERAGE_THRESHOLD.lines}%`);
  }
  
  return {
    passed: failures.length === 0,
    failures,
    message: failures.length === 0 ? 'All quality gates passed!' : `Quality gates failed: ${failures.join(', ')}`
  };
}

function displaySummary(coverage, qualityGate) {
  console.log('\n📊 Coverage Analysis Summary');
  console.log('═'.repeat(50));
  
  if (coverage.unit) {
    console.log('\n📈 Unit Test Coverage:');
    console.log(`   Statements: ${coverage.unit.total.statements.pct}% (${coverage.unit.total.statements.covered}/${coverage.unit.total.statements.total})`);
    console.log(`   Branches:   ${coverage.unit.total.branches.pct}% (${coverage.unit.total.branches.covered}/${coverage.unit.total.branches.total})`);
    console.log(`   Functions:  ${coverage.unit.total.functions.pct}% (${coverage.unit.total.functions.covered}/${coverage.unit.total.functions.total})`);
    console.log(`   Lines:      ${coverage.unit.total.lines.pct}% (${coverage.unit.total.lines.covered}/${coverage.unit.total.lines.total})`);
  }
  
  if (coverage.e2e) {
    console.log('\n🎭 E2E Test Coverage:');
    console.log(`   Combined coverage metrics available in reports`);
  }
  
  console.log('\n🚪 Quality Gate Status:');
  console.log(`   ${qualityGate.passed ? '✅ PASSED' : '❌ FAILED'}`);
  console.log(`   ${qualityGate.message}`);
  
  if (!qualityGate.passed) {
    console.log('\n🔧 Required Actions:');
    qualityGate.failures.forEach(failure => console.log(`   - ${failure}`));
  }
  
  console.log('\n📄 Reports Generated:');
  console.log('   - coverage/lcov-report/index.html (HTML Report)');
  console.log('   - coverage-report.json (JSON Report)');
  console.log('   - COVERAGE-REPORT.md (Markdown Report)');
  
  console.log('\n' + '═'.repeat(50));
  console.log(qualityGate.passed ? '🎉 Coverage analysis completed successfully!' : '⚠️  Coverage analysis completed with quality gate failures.');
}

// Run the analysis
if (require.main === module) {
  main();
}

module.exports = { main, analyzeCoverage, validateQualityGates };
# Frontend Phase 7: CSV Import Wizard Implementation

## Overview
Implement comprehensive CSV Import Wizard with intelligent data mapping, validation, and processing for all eBay data types (orders, listings, products, suppliers). Includes advanced error handling, duplicate detection, data transformation, and rollback capabilities.

## SOLID/YAGNI Compliance Strategy

### Single Responsibility Principle (SRP)
- **CSVUploader**: Only handle file upload and basic validation
- **DataMapper**: Only map CSV columns to system fields
- **DataValidator**: Only validate imported data against business rules
- **ImportProcessor**: Only process validated data and save to database
- **ErrorHandler**: Only manage import errors and validation failures
- **PreviewGenerator**: Only generate data preview and statistics

### Open/Closed Principle (OCP)
- **Import Formats**: Extensible to support new CSV formats without core changes
- **Validation Rules**: Add new validation rules through configuration
- **Data Transformers**: Support multiple data transformation strategies
- **Error Handling**: Configurable error handling and recovery strategies

### Liskov Substitution Principle (LSP)
- **CSV Parsers**: Different parsing strategies interchangeable
- **Validators**: All validation engines follow same interface
- **Data Transformers**: Different transformation engines substitutable

### Interface Segregation Principle (ISP)
- **Import Interfaces**: Separate interfaces for upload vs processing operations
- **Validation Interfaces**: Different interfaces for field vs record validation
- **Mapping Interfaces**: Segregate auto-mapping vs manual mapping operations

### Dependency Inversion Principle (DIP)
- **Import Services**: Components depend on abstract import interfaces
- **Validation Services**: Pluggable validation engines
- **Processing Services**: Configurable data processing pipelines

## CSV Import Architecture

### Main Import Wizard Layout
```typescript
// src/components/import/CSVImportWizard.tsx - Single Responsibility: Import workflow orchestration
import React, { useState, useCallback } from 'react';
import { 
  Box, 
  Container, 
  Paper, 
  Stepper,
  Step,
  StepLabel,
  Typography,
  Button,
  Alert,
  LinearProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions
} from '@mui/material';
import {
  CloudUpload,
  TableChart,
  CheckCircle,
  Error,
  Refresh
} from '@mui/icons-material';
import { FileUploadStep } from './steps/FileUploadStep';
import { DataMappingStep } from './steps/DataMappingStep';
import { ValidationStep } from './steps/ValidationStep';
import { ImportProcessStep } from './steps/ImportProcessStep';
import { ImportResultsStep } from './steps/ImportResultsStep';
import { useCSVImport } from '../../hooks/useCSVImport';

type ImportStep = 'upload' | 'mapping' | 'validation' | 'processing' | 'results';
type ImportType = 'orders' | 'listings' | 'products' | 'suppliers' | 'customers';

interface ImportContext {
  file: File | null;
  importType: ImportType;
  csvData: any[];
  mappings: Record<string, string>;
  validationResults: any;
  importResults: any;
  errors: string[];
}

const importSteps = [
  { key: 'upload', label: 'Upload CSV File', icon: <CloudUpload /> },
  { key: 'mapping', label: 'Map Data Fields', icon: <TableChart /> },
  { key: 'validation', label: 'Validate Data', icon: <CheckCircle /> },
  { key: 'processing', label: 'Import Processing', icon: <Refresh /> },
  { key: 'results', label: 'Import Results', icon: <CheckCircle /> }
];

export const CSVImportWizard: React.FC = () => {
  const [currentStep, setCurrentStep] = useState<ImportStep>('upload');
  const [importContext, setImportContext] = useState<ImportContext>({
    file: null,
    importType: 'orders',
    csvData: [],
    mappings: {},
    validationResults: null,
    importResults: null,
    errors: []
  });

  const [cancelDialogOpen, setCancelDialogOpen] = useState(false);

  const {
    parseCSV,
    validateMappings,
    processImport,
    rollbackImport,
    loading,
    progress
  } = useCSVImport();

  const updateContext = useCallback((updates: Partial<ImportContext>) => {
    setImportContext(prev => ({ ...prev, ...updates }));
  }, []);

  const handleStepComplete = useCallback(async (step: ImportStep, data: any) => {
    switch (step) {
      case 'upload':
        const csvData = await parseCSV(data.file, data.importType);
        updateContext({
          file: data.file,
          importType: data.importType,
          csvData,
          errors: []
        });
        setCurrentStep('mapping');
        break;

      case 'mapping':
        updateContext({ mappings: data.mappings });
        setCurrentStep('validation');
        break;

      case 'validation':
        updateContext({ validationResults: data.results });
        setCurrentStep('processing');
        break;

      case 'processing':
        const results = await processImport(
          importContext.csvData,
          importContext.mappings,
          importContext.importType
        );
        updateContext({ importResults: results });
        setCurrentStep('results');
        break;
    }
  }, [importContext, parseCSV, processImport, updateContext]);

  const handleStepBack = useCallback(() => {
    const stepOrder: ImportStep[] = ['upload', 'mapping', 'validation', 'processing', 'results'];
    const currentIndex = stepOrder.indexOf(currentStep);
    if (currentIndex > 0) {
      setCurrentStep(stepOrder[currentIndex - 1]);
    }
  }, [currentStep]);

  const handleCancel = useCallback(async () => {
    if (importContext.importResults?.importId) {
      await rollbackImport(importContext.importResults.importId);
    }
    // Reset wizard
    setImportContext({
      file: null,
      importType: 'orders',
      csvData: [],
      mappings: {},
      validationResults: null,
      importResults: null,
      errors: []
    });
    setCurrentStep('upload');
    setCancelDialogOpen(false);
  }, [importContext.importResults, rollbackImport]);

  const getCurrentStepIndex = () => {
    return importSteps.findIndex(step => step.key === currentStep);
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 'upload':
        return (
          <FileUploadStep
            onComplete={(data) => handleStepComplete('upload', data)}
            importType={importContext.importType}
            onImportTypeChange={(type) => updateContext({ importType: type })}
          />
        );

      case 'mapping':
        return (
          <DataMappingStep
            csvData={importContext.csvData}
            importType={importContext.importType}
            initialMappings={importContext.mappings}
            onComplete={(data) => handleStepComplete('mapping', data)}
            onBack={handleStepBack}
          />
        );

      case 'validation':
        return (
          <ValidationStep
            csvData={importContext.csvData}
            mappings={importContext.mappings}
            importType={importContext.importType}
            onComplete={(data) => handleStepComplete('validation', data)}
            onBack={handleStepBack}
          />
        );

      case 'processing':
        return (
          <ImportProcessStep
            csvData={importContext.csvData}
            mappings={importContext.mappings}
            validationResults={importContext.validationResults}
            importType={importContext.importType}
            onComplete={(data) => handleStepComplete('processing', data)}
            onCancel={() => setCancelDialogOpen(true)}
            progress={progress}
            loading={loading}
          />
        );

      case 'results':
        return (
          <ImportResultsStep
            importResults={importContext.importResults}
            importType={importContext.importType}
            onRestart={() => {
              setCurrentStep('upload');
              updateContext({
                file: null,
                csvData: [],
                mappings: {},
                validationResults: null,
                importResults: null,
                errors: []
              });
            }}
          />
        );

      default:
        return null;
    }
  };

  return (
    <Container maxWidth="lg" sx={{ py: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          CSV Import Wizard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Import your eBay data from CSV files with intelligent mapping and validation
        </Typography>
      </Box>

      {/* Progress Stepper */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Stepper activeStep={getCurrentStepIndex()} alternativeLabel>
          {importSteps.map((step, index) => (
            <Step key={step.key} completed={index < getCurrentStepIndex()}>
              <StepLabel
                icon={step.icon}
                error={importContext.errors.length > 0 && index === getCurrentStepIndex()}
              >
                {step.label}
              </StepLabel>
            </Step>
          ))}
        </Stepper>
        
        {loading && (
          <Box sx={{ mt: 2 }}>
            <LinearProgress variant="determinate" value={progress} />
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              {progress}% complete
            </Typography>
          </Box>
        )}
      </Paper>

      {/* Error Display */}
      {importContext.errors.length > 0 && (
        <Alert severity="error" sx={{ mb: 3 }}>
          <Typography variant="subtitle2" gutterBottom>
            Import Errors:
          </Typography>
          <ul style={{ margin: 0, paddingLeft: 20 }}>
            {importContext.errors.map((error, index) => (
              <li key={index}>{error}</li>
            ))}
          </ul>
        </Alert>
      )}

      {/* Step Content */}
      <Paper sx={{ p: 3 }}>
        {renderStepContent()}
      </Paper>

      {/* Cancel Confirmation Dialog */}
      <Dialog
        open={cancelDialogOpen}
        onClose={() => setCancelDialogOpen(false)}
      >
        <DialogTitle>Cancel Import?</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to cancel the import? 
            {importContext.importResults?.importId && 
              ' This will rollback any changes that have been made.'}
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCancelDialogOpen(false)}>
            Continue Import
          </Button>
          <Button onClick={handleCancel} color="error" variant="contained">
            Cancel Import
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};
```

### File Upload Step Component
```typescript
// src/components/import/steps/FileUploadStep.tsx - Single Responsibility: CSV file upload and validation
import React, { useState, useCallback } from 'react';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Chip,
  LinearProgress
} from '@mui/material';
import {
  CloudUpload,
  InsertDriveFile,
  CheckCircle,
  Error,
  Info
} from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';

type ImportType = 'orders' | 'listings' | 'products' | 'suppliers' | 'customers';

interface FileUploadStepProps {
  onComplete: (data: { file: File; importType: ImportType }) => void;
  importType: ImportType;
  onImportTypeChange: (type: ImportType) => void;
}

interface FileValidationResult {
  isValid: boolean;
  errors: string[];
  warnings: string[];
  info: {
    size: string;
    rowCount: number;
    columnCount: number;
    encoding: string;
    delimiter: string;
  };
}

const importTypeInfo = {
  orders: {
    label: 'Orders',
    description: 'Import eBay order data including buyer information, items, and status',
    expectedColumns: ['Order Number', 'Buyer Name', 'Email', 'Item Title', 'Quantity', 'Sale Price', 'Order Status'],
    sampleFile: 'ebay-orders-sample.csv'
  },
  listings: {
    label: 'Listings',
    description: 'Import eBay listing data including titles, prices, quantities, and performance',
    expectedColumns: ['Item ID', 'Title', 'Price', 'Quantity', 'Status', 'Views', 'Watchers'],
    sampleFile: 'ebay-listings-sample.csv'
  },
  products: {
    label: 'Products',
    description: 'Import product catalog with supplier information and inventory',
    expectedColumns: ['SKU', 'Product Name', 'Category', 'Cost Price', 'Selling Price', 'Supplier'],
    sampleFile: 'products-sample.csv'
  },
  suppliers: {
    label: 'Suppliers',
    description: 'Import supplier contact information and performance data',
    expectedColumns: ['Supplier Name', 'Country', 'Email', 'Phone', 'Categories'],
    sampleFile: 'suppliers-sample.csv'
  },
  customers: {
    label: 'Customers',
    description: 'Import customer information from order history',
    expectedColumns: ['Customer Name', 'Email', 'Phone', 'Address', 'Order Count'],
    sampleFile: 'customers-sample.csv'
  }
};

export const FileUploadStep: React.FC<FileUploadStepProps> = ({
  onComplete,
  importType,
  onImportTypeChange
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [validationResult, setValidationResult] = useState<FileValidationResult | null>(null);
  const [isValidating, setIsValidating] = useState(false);

  const validateCSVFile = useCallback(async (file: File): Promise<FileValidationResult> => {
    const errors: string[] = [];
    const warnings: string[] = [];

    // File size validation
    if (file.size > 50 * 1024 * 1024) { // 50MB limit
      errors.push('File size exceeds 50MB limit');
    }

    // File type validation
    if (!file.name.toLowerCase().endsWith('.csv')) {
      errors.push('File must be a CSV file');
    }

    // Read and analyze file content
    return new Promise((resolve) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const content = e.target?.result as string;
          const lines = content.split('\n');
          const firstLine = lines[0];
          
          // Detect delimiter
          const commas = (firstLine.match(/,/g) || []).length;
          const semicolons = (firstLine.match(/;/g) || []).length;
          const tabs = (firstLine.match(/\t/g) || []).length;
          
          let delimiter = ',';
          if (semicolons > commas && semicolons > tabs) delimiter = ';';
          else if (tabs > commas && tabs > semicolons) delimiter = '\t';

          const columns = firstLine.split(delimiter);
          const rowCount = lines.filter(line => line.trim()).length - 1; // Exclude header

          // Column validation
          if (columns.length < 2) {
            errors.push('CSV must have at least 2 columns');
          }

          // Row count validation
          if (rowCount === 0) {
            errors.push('CSV file appears to be empty');
          } else if (rowCount > 10000) {
            warnings.push('Large file detected. Import may take several minutes.');
          }

          // Expected columns check
          const expectedCols = importTypeInfo[importType].expectedColumns;
          const missingColumns = expectedCols.filter(col => 
            !columns.some(csvCol => 
              csvCol.toLowerCase().includes(col.toLowerCase().split(' ')[0])
            )
          );
          
          if (missingColumns.length > 0) {
            warnings.push(`Some expected columns may be missing: ${missingColumns.join(', ')}`);
          }

          resolve({
            isValid: errors.length === 0,
            errors,
            warnings,
            info: {
              size: (file.size / 1024 / 1024).toFixed(2) + ' MB',
              rowCount,
              columnCount: columns.length,
              encoding: 'UTF-8', // Assume UTF-8 for now
              delimiter
            }
          });
        } catch (error) {
          resolve({
            isValid: false,
            errors: ['Unable to parse CSV file. Please check the file format.'],
            warnings: [],
            info: {
              size: (file.size / 1024 / 1024).toFixed(2) + ' MB',
              rowCount: 0,
              columnCount: 0,
              encoding: 'Unknown',
              delimiter: ','
            }
          });
        }
      };
      reader.readAsText(file);
    });
  }, [importType]);

  const handleFileSelect = useCallback(async (files: File[]) => {
    const file = files[0];
    setSelectedFile(file);
    setIsValidating(true);
    
    try {
      const validation = await validateCSVFile(file);
      setValidationResult(validation);
    } catch (error) {
      setValidationResult({
        isValid: false,
        errors: ['Failed to validate file'],
        warnings: [],
        info: {
          size: (file.size / 1024 / 1024).toFixed(2) + ' MB',
          rowCount: 0,
          columnCount: 0,
          encoding: 'Unknown',
          delimiter: ','
        }
      });
    } finally {
      setIsValidating(false);
    }
  }, [validateCSVFile]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: handleFileSelect,
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.ms-excel': ['.csv']
    },
    multiple: false
  });

  const handleProceed = () => {
    if (selectedFile && validationResult?.isValid) {
      onComplete({ file: selectedFile, importType });
    }
  };

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Select Import Type and Upload CSV File
      </Typography>
      
      {/* Import Type Selection */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>Import Type</InputLabel>
            <Select
              value={importType}
              label="Import Type"
              onChange={(e) => onImportTypeChange(e.target.value as ImportType)}
            >
              {Object.entries(importTypeInfo).map(([key, info]) => (
                <MenuItem key={key} value={key}>
                  {info.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          
          <Alert severity="info" sx={{ mb: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              {importTypeInfo[importType].label} Import
            </Typography>
            <Typography variant="body2">
              {importTypeInfo[importType].description}
            </Typography>
          </Alert>
          
          <Typography variant="subtitle2" gutterBottom>
            Expected Columns:
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 2 }}>
            {importTypeInfo[importType].expectedColumns.map((column, index) => (
              <Chip key={index} label={column} size="small" variant="outlined" />
            ))}
          </Box>
          
          <Button
            size="small"
            onClick={() => {
              // Download sample file
              const link = document.createElement('a');
              link.href = `/samples/${importTypeInfo[importType].sampleFile}`;
              link.download = importTypeInfo[importType].sampleFile;
              link.click();
            }}
          >
            Download Sample File
          </Button>
        </CardContent>
      </Card>

      {/* File Upload Area */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box
            {...getRootProps()}
            sx={{
              border: 2,
              borderColor: isDragActive ? 'primary.main' : 'divider',
              borderStyle: 'dashed',
              borderRadius: 2,
              p: 4,
              textAlign: 'center',
              cursor: 'pointer',
              bgcolor: isDragActive ? 'action.hover' : 'transparent',
              '&:hover': { bgcolor: 'action.hover' }
            }}
          >
            <input {...getInputProps()} />
            <CloudUpload sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
            
            {isDragActive ? (
              <Typography variant="h6" color="primary">
                Drop the CSV file here...
              </Typography>
            ) : (
              <>
                <Typography variant="h6" gutterBottom>
                  Drag & drop a CSV file here
                </Typography>
                <Typography variant="body1" color="text.secondary" gutterBottom>
                  or click to select a file
                </Typography>
                <Button variant="outlined" sx={{ mt: 2 }}>
                  Choose File
                </Button>
              </>
            )}
          </Box>
        </CardContent>
      </Card>

      {/* File Validation Results */}
      {selectedFile && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
              <InsertDriveFile color="primary" />
              <Typography variant="h6">
                {selectedFile.name}
              </Typography>
              {validationResult?.isValid && (
                <Chip
                  icon={<CheckCircle />}
                  label="Valid"
                  color="success"
                  size="small"
                />
              )}
              {validationResult && !validationResult.isValid && (
                <Chip
                  icon={<Error />}
                  label="Invalid"
                  color="error"
                  size="small"
                />
              )}
            </Box>

            {isValidating && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Validating file...
                </Typography>
                <LinearProgress />
              </Box>
            )}

            {validationResult && (
              <>
                {/* File Info */}
                <Typography variant="subtitle2" gutterBottom>
                  File Information:
                </Typography>
                <List dense>
                  <ListItem>
                    <ListItemText 
                      primary="File Size" 
                      secondary={validationResult.info.size} 
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText 
                      primary="Rows" 
                      secondary={validationResult.info.rowCount.toLocaleString()} 
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText 
                      primary="Columns" 
                      secondary={validationResult.info.columnCount} 
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText 
                      primary="Delimiter" 
                      secondary={validationResult.info.delimiter === ',' ? 'Comma' : 
                               validationResult.info.delimiter === ';' ? 'Semicolon' : 'Tab'} 
                    />
                  </ListItem>
                </List>

                {/* Errors */}
                {validationResult.errors.length > 0 && (
                  <Alert severity="error" sx={{ mt: 2 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Validation Errors:
                    </Typography>
                    <List dense>
                      {validationResult.errors.map((error, index) => (
                        <ListItem key={index}>
                          <ListItemIcon>
                            <Error color="error" />
                          </ListItemIcon>
                          <ListItemText primary={error} />
                        </ListItem>
                      ))}
                    </List>
                  </Alert>
                )}

                {/* Warnings */}
                {validationResult.warnings.length > 0 && (
                  <Alert severity="warning" sx={{ mt: 2 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Warnings:
                    </Typography>
                    <List dense>
                      {validationResult.warnings.map((warning, index) => (
                        <ListItem key={index}>
                          <ListItemIcon>
                            <Info color="warning" />
                          </ListItemIcon>
                          <ListItemText primary={warning} />
                        </ListItem>
                      ))}
                    </List>
                  </Alert>
                )}
              </>
            )}
          </CardContent>
        </Card>
      )}

      {/* Actions */}
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 2 }}>
        <Button
          variant="contained"
          onClick={handleProceed}
          disabled={!selectedFile || !validationResult?.isValid || isValidating}
        >
          Next: Map Data Fields
        </Button>
      </Box>
    </Box>
  );
};
```

### Data Mapping Step Component
```typescript
// src/components/import/steps/DataMappingStep.tsx - Single Responsibility: CSV column to field mapping
import React, { useState, useEffect, useMemo } from 'react';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Switch,
  FormControlLabel
} from '@mui/material';
import {
  ExpandMore,
  AutoAwesome,
  Visibility,
  CheckCircle,
  Warning
} from '@mui/icons-material';

type ImportType = 'orders' | 'listings' | 'products' | 'suppliers' | 'customers';

interface DataMappingStepProps {
  csvData: any[];
  importType: ImportType;
  initialMappings: Record<string, string>;
  onComplete: (data: { mappings: Record<string, string> }) => void;
  onBack: () => void;
}

interface FieldDefinition {
  key: string;
  label: string;
  required: boolean;
  type: 'string' | 'number' | 'date' | 'email' | 'phone' | 'url' | 'boolean';
  description: string;
  examples: string[];
  validation?: RegExp;
}

const fieldDefinitions: Record<ImportType, FieldDefinition[]> = {
  orders: [
    {
      key: 'orderNumber',
      label: 'Order Number',
      required: true,
      type: 'string',
      description: 'Unique identifier for the order',
      examples: ['123-4567890-1234567', 'ORD-2024-001'],
      validation: /^.{5,}$/
    },
    {
      key: 'buyerName',
      label: 'Buyer Name',
      required: true,
      type: 'string',
      description: 'Full name of the buyer',
      examples: ['John Smith', 'Jane Doe']
    },
    {
      key: 'buyerEmail',
      label: 'Buyer Email',
      required: true,
      type: 'email',
      description: 'Email address of the buyer',
      examples: ['john@example.com', 'buyer@email.com']
    },
    {
      key: 'itemTitle',
      label: 'Item Title',
      required: true,
      type: 'string',
      description: 'Title of the item purchased',
      examples: ['iPhone 13 Pro Max', 'Vintage T-Shirt']
    },
    {
      key: 'quantity',
      label: 'Quantity',
      required: true,
      type: 'number',
      description: 'Number of items ordered',
      examples: ['1', '2', '5']
    },
    {
      key: 'salePrice',
      label: 'Sale Price',
      required: true,
      type: 'number',
      description: 'Price per item',
      examples: ['29.99', '$150.00', '1250']
    },
    {
      key: 'orderStatus',
      label: 'Order Status',
      required: true,
      type: 'string',
      description: 'Current status of the order',
      examples: ['Paid', 'Shipped', 'Delivered', 'Cancelled']
    },
    {
      key: 'orderDate',
      label: 'Order Date',
      required: false,
      type: 'date',
      description: 'Date when order was placed',
      examples: ['2024-01-15', '01/15/2024', '15-Jan-2024']
    }
  ],
  listings: [
    {
      key: 'itemId',
      label: 'Item ID',
      required: true,
      type: 'string',
      description: 'eBay item ID',
      examples: ['123456789012', 'ITM-2024-001']
    },
    {
      key: 'title',
      label: 'Title',
      required: true,
      type: 'string',
      description: 'Listing title',
      examples: ['iPhone 13 Pro Max 256GB', 'Vintage Nike Sneakers']
    },
    {
      key: 'price',
      label: 'Price',
      required: true,
      type: 'number',
      description: 'Current listing price',
      examples: ['99.99', '$1,299.00', '50']
    },
    {
      key: 'quantity',
      label: 'Quantity',
      required: true,
      type: 'number',
      description: 'Available quantity',
      examples: ['1', '10', '0']
    },
    {
      key: 'status',
      label: 'Status',
      required: true,
      type: 'string',
      description: 'Listing status',
      examples: ['Active', 'Ended', 'Sold', 'Out of Stock']
    }
  ],
  products: [
    {
      key: 'sku',
      label: 'SKU',
      required: true,
      type: 'string',
      description: 'Stock Keeping Unit',
      examples: ['PROD-001', 'SKU123456', 'IPH13-256-BLK']
    },
    {
      key: 'name',
      label: 'Product Name',
      required: true,
      type: 'string',
      description: 'Name of the product',
      examples: ['iPhone 13 Pro Max', 'Wireless Headphones']
    },
    {
      key: 'category',
      label: 'Category',
      required: false,
      type: 'string',
      description: 'Product category',
      examples: ['Electronics', 'Clothing', 'Home & Garden']
    },
    {
      key: 'costPrice',
      label: 'Cost Price',
      required: true,
      type: 'number',
      description: 'Cost price from supplier',
      examples: ['50.00', '$25.99', '100']
    },
    {
      key: 'sellingPrice',
      label: 'Selling Price',
      required: true,
      type: 'number',
      description: 'Selling price to customers',
      examples: ['99.99', '$149.00', '200']
    }
  ],
  suppliers: [
    {
      key: 'name',
      label: 'Supplier Name',
      required: true,
      type: 'string',
      description: 'Name of the supplier company',
      examples: ['ABC Electronics Ltd', 'Global Sourcing Inc']
    },
    {
      key: 'country',
      label: 'Country',
      required: true,
      type: 'string',
      description: 'Country where supplier is located',
      examples: ['China', 'United States', 'Germany']
    },
    {
      key: 'email',
      label: 'Email',
      required: true,
      type: 'email',
      description: 'Contact email address',
      examples: ['contact@supplier.com', 'sales@company.co.uk']
    },
    {
      key: 'phone',
      label: 'Phone',
      required: false,
      type: 'phone',
      description: 'Contact phone number',
      examples: ['+1-555-123-4567', '86-138-1234-5678']
    }
  ],
  customers: [
    {
      key: 'name',
      label: 'Customer Name',
      required: true,
      type: 'string',
      description: 'Full name of the customer',
      examples: ['John Smith', 'Mary Johnson']
    },
    {
      key: 'email',
      label: 'Email',
      required: true,
      type: 'email',
      description: 'Customer email address',
      examples: ['customer@example.com', 'buyer123@gmail.com']
    },
    {
      key: 'phone',
      label: 'Phone',
      required: false,
      type: 'phone',
      description: 'Customer phone number',
      examples: ['+1-555-987-6543', '555-123-4567']
    }
  ]
};

export const DataMappingStep: React.FC<DataMappingStepProps> = ({
  csvData,
  importType,
  initialMappings,
  onComplete,
  onBack
}) => {
  const [mappings, setMappings] = useState<Record<string, string>>(initialMappings);
  const [autoMapEnabled, setAutoMapEnabled] = useState(true);
  const [showPreview, setShowPreview] = useState(true);

  const csvColumns = useMemo(() => {
    if (csvData.length === 0) return [];
    return Object.keys(csvData[0]);
  }, [csvData]);

  const fields = fieldDefinitions[importType];
  const previewData = csvData.slice(0, 5); // Show first 5 rows for preview

  // Auto-mapping logic
  useEffect(() => {
    if (autoMapEnabled && Object.keys(initialMappings).length === 0) {
      const autoMappings: Record<string, string> = {};
      
      fields.forEach(field => {
        const matchingColumn = csvColumns.find(column => {
          const colLower = column.toLowerCase();
          const fieldLower = field.label.toLowerCase();
          const keyLower = field.key.toLowerCase();
          
          // Exact match
          if (colLower === fieldLower || colLower === keyLower) return true;
          
          // Partial match
          if (colLower.includes(keyLower) || keyLower.includes(colLower)) return true;
          if (colLower.includes(fieldLower.split(' ')[0]) || fieldLower.includes(colLower)) return true;
          
          // Special cases
          if (field.key === 'buyerEmail' && (colLower.includes('email') || colLower.includes('buyer'))) return true;
          if (field.key === 'orderNumber' && (colLower.includes('order') && colLower.includes('number'))) return true;
          if (field.key === 'itemId' && (colLower.includes('item') && colLower.includes('id'))) return true;
          
          return false;
        });
        
        if (matchingColumn) {
          autoMappings[field.key] = matchingColumn;
        }
      });
      
      setMappings(autoMappings);
    }
  }, [fields, csvColumns, autoMapEnabled, initialMappings]);

  const handleMappingChange = (fieldKey: string, columnName: string) => {
    setMappings(prev => {
      const newMappings = { ...prev };
      if (columnName === '') {
        delete newMappings[fieldKey];
      } else {
        newMappings[fieldKey] = columnName;
      }
      return newMappings;
    });
  };

  const getMappingStatus = () => {
    const requiredFields = fields.filter(f => f.required);
    const mappedRequiredFields = requiredFields.filter(f => mappings[f.key]);
    const totalMappedFields = Object.keys(mappings).length;
    
    return {
      requiredMapped: mappedRequiredFields.length,
      requiredTotal: requiredFields.length,
      totalMapped: totalMappedFields,
      totalFields: fields.length,
      isComplete: mappedRequiredFields.length === requiredFields.length
    };
  };

  const status = getMappingStatus();

  const handleProceed = () => {
    if (status.isComplete) {
      onComplete({ mappings });
    }
  };

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Map CSV Columns to Data Fields
      </Typography>
      
      <Alert 
        severity={status.isComplete ? "success" : "warning"} 
        sx={{ mb: 3 }}
        icon={status.isComplete ? <CheckCircle /> : <Warning />}
      >
        <Typography variant="subtitle2">
          Mapping Status: {status.requiredMapped}/{status.requiredTotal} required fields mapped
          {status.totalMapped > status.requiredMapped && ` (${status.totalMapped - status.requiredMapped} optional)`}
        </Typography>
        {!status.isComplete && (
          <Typography variant="body2">
            Please map all required fields before proceeding.
          </Typography>
        )}
      </Alert>

      {/* Controls */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item>
              <FormControlLabel
                control={
                  <Switch
                    checked={autoMapEnabled}
                    onChange={(e) => setAutoMapEnabled(e.target.checked)}
                  />
                }
                label="Auto-map fields"
              />
            </Grid>
            <Grid item>
              <Button
                startIcon={<AutoAwesome />}
                onClick={() => {
                  // Re-trigger auto mapping
                  setAutoMapEnabled(false);
                  setTimeout(() => setAutoMapEnabled(true), 100);
                }}
              >
                Re-map Automatically
              </Button>
            </Grid>
            <Grid item>
              <FormControlLabel
                control={
                  <Switch
                    checked={showPreview}
                    onChange={(e) => setShowPreview(e.target.checked)}
                  />
                }
                label="Show data preview"
              />
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Field Mapping */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Field Mapping
          </Typography>
          
          <Grid container spacing={2}>
            {fields.map((field) => (
              <Grid item xs={12} md={6} lg={4} key={field.key}>
                <Card variant="outlined" sx={{ height: '100%' }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      <Typography variant="subtitle2" sx={{ flex: 1 }}>
                        {field.label}
                      </Typography>
                      {field.required && (
                        <Chip label="Required" size="small" color="error" />
                      )}
                      {mappings[field.key] && (
                        <Chip 
                          label="Mapped" 
                          size="small" 
                          color="success" 
                          sx={{ ml: 1 }} 
                        />
                      )}
                    </Box>
                    
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      {field.description}
                    </Typography>
                    
                    <FormControl fullWidth size="small">
                      <InputLabel>Select CSV Column</InputLabel>
                      <Select
                        value={mappings[field.key] || ''}
                        label="Select CSV Column"
                        onChange={(e) => handleMappingChange(field.key, e.target.value)}
                      >
                        <MenuItem value="">
                          <em>Not mapped</em>
                        </MenuItem>
                        {csvColumns.map((column) => (
                          <MenuItem key={column} value={column}>
                            {column}
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                    
                    {field.examples.length > 0 && (
                      <Box sx={{ mt: 1 }}>
                        <Typography variant="caption" color="text.secondary">
                          Examples: {field.examples.slice(0, 2).join(', ')}
                        </Typography>
                      </Box>
                    )}
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </CardContent>
      </Card>

      {/* Data Preview */}
      {showPreview && previewData.length > 0 && (
        <Accordion expanded={showPreview}>
          <AccordionSummary expandIcon={<ExpandMore />}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Visibility />
              <Typography variant="h6">
                Data Preview ({previewData.length} sample rows)
              </Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell><strong>Field</strong></TableCell>
                    <TableCell><strong>CSV Column</strong></TableCell>
                    {previewData.map((_, index) => (
                      <TableCell key={index}><strong>Row {index + 1}</strong></TableCell>
                    ))}
                  </TableRow>
                </TableHead>
                <TableBody>
                  {fields.map((field) => {
                    const columnName = mappings[field.key];
                    return (
                      <TableRow key={field.key}>
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            {field.label}
                            {field.required && (
                              <Chip label="Required" size="small" color="error" />
                            )}
                          </Box>
                        </TableCell>
                        <TableCell>
                          {columnName ? (
                            <Chip label={columnName} size="small" color="primary" />
                          ) : (
                            <Typography variant="body2" color="text.secondary">
                              Not mapped
                            </Typography>
                          )}
                        </TableCell>
                        {previewData.map((row, index) => (
                          <TableCell key={index}>
                            {columnName && row[columnName] ? (
                              <Typography variant="body2">
                                {String(row[columnName]).substring(0, 50)}
                                {String(row[columnName]).length > 50 && '...'}
                              </Typography>
                            ) : (
                              <Typography variant="body2" color="text.secondary">
                                -
                              </Typography>
                            )}
                          </TableCell>
                        ))}
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </TableContainer>
          </AccordionDetails>
        </Accordion>
      )}

      {/* Actions */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 3 }}>
        <Button onClick={onBack}>
          Back
        </Button>
        <Button
          variant="contained"
          onClick={handleProceed}
          disabled={!status.isComplete}
        >
          Next: Validate Data
        </Button>
      </Box>
    </Box>
  );
};
```

## Implementation Tasks

### Task 1: Import Wizard Foundation
1. **Create CSV Import Wizard**
   - Implement multi-step wizard with progress tracking
   - Add file upload with drag-and-drop functionality
   - Set up import type selection and configuration

2. **Build File Upload System**
   - Create file validation and analysis
   - Add CSV format detection and encoding handling
   - Implement file size limits and error handling

3. **Test Import Foundation**
   - File upload and validation accuracy
   - CSV parsing with different formats and encodings
   - Progress tracking and state management

### Task 2: Data Mapping Interface
1. **Implement Data Mapping Step**
   - Create intelligent auto-mapping algorithm
   - Add manual column-to-field mapping interface
   - Build data preview with sample rows

2. **Build Field Definition System**
   - Create comprehensive field definitions for all import types
   - Add validation rules and data type checking
   - Implement mapping confidence scoring

3. **Test Mapping Features**
   - Auto-mapping accuracy across different CSV formats
   - Manual mapping interface usability
   - Data preview accuracy and performance

### Task 3: Validation & Processing
1. **Create Validation System**
   - Implement business rule validation
   - Add data type and format checking
   - Create duplicate detection and conflict resolution

2. **Build Import Processing**
   - Create batch processing with progress tracking
   - Add rollback capabilities for failed imports
   - Implement error recovery and partial import handling

3. **Test Validation & Processing**
   - Validation rule accuracy and performance
   - Batch processing with large datasets
   - Error handling and recovery mechanisms

### Task 4: Advanced Features
1. **Import Results & Analytics**
   - Create comprehensive import reporting
   - Add data quality metrics and statistics
   - Implement import history and audit trail

2. **Error Management**
   - Build detailed error reporting and resolution
   - Add data correction and re-import workflows
   - Create import optimization suggestions

3. **Test Advanced Features**
   - Results reporting accuracy
   - Error handling completeness
   - Performance optimization effectiveness

### Task 5: Integration & Performance
1. **Backend Integration**
   - Connect with all data processing APIs
   - Implement real-time progress updates
   - Add webhook support for completion notifications

2. **Performance Optimization**
   - Optimize large file handling and memory usage
   - Add background processing capabilities
   - Implement caching for repeated imports

3. **Test Integration**
   - End-to-end import workflow accuracy
   - Performance with enterprise-scale datasets
   - Cross-browser compatibility and reliability

## Quality Gates

### Performance Requirements
- [ ] File upload: <30 seconds for 10MB files
- [ ] CSV parsing: <5 seconds for 10,000 rows
- [ ] Auto-mapping: <2 seconds for any CSV format
- [ ] Data validation: <10 seconds for 5,000 records
- [ ] Import processing: <60 seconds for 1,000 records

### Functionality Requirements  
- [ ] Auto-mapping accuracy >90% for standard eBay CSV formats
- [ ] Data validation catches all critical errors
- [ ] Import process handles failures gracefully
- [ ] Rollback functionality works correctly
- [ ] Progress tracking is accurate and real-time

### SOLID Compliance Checklist
- [ ] Each step component has single responsibility
- [ ] Import system is extensible for new data types
- [ ] Validation engines are interchangeable
- [ ] Processing interfaces are properly segregated
- [ ] All services depend on abstractions

---
**Next Phase**: Performance Optimization & Polish with caching, monitoring, and production readiness.
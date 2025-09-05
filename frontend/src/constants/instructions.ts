// Instructions Constants - Following SOLID principles
// Single Responsibility: Manages all instruction text
// Open/Closed: Easy to extend new instructions

import { DATA_TYPES, getDataTypeLabel } from './dataTypes';

export interface InstructionSection {
  title: string;
  details: string[];
}

export const SMART_UPLOAD_INSTRUCTIONS: InstructionSection = {
  title: '🚀 Smart Upload Feature:',
  details: [
    'Drop a CSV file without selecting an account first',
    'The system will automatically detect your eBay username from the CSV',
    'Matching accounts will be suggested based on detected username',
    'Click on a suggested account to upload instantly'
  ]
};

export const DATA_TYPE_INSTRUCTIONS: Record<string, InstructionSection> = {
  [DATA_TYPES.ORDER]: {
    title: `For ${getDataTypeLabel(DATA_TYPES.ORDER)}:`,
    details: [
      'Export orders from eBay Seller Hub → Orders → Export to CSV',
      'The system will automatically detect duplicate orders and skip them',
      'New orders will be imported with "pending" status'
    ]
  },
  [DATA_TYPES.LISTING]: {
    title: `For ${getDataTypeLabel(DATA_TYPES.LISTING)}:`,
    details: [
      'Export listings from eBay Seller Hub → Listings → Export to CSV',
      'The system will update inventory levels and listing information',
      'Existing listings will be updated with new data'
    ]
  }
};

// Helper function following Single Responsibility Principle
export const getAllInstructionSections = (): InstructionSection[] => {
  return [
    SMART_UPLOAD_INSTRUCTIONS,
    ...Object.values(DATA_TYPE_INSTRUCTIONS)
  ];
};

export const getInstructionForDataType = (dataType: string): InstructionSection | undefined => {
  return DATA_TYPE_INSTRUCTIONS[dataType];
};
// Data Types Constants - Following SOLID principles
// Open/Closed: Easy to extend new data types
// Single Responsibility: Only manages data type definitions

export interface DataTypeOption {
  value: string;
  label: string;
  description?: string;
}

export const DATA_TYPES = {
  ORDER: 'order',
  LISTING: 'listing',
} as const;

export type DataType = typeof DATA_TYPES[keyof typeof DATA_TYPES];

export const DATA_TYPE_OPTIONS: DataTypeOption[] = [
  {
    value: DATA_TYPES.ORDER,
    label: 'Orders',
    description: 'eBay order data from Seller Hub exports'
  },
  {
    value: DATA_TYPES.LISTING,
    label: 'Listings',
    description: 'eBay listing data from Seller Hub exports'
  },
];

export const DEFAULT_DATA_TYPE: DataType = DATA_TYPES.ORDER;

// Helper functions following Single Responsibility Principle
export const getDataTypeLabel = (dataType: DataType): string => {
  const option = DATA_TYPE_OPTIONS.find(opt => opt.value === dataType);
  return option?.label || dataType;
};

export const getDataTypeDescription = (dataType: DataType): string | undefined => {
  const option = DATA_TYPE_OPTIONS.find(opt => opt.value === dataType);
  return option?.description;
};

export const isValidDataType = (value: string): value is DataType => {
  return Object.values(DATA_TYPES).includes(value as DataType);
};
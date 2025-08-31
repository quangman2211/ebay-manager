import React from 'react';
import {
  Box,
  Typography,
  Tooltip,
  Chip,
  Stack,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Visibility as VisibilityIcon,
  ShoppingCart as ShoppingCartIcon,
} from '@mui/icons-material';

interface ListingPerformanceIndicatorProps {
  listing: any; // Listing type from your types
  compact?: boolean;
}

const ListingPerformanceIndicator: React.FC<ListingPerformanceIndicatorProps> = ({
  listing,
  compact = false,
}) => {
  const csvRow = listing.csv_row;
  
  // Calculate basic metrics from CSV data
  const soldQuantity = parseInt(csvRow['Sold quantity'] || '0');
  const availableQuantity = parseInt(csvRow['Available quantity'] || '0');
  const watchers = parseInt(csvRow['Watchers'] || '0');
  const totalQuantity = soldQuantity + availableQuantity;
  
  const sellThroughRate = totalQuantity > 0 ? (soldQuantity / totalQuantity * 100) : 0;
  
  // Determine performance indicators
  const getPerformanceColor = (rate: number): 'success' | 'warning' | 'error' => {
    if (rate >= 70) return 'success';
    if (rate >= 30) return 'warning';
    return 'error';
  };
  
  const getWatchersColor = (count: number): 'success' | 'info' | 'default' => {
    if (count >= 10) return 'success';
    if (count >= 5) return 'info';
    return 'default';
  };
  
  const performance = getPerformanceColor(sellThroughRate);
  const watchersColor = getWatchersColor(watchers);
  
  const getTrendIcon = (rate: number) => {
    if (rate >= 50) return <TrendingUpIcon fontSize="small" />;
    return <TrendingDownIcon fontSize="small" />;
  };

  if (compact) {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
        <Tooltip title={`Sell-through Rate: ${sellThroughRate.toFixed(1)}%`}>
          <Chip
            icon={getTrendIcon(sellThroughRate)}
            label={`${sellThroughRate.toFixed(0)}%`}
            size="small"
            color={performance}
            variant="outlined"
            sx={{ minWidth: 'auto', fontSize: '0.65rem', height: '20px' }}
          />
        </Tooltip>
        
        {watchers > 0 && (
          <Tooltip title={`${watchers} watchers`}>
            <Chip
              icon={<VisibilityIcon fontSize="small" />}
              label={watchers}
              size="small"
              color={watchersColor}
              variant="filled"
              sx={{ 
                minWidth: 'auto', 
                fontSize: '0.65rem', 
                height: '20px',
                '& .MuiChip-icon': {
                  fontSize: '12px'
                }
              }}
            />
          </Tooltip>
        )}
      </Box>
    );
  }

  return (
    <Box sx={{ p: 1 }}>
      <Stack spacing={1}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="body2" fontWeight="medium">
            Performance
          </Typography>
          <Chip
            icon={getTrendIcon(sellThroughRate)}
            label={`${sellThroughRate.toFixed(1)}%`}
            size="small"
            color={performance}
            variant="filled"
          />
        </Box>
        
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <ShoppingCartIcon fontSize="small" color="action" />
            <Typography variant="body2" color="textSecondary">
              {soldQuantity} sold
            </Typography>
          </Box>
          
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <VisibilityIcon fontSize="small" color="action" />
            <Typography variant="body2" color="textSecondary">
              {watchers} watchers
            </Typography>
          </Box>
        </Box>
        
        {/* Quick indicators */}
        <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
          {soldQuantity === 0 && availableQuantity > 0 && (
            <Chip
              label="No Sales Yet"
              size="small"
              color="warning"
              variant="outlined"
            />
          )}
          
          {watchers >= 10 && (
            <Chip
              label="High Interest"
              size="small"
              color="success"
              variant="outlined"
            />
          )}
          
          {availableQuantity === 0 && soldQuantity > 0 && (
            <Chip
              label="Sold Out"
              size="small"
              color="error"
              variant="filled"
            />
          )}
        </Box>
      </Stack>
    </Box>
  );
};

export default ListingPerformanceIndicator;
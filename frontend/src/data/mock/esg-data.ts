import type { EnergyData, CarbonData, WasteData, Company, UploadedFile } from '../../types/esg';

export const company: Company = {
  name: 'Apex Manufacturing Co.',
  industry: 'Manufacturing',
  employeeCount: '50-100',
  location: 'Portland, OR',
};

export const energyData: EnergyData[] = [
  { month: 'Jan', kWh: 12450, cost: 1868 },
  { month: 'Feb', kWh: 11800, cost: 1770 },
  { month: 'Mar', kWh: 13200, cost: 1980 },
  { month: 'Apr', kWh: 14500, cost: 2175 },
  { month: 'May', kWh: 16200, cost: 2430 },
  { month: 'Jun', kWh: 18900, cost: 2835 },
  { month: 'Jul', kWh: 20100, cost: 3015 },
  { month: 'Aug', kWh: 19500, cost: 2925 },
  { month: 'Sep', kWh: 16800, cost: 2520 },
  { month: 'Oct', kWh: 14900, cost: 2235 },
  { month: 'Nov', kWh: 13100, cost: 1965 },
  { month: 'Dec', kWh: 14200, cost: 2130 },
];

export const carbonData: CarbonData[] = [
  { month: 'Jan', scope1: 12.4, scope2: 28.6, scope3: 18.2, total: 59.2 },
  { month: 'Feb', scope1: 11.8, scope2: 27.1, scope3: 17.4, total: 56.3 },
  { month: 'Mar', scope1: 13.2, scope2: 30.2, scope3: 19.1, total: 62.5 },
  { month: 'Apr', scope1: 14.5, scope2: 33.4, scope3: 20.8, total: 68.7 },
  { month: 'May', scope1: 16.2, scope2: 37.1, scope3: 23.2, total: 76.5 },
  { month: 'Jun', scope1: 18.9, scope2: 43.5, scope3: 27.1, total: 89.5 },
  { month: 'Jul', scope1: 20.1, scope2: 46.2, scope3: 28.4, total: 94.7 },
  { month: 'Aug', scope1: 19.5, scope2: 44.8, scope3: 27.6, total: 91.9 },
  { month: 'Sep', scope1: 16.8, scope2: 38.6, scope3: 24.2, total: 79.6 },
  { month: 'Oct', scope1: 14.9, scope2: 34.2, scope3: 21.5, total: 70.6 },
  { month: 'Nov', scope1: 13.1, scope2: 30.1, scope3: 18.9, total: 62.1 },
  { month: 'Dec', scope1: 14.2, scope2: 32.7, scope3: 20.3, total: 67.2 },
];

export const wasteData: WasteData[] = [
  { month: 'Jan', landfill: 2.4, recycled: 8.6, total: 11.0 },
  { month: 'Feb', landfill: 2.2, recycled: 8.2, total: 10.4 },
  { month: 'Mar', landfill: 2.6, recycled: 9.1, total: 11.7 },
  { month: 'Apr', landfill: 2.9, recycled: 10.2, total: 13.1 },
  { month: 'May', landfill: 3.2, recycled: 11.4, total: 14.6 },
  { month: 'Jun', landfill: 3.8, recycled: 13.2, total: 17.0 },
  { month: 'Jul', landfill: 4.0, recycled: 14.1, total: 18.1 },
  { month: 'Aug', landfill: 3.9, recycled: 13.7, total: 17.6 },
  { month: 'Sep', landfill: 3.4, recycled: 11.8, total: 15.2 },
  { month: 'Oct', landfill: 3.0, recycled: 10.5, total: 13.5 },
  { month: 'Nov', landfill: 2.6, recycled: 9.2, total: 11.8 },
  { month: 'Dec', landfill: 2.8, recycled: 10.0, total: 12.8 },
];

export const uploadedFiles: UploadedFile[] = [
  { id: '1', name: 'Fuel_Invoice.pdf', type: 'pdf', size: '2.4 MB', uploadedAt: '2024-12-15' },
  { id: '2', name: 'Electricity_Bill.jpg', type: 'jpg', size: '1.8 MB', uploadedAt: '2024-12-10' },
  { id: '3', name: 'Expense_Report.xlsx', type: 'xlsx', size: '856 KB', uploadedAt: '2024-12-08' },
];

export const totalEnergy = energyData.reduce((acc, d) => acc + d.kWh, 0);
export const totalCarbon = carbonData.reduce((acc, d) => acc + d.total, 0);
export const totalWaste = wasteData.reduce((acc, d) => acc + d.total, 0);
export const recyclingRate = (wasteData.reduce((acc, d) => acc + d.recycled, 0) / wasteData.reduce((acc, d) => acc + d.total, 0)) * 100;
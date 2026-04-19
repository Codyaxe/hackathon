export interface EnergyData {
  month: string;
  kWh: number;
  cost: number;
}

export interface CarbonData {
  month: string;
  scope1: number;
  scope2: number;
  scope3: number;
  total: number;
}

export interface WasteData {
  month: string;
  landfill: number;
  recycled: number;
  total: number;
}

export interface ESGMetrics {
  energy: EnergyData[];
  carbon: CarbonData[];
  waste: WasteData[];
}

export interface UploadedFile {
  id: string;
  name: string;
  type: 'pdf' | 'jpg' | 'xlsx';
  size: string;
  uploadedAt: string;
}

export interface Company {
  name: string;
  industry: string;
  employeeCount: string;
  location: string;
}

export type ESGScore = 'excellent' | 'good' | 'fair' | 'poor';

export interface ScoreCard {
  label: string;
  value: string | number;
  unit: string;
  score: ESGScore;
  trend: 'up' | 'down' | 'stable';
  change?: number;
}
export interface TimeSeriesData {
    time: string;
    simulated: number;
    actual: number;
    temperature?: number;
}

export interface ZoneData {
    name: string;
    simulated: number;
    actual: number;
    variance: number;
}

export interface DailyMetrics {
    totalSimulatedkWh: number;
    totalActualkWh: number;
    estimatedCostSimulated: number;
    estimatedCostActual: number;
    peakDemandSimulated: number;
    peakDemandActual: number;
    carbonEmissionVariance: number;
}

// Generate 24 hours of mock power consumption data
export const generateTimeSeriesData = (): TimeSeriesData[] => {
    const data: TimeSeriesData[] = [];
    const baseLoad = 15; // kW

    for (let i = 0; i < 24; i++) {
        const time = `${i.toString().padStart(2, '0')}:00`;

        // Create a typical office load profile
        let simulated = baseLoad;
        if (i >= 8 && i <= 18) {
            simulated += 40 + Math.sin((i - 8) / 10 * Math.PI) * 30;
        } else if (i > 18 && i <= 22) {
            simulated += 15 - (i - 18) * 3;
        }

        // Add some noise and variance for actual data
        // In this mock, actual is slightly higher during peak hours, lower off-peak
        const noise = (Math.random() - 0.5) * 5;
        let actual = simulated + noise;

        if (i >= 9 && i <= 16) {
            actual += 8 + Math.random() * 5; // HVAC running harder than simulated
        } else if (i >= 22 || i <= 5) {
            actual -= 3 + Math.random() * 2; // Better standby idle than simulated
        }

        // Ensure no negative values
        simulated = Math.max(0, Math.round(simulated * 10) / 10);
        actual = Math.max(0, Math.round(actual * 10) / 10);

        // Ambient temperature mock
        let temp = 22;
        if (i >= 6 && i <= 15) {
            temp += (i - 6) * 1.5;
        } else if (i > 15) {
            temp = 35.5 - (i - 15) * 1.2;
        }

        data.push({
            time,
            simulated,
            actual,
            temperature: Math.round(temp * 10) / 10
        });
    }

    return data;
};

export const MOCK_TIME_SERIES = generateTimeSeriesData();

export const MOCK_ZONE_DATA: ZoneData[] = [
    { name: 'HVAC System', simulated: 245.5, actual: 310.2, variance: 26.3 },
    { name: 'Lighting', simulated: 120.0, actual: 115.8, variance: -3.5 },
    { name: 'Workstations', simulated: 180.5, actual: 195.0, variance: 8.0 },
    { name: 'Server Room', simulated: 450.0, actual: 445.5, variance: -1.0 },
    { name: 'Common Areas', simulated: 45.0, actual: 62.3, variance: 38.4 },
];

export const MOCK_METRICS: DailyMetrics = {
    totalSimulatedkWh: 1041.0,
    totalActualkWh: 1128.8,
    estimatedCostSimulated: 156.15,
    estimatedCostActual: 169.32,
    peakDemandSimulated: 95.2,
    peakDemandActual: 112.5,
    carbonEmissionVariance: +8.4, // percentage
};

export const MOCK_SUGGESTIONS = [
    {
        id: 1,
        category: 'HVAC',
        title: 'HVAC Schedule Optimization',
        description: 'Actual HVAC consumption is 26.3% higher than simulated. The sensors detect cooling operations starting at 6:00 AM, but occupancy data shows minimal presence before 8:00 AM.',
        action: 'Adjust HVAC start time to 7:15 AM to match realistic occupancy ramp-up.',
        potentialSavings: '$12.50 / day',
        impact: 'High',
    },
    {
        id: 2,
        category: 'Lighting',
        title: 'Common Area Lighting Overuse',
        description: 'Common areas show 38.4% higher usage than simulated. Lights remain at 100% brightness during midday when natural ambient light is sufficient.',
        action: 'Enable automated daylight harvesting or install photosensors near large windows.',
        potentialSavings: '$3.20 / day',
        impact: 'Medium',
    },
    {
        id: 3,
        category: 'Workstations',
        title: 'Phantom Loads Detected',
        description: 'Workstations show continuous 2.5kW drain between 10:00 PM and 5:00 AM. Simulation assumes sleep modes are active.',
        action: 'Enforce network-wide sleep policies for idle desktops after hours.',
        potentialSavings: '$4.15 / day',
        impact: 'Medium',
    }
];

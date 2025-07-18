'use client';

import { useEffect, useState } from 'react';
import { Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

interface ForecastData {
  Store: string;
  Product: string;
  'Forecasted Demand': number;
}

export default function ForecastChart() {
  const [data, setData] = useState<ForecastData[]>([]);

  useEffect(() => {
    fetch('http://localhost:8000/download/forecast_df.csv')
      .then((res) => res.text())
      .then((csv) => {
        const rows = csv.trim().split('\n').slice(1); // skip header
        const parsed = rows.map((line) => {
          const [Store, Product, DemandStr] = line.split(',');
          return {
            Store,
            Product,
            'Forecasted Demand': parseInt(DemandStr),
          };
        });
        setData(parsed);
      });
  }, []);

  const labels = data.map((row) => `${row.Product} (${row.Store})`);
  const demandValues = data.map((row) => row['Forecasted Demand']);

  const chartData = {
    labels,
    datasets: [
      {
        label: 'Forecasted Demand',
        data: demandValues,
        backgroundColor: '#42A5F5',
        borderColor: '#1E88E5',
        borderWidth: 1,
      },
    ],
  };

  return (
    <div className="bg-white rounded-xl p-6 shadow-md" style={{ height: '500px' }}>
      <Bar
        data={chartData}
        height={400}
        options={{
          responsive: true,
          maintainAspectRatio: false,
          animation: {
            duration: 0, // ✅ disables animation properly in TS
          },
          transitions: {
            active: {
              animation: {
                duration: 0,
              },
            },
          },
          plugins: {
            legend: { display: false },
            tooltip: { mode: 'index', intersect: false },
          },
          scales: {
            y: {
              beginAtZero: true,
              title: {
                display: true,
                text: 'Demand',
                font: { size: 14 },
              },
            },
            x: {
              ticks: {
                autoSkip: false,
                maxRotation: 45,
                minRotation: 45,
              },
            },
          },
        }}
      />
    </div>
  );
}

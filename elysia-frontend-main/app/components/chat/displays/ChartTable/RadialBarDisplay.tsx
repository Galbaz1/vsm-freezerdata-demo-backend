"use client";

import React from "react";
import {
  RadialBarChart,
  RadialBar,
  Legend,
  ResponsiveContainer,
  PolarAngleAxis,
} from "recharts";
import { ResultPayload } from "@/app/types/chat";
import { Separator } from "@/components/ui/separator";

interface RadialBarDisplayProps {
  result: ResultPayload;
}

interface RadialBarChartPayload {
  _REF_ID?: string;
  title: string;
  description: string;
  data: {
    name: string;
    value: number;
    max_value: number;
    color?: string;
  }[];
}

// Helper to get color based on percentage
const getColorForScore = (value: number, maxValue: number, customColor?: string): string => {
  if (customColor) return customColor;
  
  const percentage = (value / maxValue) * 100;
  if (percentage >= 70) return "#10B981"; // Green
  if (percentage >= 30) return "#F59E0B"; // Yellow
  return "#EF4444"; // Red
};

const RadialBarDisplay: React.FC<RadialBarDisplayProps> = ({ result }) => {
  return (
    <div className="w-full flex flex-col justify-center items-center gap-8">
      {(result.objects as RadialBarChartPayload[]).map((chartItem, chartIndex) => {
        // Transform data to include percentage
        const transformedData = chartItem.data.map((item) => ({
          name: item.name,
          value: item.value,
          fill: getColorForScore(item.value, item.max_value, item.color),
          percentage: ((item.value / item.max_value) * 100).toFixed(1),
        }));

        return (
          <div
            key={chartItem._REF_ID || chartIndex}
            className="w-full flex flex-col gap-4 bg-background rounded-lg p-4"
          >
            <div className="w-full flex flex-col gap-1">
              <p className="text-lg text-primary">
                {chartItem.title || result.metadata?.title || "Health Metrics"}
              </p>
              <p className="text-sm text-secondary">{chartItem.description}</p>
              <div className="flex flex-wrap gap-4 text-sm text-secondary">
                <span className="flex items-center gap-1">
                  <div className="w-2 h-2 bg-highlight rounded-full"></div>
                  Metrics: {chartItem.data.length}
                </span>
              </div>
            </div>

            <Separator />

            {/* Chart Container */}
            <div className="w-full h-[40vh]">
              <ResponsiveContainer width="100%" height="100%">
                <RadialBarChart
                  cx="50%"
                  cy="50%"
                  innerRadius="10%"
                  outerRadius="90%"
                  barSize={20}
                  data={transformedData}
                  startAngle={90}
                  endAngle={-270}
                >
                  <PolarAngleAxis
                    type="number"
                    domain={[0, 100]}
                    angleAxisId={0}
                    tick={false}
                  />
                  <RadialBar
                    background
                    dataKey="value"
                    cornerRadius={10}
                    label={{
                      position: 'insideStart',
                      fill: '#fff',
                      fontSize: 12,
                      // eslint-disable-next-line @typescript-eslint/no-explicit-any
                      formatter: (value: number, entry: any) => entry?.name && entry?.percentage ? `${entry.name}: ${entry.percentage}%` : ''
                    }}
                  />
                  <Legend
                    iconSize={10}
                    layout="vertical"
                    verticalAlign="middle"
                    align="right"
                    wrapperStyle={{
                      fontSize: "14px",
                    }}
                    // eslint-disable-next-line @typescript-eslint/no-explicit-any, @typescript-eslint/no-unused-vars
                    formatter={(value, _entry: any) => {
                      const item = transformedData.find(d => d.name === value);
                      return `${value}: ${item?.value}/${chartItem.data.find(d => d.name === value)?.max_value} (${item?.percentage}%)`;
                    }}
                  />
                </RadialBarChart>
              </ResponsiveContainer>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default RadialBarDisplay;


"use client";

import React from "react";
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { ResultPayload } from "@/app/types/chat";
import { Separator } from "@/components/ui/separator";
import { getColor } from "./util";

interface PieDisplayProps {
  result: ResultPayload;
}

interface PieChartPayload {
  _REF_ID?: string;
  title: string;
  description: string;
  data: {
    name: string;
    value: number;
    color?: string;
  }[];
}

// Custom label for percentage display
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const renderLabel = (entry: any) => {
  const percent = ((entry.value / entry.payload.total) * 100).toFixed(1);
  return `${entry.name} (${percent}%)`;
};

// Custom tooltip
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0];
    const total = data.payload.total;
    const percent = ((data.value / total) * 100).toFixed(1);
    
    return (
      <div className="bg-background_alt border border-foreground_alt rounded-lg p-3">
        <p className="text-sm text-primary font-semibold">{data.name}</p>
        <p className="text-sm" style={{ color: data.payload.fill }}>
          Value: {data.value}
        </p>
        <p className="text-sm text-secondary">
          {percent}% of total
        </p>
      </div>
    );
  }
  return null;
};

const PieDisplay: React.FC<PieDisplayProps> = ({ result }) => {
  return (
    <div className="w-full flex flex-col justify-center items-center gap-8">
      {(result.objects as PieChartPayload[]).map((chartItem, chartIndex) => {
        const total = chartItem.data.reduce((sum, slice) => sum + slice.value, 0);
        const dataWithTotal = chartItem.data.map(slice => ({
          ...slice,
          total
        }));

        return (
          <div
            key={chartItem._REF_ID || chartIndex}
            className="w-full flex flex-col gap-4 bg-background rounded-lg p-4"
          >
            <div className="w-full flex flex-col gap-1">
              <p className="text-lg text-primary">
                {chartItem.title || result.metadata?.title || "Pie Chart"}
              </p>
              <p className="text-sm text-secondary">{chartItem.description}</p>
              <div className="flex flex-wrap gap-4 text-sm text-secondary">
                <span className="flex items-center gap-1">
                  <div className="w-2 h-2 bg-highlight rounded-full"></div>
                  Slices: {chartItem.data.length}
                </span>
                <span className="flex items-center gap-1">
                  <div className="w-2 h-2 bg-highlight rounded-full"></div>
                  Total: {total.toFixed(0)}
                </span>
              </div>
            </div>

            <Separator />

            {/* Chart Container */}
            <div className="w-full h-[40vh]">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={dataWithTotal}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={renderLabel}
                    outerRadius={120}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {dataWithTotal.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={entry.color || getColor(index)}
                      />
                    ))}
                  </Pie>
                  <Tooltip content={<CustomTooltip />} />
                  <Legend
                    wrapperStyle={{
                      paddingTop: "20px",
                      fontSize: "14px",
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default PieDisplay;


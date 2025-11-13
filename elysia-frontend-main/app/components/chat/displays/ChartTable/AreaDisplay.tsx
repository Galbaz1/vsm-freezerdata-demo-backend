"use client";

import React from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { ResultPayload } from "@/app/types/chat";
import { Separator } from "@/components/ui/separator";
import { getColor } from "./util";

interface AreaDisplayProps {
  result: ResultPayload;
}

interface AreaChartPayload {
  _REF_ID?: string;
  title: string;
  description: string;
  x_axis_label: string;
  y_axis_label: string;
  data: {
    x_axis: (string | number | Date)[];
    series: {
      name: string;
      data: (number | null)[];
      color?: string;
      fill_opacity?: number;
    }[];
  };
}

// Custom tooltip component
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-background_alt border border-foreground_alt rounded-lg p-3">
        <p className="text-sm text-primary font-semibold">{`${label}`}</p>
        {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
        {payload.map((entry: any, index: number) => (
          <p key={index} className="text-sm" style={{ color: entry.color }}>
            {`${entry.dataKey}: ${entry.value?.toFixed(2) ?? 'N/A'}`}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

const AreaDisplay: React.FC<AreaDisplayProps> = ({ result }) => {
  // Transform the chart data for Recharts
  const transformChartData = (chartItem: AreaChartPayload) => {
    const { data, x_axis_label } = chartItem;
    const { x_axis, series } = data;

    // Create data points for the chart
    const transformedData = [];

    for (let i = 0; i < x_axis.length; i++) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const dataPoint: any = {
        [x_axis_label]: x_axis[i],
      };

      // Add all series data
      series.forEach((s) => {
        dataPoint[s.name] = s.data[i];
      });

      transformedData.push(dataPoint);
    }

    return {
      data: transformedData,
      xAxisKey: x_axis_label,
      series: series,
    };
  };

  return (
    <div className="w-full flex flex-col justify-center items-center gap-8">
      {(result.objects as AreaChartPayload[]).map((chartItem, chartIndex) => {
        const {
          data: transformedData,
          xAxisKey,
          series,
        } = transformChartData(chartItem);

        return (
          <div
            key={chartItem._REF_ID || chartIndex}
            className="w-full flex flex-col gap-4 bg-background rounded-lg p-4"
          >
            <div className="w-full flex flex-col gap-1">
              <p className="text-lg text-primary">
                {chartItem.title || result.metadata?.title || "Area Chart"}
              </p>
              <p className="text-sm text-secondary">{chartItem.description}</p>
              <div className="flex flex-wrap gap-4 text-sm text-secondary">
                <span className="flex items-center gap-1">
                  <div className="w-2 h-2 bg-highlight rounded-full"></div>
                  Data Points: {transformedData.length}
                </span>
                <span className="flex items-center gap-1">
                  <div className="w-2 h-2 bg-highlight rounded-full"></div>
                  Series: {series.length}
                </span>
              </div>
            </div>

            <Separator />

            {/* Chart Container */}
            <div className="w-full h-[40vh]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart
                  data={transformedData}
                  margin={{ top: 10, right: 30, left: 10, bottom: 10 }}
                >
                  <defs>
                    {series.map((s, index) => (
                      <linearGradient
                        key={`gradient-${s.name}`}
                        id={`color-${s.name.replace(/\s/g, '-')}`}
                        x1="0"
                        y1="0"
                        x2="0"
                        y2="1"
                      >
                        <stop
                          offset="5%"
                          stopColor={s.color || getColor(index)}
                          stopOpacity={s.fill_opacity || 0.8}
                        />
                        <stop
                          offset="95%"
                          stopColor={s.color || getColor(index)}
                          stopOpacity={s.fill_opacity || 0.1}
                        />
                      </linearGradient>
                    ))}
                  </defs>
                  <CartesianGrid
                    horizontal={true}
                    vertical={false}
                    stroke="#E5E7EB"
                    strokeOpacity={0.3}
                  />
                  <XAxis
                    dataKey={xAxisKey}
                    stroke="#6B7280"
                    fontSize={12}
                    tick={{ fill: "#6B7280" }}
                    axisLine={{ stroke: "#D1D5DB" }}
                  />
                  <YAxis
                    stroke="#6B7280"
                    fontSize={12}
                    tick={{ fill: "#6B7280" }}
                    axisLine={{ stroke: "#D1D5DB" }}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend
                    wrapperStyle={{
                      paddingTop: "10px",
                      fontSize: "14px",
                    }}
                  />
                  {series.map((s, index) => (
                    <Area
                      key={s.name}
                      type="monotone"
                      dataKey={s.name}
                      stroke={s.color || getColor(index)}
                      fill={`url(#color-${s.name.replace(/\s/g, '-')})`}
                      strokeWidth={2}
                    />
                  ))}
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default AreaDisplay;


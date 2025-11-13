"use client";

import React from "react";
import {
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { ResultPayload } from "@/app/types/chat";
import { Separator } from "@/components/ui/separator";
import { getColor } from "./util";

interface RadarDisplayProps {
  result: ResultPayload;
}

interface RadarChartPayload {
  _REF_ID?: string;
  title: string;
  description: string;
  metrics: string[];
  data: {
    [seriesName: string]: number[];
  };
}

// Custom tooltip
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-background_alt border border-foreground_alt rounded-lg p-3">
        <p className="text-sm text-primary font-semibold">{payload[0].payload.metric}</p>
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

const RadarDisplay: React.FC<RadarDisplayProps> = ({ result }) => {
  const transformChartData = (chartItem: RadarChartPayload) => {
    const { metrics, data } = chartItem;

    // Transform to Recharts format
    const transformedData = metrics.map((metric, index) => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const point: any = {
        metric: metric,
      };

      Object.entries(data).forEach(([seriesName, values]) => {
        point[seriesName] = values[index];
      });

      return point;
    });

    return {
      data: transformedData,
      seriesNames: Object.keys(data),
    };
  };

  return (
    <div className="w-full flex flex-col justify-center items-center gap-8">
      {(result.objects as RadarChartPayload[]).map((chartItem, chartIndex) => {
        const { data: transformedData, seriesNames } = transformChartData(chartItem);

        return (
          <div
            key={chartItem._REF_ID || chartIndex}
            className="w-full flex flex-col gap-4 bg-background rounded-lg p-4"
          >
            <div className="w-full flex flex-col gap-1">
              <p className="text-lg text-primary">
                {chartItem.title || result.metadata?.title || "Radar Chart"}
              </p>
              <p className="text-sm text-secondary">{chartItem.description}</p>
              <div className="flex flex-wrap gap-4 text-sm text-secondary">
                <span className="flex items-center gap-1">
                  <div className="w-2 h-2 bg-highlight rounded-full"></div>
                  Metrics: {chartItem.metrics.length}
                </span>
                <span className="flex items-center gap-1">
                  <div className="w-2 h-2 bg-highlight rounded-full"></div>
                  Series: {seriesNames.length}
                </span>
              </div>
            </div>

            <Separator />

            <div className="w-full h-[40vh]">
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart data={transformedData}>
                  <PolarGrid stroke="#E5E7EB" strokeOpacity={0.5} />
                  <PolarAngleAxis
                    dataKey="metric"
                    tick={{ fill: "#6B7280", fontSize: 12 }}
                  />
                  <PolarRadiusAxis
                    angle={90}
                    domain={[0, 'auto']}
                    tick={{ fill: "#6B7280", fontSize: 10 }}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend
                    wrapperStyle={{
                      paddingTop: "10px",
                      fontSize: "14px",
                    }}
                  />
                  {seriesNames.map((seriesName, index) => (
                    <Radar
                      key={seriesName}
                      name={seriesName}
                      dataKey={seriesName}
                      stroke={getColor(index)}
                      fill={getColor(index)}
                      fillOpacity={0.3}
                      strokeWidth={2}
                    />
                  ))}
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default RadarDisplay;


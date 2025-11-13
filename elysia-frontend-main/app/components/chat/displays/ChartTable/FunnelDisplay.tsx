"use client";

import React from "react";
import {
  FunnelChart,
  Funnel,
  Tooltip,
  Legend,
  ResponsiveContainer,
  LabelList,
} from "recharts";
import { ResultPayload } from "@/app/types/chat";
import { Separator } from "@/components/ui/separator";
import { getColor } from "./util";

interface FunnelDisplayProps {
  result: ResultPayload;
}

interface FunnelChartPayload {
  _REF_ID?: string;
  title: string;
  description: string;
  stages: {
    name: string;
    value: number;
    color?: string;
  }[];
}

// Custom tooltip
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0];
    return (
      <div className="bg-background_alt border border-foreground_alt rounded-lg p-3">
        <p className="text-sm text-primary font-semibold">{data.name}</p>
        <p className="text-sm" style={{ color: data.payload.fill }}>
          Value: {data.value}
        </p>
      </div>
    );
  }
  return null;
};

const FunnelDisplay: React.FC<FunnelDisplayProps> = ({ result }) => {
  return (
    <div className="w-full flex flex-col justify-center items-center gap-8">
      {(result.objects as FunnelChartPayload[]).map((chartItem, chartIndex) => {
        // Add fill colors to data
        const dataWithColors = chartItem.stages.map((stage, index) => ({
          ...stage,
          fill: stage.color || getColor(index),
        }));

        return (
          <div
            key={chartItem._REF_ID || chartIndex}
            className="w-full flex flex-col gap-4 bg-background rounded-lg p-4"
          >
            <div className="w-full flex flex-col gap-1">
              <p className="text-lg text-primary">
                {chartItem.title || result.metadata?.title || "Funnel Chart"}
              </p>
              <p className="text-sm text-secondary">{chartItem.description}</p>
              <div className="flex flex-wrap gap-4 text-sm text-secondary">
                <span className="flex items-center gap-1">
                  <div className="w-2 h-2 bg-highlight rounded-full"></div>
                  Stages: {chartItem.stages.length}
                </span>
              </div>
            </div>

            <Separator />

            <div className="w-full h-[40vh]">
              <ResponsiveContainer width="100%" height="100%">
                <FunnelChart>
                  <Tooltip content={<CustomTooltip />} />
                  <Funnel
                    dataKey="value"
                    data={dataWithColors}
                    isAnimationActive
                  >
                    <LabelList
                      position="inside"
                      fill="#fff"
                      stroke="none"
                      dataKey="name"
                      fontSize={14}
                    />
                  </Funnel>
                  <Legend
                    wrapperStyle={{
                      paddingTop: "20px",
                      fontSize: "14px",
                    }}
                  />
                </FunnelChart>
              </ResponsiveContainer>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default FunnelDisplay;


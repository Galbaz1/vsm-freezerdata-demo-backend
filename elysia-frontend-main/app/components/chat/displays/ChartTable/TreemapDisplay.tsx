"use client";

import React from "react";
import {
  Treemap,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { ResultPayload } from "@/app/types/chat";
import { Separator } from "@/components/ui/separator";
import { getColor } from "./util";

interface TreemapDisplayProps {
  result: ResultPayload;
}

interface TreemapNode {
  name: string;
  value: number;
  children?: TreemapNode[];
}

interface TreemapChartPayload {
  _REF_ID?: string;
  title: string;
  description: string;
  data: TreemapNode[];
}

// Custom content renderer for treemap cells
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const CustomContent = (props: any) => {
  const { x, y, width, height, index, name, value } = props;

  if (width < 40 || height < 30) {
    return null;
  }

  return (
    <g>
      <rect
        x={x}
        y={y}
        width={width}
        height={height}
        style={{
          fill: getColor(index),
          stroke: "#fff",
          strokeWidth: 2,
        }}
      />
      <text
        x={x + width / 2}
        y={y + height / 2 - 7}
        textAnchor="middle"
        fill="#fff"
        fontSize={12}
        fontWeight="bold"
      >
        {name}
      </text>
      <text
        x={x + width / 2}
        y={y + height / 2 + 7}
        textAnchor="middle"
        fill="#fff"
        fontSize={11}
      >
        {value}
      </text>
    </g>
  );
};

// Custom tooltip
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0];
    return (
      <div className="bg-background_alt border border-foreground_alt rounded-lg p-3">
        <p className="text-sm text-primary font-semibold">{data.payload.name}</p>
        <p className="text-sm text-secondary">
          Value: {data.value}
        </p>
      </div>
    );
  }
  return null;
};

const TreemapDisplay: React.FC<TreemapDisplayProps> = ({ result }) => {
  return (
    <div className="w-full flex flex-col justify-center items-center gap-8">
      {(result.objects as TreemapChartPayload[]).map((chartItem, chartIndex) => {
        return (
          <div
            key={chartItem._REF_ID || chartIndex}
            className="w-full flex flex-col gap-4 bg-background rounded-lg p-4"
          >
            <div className="w-full flex flex-col gap-1">
              <p className="text-lg text-primary">
                {chartItem.title || result.metadata?.title || "Treemap Chart"}
              </p>
              <p className="text-sm text-secondary">{chartItem.description}</p>
              <div className="flex flex-wrap gap-4 text-sm text-secondary">
                <span className="flex items-center gap-1">
                  <div className="w-2 h-2 bg-highlight rounded-full"></div>
                  Nodes: {chartItem.data.length}
                </span>
              </div>
            </div>

            <Separator />

            <div className="w-full h-[40vh]">
              <ResponsiveContainer width="100%" height="100%">
                <Treemap
                  data={chartItem.data}
                  dataKey="value"
                  stroke="#fff"
                  fill="#8884d8"
                  content={<CustomContent />}
                >
                  <Tooltip content={<CustomTooltip />} />
                </Treemap>
              </ResponsiveContainer>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default TreemapDisplay;


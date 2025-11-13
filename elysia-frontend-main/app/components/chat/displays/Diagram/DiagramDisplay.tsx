"use client";

import React from "react";
import Image from "next/image";
import MarkdownFormat from "../../components/MarkdownFormat";
import { DiagramPayload } from "@/app/types/displays";

interface DiagramDisplayProps {
  diagrams: DiagramPayload[];
}

const DiagramDisplay: React.FC<DiagramDisplayProps> = ({ diagrams }) => {
  if (!diagrams || diagrams.length === 0) {
    return null;
  }

  // Filter out any undefined/null diagrams
  const validDiagrams = diagrams.filter((diagram) => diagram != null);

  if (validDiagrams.length === 0) {
    return null;
  }

  return (
    <div className="w-full flex flex-col gap-4 fade-in">
      <div className="flex items-center gap-2">
        <p className="text-lg font-semibold">
          {validDiagrams.length} Diagram{validDiagrams.length > 1 ? "s" : ""}
        </p>
      </div>

      <div className="flex flex-col gap-6">
        {validDiagrams.map((diagram, index) => {
          if (!diagram) return null;
          
          const diagramId = diagram.diagram_id || diagram.title || `diagram-${index}`;
          const title = diagram.title || "Diagram";
          
          return (
          <div
            key={diagramId}
            className="border border-border rounded-lg p-4 flex flex-col gap-3 hover:border-primary transition-all"
          >
            {/* Title */}
            <div className="flex flex-col gap-1">
              <h3 className="text-lg font-semibold">{title}</h3>
              {diagram.description && (
                <p className="text-sm text-muted-foreground">{diagram.description}</p>
              )}
            </div>

            {/* Diagram Content */}
            <div className="w-full">
              {/* PNG Diagram */}
              {diagram.png_url && typeof diagram.png_url === "string" && (
                <div className="relative w-full min-h-[300px] bg-background rounded overflow-hidden border border-border">
                  <Image
                    src={diagram.png_url}
                    alt={title || "Diagram"}
                    fill
                    className="object-contain p-4"
                    unoptimized // For localhost images
                  />
                </div>
              )}

              {/* Mermaid Diagram */}
              {diagram.mermaid_code && !diagram.png_url && (
                <div className="w-full bg-background rounded border border-border p-4">
                  <MarkdownFormat
                    text={`\`\`\`mermaid\n${diagram.mermaid_code}\n\`\`\``}
                    variant="primary"
                  />
                </div>
              )}

              {/* Fallback: Markdown (if neither PNG nor Mermaid) */}
              {!diagram.png_url && !diagram.mermaid_code && diagram.markdown && (
                <div className="w-full bg-background rounded border border-border p-4">
                  <MarkdownFormat text={diagram.markdown} variant="primary" />
                </div>
              )}
            </div>
          </div>
          );
        })}
      </div>
    </div>
  );
};

export default DiagramDisplay;


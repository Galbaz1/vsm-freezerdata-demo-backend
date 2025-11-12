/* eslint-disable */

"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import { useContext, useEffect, useRef, useState } from "react";
import { ChatContext } from "../../contexts/ChatContext";
import CitationBubble from "./CitationBubble";
import { visit } from "unist-util-visit";
import { Element, Root } from "hast";
import mermaid from "mermaid";

interface MarkdownFormatProps {
  text?: string;
  variant?: "primary" | "secondary" | "highlight";
  ref_ids?: string[];
}

const MarkdownFormat: React.FC<MarkdownFormatProps> = ({
  text,
  variant = "primary",
  ref_ids = [],
}) => {
  const { getCitationPreview } = useContext(ChatContext);

  // Filter ref_ids to only include those with valid citation previews
  const validRefIds = ref_ids.filter(
    (ref_id) => getCitationPreview(ref_id) !== null
  );

  // Create citation markers map for quick lookup (only for valid citations)
  const citationMap = new Map<number, string>();
  validRefIds.forEach((ref_id, index) => {
    citationMap.set(index + 1, ref_id);
  });

  // Custom rehype plugin to convert citation markers to CitationBubble components
  const rehypeCitations = () => {
    return (tree: Root) => {
      visit(tree, "text", (node, index, parent) => {
        if (!node.value || !parent || typeof index !== "number") return;

        const citationRegex = /\[(\d+)\]/g;
        const matches = [...node.value.matchAll(citationRegex)];

        if (matches.length === 0) return;

        const newNodes: (Element | { type: "text"; value: string })[] = [];
        let lastIndex = 0;

        matches.forEach((match) => {
          const fullMatch = match[0];
          const citationNumber = parseInt(match[1]);
          const matchIndex = match.index!;

          // Add text before the citation
          if (matchIndex > lastIndex) {
            newNodes.push({
              type: "text",
              value: node.value.slice(lastIndex, matchIndex),
            });
          }

          // Get the ref_id for this citation number
          const ref_id = citationMap.get(citationNumber);
          if (ref_id) {
            const citationPreview = getCitationPreview(ref_id);
            if (citationPreview) {
              // Create a span element with citation data
              newNodes.push({
                type: "element",
                tagName: "span",
                properties: {
                  "data-citation": "true",
                  "data-ref-id": ref_id,
                  "data-citation-number": citationNumber.toString(),
                },
                children: [],
              } as Element);
            } else {
              // Safety fallback: if no preview found (shouldn't happen since we pre-filter), keep the original text
              newNodes.push({
                type: "text",
                value: fullMatch,
              });
            }
          } else {
            // Safety fallback: if no ref_id found (shouldn't happen since we pre-filter), keep the original text
            newNodes.push({
              type: "text",
              value: fullMatch,
            });
          }

          lastIndex = matchIndex + fullMatch.length;
        });

        // Add remaining text after the last citation
        if (lastIndex < node.value.length) {
          newNodes.push({
            type: "text",
            value: node.value.slice(lastIndex),
          });
        }

        // Replace the original text node with the new nodes
        parent.children.splice(index, 1, ...newNodes);
      });
    };
  };

  // Add citation markers to the text (only for valid citations)
  const processTextWithCitations = (
    originalText: string,
    validRefIds: string[]
  ): string => {
    if (!validRefIds || validRefIds.length === 0) {
      return originalText;
    }

    // For now, append citations at the end. In the future, you might want to
    // integrate them more intelligently based on content analysis
    let processedText = originalText;

    // Add citation markers at the end of sentences or key points
    // This is a simple implementation - you could make this more sophisticated
    validRefIds.forEach((_, index) => {
      const citationMarker = `[${index + 1}]`;
      // For now, just append all citations at the end
      if (index === 0) {
        processedText += " ";
      }
      processedText += citationMarker;
      if (index < validRefIds.length - 1) {
        processedText += " ";
      }
    });

    return processedText;
  };

  // Initialize Mermaid on component mount
  useEffect(() => {
    mermaid.initialize({
      startOnLoad: false,
      theme: "default",
      securityLevel: "loose",
    });
  }, []);

  // Custom code component for Mermaid rendering
  const MermaidCode = ({ inline, className, children, ...props }: any) => {
    const [svg, setSvg] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);
    const idRef = useRef(`mermaid-${Math.random().toString(36).substr(2, 9)}`);

    const isMermaid = className && /^language-mermaid/.test(className.toLowerCase());

    useEffect(() => {
      if (!isMermaid || inline || !children) {
        return;
      }

      const code = String(children).replace(/\n$/, "");
      
      mermaid
        .render(idRef.current, code)
        .then(({ svg: renderedSvg }) => {
          setSvg(renderedSvg);
          setError(null);
        })
        .catch((err) => {
          console.error("Mermaid rendering error:", err);
          setError(err.message || "Failed to render Mermaid diagram");
          setSvg(null);
        });
    }, [isMermaid, inline, children]);

    if (inline || !isMermaid) {
      return <code className={className} {...props}>{children}</code>;
    }

    if (error) {
      return (
        <div className="mermaid-container my-4 p-4 bg-red-50 border border-red-200 rounded">
          <pre className="text-red-600 text-sm">Mermaid Error: {error}</pre>
        </div>
      );
    }

    if (svg) {
      return (
        <div 
          className="mermaid-container my-4 flex justify-center"
          dangerouslySetInnerHTML={{ __html: svg }}
        />
      );
    }

    return (
      <div className="mermaid-container my-4 p-4 bg-gray-50 border border-gray-200 rounded">
        <div className="text-gray-500 text-sm">Loading diagram...</div>
      </div>
    );
  };

  // Custom component renderer for citation spans
  const components = {
    // eslint-disable-next-line @typescript-eslint/no-unused-vars

    span: ({ node, ...props }: any) => {
      if (props["data-citation"] === "true") {
        const refId = props["data-ref-id"];
        const citationPreview = getCitationPreview(refId);

        if (!citationPreview) {
          // Safety fallback: shouldn't happen since we pre-filter citations
          return null;
        }

        return <CitationBubble citationPreview={citationPreview} />;
      }

      return <span {...props} />;
    },
    code: MermaidCode,
  };

  const paragraph_class = `${
    variant === "primary"
      ? "prose-p:text-primary"
      : variant === "secondary"
        ? "prose-p:text-secondary"
        : "prose-p:text-highlight"
  } prose-p:leading-relaxed prose-p:my-2`;
  const img_class = "prose-img:max-w-full prose-img:h-auto";
  const strong_class = "prose-strong:text-primary prose-strong:font-bold";
  const a_class = "prose-a:text-primary";
  const heading_class =
    "prose-headings:text-primary prose-headings:text-xl prose-headings:font-heading prose-headings:font-bold";
  const ol_class =
    "prose-ol:text-primary prose-ol:text-base prose-ol:font-light";
  const ul_class =
    "prose-ul:text-primary prose-ul:text-base prose-ul:font-normal";
  const code_class = `${
    variant === "primary"
      ? "prose-code:text-accent"
      : "prose-code:text-secondary"
  } prose-code:font-mono prose-code:text-sm prose-code:font-normal`;
  const pre_class =
    "prose-pre:bg-background_alt prose-pre:p-4 prose-pre:text-sm prose-pre:font-light prose-pre:w-full prose-pre:my-2";

  // TODO: Figure out how to add some stripy colors to the table
  const table_class =
    "prose-table:text-primary prose-th:text-primary prose-td:text-primary prose-table:border-0";

  const processedText = processTextWithCitations(
    text?.trim() || "",
    validRefIds
  );

  if (!text) {
    return null;
  }

  return (
    <div
      className={`markdown-container flex-grow justify-start items-start text-wrap prose max-w-none prose:w-full break-words ${paragraph_class} ${img_class} ${strong_class} ${a_class} ${heading_class} ${ol_class} ${ul_class} ${code_class} ${pre_class} ${table_class}`}
    >
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight, rehypeCitations]}
        components={components}
      >
        {processedText}
      </ReactMarkdown>
    </div>
  );
};

export default MarkdownFormat;

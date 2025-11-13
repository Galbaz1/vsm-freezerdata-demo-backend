import React, { useContext } from "react";
import { ResultPayload } from "@/app/types/chat";
import {
  ProductPayload,
  ThreadPayload,
  SingleMessagePayload,
  AggregationPayload,
  DocumentPayload,
  TicketPayload,
} from "@/app/types/displays";

import TicketsDisplay from "./displays/Ticket/TicketDisplay";
import ProductDisplay from "./displays/Product/ProductDisplay";
import ThreadDisplay from "./displays/MessageThread/ThreadDisplay";
import SingleMessageDisplay from "./displays/MessageThread/SingleMessageDisplay";
import BoringGenericDisplay from "./displays/Generic/BoringGeneric";
import AggregationDisplay from "./displays/ChartTable/AggregationDisplay";
import DocumentDisplay from "./displays/Document/DocumentDisplay";
import BarDisplay from "./displays/ChartTable/BarDisplay";
import ScatterOrLineDisplay from "./displays/ChartTable/ScatterOrLineDisplay";
import HistogramDisplay from "./displays/ChartTable/HistogramDisplay";
import AreaDisplay from "./displays/ChartTable/AreaDisplay";
import PieDisplay from "./displays/ChartTable/PieDisplay";
import RadialBarDisplay from "./displays/ChartTable/RadialBarDisplay";
import ComposedDisplay from "./displays/ChartTable/ComposedDisplay";
import RadarDisplay from "./displays/ChartTable/RadarDisplay";
import FunnelDisplay from "./displays/ChartTable/FunnelDisplay";
import TreemapDisplay from "./displays/ChartTable/TreemapDisplay";
import ImageGalleryDisplay, { ImagePayload } from "./displays/Image/ImageGalleryDisplay";
import { DisplayContext } from "../contexts/DisplayContext";

interface RenderDisplayProps {
  payload: ResultPayload;
  index: number;
  messageId: string;
  handleResultPayloadChange: (
    type: string,
    payload: /* eslint-disable @typescript-eslint/no-explicit-any */ any,
    collection_name: string
  ) => void;
}

const RenderDisplay: React.FC<RenderDisplayProps> = ({
  payload,
  index,
  messageId,
  handleResultPayloadChange,
}) => {
  const keyBase = `${index}-${messageId}`;
  const { currentCollectionName } = useContext(DisplayContext);

  const handleResultPayloadChangeWithCollectionName = (
    type: string,
    payload: /* eslint-disable @typescript-eslint/no-explicit-any */ any
  ) => {
    handleResultPayloadChange(type, payload, currentCollectionName);
  };

  switch (payload.type) {
    case "ticket":
      return (
        <TicketsDisplay
          key={`${keyBase}-tickets`}
          tickets={payload.objects as TicketPayload[]}
          handleResultPayloadChange={
            handleResultPayloadChangeWithCollectionName
          }
        />
      );
    case "product":
    case "ecommerce":
      return (
        <ProductDisplay
          key={`${keyBase}-product`}
          products={payload.objects as ProductPayload[]}
          handleResultPayloadChange={
            handleResultPayloadChangeWithCollectionName
          }
        />
      );
    case "conversation":
      return (
        <ThreadDisplay
          key={`${keyBase}-conversation`}
          payload={payload.objects as ThreadPayload[]}
          handleResultPayloadChange={
            handleResultPayloadChangeWithCollectionName
          }
        />
      );
    case "message":
      return (
        <SingleMessageDisplay
          key={`${keyBase}-message`}
          payload={payload.objects as SingleMessagePayload[]}
        />
      );
    case "table":
    case "mapped":
      return (
        <BoringGenericDisplay
          key={`${keyBase}-boring-generic`}
          payload={payload.objects as { [key: string]: string }[]}
        />
      );
    case "aggregation":
      return (
        <AggregationDisplay
          key={`${keyBase}-aggregation`}
          aggregation={payload.objects as AggregationPayload[]}
        />
      );
    case "document":
      return (
        <DocumentDisplay
          key={`${keyBase}-document`}
          payload={payload.objects as DocumentPayload[]}
          handleResultPayloadChange={
            handleResultPayloadChangeWithCollectionName
          }
        />
      );
    case "bar_chart":
      return <BarDisplay key={`${keyBase}-chart`} result={payload} />;
    case "scatter_or_line_chart":
      return <ScatterOrLineDisplay key={`${keyBase}-chart`} result={payload} />;
    case "histogram_chart":
      return <HistogramDisplay key={`${keyBase}-chart`} result={payload} />;
    case "area_chart":
      return <AreaDisplay key={`${keyBase}-chart`} result={payload} />;
    case "pie_chart":
      return <PieDisplay key={`${keyBase}-chart`} result={payload} />;
    case "radial_bar_chart":
      return <RadialBarDisplay key={`${keyBase}-chart`} result={payload} />;
    case "composed_chart":
      return <ComposedDisplay key={`${keyBase}-chart`} result={payload} />;
    case "radar_chart":
      return <RadarDisplay key={`${keyBase}-chart`} result={payload} />;
    case "funnel_chart":
      return <FunnelDisplay key={`${keyBase}-chart`} result={payload} />;
    case "treemap_chart":
      return <TreemapDisplay key={`${keyBase}-chart`} result={payload} />;
    case "image_gallery":
      return (
        <ImageGalleryDisplay
          key={`${keyBase}-image-gallery`}
          images={payload.objects as ImagePayload[]}
        />
      );
    default:
      if (process.env.NODE_ENV === "development") {
        console.warn("Unhandled ResultPayload type:", payload.type);
      }
      return null;
  }
};

export default RenderDisplay;

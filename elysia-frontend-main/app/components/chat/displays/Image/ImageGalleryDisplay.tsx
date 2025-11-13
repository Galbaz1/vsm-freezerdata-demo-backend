"use client";

import React from "react";
import Image from "next/image";

export interface ImagePayload {
  image_id: string;
  image_url: string;
  image_description: string;
  manual_name: string;
  page_number: number;
  component_tags?: string[];
  smido_tags?: string[];
}

interface ImageGalleryDisplayProps {
  images: ImagePayload[];
}

const ImageGalleryDisplay: React.FC<ImageGalleryDisplayProps> = ({ images }) => {
  if (!images || images.length === 0) {
    return null;
  }

  return (
    <div className="w-full flex flex-col gap-4 fade-in">
      <div className="flex items-center gap-2">
        <p className="text-lg font-semibold">
          {images.length} Manual Image{images.length > 1 ? "s" : ""}
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {images.map((img) => (
          <div
            key={img.image_id}
            className="border border-border rounded-lg p-3 flex flex-col gap-3 hover:border-primary transition-all"
          >
            {/* Image */}
            <div className="relative w-full h-64 bg-background rounded overflow-hidden">
              <Image
                src={img.image_url}
                alt={img.image_description}
                fill
                className="object-contain"
                unoptimized // For localhost images
              />
            </div>

            {/* Description */}
            <div className="flex flex-col gap-2">
              <p className="text-sm text-foreground">
                {img.image_description}
              </p>

              {/* Metadata */}
              <div className="flex flex-wrap gap-2 items-center text-xs text-muted-foreground">
                <span className="bg-secondary px-2 py-1 rounded">
                  {img.manual_name}
                </span>
                <span>p. {img.page_number}</span>

                {/* Component tags */}
                {img.component_tags && img.component_tags.length > 0 && (
                  <div className="flex gap-1">
                    {img.component_tags.slice(0, 3).map((tag) => (
                      <span
                        key={tag}
                        className="bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 px-2 py-0.5 rounded text-xs"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                )}

                {/* SMIDO tags */}
                {img.smido_tags && img.smido_tags.length > 0 && (
                  <div className="flex gap-1">
                    {img.smido_tags.slice(0, 2).map((tag) => (
                      <span
                        key={tag}
                        className="bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 px-2 py-0.5 rounded text-xs"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ImageGalleryDisplay;


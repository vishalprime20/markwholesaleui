"use client";

import { withBase } from "@/lib/basePath";
import type { ImageProps } from "next/image";
import { useSyncExternalStore } from "react";

type Props = Omit<ImageProps, "src"> & { src: string };

function subscribe() {
  return () => {};
}

function clientBaseAwareSrc(src: string) {
  return withBase(src);
}

function serverSrc(src: string) {
  return withBase(src);
}

/**
 * Native img so GitHub Pages (basePath /markwholesaleui) is applied.
 * next/image unoptimized does not prefix /media paths.
 *
 * useSyncExternalStore re-reads window.location after hydrate so a missed
 * NEXT_PUBLIC_BASE_PATH at build still gets /markwholesaleui in the browser.
 */
export function MediaImage({
  src,
  alt,
  width,
  height,
  className,
  sizes,
  priority,
  fill,
  style,
}: Props) {
  const resolved = useSyncExternalStore(
    subscribe,
    () => clientBaseAwareSrc(src),
    () => serverSrc(src),
  );

  if (fill) {
    return (
      // eslint-disable-next-line @next/next/no-img-element
      <img
        src={resolved}
        alt={alt}
        className={className}
        sizes={sizes}
        fetchPriority={priority ? "high" : undefined}
        decoding="async"
        style={{
          position: "absolute",
          inset: 0,
          width: "100%",
          height: "100%",
          ...style,
        }}
      />
    );
  }

  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src={resolved}
      alt={alt}
      width={typeof width === "number" ? width : undefined}
      height={typeof height === "number" ? height : undefined}
      className={className}
      sizes={sizes}
      fetchPriority={priority ? "high" : undefined}
      decoding="async"
      style={style}
    />
  );
}

import { withBase } from "@/lib/basePath";
import type { ImageProps } from "next/image";

/**
 * Static-export safe image: GitHub Pages basePath is applied in src.
 * next/image leaves /media paths unprefixed when unoptimized.
 */
export function MediaImage({
  src,
  alt = "",
  className = "",
  fill,
  style,
  width,
  height,
}: ImageProps) {
  const resolved = typeof src === "string" ? withBase(src) : "";
  const imgClass = fill ? `absolute inset-0 h-full w-full ${className}` : className;

  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src={resolved}
      alt={alt}
      className={imgClass}
      style={style}
      width={typeof width === "number" ? width : undefined}
      height={typeof height === "number" ? height : undefined}
      decoding="async"
    />
  );
}

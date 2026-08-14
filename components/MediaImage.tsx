import { withBase } from "@/lib/basePath";
import NextImage, { type ImageProps } from "next/image";

export function MediaImage({ src, ...props }: ImageProps) {
  const resolved = typeof src === "string" ? withBase(src) : src;
  return <NextImage src={resolved} {...props} />;
}

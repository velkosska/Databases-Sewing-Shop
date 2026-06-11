import { CameraIcon } from "./icons";

interface ImagePlaceholderProps {
  caption: string;
  /** Short label for screen readers */
  alt: string;
  className?: string;
  aspect?: "video" | "square" | "portrait" | "wide";
}

const aspectClasses = {
  video: "aspect-[4/3]",
  square: "aspect-square",
  portrait: "aspect-[3/4]",
  wide: "aspect-[16/10]",
};

export function ImagePlaceholder({
  caption,
  alt,
  className = "",
  aspect = "video",
}: ImagePlaceholderProps) {
  return (
    <div
      role="img"
      aria-label={alt}
      className={`landing-placeholder ${aspectClasses[aspect]} ${className}`}
    >
      <CameraIcon className="w-10 h-10 text-[var(--landing-accent)]/60" />
      <span className="mt-3 text-sm text-[var(--landing-muted)] text-center px-4">{caption}</span>
    </div>
  );
}

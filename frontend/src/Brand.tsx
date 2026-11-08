export default function Brand({
  compact = false,
  onNavigate,
}: {
  compact?: boolean;
  onNavigate: () => void;
}) {
  return (
    <a
      className={`brand ${compact ? "brand-compact" : ""}`}
      href="/"
      aria-label="Sampati home"
      onClick={(event) => {
        event.preventDefault();
        onNavigate();
      }}
    >
      <img
        className="brand-symbol"
        src="/artwork/sampati-emblem.png?v=b7e5b47f"
        width={48}
        height={48}
        alt=""
      />
      <span className="brand-wordmark">
        <strong>SAMPATI</strong>
        <span className="brand-devanagari" lang="hi">
          सम्पाति
        </span>
      </span>
    </a>
  );
}

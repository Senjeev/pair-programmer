import DotGrid from "../lib/DotGrid/DotGrid";
import "../lib/DotGrid/DotGrid.css";

export default function BackgroundGrid() {
  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        zIndex: -1,
        width: "100vw",
        height: "100vh",
        background: "#1d1d1eff"
      }}
    >
      <DotGrid
        dotSize={5}
        gap={15}
        baseColor="#2d2d2dff"
        activeColor="#5227FF"
        proximity={120}
        shockRadius={250}
        shockStrength={5}
        resistance={750}
        returnDuration={1.5}
      />
    </div>
  );
}

import { useEffect, useRef } from "react";

function CustomCursor() {
  const ringRef = useRef<HTMLDivElement>(null);
  const dotRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let ringX = 0;
    let ringY = 0;
    let targetX = 0;
    let targetY = 0;
    let rafId = 0;

    const handleMove = (event: MouseEvent) => {
      targetX = event.clientX;
      targetY = event.clientY;

      if (dotRef.current) {
        dotRef.current.style.left = `${targetX}px`;
        dotRef.current.style.top = `${targetY}px`;
      }
    };

    const animate = () => {
      ringX += (targetX - ringX) * 0.14;
      ringY += (targetY - ringY) * 0.14;

      if (ringRef.current) {
        ringRef.current.style.left = `${ringX}px`;
        ringRef.current.style.top = `${ringY}px`;
      }

      rafId = window.requestAnimationFrame(animate);
    };

    const hideCursor = () => {
      if (ringRef.current) ringRef.current.style.opacity = "0";
      if (dotRef.current) dotRef.current.style.opacity = "0";
    };

    const showCursor = () => {
      if (ringRef.current) ringRef.current.style.opacity = "1";
      if (dotRef.current) dotRef.current.style.opacity = "1";
    };

    const handleTouch = () => hideCursor();

    window.addEventListener("mousemove", handleMove);
    window.addEventListener("mouseenter", showCursor);
    window.addEventListener("mouseleave", hideCursor);
    window.addEventListener("touchstart", handleTouch, { passive: true });

    animate();

    return () => {
      window.removeEventListener("mousemove", handleMove);
      window.removeEventListener("mouseenter", showCursor);
      window.removeEventListener("mouseleave", hideCursor);
      window.removeEventListener("touchstart", handleTouch);
      window.cancelAnimationFrame(rafId);
    };
  }, []);

  return (
    <>
      <div className="cursor-ring" ref={ringRef} />
      <div className="cursor-dot" ref={dotRef} />
    </>
  );
}

export default CustomCursor;

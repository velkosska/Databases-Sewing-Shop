"use client";

import { useEffect, useState } from "react";

/** Returns true once the user has scrolled past the hero (navbar becomes solid cream). */
export function useNavbarSolid(threshold = 80) {
  const [solid, setSolid] = useState(false);

  useEffect(() => {
    function onScroll() {
      setSolid(window.scrollY > threshold);
    }
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, [threshold]);

  return solid;
}

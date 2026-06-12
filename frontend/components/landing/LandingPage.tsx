"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { About } from "./About";
import { ContactCTA } from "./ContactCTA";
import { LandingFooter } from "./Footer";
import { FloatingWhatsApp } from "./FloatingWhatsApp";
import { Gallery } from "./Gallery";
import { Hero } from "./Hero";
import { HowItWorks } from "./HowItWorks";
import { LandingNavbar } from "./Navbar";
import { Services } from "./Services";
import { TrustSection } from "./TrustSection";
import { ValueProps } from "./ValueProps";
import { scrollToId } from "./scroll";

export function LandingPage() {
  const router = useRouter();

  useEffect(() => {
    const hash = window.location.hash.replace(/^#/, "");
    if (!hash) return;
    const timer = window.setTimeout(() => scrollToId(hash), 100);
    return () => window.clearTimeout(timer);
  }, []);

  function handleOrderClick() {
    router.push("/presupuesto");
  }

  return (
    <>
      <LandingNavbar onOrderClick={handleOrderClick} />
      <main>
        <Hero onOrderClick={handleOrderClick} />
        <ValueProps />
        <Services />
        <HowItWorks />
        <TrustSection />
        <About />
        <Gallery />
        <ContactCTA onOrderClick={handleOrderClick} />
      </main>
      <LandingFooter />
      <FloatingWhatsApp />
    </>
  );
}

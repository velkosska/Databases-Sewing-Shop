"use client";

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

export function LandingPage() {
  const router = useRouter();

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

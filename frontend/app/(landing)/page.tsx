import type { Metadata } from "next";
import { LandingPage } from "@/components/landing/LandingPage";

export const metadata: Metadata = {
  title: "Costuras de Paqui — Arreglos y confecciones en Madrid",
  description:
    "Dale una segunda oportunidad a tu ropa. Arreglos, confecciones a medida y transformaciones con trato cercano en Madrid.",
};

export default function HomePage() {
  return <LandingPage />;
}

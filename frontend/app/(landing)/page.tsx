import type { Metadata } from "next";
import { LandingPage } from "@/components/landing/LandingPage";

export const metadata: Metadata = {
  title: "Costuras de Paqui — Arreglos y transformaciones en Madrid",
  description:
    "Dale una segunda oportunidad a tu ropa. Arreglos, bordados, ropa de hogar, motoristas y tintorería con trato cercano en Madrid.",
};

export default function HomePage() {
  return <LandingPage />;
}

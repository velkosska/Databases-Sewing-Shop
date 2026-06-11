"use client";

import Link from "next/link";

interface PresupuestoModalProps {
  open: boolean;
  onClose: () => void;
}

export function PresupuestoModal({ open, onClose }: PresupuestoModalProps) {
  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby="presupuesto-modal-title"
      onClick={onClose}
    >
      <div
        className="w-full max-w-md rounded-2xl bg-[var(--landing-cream)] p-8 shadow-xl ring-1 ring-[var(--landing-border)]"
        onClick={(e) => e.stopPropagation()}
      >
        <h3
          id="presupuesto-modal-title"
          className="font-[family-name:var(--font-playfair)] text-2xl text-[var(--landing-ink)]"
        >
          Presupuesto en camino
        </h3>
        <p className="mt-4 text-[var(--landing-muted)] leading-relaxed">
          Estamos preparando un formulario sencillo para que pidas presupuesto sin salir de la web. Por ahora,
          escríbenos por WhatsApp o llámanos — te atendemos personalmente.
        </p>
        <div className="mt-8 flex flex-col gap-3 sm:flex-row">
          <Link href="/presupuesto" className="landing-btn landing-btn--primary min-h-12 flex-1 text-center" onClick={onClose}>
            Hacer pedido
          </Link>
          <button type="button" onClick={onClose} className="landing-btn landing-btn--ghost min-h-12 flex-1">
            Cerrar
          </button>
        </div>
      </div>
    </div>
  );
}

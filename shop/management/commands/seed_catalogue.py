"""Seed default catalogue services for Costuras de Paqui (idempotent)."""

from decimal import Decimal

from django.core.management.base import BaseCommand

from shop.models import CatalogueItem

# Matches frontend/components/landing/constants.ts SERVICES
DEFAULT_CATALOGUE = [
    {
        "name": "Arreglos de ropa",
        "garment_types": ["Pantalón", "Vestido", "Chaqueta", "Falda", "Camisa", "Abrigo"],
        "base_price": Decimal("25.00"),
        "price_hint": "Precio base — ajustar según el arreglo",
        "requires_measurements": False,
    },
    {
        "name": "Arreglo de prendas de motoristas",
        "garment_types": ["Chaqueta", "Pantalón", "Mono", "Guantes"],
        "base_price": Decimal("45.00"),
        "price_hint": "Presupuesto según prenda y tipo de arreglo",
        "requires_measurements": False,
    },
    {
        "name": "Cambios de cremalleras",
        "garment_types": ["Pantalón", "Chaqueta", "Falda", "Bolso", "Cazadora"],
        "base_price": Decimal("18.00"),
        "price_hint": "Según tipo de cremallera y prenda",
        "requires_measurements": False,
    },
    {
        "name": "Bajos",
        "garment_types": ["Pantalón", "Falda", "Vestido", "Chaqueta"],
        "base_price": Decimal("12.00"),
        "price_hint": "Según tipo de prenda y acabado",
        "requires_measurements": False,
    },
    {
        "name": "Reducción de tallas",
        "garment_types": ["Pantalón", "Vestido", "Chaqueta", "Blusa", "Traje"],
        "base_price": Decimal("30.00"),
        "price_hint": "Según prenda y trabajo necesario",
        "requires_measurements": True,
    },
    {
        "name": "Modificación de ropa de hogar",
        "garment_types": ["Cortina", "Cojín", "Mantel", "Funda", "Estor"],
        "base_price": Decimal("35.00"),
        "price_hint": "Según pieza y tipo de modificación",
        "requires_measurements": True,
    },
    {
        "name": "Bordados",
        "garment_types": ["Camisa", "Chaqueta", "Toalla", "Prenda infantil", "Textil hogar"],
        "base_price": Decimal("20.00"),
        "price_hint": "Según diseño y tamaño",
        "requires_measurements": False,
    },
    {
        "name": "Tintorería",
        "garment_types": ["Prenda"],
        "base_price": Decimal("15.00"),
        "price_hint": "Según tipo de prenda",
        "requires_measurements": False,
    },
]

# Retired services (confección removed — Paqui does not offer made-to-order)
REMOVED_CATALOGUE_NAMES = [
    "Confección a medida",
    "Cortinas",
    "Ropa de hogar",
    "Ropa de motoristas",
]


class Command(BaseCommand):
    help = "Ensure default catalogue services exist (safe to run on every deploy)."

    def handle(self, *args, **options):
        created = 0
        updated = 0
        for entry in DEFAULT_CATALOGUE:
            _, was_created = CatalogueItem.objects.update_or_create(
                name=entry["name"],
                defaults={
                    "garment_types": entry["garment_types"],
                    "base_price": entry["base_price"],
                    "price_hint": entry["price_hint"],
                    "requires_measurements": entry["requires_measurements"],
                },
            )
            if was_created:
                created += 1
            else:
                updated += 1

        removed, _ = CatalogueItem.objects.filter(name__in=REMOVED_CATALOGUE_NAMES).delete()

        total = CatalogueItem.objects.count()
        self.stdout.write(
            self.style.SUCCESS(
                f"Catalogue ready: {total} item(s) ({created} created, {updated} updated, {removed} removed)."
            )
        )

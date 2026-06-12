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
        "name": "Confección a medida",
        "garment_types": ["Vestido", "Traje", "Blusa", "Pantalón", "Falda", "Chaqueta"],
        "base_price": Decimal("80.00"),
        "price_hint": "Presupuesto según prenda y tejido",
        "requires_measurements": True,
    },
    {
        "name": "Cortinas",
        "garment_types": ["Cortina salón", "Cortina dormitorio", "Estor"],
        "base_price": Decimal("60.00"),
        "price_hint": "Según medidas y tejido",
        "requires_measurements": True,
    },
    {
        "name": "Ropa de hogar",
        "garment_types": ["Mantel", "Funda", "Cojín", "Cortina"],
        "base_price": Decimal("45.00"),
        "price_hint": "Según medidas y tejido",
        "requires_measurements": True,
    },
    {
        "name": "Ropa de motoristas",
        "garment_types": ["Chaqueta", "Pantalón", "Mono"],
        "base_price": Decimal("70.00"),
        "price_hint": "Arreglo o confección — presupuesto según trabajo",
        "requires_measurements": True,
    },
    {
        "name": "Tintorería",
        "garment_types": ["Prenda"],
        "base_price": Decimal("15.00"),
        "price_hint": "Según tipo de prenda",
        "requires_measurements": False,
    },
]


class Command(BaseCommand):
    help = "Ensure default catalogue services exist (safe to run on every deploy)."

    def handle(self, *args, **options):
        created = 0
        for entry in DEFAULT_CATALOGUE:
            _, was_created = CatalogueItem.objects.get_or_create(
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

        total = CatalogueItem.objects.count()
        self.stdout.write(
            self.style.SUCCESS(
                f"Catalogue ready: {total} item(s) ({created} newly created)."
            )
        )
